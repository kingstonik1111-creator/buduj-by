-- BUDUJ.BY · живая лента событий · 17.08.2026
--
-- Всплывашки на главной показывали выдуманных людей: «Александр из Минска
-- нашёл электрика». Список крутился по кругу, распознавался за пять минут
-- наблюдения и бил по доверию ровно там, где его надо строить.
--
-- Механику оставляем — она работает. Но крутим настоящие события:
-- размещённые заказы и отклики мастеров. Персональных данных не отдаём,
-- только категория, город и время.
--
-- Выполнить в Supabase → SQL Editor → Run

create or replace function public.recent_activity(p_limit int default 12)
returns table (
  kind       text,
  category   text,
  city       text,
  happened_at timestamptz
)
language sql
security definer
set search_path = public
stable
as $$
  (
    select 'order'::text, coalesce(o.category,'Другое'), o.city, o.created_at
    from public.orders o
    where o.created_at > now() - interval '14 days'
      and o.city is not null
  )
  union all
  (
    select 'response'::text, coalesce(o.category,'Другое'), o.city, r.created_at
    from public.responses r
    join public.orders o on o.id = r.order_id
    where r.created_at > now() - interval '14 days'
      and o.city is not null
  )
  union all
  (
    select 'contact'::text, coalesce(o.category,'Другое'), o.city, c.created_at
    from public.revealed_contacts c
    join public.orders o on o.id = c.order_id
    where c.created_at > now() - interval '14 days'
      and o.city is not null
  )
  order by 4 desc
  limit least(coalesce(p_limit, 12), 30)
$$;

revoke all on function public.recent_activity(int) from public;
grant execute on function public.recent_activity(int) to anon, authenticated;

-- Проверка
select * from public.recent_activity(20);
