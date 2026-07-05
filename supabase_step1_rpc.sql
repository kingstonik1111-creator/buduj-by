-- ============================================================
-- BUDUJ.BY — ШАГ 1: функции для входа по телефону
-- Запустить ПЕРВЫМ (Supabase → SQL Editor → Run).
-- Безопасно: только добавляет функции, ничего не ломает.
--
-- Зачем: чтобы после закрытия колонок (шаг 2) вход и
-- регистрация по телефону продолжали работать.
-- ============================================================

-- Вернуть служебный email по номеру телефона (для входа)
CREATE OR REPLACE FUNCTION public.get_login_email(p_phone text)
RETURNS text
LANGUAGE sql
SECURITY DEFINER
SET search_path = public
AS $$
  SELECT auth_email FROM profiles WHERE phone = p_phone LIMIT 1;
$$;

-- Проверить, занят ли номер (для регистрации)
CREATE OR REPLACE FUNCTION public.phone_taken(p_phone text)
RETURNS boolean
LANGUAGE sql
SECURITY DEFINER
SET search_path = public
AS $$
  SELECT EXISTS (SELECT 1 FROM profiles WHERE phone = p_phone);
$$;

GRANT EXECUTE ON FUNCTION public.get_login_email(text) TO anon, authenticated;
GRANT EXECUTE ON FUNCTION public.phone_taken(text)     TO anon, authenticated;
