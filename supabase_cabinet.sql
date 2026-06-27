-- ============================================
-- BUDUJ.BY — SQL для кабинета (запустить в Supabase SQL Editor)
-- ============================================

-- 1. Добавить колонки в существующие таблицы
ALTER TABLE orders ADD COLUMN IF NOT EXISTS owner_id uuid;
ALTER TABLE responses ADD COLUMN IF NOT EXISTS master_user_id uuid;

-- 2. Профили пользователей
CREATE TABLE IF NOT EXISTS profiles (
  id uuid PRIMARY KEY,
  created_at timestamptz DEFAULT now(),
  role text NOT NULL CHECK (role IN ('master','client')),
  name text,
  phone text,
  city text,
  spec text,
  bio text,
  subscription_plan text DEFAULT 'free',
  subscription_end timestamptz,
  rating numeric(2,1) DEFAULT 0,
  reviews_count int DEFAULT 0
);

-- 3. Сообщения чата
CREATE TABLE IF NOT EXISTS messages (
  id uuid DEFAULT gen_random_uuid() PRIMARY KEY,
  created_at timestamptz DEFAULT now(),
  order_id uuid REFERENCES orders(id) ON DELETE CASCADE,
  sender_id uuid NOT NULL,
  receiver_id uuid NOT NULL,
  content text NOT NULL,
  read boolean DEFAULT false
);

-- 4. Отзывы клиентов о мастерах
CREATE TABLE IF NOT EXISTS reviews (
  id uuid DEFAULT gen_random_uuid() PRIMARY KEY,
  created_at timestamptz DEFAULT now(),
  order_id uuid REFERENCES orders(id),
  master_id uuid NOT NULL,
  client_id uuid NOT NULL,
  rating int NOT NULL CHECK (rating BETWEEN 1 AND 5),
  text text,
  UNIQUE(order_id, client_id)
);

-- 5. Журнал раскрытых номеров (клиент нажал "Показать номер")
CREATE TABLE IF NOT EXISTS revealed_contacts (
  id uuid DEFAULT gen_random_uuid() PRIMARY KEY,
  created_at timestamptz DEFAULT now(),
  client_id uuid NOT NULL,
  master_id uuid NOT NULL,
  order_id uuid REFERENCES orders(id),
  UNIQUE(client_id, master_id, order_id)
);

-- ============================================
-- RLS ПОЛИТИКИ
-- ============================================

-- Profiles
ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;
CREATE POLICY "profiles_select" ON profiles FOR SELECT USING (true);
CREATE POLICY "profiles_insert" ON profiles FOR INSERT WITH CHECK (auth.uid() = id);
CREATE POLICY "profiles_update" ON profiles FOR UPDATE USING (auth.uid() = id);

-- Messages
ALTER TABLE messages ENABLE ROW LEVEL SECURITY;
CREATE POLICY "messages_select" ON messages FOR SELECT
  USING (auth.uid() = sender_id OR auth.uid() = receiver_id);
CREATE POLICY "messages_insert" ON messages FOR INSERT
  WITH CHECK (auth.uid() = sender_id);
CREATE POLICY "messages_update" ON messages FOR UPDATE
  USING (auth.uid() = receiver_id);

-- Reviews
ALTER TABLE reviews ENABLE ROW LEVEL SECURITY;
CREATE POLICY "reviews_select" ON reviews FOR SELECT USING (true);
CREATE POLICY "reviews_insert" ON reviews FOR INSERT
  WITH CHECK (auth.uid() = client_id);

-- Revealed contacts
ALTER TABLE revealed_contacts ENABLE ROW LEVEL SECURITY;
CREATE POLICY "revealed_select" ON revealed_contacts FOR SELECT
  USING (auth.uid() = client_id OR auth.uid() = master_id);
CREATE POLICY "revealed_insert" ON revealed_contacts FOR INSERT
  WITH CHECK (auth.uid() = client_id);

-- ============================================
-- REALTIME — включить для чата
-- ============================================
ALTER PUBLICATION supabase_realtime ADD TABLE messages;
