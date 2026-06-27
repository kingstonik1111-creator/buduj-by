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
ALTER TABLE profiles ADD COLUMN IF NOT EXISTS last_seen_at     timestamptz;

-- 2. Верификация мастера (по желанию)
ALTER TABLE profiles ADD COLUMN IF NOT EXISTS is_verified      boolean DEFAULT false;
ALTER TABLE profiles ADD COLUMN IF NOT EXISTS verified_status  text DEFAULT 'none';   -- none / pending / approved
ALTER TABLE profiles ADD COLUMN IF NOT EXISTS verified_doc_url text;

-- 3. Shadow ban: мастера с истёкшей подпиской скрыты из поиска
--    (видят только себя, клиенты видят только активных мастеров)
DROP POLICY IF EXISTS "profiles_select" ON profiles;
CREATE POLICY "profiles_select" ON profiles
  FOR SELECT USING (
    role = 'client'
    OR subscription_end > now()
    OR auth.uid() = id
  );

-- 4. Заказы: RLS для вставки
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT FROM pg_policies WHERE tablename='orders' AND policyname='orders_insert'
  ) THEN
    CREATE POLICY "orders_insert" ON orders
      FOR INSERT WITH CHECK (auth.uid() = owner_id);
  END IF;
END$$;

-- 5. Отклики: is_read (заказчик просмотрел отклик)
ALTER TABLE responses ADD COLUMN IF NOT EXISTS is_read boolean DEFAULT false;

-- 6. Сообщения: is_read (получатель прочитал)
ALTER TABLE messages  ADD COLUMN IF NOT EXISTS is_read boolean DEFAULT false;

-- 7. Realtime для messages (чат)
ALTER PUBLICATION supabase_realtime ADD TABLE messages;

-- 8. Избранные мастера (Мои мастера)
CREATE TABLE IF NOT EXISTS favorites (
  id         uuid DEFAULT gen_random_uuid() PRIMARY KEY,
  created_at timestamptz DEFAULT now(),
  client_id  uuid NOT NULL,
  master_id  uuid NOT NULL,
  UNIQUE(client_id, master_id)
);
ALTER TABLE favorites ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "fav_select"  ON favorites;
DROP POLICY IF EXISTS "fav_insert"  ON favorites;
DROP POLICY IF EXISTS "fav_delete"  ON favorites;
CREATE POLICY "fav_select" ON favorites FOR SELECT USING (auth.uid() = client_id);
CREATE POLICY "fav_insert" ON favorites FOR INSERT WITH CHECK (auth.uid() = client_id);
CREATE POLICY "fav_delete" ON favorites FOR DELETE USING (auth.uid() = client_id);

-- 9. Включить pg_cron (для ежедневных уведомлений)
CREATE EXTENSION IF NOT EXISTS pg_cron;

-- 10. Ежедневная задача: вызов Edge Function notify-subscriptions каждый день в 9:00
--     ЗАМЕНИТЕ your-project-ref на ваш реальный ref (Supabase → Settings → General)
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
-- SELECT column_name FROM information_schema.columns WHERE table_name = 'favorites';
-- SELECT * FROM cron.job;
