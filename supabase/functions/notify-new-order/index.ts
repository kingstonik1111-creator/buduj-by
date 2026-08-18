// BUDUJ.BY — Edge Function: уведомление мастеров о новом заказе
// Вызывается через Database Webhook при INSERT в таблицу orders
//
// Суpabase → Database → Webhooks → Create Webhook:
//   Table: orders  |  Events: INSERT  |  URL: [URL этой функции]
//
// Секреты (Supabase → Settings → Edge Functions → Secrets):
//   TELEGRAM_BOT_TOKEN — токен бота от @BotFather
//   TELEGRAM_ADMIN_ID  — ваш личный chat_id (узнать у @userinfobot),
//                        чтобы копия каждой заявки приходила лично вам

import { serve } from 'https://deno.land/std@0.168.0/http/server.ts'
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

const TG_TOKEN = Deno.env.get('TELEGRAM_BOT_TOKEN') ?? ''
const ADMIN_ID = Deno.env.get('TELEGRAM_ADMIN_ID') ?? ''
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
          // Заказы теперь открыты всем — ведём прямо в список,
          // а не в кабинет, где раньше стоял замок.
          { text: '📋 Смотреть заказы', url: `${SITE_URL}/jobs.html` }
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

    // Копия администратору. Стоит выше всех проверок и фильтров:
    // владелец должен видеть каждую заявку, даже если она не подошла
    // ни одному мастеру или пришла без города. Иначе площадка молчит,
    // и о заказе узнаёшь случайно.
    if (ADMIN_ID) {
      const a = [
        `🆕 <b>Заявка на BUDUJ.BY</b>`,
        ``,
        `📋 ${order.category || 'Без категории'}`,
        `📍 ${order.city || 'город не указан'}`,
        `${(order.title || 'Без названия').substring(0, 200)}`,
        order.budget ? `💰 ${order.budget}` : ``,
        order.is_urgent ? `🔥 Срочно` : ``,
        ``,
        `👉 ${SITE_URL}/jobs.html`,
      ].filter(Boolean).join('\n')
      await sendTelegram(ADMIN_ID, a)
    }

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
      // Подписку намеренно НЕ фильтруем. Раньше уведомление уходило только
      // тем, у кого она активна, — то есть самый дешёвый канал продаж был
      // выключен: мастер без подписки о заказе не узнавал и повода платить
      // не получал. Уведомление — крючок, а не награда за оплату.
      .select('id, name, telegram_chat_id, categories, subscription_end')
      .eq('role', 'master')
      .eq('city', order.city)
      .not('telegram_chat_id', 'is', null)

    const category = order.category || 'Другое'

    // Шлём только тем, кому заказ подходит по специализации.
    // «Другое» и мастера без выбранных категорий — получают всё.
    const targets = (masters ?? []).filter((m: any) => {
      const cats = Array.isArray(m.categories) ? m.categories : []
      return cats.length === 0 || category === 'Другое' || cats.includes(category)
    })

    if (!targets.length) {
      return new Response(JSON.stringify({ ok: true, notified: 0 }), {
        headers: { 'Content-Type': 'application/json' }
      })
    }

    const title = (order.title || 'Без названия').substring(0, 160)
    const budget = order.budget ? `\n💰 Бюджет: ${order.budget}` : ''
    const urgency = order.is_urgent ? '\n🔥 Срочно!' : ''

    const head =
      `🔔 <b>Новый заказ в ${order.city}</b>\n\n` +
      `📋 <b>${category}</b>\n` +
      `${title}${title.length >= 160 ? '…' : ''}` +
      budget +
      urgency

    const now = Date.now()
    let notified = 0

    for (const master of targets) {
      const active = master.subscription_end &&
                     new Date(master.subscription_end).getTime() > now

      // Мастеру с подпиской — прямая ссылка на отклик.
      // Без подписки — тот же заказ, но с ценой ответа. Цена сравнивается
      // с конкретным заказом на экране, а не с абстракцией.
      const tail = active
        ? `\n\n👉 Откликнуться: ${SITE_URL}/jobs.html`
        : `\n\n🔓 Чтобы ответить и получить контакт заказчика — подписка от 19 BYN/мес.` +
          `\nНе получите ни одного заказа за месяц — продлим следующий бесплатно.` +
          `\n\n👉 ${SITE_URL}/dashboard.html`

      await sendTelegram(master.telegram_chat_id, head + tail)
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
