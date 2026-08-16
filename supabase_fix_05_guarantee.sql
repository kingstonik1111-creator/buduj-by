-- BUDUJ.BY · гарантия на подписку · 16.08.2026
--
-- «Не получили ни одного заказа за месяц — продлеваем бесплатно.»
--
-- Определение «не получил заказ»: за оплаченный период ни один заказчик
-- не открыл контакт мастера (таблица revealed_contacts).
--
-- Условие добросовестности: мастер откликнулся хотя бы на 3 заказа
-- ЛИБО подходящих заказов (его город + его категории) было меньше 3.
-- Если заказы были, а он не откликался — площадка своё дала, гарантия не идёт.
--
-- Выполнить в Supabase → SQL Editor → Run

-- ── 1 · ЖУРНАЛ ПРОДЛЕНИЙ ────────────────────────────────────────
-- Нужен для прозрачности: мастер и мы видим, за что продлили.
create table if not exists public.subscription_guarantees (
  id            uuid primary key default gen_random_uuid(),
  created_at    timestamptz not null default now(),
  master_id     uuid not null references public.profiles(id) on delete cascade,
  period_start  timestamptz not null,
  period_end    timestamptz not null,
  extended_to   timestamptz not null,
  contacts_open int not null,
  responses_made int not null,
  orders_available int not null
);

create index if not exists subscription_guarantees_master_idx
  on public.subscription_guarantees (master_id, created_at desc);

alter table public.subscription_guarantees enable row level security;

drop policy if exists "guarantees_select_own" on public.subscription_guarantees;
create policy "guarantees_select_own" on public.subscription_guarantees
  for select to authenticated using (auth.uid() = master_id);

-- ── 2 · ПРОВЕРКА ПРАВА НА ГАРАНТИЮ ──────────────────────────────
-- Возвращает одну строку с цифрами и решением. Используется и роботом,
-- и кабинетом — чтобы мастер видел своё положение в любой момент.
create or replace function public.guarantee_status(p_master uuid)
returns table (
  eligible          boolean,
  reason            text,
  contacts_open     int,
  responses_made    int,
  orders_available  int,
  period_start      timestamptz,
  period_end        timestamptz
)
language plpgsql
security definer
set search_path = public
as $$
declare
  v_end   timestamptz;
  v_start timestamptz;
  v_city  text;
  v_cats  text[];
  v_contacts int;
  v_resp     int;
  v_orders   int;
begin
  select p.subscription_end, p.city, coalesce(p.categories,'{}')
    into v_end, v_city, v_cats
    from public.profiles p
   where p.id = p_master and p.role = 'master';

  if v_end is null then
    return query select false, 'нет подписки'::text, 0, 0, 0,
                        null::timestamptz, null::timestamptz;
    return;
  end if;

  v_start := v_end - interval '30 days';

  select count(*) into v_contacts
    from public.revealed_contacts rc
   where rc.master_id = p_master
     and rc.created_at between v_start and v_end;

  select count(*) into v_resp
    from public.responses r
   where r.master_user_id = p_master
     and r.created_at between v_start and v_end;

  -- Заказы, которые мастер мог взять: его город и хотя бы одна его категория
  select count(*) into v_orders
    from public.orders o
   where o.created_at between v_start and v_end
     and o.city = v_city
     and (v_cats = '{}' or o.category = any(v_cats) or o.category = 'Другое');

  if v_contacts > 0 then
    return query select false, 'контакт открывали — заказы были'::text,
                        v_contacts, v_resp, v_orders, v_start, v_end;
  elsif v_resp < 3 and v_orders >= 3 then
    return query select false, 'подходящие заказы были, но откликов меньше трёх'::text,
                        v_contacts, v_resp, v_orders, v_start, v_end;
  else
    return query select true, 'ни один заказчик не вышел на связь'::text,
                        v_contacts, v_resp, v_orders, v_start, v_end;
  end if;
end
$$;

grant execute on function public.guarantee_status(uuid) to authenticated;

-- ── 3 · РОБОТ: ПРОДЛЕВАЕТ САМ ───────────────────────────────────
-- Просить не надо: в день окончания подписки проверяем и продлеваем.
create or replace function public.apply_subscription_guarantees()
returns int
language plpgsql
security definer
set search_path = public
as $$
declare
  r        record;
  st       record;
  v_count  int := 0;
begin
  for r in
    select p.id, p.subscription_end
      from public.profiles p
     where p.role = 'master'
       and p.subscription_plan in ('basic','pro','biz')   -- только платившие
       and p.subscription_end is not null
       and p.subscription_end <= now()
       and p.subscription_end > now() - interval '2 days' -- окно на сутки-двое
       and not exists (
             select 1 from public.subscription_guarantees g
              where g.master_id = p.id
                and g.period_end = p.subscription_end     -- за этот период уже продлевали
           )
  loop
    select * into st from public.guarantee_status(r.id);
    if st.eligible then
      insert into public.subscription_guarantees
        (master_id, period_start, period_end, extended_to,
         contacts_open, responses_made, orders_available)
      values
        (r.id, st.period_start, st.period_end, r.subscription_end + interval '30 days',
         st.contacts_open, st.responses_made, st.orders_available);

      update public.profiles
         set subscription_end = r.subscription_end + interval '30 days'
       where id = r.id;

      v_count := v_count + 1;
    end if;
  end loop;
  return v_count;
end
$$;

-- ── 4 · ЕЖЕДНЕВНЫЙ ЗАПУСК ───────────────────────────────────────
-- pg_cron уже используется в проекте (notify-subscriptions-daily).
select cron.unschedule('subscription-guarantees-daily')
 where exists (select 1 from cron.job where jobname = 'subscription-guarantees-daily');

select cron.schedule(
  'subscription-guarantees-daily',
  '15 9 * * *',
  $$ select public.apply_subscription_guarantees(); $$
);

-- ── 5 · ПРОВЕРКА ────────────────────────────────────────────────
select jobname, schedule, active from cron.job
 where jobname in ('subscription-guarantees-daily','notify-subscriptions-daily');
