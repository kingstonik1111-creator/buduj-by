// BUDUJ.BY — Edge Function: вебхук от BePaid после оплаты
// BePaid присылает POST когда платёж прошёл успешно
// Мы обновляем subscription_plan и subscription_end в profiles
//
// Секреты:
//   BEPAID_SECRET_KEY — для проверки подписи

import { serve } from 'https://deno.land/std@0.168.0/http/server.ts'
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

const SECRET_KEY = Deno.env.get('BEPAID_SECRET_KEY') ?? ''

const PLAN_DAYS: Record<string, number> = {
  basic: 30,
  pro:   30,
  biz:   30,
}

serve(async (req) => {
  try {
    const body = await req.text()
    const data = JSON.parse(body)

    // Проверяем статус платежа
    const transaction = data.transaction
    if (!transaction) {
      return new Response('no transaction', { status: 400 })
    }

    const status = transaction.status
    if (status !== 'successful') {
      // Платёж не прошёл — ничего не делаем
      return new Response(JSON.stringify({ ok: true, skipped: true }), {
        headers: { 'Content-Type': 'application/json' }
      })
    }

    // Парсим tracking_id: "{master_uuid}:{plan}"
    const trackingId: string = transaction.tracking_id ?? ''
    const parts = trackingId.split(':')
    if (parts.length < 2) {
      return new Response('invalid tracking_id', { status: 400 })
    }

    const masterId = parts[0]
    const plan = parts[1]
    const days = PLAN_DAYS[plan] ?? 30

    const sb = createClient(
      Deno.env.get('SUPABASE_URL')!,
      Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!
    )

    // Считаем новую дату окончания подписки
    // Если у мастера ещё активная подписка — продлеваем от её конца
    const { data: profile } = await sb
      .from('profiles')
      .select('subscription_end')
      .eq('id', masterId)
      .single()

    const now = new Date()
    const currentEnd = profile?.subscription_end ? new Date(profile.subscription_end) : now
    const baseDate = currentEnd > now ? currentEnd : now
    const newEnd = new Date(baseDate.getTime() + days * 86400000)

    const { error } = await sb
      .from('profiles')
      .update({
        subscription_plan: plan,
        subscription_end: newEnd.toISOString(),
      })
      .eq('id', masterId)

    if (error) {
      console.error('Supabase update error:', error)
      return new Response(JSON.stringify({ ok: false, error: error.message }), {
        status: 500, headers: { 'Content-Type': 'application/json' }
      })
    }

    console.log(`✅ Subscription updated: master=${masterId} plan=${plan} until=${newEnd.toISOString()}`)

    return new Response(JSON.stringify({ ok: true, master: masterId, plan, until: newEnd }), {
      headers: { 'Content-Type': 'application/json' }
    })

  } catch (err) {
    console.error('Webhook error:', err)
    return new Response(JSON.stringify({ ok: false, error: String(err) }), {
      status: 500, headers: { 'Content-Type': 'application/json' }
    })
  }
})
