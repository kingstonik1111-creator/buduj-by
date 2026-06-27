-- ============================================================
-- BUDUJ.BY — все обновления Supabase (запустить одним блоком)
-- Supabase → SQL Editor → вставить → Run
-- ============================================================

-- 1. Новые колонки в таблице profiles
ALTER TABLE profiles ADD COLUMN IF NOT EXISTS auth_email       text;
ALTER TABLE profiles ADD COLUMN IF NOT EXISTS telegram_chat_id text;
ALTER TABLE profiles ADD COLUMN IF NOT EXISTS first_name       text;
ALTER TABLE profiles ADD COLUMN IF NOT EXISTS last_name        text;
ALTER TABLE profiles ADD COLUMN IF NOT EXISTS avatar_url       text;

-- 2. Shadow ban: мастера с истёкшей подпиской скрыты из поиска
--    (видят только себя, клиенты видят только активных мастеров)
DROP POLICY IF EXISTS "profiles_select" ON profiles;
CREATE POLICY "profiles_select" ON profiles
  FOR SELECT USING (
    role = 'client'
    OR subscription_end > now()
    OR auth.uid() = id
  );

-- 3. Включить pg_cron (для ежедневных уведомлений)
CREATE EXTENSION IF NOT EXISTS pg_cron;

-- 4. Ежедневная задача: вызов Edge Function notify-subscriptions каждый день в 9:00
--    ЗАМЕНИТЕ your-project-ref на ваш реальный ref (Supabase → Settings → General)
SELECT cron.schedule(
  'notify-subscriptions-daily',
  '0 9 * * *',
  $$
  SELECT net.http_post(
    url     := 'https://your-project-ref.supabase.co/functions/v1/notify-subscriptions',
    headers := jsonb_build_object(
      'Authorization', 'Bearer ' || current_setting('app.anon_key'),
      'Content-Type',  'application/json'
    ),
    body    := '{}'::jsonb
  );
  $$
);

-- Проверить что всё добавлено:
-- SELECT column_name FROM information_schema.columns WHERE table_name = 'profiles';
-- SELECT * FROM cron.job;
