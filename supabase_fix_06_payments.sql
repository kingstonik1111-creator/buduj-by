-- BUDUJ.BY · журнал платежей · 16.08.2026
--
-- Зачем: вебхук bePaid может прийти дважды (повтор при таймауте, ручной
-- перезапуск из кабинета банка). Без журнала каждый повтор продлевал бы
-- подписку ещё на месяц. Плюс это основа для сверки денег.
--
-- Выполнить в Supabase → SQL Editor → Run

create table if not exists public.payments (
  id            uuid primary key default gen_random_uuid(),
  created_at    timestamptz not null default now(),
  master_id     uuid references public.profiles(id) on delete set null,
  plan          text,
  amount_minor  int,                 -- в копейках, как отдаёт bePaid
  currency      text default 'BYN',
  status        text,                -- successful | failed | incomplete
  bepaid_uid    text unique,         -- ключ идемпотентности
  tracking_id   text,
  test_mode     boolean default false,
  raw           jsonb                -- полное уведомление, для разбора спорных
);

create index if not exists payments_master_idx on public.payments (master_id, created_at desc);
create index if not exists payments_status_idx on public.payments (status, created_at desc);

alter table public.payments enable row level security;

-- Мастер видит только свои платежи. Записывает — только сервисная роль
-- (вебхук), поэтому политики на insert нет намеренно.
drop policy if exists "payments_select_own" on public.payments;
create policy "payments_select_own" on public.payments
  for select to authenticated using (auth.uid() = master_id);

-- Проверка
select count(*) as "платежей в журнале" from public.payments;
