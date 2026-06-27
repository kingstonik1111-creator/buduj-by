-- BUDUJ.BY — настройка уведомлений об истечении подписки
-- Запустить в Supabase → SQL Editor

-- 1. Добавить столбец telegram_chat_id в profiles
--    (сюда будет сохраняться chat_id мастера после привязки Telegram-бота)
ALTER TABLE profiles ADD COLUMN IF NOT EXISTS telegram_chat_id text;

-- 2. Убедиться что auth_email тоже есть (для телефонных аккаунтов)
ALTER TABLE profiles ADD COLUMN IF NOT EXISTS auth_email text;

-- 2а. Поля профиля заказчика (имя, фамилия, фото)
ALTER TABLE profiles ADD COLUMN IF NOT EXISTS first_name text;
ALTER TABLE profiles ADD COLUMN IF NOT EXISTS last_name  text;
ALTER TABLE profiles ADD COLUMN IF NOT EXISTS avatar_url text;

-- 3. Shadow ban: скрывать мастеров с истёкшей подпиской из поиска
--    Только сам мастер и клиенты видят активные профили
DROP POLICY IF EXISTS "profiles_select" ON profiles;
CREATE POLICY "profiles_select" ON profiles
  FOR SELECT USING (
    role = 'client'
    OR subscription_end > now()
    OR auth.uid() = id
  );

-- 4. Включить расширение pg_cron (один раз для проекта)
--    Если уже включено — просто пропустите этот шаг
CREATE EXTENSION IF NOT EXISTS pg_cron;

-- 5. Создать задачу cron — запускать Edge Function каждый день в 9:00 UTC
--    (замените YOUR_PROJECT_REF на ваш ref из Supabase, напр. abcdefghij)
SELECT cron.schedule(
  'notify-subscriptions-daily',          -- имя задачи
  '0 9 * * *',                           -- каждый день в 9:00 UTC
  $$
  SELECT net.http_post(
    url     := 'https://YOUR_PROJECT_REF.supabase.co/functions/v1/notify-subscriptions',
    headers := jsonb_build_object(
      'Authorization', 'Bearer ' || current_setting('app.anon_key'),
      'Content-Type',  'application/json'
    ),
    body    := '{}'::jsonb
  );
  $$
);

-- Проверить что задача создана:
-- SELECT * FROM cron.job;

-- Удалить задачу если нужно переделать:
-- SELECT cron.unschedule('notify-subscriptions-daily');
