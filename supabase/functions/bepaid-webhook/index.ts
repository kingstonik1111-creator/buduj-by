// BUDUJ.BY — Edge Function: вебхук от bePaid после оплаты
//
// Оплата считается состоявшейся ТОЛЬКО после этого уведомления —
// возврат пользователя на success_url ничего не активирует.
//
// Защита (раньше её не было вообще: функция принимала любой POST
// и выдавала подписку тому, чей UUID был в теле):
//   1. подпись запроса — HMAC-SHA256 тела на секретном ключе магазина;
//   2. независимая перепроверка транзакции по API bePaid;
//   3. сумма сверяется с нашим прайсом, а не берётся из уведомления;
//   4. идемпотентность по uid транзакции — повтор не продлит дважды.
//
// Секреты (Supabase → Edge Functions → Secrets):
//   BEPAID_SHOP_ID    — ID магазина
//   BEPAID_SECRET_KEY — секретный ключ
//   BEPAID_STRICT     — '0' на время первой настройки (см. ниже), потом убрать

import { serve } from 'https://deno.land/std@0.168.0/http/server.ts'
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

const SHOP_ID    = Deno.env.get('BEPAID_SHOP_ID') ?? ''
const SECRET_KEY = Deno.env.get('BEPAID_SECRET_KEY') ?? ''
// STRICT=0 — не отклонять запрос без подписи, только записать в лог.
// Нужно ровно один раз: чтобы на первом тестовом платеже увидеть,
// как bePaid реально называет заголовок подписи. Потом удалить секрет.
const STRICT     = (Deno.env.get('BEPAID_STRICT') ?? '1') !== '0'

const GATEWAY = 'https://gateway.bepaid.by'

// Цены в копейках — тот же источник правды, что в create-payment.
// Сумму из уведомления не принимаем на веру: иначе можно оплатить 1 копейку
// и получить «Бизнес».
const PLANS: Record<string, number> = { basic: 1900, pro: 3900, biz: 7900 }
const PLAN_DAYS = 30

function b64(buf: ArrayBuffer): string {
  return btoa(String.fromCharCode(...new Uint8Array(buf)))
}

async function hmacBase64(body: string, key: string): Promise<string> {
  const k = await crypto.subtle.importKey(
    'raw', new TextEncoder().encode(key),
    { name: 'HMAC', hash: 'SHA-256' }, false, ['sign']
  )
  return b64(await crypto.subtle.sign('HMAC', k, new TextEncoder().encode(body)))
}

// Сравнение без утечки времени
function safeEqual(a: string, b: string): boolean {
  if (a.length !== b.length) return false
  let diff = 0
  for (let i = 0; i < a.length; i++) diff |= a.charCodeAt(i) ^ b.charCodeAt(i)
  return diff === 0
}

// Независимая проверка: спрашиваем у bePaid, что за транзакция.
// Подделать уведомление, не имея реальной транзакции, так нельзя.
async function verifyWithBepaid(uid: string) {
  if (!SHOP_ID || !SECRET_KEY) return null
  try {
    const resp = await fetch(`${GATEWAY}/transactions/${uid}`, {
      headers: {
        'Authorization': 'Basic ' + btoa(`${SHOP_ID}:${SECRET_KEY}`),
        'Accept': 'application/json',
        'X-API-Version': '2',
      },
    })
    if (!resp.ok) {
      console.error('bePaid verify HTTP', resp.status, await resp.text())
      return null
    }
    return await resp.json()
  } catch (e) {
    console.error('bePaid verify failed:', String(e))
    return null
  }
}

serve(async (req) => {
  const sb = createClient(
    Deno.env.get('SUPABASE_URL')!,
    Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!
  )

  try {
    const raw = await req.text()

    // ── 1. Подпись ────────────────────────────────────────────────
    const headers: Record<string, string> = {}
    req.headers.forEach((v, k) => { headers[k.toLowerCase()] = v })

    const sigHeader =
      headers['content-signature'] ??
      headers['x-signature'] ??
      headers['signature'] ??
      null

    if (sigHeader) {
      const expected = await hmacBase64(raw, SECRET_KEY)
      if (!safeEqual(sigHeader.trim(), expected)) {
        console.error('Подпись не совпала', { got: sigHeader })
        if (STRICT) return new Response('bad signature', { status: 401 })
      }
    } else {
      // Заголовка нет — записываем какие вообще пришли, чтобы узнать имя
      console.warn('Подписи нет. Заголовки:', JSON.stringify(headers))
      if (STRICT) return new Response('no signature', { status: 401 })
    }

    const data = JSON.parse(raw)
    const tx = data.transaction ?? data
    if (!tx?.uid) return new Response('no transaction', { status: 400 })

    // ── 2. Перепроверка у банка ───────────────────────────────────
    const verified = await verifyWithBepaid(tx.uid)
    const vtx = verified?.transaction ?? verified
    const status = (vtx?.status ?? tx.status) as string
    const amount = Number(vtx?.amount ?? tx.amount ?? 0)
    const trackingId = String(vtx?.tracking_id ?? tx.tracking_id ?? '')
    const isTest = Boolean(vtx?.test ?? tx.test ?? false)

    if (!verified && STRICT) {
      console.error('Транзакция не подтверждена банком:', tx.uid)
      return new Response('unverified', { status: 401 })
    }

    // ── 3. Разбираем tracking_id: "{uuid мастера}:{тариф}" ────────
    const [masterId, plan] = trackingId.split(':')
    const expected = PLANS[plan]

    // ── 4. Пишем в журнал. Уникальность bepaid_uid = идемпотентность
    const { error: logErr } = await sb.from('payments').insert({
      master_id: masterId || null,
      plan: plan || null,
      amount_minor: amount,
      currency: vtx?.currency ?? tx.currency ?? 'BYN',
      status,
      bepaid_uid: tx.uid,
      tracking_id: trackingId,
      test_mode: isTest,
      raw: data,
    })

    if (logErr) {
      // 23505 — такой uid уже обработан, это повтор уведомления
      if ((logErr as any).code === '23505') {
        console.log('Повтор уведомления, пропускаем:', tx.uid)
        return new Response(JSON.stringify({ ok: true, duplicate: true }), {
          headers: { 'Content-Type': 'application/json' },
        })
      }
      console.error('Не удалось записать платёж:', logErr)
    }

    // ── 5. Активируем подписку только при успехе и верной сумме ───
    if (status !== 'successful') {
      return new Response(JSON.stringify({ ok: true, skipped: status }), {
        headers: { 'Content-Type': 'application/json' },
      })
    }
    if (!masterId || !expected) {
      console.error('Непонятный tracking_id:', trackingId)
      return new Response('bad tracking_id', { status: 400 })
    }
    if (amount !== expected) {
      console.error(`Сумма не совпала: пришло ${amount}, ждали ${expected} (${plan})`)
      return new Response('amount mismatch', { status: 400 })
    }

    // Продлеваем от конца текущей подписки, если она ещё активна
    const { data: profile } = await sb
      .from('profiles').select('subscription_end').eq('id', masterId).single()

    const now = new Date()
    const cur = profile?.subscription_end ? new Date(profile.subscription_end) : now
    const base = cur > now ? cur : now
    const newEnd = new Date(base.getTime() + PLAN_DAYS * 86400000)

    const { error } = await sb.from('profiles').update({
      subscription_plan: plan,
      subscription_end: newEnd.toISOString(),
    }).eq('id', masterId)

    if (error) {
      console.error('Не удалось продлить подписку:', error)
      return new Response(JSON.stringify({ ok: false, error: error.message }), {
        status: 500, headers: { 'Content-Type': 'application/json' },
      })
    }

    console.log(`✅ Подписка продлена: мастер=${masterId} тариф=${plan} до ${newEnd.toISOString()}`)
    return new Response(JSON.stringify({ ok: true, until: newEnd }), {
      headers: { 'Content-Type': 'application/json' },
    })

  } catch (err) {
    console.error('Webhook error:', err)
    return new Response(JSON.stringify({ ok: false, error: String(err) }), {
      status: 500, headers: { 'Content-Type': 'application/json' },
    })
  }
})
