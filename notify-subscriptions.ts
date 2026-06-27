// BUDUJ.BY — Edge Function: уведомления об истечении подписки
// Запускается каждый день в 9:00 через pg_cron
//
// Переменные среды (Supabase → Settings → Edge Functions → Secrets):
//   RESEND_API_KEY      — ключ от resend.com (бесплатно 3000 писем/мес)
//   TELEGRAM_BOT_TOKEN  — токен бота от @BotFather
//   TELEGRAM_ADMIN_ID   — ваш chat_id в Telegram (узнать через @userinfobot)

import { serve } from 'https://deno.land/std@0.168.0/http/server.ts'
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

const RESEND_KEY    = Deno.env.get('RESEND_API_KEY') ?? ''
const TG_TOKEN      = Deno.env.get('TELEGRAM_BOT_TOKEN') ?? ''
const TG_ADMIN      = Deno.env.get('TELEGRAM_ADMIN_ID') ?? ''
const SITE_URL      = 'https://buduj.by'

// ── отправка email через Resend ──────────────────────────────────────────────
async function sendEmail(to: string, subject: string, html: string) {
  if (!RESEND_KEY || to.includes('@users.buduj.by')) return // пропускаем fake email
  await fetch('https://api.resend.com/emails', {
    method: 'POST',
    headers: { Authorization: `Bearer ${RESEND_KEY}`, 'Content-Type': 'application/json' },
    body: JSON.stringify({ from: 'BUDUJ.BY <noreply@buduj.by>', to, subject, html }),
  })
}

// ── отправка в Telegram ──────────────────────────────────────────────────────
async function sendTelegram(chatId: string, text: string) {
  if (!TG_TOKEN || !chatId) return
  await fetch(`https://api.telegram.org/bot${TG_TOKEN}/sendMessage`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ chat_id: chatId, text, parse_mode: 'HTML' }),
  })
}

serve(async () => {
  const sb = createClient(
    Deno.env.get('SUPABASE_URL')!,
    Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!
  )

  const now   = new Date()
  const d3    = new Date(now.getTime() + 3  * 86400000).toISOString()
  const d14   = new Date(now.getTime() + 14 * 86400000).toISOString()
  const d1ago = new Date(now.getTime() - 1  * 86400000).toISOString()

  // Мастера у которых подписка истекла вчера (за последние 24ч)
  const { data: expired } = await sb.from('profiles')
    .select('name, auth_email, phone, telegram_chat_id')
    .eq('role', 'master')
    .gte('subscription_end', d1ago)
    .lt('subscription_end', now.toISOString())

  // Мастера с окончанием через 3 дня
  const { data: soon3 } = await sb.from('profiles')
    .select('name, auth_email, phone, telegram_chat_id')
    .eq('role', 'master')
    .gte('subscription_end', now.toISOString())
    .lte('subscription_end', d3)

  // Мастера с окончанием через 14 дней
  const { data: soon14 } = await sb.from('profiles')
    .select('name, auth_email, phone, telegram_chat_id')
    .eq('role', 'master')
    .gte('subscription_end', d3)
    .lte('subscription_end', d14)

  // ── Уведомления об истечении ────────────────────────────────────────────────
  for (const m of (expired ?? [])) {
    const name = m.name ?? 'Мастер'

    // Email
    await sendEmail(m.auth_email, '🔒 Подписка BUDUJ.BY истекла', `
      <div style="font-family:sans-serif;max-width:520px;margin:0 auto">
        <h2 style="color:#F5A623">BUDUJ.BY</h2>
        <p>Здравствуйте, <strong>${name}</strong>!</p>
        <p>Ваша подписка <strong>истекла</strong>. Ваш профиль скрыт из поиска и отклики на заказы заблокированы.</p>
        <a href="${SITE_URL}/login.html" style="display:inline-block;padding:12px 28px;background:#F5A623;color:#1C1512;border-radius:10px;font-weight:700;text-decoration:none;margin:16px 0">Продлить подписку →</a>
        <p style="color:#888;font-size:12px">По вопросам: +375 29 000-00-00</p>
      </div>
    `)

    // Telegram мастеру (если привязан)
    if (m.telegram_chat_id) {
      await sendTelegram(m.telegram_chat_id,
        `🔒 <b>Подписка BUDUJ.BY истекла</b>\n\nВаш профиль скрыт из поиска. Продлите подписку: ${SITE_URL}/login.html`)
    }

    // Telegram вам (админу)
    await sendTelegram(TG_ADMIN,
      `🔴 Мастер <b>${name}</b> (${m.phone ?? m.auth_email}) — подписка истекла, аккаунт в теневом режиме`)
  }

  // ── Предупреждения за 3 дня ─────────────────────────────────────────────────
  for (const m of (soon3 ?? [])) {
    const name = m.name ?? 'Мастер'
    await sendEmail(m.auth_email, '⚠️ Подписка BUDUJ.BY истекает через 3 дня', `
      <div style="font-family:sans-serif;max-width:520px;margin:0 auto">
        <h2 style="color:#F5A623">BUDUJ.BY</h2>
        <p>Здравствуйте, <strong>${name}</strong>!</p>
        <p>До истечения подписки осталось <strong>3 дня</strong>. Продлите её заранее чтобы не потерять доступ.</p>
        <a href="${SITE_URL}/login.html" style="display:inline-block;padding:12px 28px;background:#F5A623;color:#1C1512;border-radius:10px;font-weight:700;text-decoration:none;margin:16px 0">Продлить подписку →</a>
      </div>
    `)
    if (m.telegram_chat_id) {
      await sendTelegram(m.telegram_chat_id,
        `⚠️ До окончания подписки BUDUJ.BY осталось <b>3 дня</b>. Продлите: ${SITE_URL}/login.html`)
    }
  }

  // ── Напоминания за 14 дней ──────────────────────────────────────────────────
  for (const m of (soon14 ?? [])) {
    await sendEmail(m.auth_email, '📅 Напоминание: подписка BUDUJ.BY истекает через 2 недели', `
      <div style="font-family:sans-serif;max-width:520px;margin:0 auto">
        <h2 style="color:#F5A623">BUDUJ.BY</h2>
        <p>Здравствуйте, <strong>${m.name ?? 'Мастер'}</strong>!</p>
        <p>Напоминаем: подписка истекает через <strong>14 дней</strong>.</p>
        <a href="${SITE_URL}/login.html" style="display:inline-block;padding:12px 28px;background:#F5A623;color:#1C1512;border-radius:10px;font-weight:700;text-decoration:none;margin:16px 0">Продлить заранее →</a>
      </div>
    `)
    if (m.telegram_chat_id) {
      await sendTelegram(m.telegram_chat_id,
        `📅 Напоминание: подписка BUDUJ.BY истекает через 14 дней. ${SITE_URL}/login.html`)
    }
  }

  const total = (expired?.length ?? 0) + (soon3?.length ?? 0) + (soon14?.length ?? 0)
  return new Response(JSON.stringify({ ok: true, notified: total }), {
    headers: { 'Content-Type': 'application/json' },
  })
})
