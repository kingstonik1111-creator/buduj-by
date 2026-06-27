// BUDUJ.BY — Edge Function: создание платежа BePaid
// Вызывается из dashboard.html когда мастер нажимает "Оплатить подписку"
// Возвращает URL страницы оплаты BePaid
//
// Секреты (Supabase → Settings → Edge Functions → Secrets):
//   BEPAID_SHOP_ID    — ID магазина (число, из личного кабинета bepaid.by)
//   BEPAID_SECRET_KEY — секретный ключ

import { serve } from 'https://deno.land/std@0.168.0/http/server.ts'
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

const SHOP_ID     = Deno.env.get('BEPAID_SHOP_ID') ?? ''
const SECRET_KEY  = Deno.env.get('BEPAID_SECRET_KEY') ?? ''
const BEPAID_URL  = 'https://checkout.bepaid.by/ctp/api/checkouts'
const SITE_URL    = 'https://buduj.by'

const PLANS: Record<string, { name: string; amount: number }> = {
  basic: { name: 'Базовый',  amount: 2500  }, // 25 BYN в копейках
  pro:   { name: 'Профи ⭐', amount: 6000  }, // 60 BYN
  biz:   { name: 'Бизнес',   amount: 12500 }, // 125 BYN
}

const CORS = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, content-type',
}

serve(async (req) => {
  if (req.method === 'OPTIONS') return new Response('ok', { headers: CORS })

  try {
    // Проверяем авторизацию — только залогиненные мастера
    const sb = createClient(
      Deno.env.get('SUPABASE_URL')!,
      Deno.env.get('SUPABASE_ANON_KEY')!,
      { global: { headers: { Authorization: req.headers.get('Authorization') ?? '' } } }
    )

    const { data: { user }, error: authErr } = await sb.auth.getUser()
    if (authErr || !user) {
      return new Response(JSON.stringify({ error: 'Unauthorized' }), {
        status: 401, headers: { ...CORS, 'Content-Type': 'application/json' }
      })
    }

    const { plan } = await req.json()
    const planData = PLANS[plan]
    if (!planData) {
      return new Response(JSON.stringify({ error: 'Invalid plan' }), {
        status: 400, headers: { ...CORS, 'Content-Type': 'application/json' }
      })
    }

    // Получаем профиль мастера (email для BePaid)
    const sbAdmin = createClient(
      Deno.env.get('SUPABASE_URL')!,
      Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!
    )
    const { data: profile } = await sbAdmin
      .from('profiles')
      .select('name, phone, auth_email')
      .eq('id', user.id)
      .single()

    // tracking_id: UUID:plan — по нему вебхук поймёт кому продлить подписку
    const trackingId = `${user.id}:${plan}`

    const payload = {
      checkout: {
        test: false, // поменяй на true для тестовых платежей
        transaction_type: 'payment',
        attempts: 3,
        settings: {
          success_url: `${SITE_URL}/dashboard.html?payment=success&plan=${plan}`,
          fail_url:    `${SITE_URL}/dashboard.html?payment=fail`,
          notification_url: `${Deno.env.get('SUPABASE_URL')}/functions/v1/bepaid-webhook`,
          language: 'ru',
        },
        order: {
          currency: 'BYN',
          amount: planData.amount,
          description: `Подписка BUDUJ.BY — ${planData.name} (1 месяц)`,
          tracking_id: trackingId,
        },
        customer: {
          email: profile?.auth_email ?? user.email ?? '',
          phone: profile?.phone ?? '',
          first_name: (profile?.name ?? '').split(' ')[0] ?? '',
          last_name: (profile?.name ?? '').split(' ')[1] ?? '',
        },
      }
    }

    const auth = btoa(`${SHOP_ID}:${SECRET_KEY}`)
    const resp = await fetch(BEPAID_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Basic ${auth}`,
        'Accept': 'application/json',
      },
      body: JSON.stringify(payload),
    })

    const data = await resp.json()

    if (!resp.ok || !data.checkout?.redirect_url) {
      console.error('BePaid error:', JSON.stringify(data))
      return new Response(JSON.stringify({ error: 'Ошибка создания платежа', details: data }), {
        status: 500, headers: { ...CORS, 'Content-Type': 'application/json' }
      })
    }

    return new Response(JSON.stringify({ url: data.checkout.redirect_url }), {
      headers: { ...CORS, 'Content-Type': 'application/json' }
    })

  } catch (err) {
    return new Response(JSON.stringify({ error: String(err) }), {
      status: 500, headers: { ...CORS, 'Content-Type': 'application/json' }
    })
  }
})
