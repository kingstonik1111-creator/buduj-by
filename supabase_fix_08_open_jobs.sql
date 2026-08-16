-- BUDUJ.BY · открытая витрина заказов · 16.08.2026
--
-- Было: мастер без подписки не видел ни одного заказа — RLS не пускала.
-- То есть площадка просила 19 рублей за веру: заплати, потом посмотрим,
-- есть ли для тебя работа. Так не платят.
--
-- Стало: заказы видны всем, контакты — нет. Мастер сам считает,
-- окупается ли подписка, ещё до оплаты. А если заказов в его городе
-- действительно нет, он это увидит и не заплатит — и не расскажет
-- потом коллегам, что площадка пустая.
--
-- Телефон и email заказчика функция не отдаёт вообще: контакт идёт
-- только через отклик, как и раньше.
--
-- Выполнить в Supabase → SQL Editor → Run

create or replace function public.orders_public(
  p_city     text default null,
  p_category text default null,
  p_limit    int  default 60
)
returns table (
  id             uuid,
  created_at     timestamptz,
  title          text,
  city           text,
  category       text,
  budget         text,
  timing         text,
  responses_cnt  bigint
)
language sql
security definer
set search_path = public
stable
as $$
  select
    o.id, o.created_at, o.title, o.city, o.category, o.budget, o.timing,
    (select count(*) from public.responses r where r.order_id = o.id)
  from public.orders o
  where o.status = 'open'
    and (p_city     is null or p_city     = '' or o.city     = p_city)
    and (p_category is null or p_category = '' or o.category = p_category)
  order by o.created_at desc
  limit least(coalesce(p_limit, 60), 200)
$$;

revoke all on function public.orders_public(text, text, int) from public;
grant execute on function public.orders_public(text, text, int) to anon, authenticated;

-- ── СПРОС В ЦИФРАХ ──────────────────────────────────────────────
-- Для страницы «Для мастеров»: сколько заказов за последние 7 дней
-- по городам и категориям. Мастеру важна ровно эта цифра, а не
-- «65 видов работ в каталоге».
create or replace function public.demand_stats(p_days int default 7)
returns table (city text, category text, orders_count bigint)
language sql
security definer
set search_path = public
stable
as $$
  select o.city, o.category, count(*)
  from public.orders o
  where o.created_at > now() - (coalesce(p_days, 7) || ' days')::interval
    and o.city is not null
  group by o.city, o.category
  order by count(*) desc
$$;

revoke all on function public.demand_stats(int) from public;
grant execute on function public.demand_stats(int) to anon, authenticated;

-- ── ПРОВЕРКА ────────────────────────────────────────────────────
select count(*) as "заказов видно анониму" from public.orders_public();
