// BUDUJ.BY — Edge Function: уведомление мастеров о новом заказе
// Вызывается через Database Webhook при INSERT в таблицу orders
//
// Суpabase → Database → Webhooks → Create Webhook:
//   Table: orders  |  Events: INSERT  |  URL: [URL этой функции]
//
// Секреты (Supabase → Settings → Edge Functions → Secrets):
//   TELEGRAM_BOT_TOKEN — токен бота от @BotFather

import { serve } from 'https://deno.land/std@0.168.0/http/server.ts'
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

const TG_TOKEN = Deno.env.get('TELEGRAM_BOT_TOKEN') ?? ''
const SITE_URL = 'https://buduj.by'

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
          { text: '📋 Смотреть заказы', url: `${SITE_URL}/dashboard.html` }
        ]]
      }
    }),
  })
}

serve(async (req) => {
  try {
    const body = await req.json()

    // Database Webhook payload: { type, table, schema, record, old_record }
    const order = body.record ?? body

    if (!order?.city || order.status !== 'open') {
      return new Response(JSON.stringify({ ok: true, skipped: true }), {
        headers: { 'Content-Type': 'application/json' }
      })
    }

    const sb = createClient(
      Deno.env.get('SUPABASE_URL')!,
      Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!
    )

    // Мастера в этом городе с активной подпиской и привязанным Telegram
    const { data: masters } = await sb
      .from('profiles')
      .select('id, name, telegram_chat_id')
      .eq('role', 'master')
      .eq('city', order.city)
      .gt('subscription_end', new Date().toISOString())
      .not('telegram_chat_id', 'is', null)

    if (!masters?.length) {
      return new Response(JSON.stringify({ ok: true, notified: 0 }), {
        headers: { 'Content-Type': 'application/json' }
      })
    }

    const category = order.category || 'Другое'
    const title = (order.title || 'Без названия').substring(0, 160)
    const budget = order.budget ? `\n💰 Бюджет: ${order.budget} BYN` : ''
    const urgency = order.is_urgent ? '\n🔥 Срочно!' : ''

    const text =
      `🔔 <b>Новый заказ в ${order.city}!</b>\n\n` +
      `📋 <b>${category}</b>\n` +
      `${title}${title.length >= 160 ? '…' : ''}` +
      budget +
      urgency +
      `\n\n👉 Войдите в кабинет чтобы откликнуться`

    let notified = 0
    for (const master of masters) {
      await sendTelegram(master.telegram_chat_id, text)
      notified++
    }

    return new Response(JSON.stringify({ ok: true, notified }), {
      headers: { 'Content-Type': 'application/json' }
    })
  } catch (err) {
    return new Response(JSON.stringify({ ok: false, error: String(err) }), {
      status: 500,
      headers: { 'Content-Type': 'application/json' }
    })
  }
})
