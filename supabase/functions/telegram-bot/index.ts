// BUDUJ.BY — Telegram Bot Webhook
// Мастер нажимает "Подключить Telegram" в кабинете → переходит в бота с deep link
// Бот получает /start UUID → сохраняет telegram_chat_id в profiles → отправляет подтверждение
//
// После деплоя нужно зарегистрировать webhook:
//   https://api.telegram.org/bot<TOKEN>/setWebhook?url=https://inhlhqzavjtghechstzb.supabase.co/functions/v1/telegram-bot
//
// Секреты (Supabase → Settings → Edge Functions → Secrets):
//   TELEGRAM_BOT_TOKEN — токен от @BotFather

import { serve } from 'https://deno.land/std@0.168.0/http/server.ts'
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

const TG_TOKEN = Deno.env.get('TELEGRAM_BOT_TOKEN') ?? ''

async function sendTg(chatId: number, text: string, keyboard?: object) {
  const payload: Record<string, unknown> = { chat_id: chatId, text, parse_mode: 'HTML' }
  if (keyboard) payload.reply_markup = keyboard
  await fetch(`https://api.telegram.org/bot${TG_TOKEN}/sendMessage`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
}

serve(async (req) => {
  try {
    const body = await req.json()
    const msg = body.message
    if (!msg) return new Response('ok')

    const chatId: number = msg.chat.id
    const text: string = msg.text || ''
    const firstName: string = msg.from?.first_name || ''

    // /start [UUID] — привязка аккаунта
    if (text.startsWith('/start')) {
      const parts = text.split(' ')
      const masterId = parts[1]?.trim()

      // Без UUID — просто приветствие
      if (!masterId || masterId.length < 30) {
        await sendTg(chatId,
          `👋 Привет, ${firstName}!\n\n` +
          `Я бот <b>BUDUJ.BY</b> — площадки строительных мастеров Беларуси.\n\n` +
          `Чтобы подключить уведомления о новых заказах, перейдите в личный кабинет на сайте и нажмите кнопку <b>«Подключить Telegram»</b>.`
        )
        return new Response('ok')
      }

      const sb = createClient(
        Deno.env.get('SUPABASE_URL')!,
        Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!
      )

      // Проверяем что мастер существует
      const { data: profile, error } = await sb
        .from('profiles')
        .select('id, name, city, role')
        .eq('id', masterId)
        .eq('role', 'master')
        .single()

      if (error || !profile) {
        await sendTg(chatId,
          `❌ Аккаунт не найден.\n\n` +
          `Убедитесь, что вы авторизованы в личном кабинете и повторите попытку.`
        )
        return new Response('ok')
      }

      // Сохраняем chat_id
      await sb
        .from('profiles')
        .update({ telegram_chat_id: String(chatId) })
        .eq('id', masterId)

      const masterName = profile.name || firstName || 'Мастер'
      const city = profile.city || 'вашем городе'

      await sendTg(chatId,
        `✅ <b>Уведомления подключены!</b>\n\n` +
        `Привет, ${masterName}! 👋\n\n` +
        `Теперь я буду сообщать вам о новых заказах в <b>${city}</b> — как только клиент создаст заказ, я сразу напишу сюда.\n\n` +
        `🔔 Оставайтесь на связи — удачи в работе!`,
        {
          inline_keyboard: [[
            { text: '📋 Открыть кабинет', url: 'https://buduj.by/dashboard.html' }
          ]]
        }
      )

      return new Response('ok')
    }

    // Любое другое сообщение
    await sendTg(chatId,
      `👋 Привет!\n\nЯ бот <b>BUDUJ.BY</b>. Я уведомляю мастеров о новых заказах.\n\n` +
      `Если вы мастер и хотите получать уведомления — войдите в кабинет на сайте и нажмите <b>«Подключить Telegram»</b>.`,
      {
        inline_keyboard: [[
          { text: '🏗 Открыть BUDUJ.BY', url: 'https://buduj.by' }
        ]]
      }
    )

    return new Response('ok')
  } catch (err) {
    console.error(err)
    return new Response('error', { status: 500 })
  }
})
