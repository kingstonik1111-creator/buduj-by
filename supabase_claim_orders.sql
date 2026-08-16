-- BUDUJ.BY · миграция от 16.08.2026
-- Замыкаем петлю заказчика: заявка с сайта больше не теряется.
--
-- Проблема, которую чиним:
--   orders.html вставлял заказ без owner_id (RLS это разрешает для анонима),
--   а кабинет показывает «Мои заказы» и принимает отклик только по
--   owner_id = auth.uid(). Заказчик с сайта не видел ни одного отклика.
--
-- Решение:
--   1) у заказа появляется claim_token — одноразовый ключ на этот заказ;
--   2) аноним создаёт заказ через RPC и получает токен;
--   3) после регистрации/входа вызывается claim_order(токен) —
--      заказ привязывается к аккаунту.
--
-- Выполнить в Supabase → SQL Editor → Run

-- ── 1 · ТОКЕН ПРИВЯЗКИ ──────────────────────────────────────────
alter table public.orders
  add column if not exists claim_token uuid default gen_random_uuid();

alter table public.orders
  add column if not exists timing text;

create index if not exists orders_claim_token_idx
  on public.orders (claim_token);

-- Уже лежащим анонимным заказам тоже раздаём токены
update public.orders
   set claim_token = gen_random_uuid()
 where claim_token is null;

-- ── 2 · СОЗДАНИЕ ЗАКАЗА С САЙТА ─────────────────────────────────
-- SECURITY DEFINER: обходит RLS контролируемо, наружу отдаёт только токен.
-- Читать чужие заказы через эту функцию нельзя.
create or replace function public.create_order_public(
  p_title    text,
  p_city     text,
  p_phone    text,
  p_name     text default null,
  p_category text default null,
  p_email    text default null,
  p_timing   text default null,
  p_budget   text default null
) returns uuid
language plpgsql
security definer
set search_path = public
as $$
declare
  v_token uuid;
begin
  if coalesce(btrim(p_title), '') = '' then
    raise exception 'Опишите задачу';
  end if;
  if coalesce(btrim(p_city), '') = '' then
    raise exception 'Выберите город';
  end if;
  if length(coalesce(btrim(p_phone), '')) < 6 then
    raise exception 'Введите телефон';
  end if;

  insert into public.orders (
    title, city, phone, name, category, email, timing, budget, status, owner_id
  ) values (
    left(btrim(p_title), 2000),
    btrim(p_city),
    btrim(p_phone),
    left(btrim(coalesce(p_name, '')), 200),
    coalesce(nullif(btrim(coalesce(p_category, '')), ''), 'Другое'),
    nullif(btrim(coalesce(p_email, '')), ''),
    nullif(btrim(coalesce(p_timing, '')), ''),
    coalesce(nullif(btrim(coalesce(p_budget, '')), ''), 'Нужна смета'),
    'open',
    auth.uid()     -- если человек уже вошёл — сразу его заказ
  )
  returning claim_token into v_token;

  return v_token;
end
$$;

revoke all on function public.create_order_public(text,text,text,text,text,text,text,text) from public;
grant execute on function public.create_order_public(text,text,text,text,text,text,text,text)
  to anon, authenticated;

-- ── 3 · ПРИВЯЗКА ЗАКАЗА К АККАУНТУ ──────────────────────────────
-- Вызывается сразу после регистрации или входа заказчика.
-- Привязать можно только ничей заказ и только зная его токен.
create or replace function public.claim_order(p_token uuid)
returns uuid
language plpgsql
security definer
set search_path = public
as $$
declare
  v_id uuid;
begin
  if auth.uid() is null then
    raise exception 'Требуется вход';
  end if;

  update public.orders
     set owner_id = auth.uid()
   where claim_token = p_token
     and owner_id is null
  returning id into v_id;

  return v_id;   -- null, если заказ уже привязан или токен не найден
end
$$;

revoke all on function public.claim_order(uuid) from public;
grant execute on function public.claim_order(uuid) to authenticated;

-- ── 4 · ПРОВЕРКА ────────────────────────────────────────────────
-- select public.create_order_public('Тест','Минск','+375291112233','Стас');
-- select id, owner_id, claim_token from public.orders order by created_at desc limit 3;
