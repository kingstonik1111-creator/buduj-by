-- BUDUJ.BY · исправления №3 и №4 от 16.08.2026
-- Отзывы сохраняются, рейтинг мастера пересчитывается сам.
--
-- Что было:
--   №3 profile.html не передавал client_id (NOT NULL), а политика требует
--      auth.uid() = client_id. Любая попытка отзыва падала с ошибкой.
--   №4 Триггера пересчёта не было: profiles.rating и reviews_count
--      не менялись никогда, звёзды в каталоге были статичными.
--
-- Выполнить в Supabase → SQL Editor → Run

-- ── 1 · ЗНАЧОК «ПРОВЕРЕННЫЙ ЗАКАЗ» ──────────────────────────────
-- Отзыв считается проверенным, если в базе есть след реального
-- взаимодействия: заказчик открывал контакт мастера или принял его отклик.
alter table public.reviews
  add column if not exists is_verified_order boolean not null default false;

-- ── 2 · ОДИН ОТЗЫВ ОДНОМУ МАСТЕРУ ───────────────────────────────
-- На паре (order_id, client_id) уникальность уже есть, но отзыв без
-- заказа можно было оставлять бесконечно. Закрываем.
create unique index if not exists reviews_one_per_master_idx
  on public.reviews (master_id, client_id)
  where order_id is null;

-- ── 3 · САМ СЕБЕ ОТЗЫВ НЕ НАПИШЕШЬ ──────────────────────────────
alter table public.reviews
  drop constraint if exists reviews_not_self;
alter table public.reviews
  add constraint reviews_not_self check (master_id <> client_id);

-- ── 4 · ПРОСТАВЛЯЕМ ПРИЗНАК ПРОВЕРЕННОГО ────────────────────────
create or replace function public.reviews_mark_verified()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
begin
  new.is_verified_order := exists (
    select 1 from public.revealed_contacts rc
     where rc.client_id = new.client_id
       and rc.master_id = new.master_id
  ) or exists (
    select 1
      from public.orders o
      join public.responses r on r.id = o.accepted_response_id
     where o.owner_id = new.client_id
       and r.master_user_id = new.master_id
  );
  return new;
end
$$;

drop trigger if exists reviews_mark_verified_trg on public.reviews;
create trigger reviews_mark_verified_trg
  before insert on public.reviews
  for each row execute function public.reviews_mark_verified();

-- ── 5 · ПЕРЕСЧЁТ РЕЙТИНГА МАСТЕРА (ошибка №4) ───────────────────
create or replace function public.recalc_master_rating()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
declare
  v_master uuid := coalesce(new.master_id, old.master_id);
begin
  update public.profiles p
     set rating = coalesce((
           select round(avg(r.rating)::numeric, 2)
             from public.reviews r where r.master_id = v_master
         ), 0),
         reviews_count = (
           select count(*) from public.reviews r where r.master_id = v_master
         )
   where p.id = v_master;
  return null;
end
$$;

drop trigger if exists recalc_master_rating_trg on public.reviews;
create trigger recalc_master_rating_trg
  after insert or update or delete on public.reviews
  for each row execute function public.recalc_master_rating();

-- ── 6 · ПЕРЕСЧИТЫВАЕМ ТО, ЧТО УЖЕ ЕСТЬ ──────────────────────────
update public.profiles p
   set rating = coalesce((
         select round(avg(r.rating)::numeric, 2)
           from public.reviews r where r.master_id = p.id
       ), 0),
       reviews_count = (
         select count(*) from public.reviews r where r.master_id = p.id
       )
 where p.role = 'master';

-- ── 7 · ЧИТАТЬ ОТЗЫВЫ МОЖНО ВСЕМ ────────────────────────────────
grant select on public.reviews to anon, authenticated;

-- ── 8 · ПРОВЕРКА ────────────────────────────────────────────────
select
  (select count(*) from public.reviews)                      as "отзывов",
  (select count(*) from public.profiles where role='master') as "мастеров",
  (select string_agg(tgname, ', ')
     from pg_trigger
    where tgrelid = 'public.reviews'::regclass
      and not tgisinternal)                                  as "триггеры на reviews";
