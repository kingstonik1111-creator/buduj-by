-- BUDUJ.BY · портфолио мастера · 16.08.2026
--
-- Тарифы продавали «5 фото» и «20 фото», а функции не существовало:
-- в profile.html стояла заглушка «Мастер скоро добавит фото работ».
-- profile.html при этом уже умеет рисовать галерею из profiles.portfolio_urls —
-- не хватало только самой колонки и хранилища.
--
-- Выполнить в Supabase → SQL Editor → Run

-- ── 1 · КОЛОНКА ─────────────────────────────────────────────────
alter table public.profiles
  add column if not exists portfolio_urls text[] default '{}';

-- Каталог и профиль читают аноним — колонку надо открыть явно,
-- доступ к profiles выдан поколоночно.
grant select (portfolio_urls) on public.profiles to anon;

-- ── 2 · ХРАНИЛИЩЕ ───────────────────────────────────────────────
insert into storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
values ('portfolio', 'portfolio', true, 5242880,
        array['image/jpeg','image/png','image/webp','image/heic','image/heif'])
on conflict (id) do update
  set public = true,
      file_size_limit = 5242880,
      allowed_mime_types = excluded.allowed_mime_types;

-- Смотреть фото работ может кто угодно — это витрина
drop policy if exists "portfolio_read" on storage.objects;
create policy "portfolio_read" on storage.objects
  for select using (bucket_id = 'portfolio');

-- Загружать и удалять — только в свою папку. Имя папки = uuid мастера,
-- поэтому чужие файлы тронуть нельзя.
drop policy if exists "portfolio_insert_own" on storage.objects;
create policy "portfolio_insert_own" on storage.objects
  for insert to authenticated
  with check (bucket_id = 'portfolio'
              and (storage.foldername(name))[1] = auth.uid()::text);

drop policy if exists "portfolio_delete_own" on storage.objects;
create policy "portfolio_delete_own" on storage.objects
  for delete to authenticated
  using (bucket_id = 'portfolio'
         and (storage.foldername(name))[1] = auth.uid()::text);

-- ── 3 · ЛИМИТ ПО ТАРИФУ ─────────────────────────────────────────
-- Столько фото обещано на витрине for-masters.html.
-- Без подписки даём 3: чтобы мастер собрал профиль до оплаты,
-- иначе он платит вслепую. Показываться они всё равно начнут
-- только с активной подпиской (теневой режим).
create or replace function public.portfolio_limit(p_plan text, p_end timestamptz)
returns int
language sql
immutable
as $$
  select case
    when p_end is null or p_end < now() then 3
    when p_plan = 'basic' then 5
    when p_plan in ('pro','biz') then 20
    else 3
  end
$$;

create or replace function public.enforce_portfolio_limit()
returns trigger
language plpgsql
as $$
declare
  v_max int;
begin
  if new.portfolio_urls is null then
    new.portfolio_urls := '{}';
  end if;

  v_max := public.portfolio_limit(new.subscription_plan, new.subscription_end);

  if array_length(new.portfolio_urls, 1) > v_max then
    raise exception 'На вашем тарифе можно не больше % фото работ', v_max
      using errcode = 'check_violation';
  end if;
  return new;
end
$$;

drop trigger if exists enforce_portfolio_limit_trg on public.profiles;
create trigger enforce_portfolio_limit_trg
  before insert or update of portfolio_urls on public.profiles
  for each row execute function public.enforce_portfolio_limit();

-- ── 4 · ПРОВЕРКА ────────────────────────────────────────────────
select
  (select count(*) from storage.buckets where id='portfolio')          as "бакет создан",
  (select count(*) from information_schema.columns
    where table_name='profiles' and column_name='portfolio_urls')      as "колонка есть",
  (select count(*) from pg_policies
    where tablename='objects' and policyname like 'portfolio%')        as "политик хранилища";
