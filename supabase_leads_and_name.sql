-- BUDUJ.BY · миграция от 07.08.2026
-- 1) поле «Имя» в заказах
-- 2) таблица лидов с попапов (чтобы заявки не терялись мимо базы)
-- Выполнить в Supabase → SQL Editor → Run

-- ── 1 · ИМЯ ЗАКАЗЧИКА ───────────────────────────────────────────
alter table public.orders
  add column if not exists name text;

-- ── 2 · ЛИДЫ С САЙТА ────────────────────────────────────────────
create table if not exists public.leads (
  id          uuid primary key default gen_random_uuid(),
  created_at  timestamptz not null default now(),
  source      text,                 -- какой попап/форма
  contact     text not null,        -- телефон или email
  page        text,                 -- откуда пришёл
  status      text default 'new',   -- new | contacted | closed
  note        text
);

create index if not exists leads_created_idx on public.leads (created_at desc);
create index if not exists leads_status_idx  on public.leads (status);

alter table public.leads enable row level security;

-- Аноним может только оставить заявку, но не читать чужие
drop policy if exists "leads_insert_anon" on public.leads;
create policy "leads_insert_anon"
  on public.leads for insert
  to anon, authenticated
  with check (true);

-- Читать может только авторизованный (кабинет владельца)
drop policy if exists "leads_select_auth" on public.leads;
create policy "leads_select_auth"
  on public.leads for select
  to authenticated
  using (true);
