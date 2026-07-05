-- ============================================================
-- BUDUJ.BY — ЗАКРЫТИЕ ДОСТУПА (запустить одним блоком)
-- Supabase → SQL Editor → вставить всё → Run
--
-- Что делает:
--   1) Заказы больше НЕ видны публично. Их видит только автор заказа
--      или зарегистрированный мастер с активной подпиской/пробным.
--   2) Откликнуться на заказ может ТОЛЬКО авторизованный мастер
--      с активной подпиской (аноним больше не может).
--   3) Клиенты по-прежнему могут разместить заказ без регистрации.
-- ============================================================

-- ── ЗАКАЗЫ ──────────────────────────────────────────────────
ALTER TABLE orders ENABLE ROW LEVEL SECURITY;

-- Кто может ВИДЕТЬ заказы: автор заказа ИЛИ активный мастер
DROP POLICY IF EXISTS "orders_select" ON orders;
CREATE POLICY "orders_select" ON orders
  FOR SELECT USING (
    auth.uid() = owner_id
    OR EXISTS (
      SELECT 1 FROM profiles p
      WHERE p.id = auth.uid()
        AND p.role = 'master'
        AND p.subscription_end > now()
    )
  );

-- Кто может РАЗМЕЩАТЬ заказ: аноним-клиент ИЛИ сам автор (без изменений)
DROP POLICY IF EXISTS "orders_insert" ON orders;
CREATE POLICY "orders_insert" ON orders
  FOR INSERT WITH CHECK (
    (auth.uid() IS NULL AND owner_id IS NULL)
    OR auth.uid() = owner_id
  );

-- Кто может РЕДАКТИРОВАТЬ заказ: только автор (без изменений)
DROP POLICY IF EXISTS "orders_update" ON orders;
CREATE POLICY "orders_update" ON orders
  FOR UPDATE USING (auth.uid() = owner_id)
  WITH CHECK (auth.uid() = owner_id);

-- ── ОТКЛИКИ ─────────────────────────────────────────────────
ALTER TABLE responses ENABLE ROW LEVEL SECURITY;

-- Откликнуться может ТОЛЬКО авторизованный мастер с активной подпиской,
-- и только от своего имени (master_id = его id).
DROP POLICY IF EXISTS "responses_insert" ON responses;
CREATE POLICY "responses_insert" ON responses
  FOR INSERT WITH CHECK (
    auth.uid() = master_id
    AND EXISTS (
      SELECT 1 FROM profiles p
      WHERE p.id = auth.uid()
        AND p.role = 'master'
        AND p.subscription_end > now()
    )
  );

-- Кто видит отклики: автор заказа и сам мастер (без изменений)
DROP POLICY IF EXISTS "responses_select" ON responses;
CREATE POLICY "responses_select" ON responses
  FOR SELECT USING (
    auth.uid() IN (SELECT owner_id FROM orders WHERE id = order_id)
    OR auth.uid() = master_id
  );

-- ============================================================
-- ПРОВЕРКА (по желанию, выполнить отдельно):
--   select policyname, cmd from pg_policies where tablename in ('orders','responses');
-- ============================================================
