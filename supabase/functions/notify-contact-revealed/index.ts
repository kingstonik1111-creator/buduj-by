// BUDUJ.BY — Edge Function: мастеру открыли контакт
//
// Вызывается через Database Webhook при INSERT в revealed_contacts.
//   Supabase → Database → Webhooks → Create:
//   Table: revealed_contacts | Events: INSERT | Type: Supabase Edge Functions
//   Function: notify-contact-revealed
//
// Зачем: это единственный момент, когда подписка доказывает себя.
// Раньше мастер о нём не узнавал — платил и сидел в тишине, даже когда
// всё работало. По этому же событию считается гарантия, то есть мастер
// не видел того, от чего зависят его деньги.
//
// Секреты: TELEGRAM_BOT_TOKEN

import { serve } from 'https://deno.land/std@0.168.0/http/server.ts'
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

const TG_TOKEN = Deno.env.get('TELEGRAM_BOT_TOKEN') ?? ''
const SITE_URL = 'https://buduj.by'

function serviceKey(): string {
  const legacy = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')
  if (legacy) return legacy
  try {
    const parsed = JSON.parse(Deno.env.get('SUPABASE_SECRET_KEYS') ?? '{}')
    const first = Object.values(parsed).find(v => typeof v === 'string' && v.length > 20)
    if (first) return first as string
  } catch (_) { /* формат изменился */ }
  throw new Error('Нет сервисного ключа')
}

async function sendTelegram(chatId: string, text: string) {
  if (!TG_TOKEN || !chatId) return
  await fetch(`https://api.telegram.org/bot${TG_TOKEN}/sendMessage`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      chat_id: chatId,
      text,
      parse_mode: 'HTML',
      reply_markup: {
        inline_keyboard: [[
          { text: '📋 Мои отклики', url: `${SITE_URL}/dashboard.html` }
        ]]
      }
    }),
  })
}

serve(async (req) => {
  try {
    const body = await req.json()
    const rec = body.record ?? body
    if (!rec?.master_id) {
      return new Response(JSON.stringify({ ok: true, skipped: true }), {
        headers: { 'Content-Type': 'application/json' }
      })
    }

    const sb = createClient(Deno.env.get('SUPABASE_URL')!, serviceKey())

    const { data: master } = await sb
      .from('profiles')
      .select('name, telegram_chat_id')
      .eq('id', rec.master_id)
      .single()

    if (!master?.telegram_chat_id) {
      return new Response(JSON.stringify({ ok: true, notified: 0, reason: 'нет telegram' }), {
        headers: { 'Content-Type': 'application/json' }
      })
    }

    // Заголовок заказа — чтобы мастер понял, о какой работе речь
    let orderTitle = ''
    if (rec.order_id) {
      const { data: o } = await sb
        .from('orders').select('title, city').eq('id', rec.order_id).single()
      if (o) orderTitle = `\n\n📋 ${o.title}${o.city ? ` · ${o.city}` : ''}`
    }

    await sendTelegram(master.telegram_chat_id,
      `📞 <b>Заказчик открыл ваш контакт</b>${orderTitle}\n\n` +
      `Скорее всего он позвонит или напишет в ближайшее время — ` +
      `держите телефон под рукой.\n\n` +
      `Кто отвечает первым, тот обычно и получает работу.`
    )

    return new Response(JSON.stringify({ ok: true, notified: 1 }), {
      headers: { 'Content-Type': 'application/json' }
    })
  } catch (err) {
    console.error('notify-contact-revealed:', err)
    return new Response(JSON.stringify({ ok: false, error: String(err) }), {
      status: 500, headers: { 'Content-Type': 'application/json' }
    })
  }
})
