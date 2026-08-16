-- BUDUJ.BY · просмотры профиля и уведомление об открытом контакте · 16.08.2026
--
-- Две дыры, которые видно только с места мастера:
--
-- 1. Он не узнаёт, что заказчик открыл его контакт. Запись падает
--    в revealed_contacts, и всё. А это единственный момент, когда
--    подписка доказывает себя. Плюс по этому же событию считается
--    гарантия — то есть мастер не видит того, от чего зависят деньги.
--
-- 2. «Статистика просмотров» продаётся в тарифах Профи и Бизнес,
--    а в коде её нет вовсе. Та же история, что была с портфолио.
--
-- Выполнить в Supabase → SQL Editor → Run

-- ── 1 · ПРОСМОТРЫ ПРОФИЛЯ ───────────────────────────────────────
create table if not exists public.profile_views (
  id         bigserial primary key,
  master_id  uuid not null references public.profiles(id) on delete cascade,
  created_at timestamptz not null default now(),
  source     text
);

create index if not exists profile_views_master_idx
  on public.profile_views (master_id, created_at desc);

alter table public.profile_views enable row level security;

-- Мастер видит только свои просмотры. Писать напрямую нельзя —
-- только через функцию ниже, иначе счётчик можно накрутить.
drop policy if exists "views_select_own" on public.profile_views;
create policy "views_select_own" on public.profile_views
  for select to authenticated using (auth.uid() = master_id);

-- Записываем просмотр. Свои же заходы не считаем — иначе мастер
-- накрутит себе статистику, обновляя страницу, и она станет бесполезной.
create or replace function public.track_profile_view(p_master uuid, p_source text default null)
returns void
language plpgsql
security definer
set search_path = public
as $$
begin
  if p_master is null then return; end if;
  if auth.uid() = p_master then return; end if;

  -- Не чаще раза в час с одной сессии на одного мастера
  if exists (
    select 1 from public.profile_views v
     where v.master_id = p_master
       and v.created_at > now() - interval '1 hour'
       and coalesce(v.source,'') = coalesce(p_source,'')
  ) then
    return;
  end if;

  insert into public.profile_views (master_id, source) values (p_master, p_source);
end
$$;

revoke all on function public.track_profile_view(uuid, text) from public;
grant execute on function public.track_profile_view(uuid, text) to anon, authenticated;

-- Сводка для кабинета мастера
create or replace function public.my_stats()
returns table (
  views_7      bigint,
  views_30     bigint,
  contacts_7   bigint,
  contacts_30  bigint,
  responses_30 bigint
)
language sql
security definer
set search_path = public
stable
as $$
  select
    (select count(*) from public.profile_views v
      where v.master_id = auth.uid() and v.created_at > now() - interval '7 days'),
    (select count(*) from public.profile_views v
      where v.master_id = auth.uid() and v.created_at > now() - interval '30 days'),
    (select count(*) from public.revealed_contacts c
      where c.master_id = auth.uid() and c.created_at > now() - interval '7 days'),
    (select count(*) from public.revealed_contacts c
      where c.master_id = auth.uid() and c.created_at > now() - interval '30 days'),
    (select count(*) from public.responses r
      where r.master_user_id = auth.uid() and r.created_at > now() - interval '30 days')
$$;

revoke all on function public.my_stats() from public;
grant execute on function public.my_stats() to authenticated;

-- ── 2 · ПРОВЕРКА ────────────────────────────────────────────────
select
  (select count(*) from information_schema.tables
    where table_name='profile_views')                    as "таблица просмотров",
  (select count(*) from information_schema.routines
    where routine_name in ('track_profile_view','my_stats')) as "функций";
