-- BUDUJ.BY · завершение заказа · 16.08.2026
--
-- Было: статус заказа никогда не становился «выполнен». После принятия
-- мастера он навсегда застревал в in_progress. Из-за этого:
--   — момента «работа сдана» в системе не существовало, а это единственный
--     естественный повод попросить отзыв;
--   — отзыв можно было оставить только зайдя на профиль мастера вручную,
--     вне связи с заказом;
--   — площадка не знала, состоялась сделка или нет, и не могла показать
--     мастеру, что подписка окупилась.
--
-- Стало: заказчик отмечает исход. Три возможных: выполнен, не сложилось,
-- отменён. После «выполнен» открывается отзыв на принятого мастера.
--
-- Выполнить в Supabase → SQL Editor → Run

alter table public.orders
  add column if not exists completed_at timestamptz;

-- Допустимые статусы. Раньше ограничения не было вовсе — в колонку можно
-- было записать что угодно, и интерфейс молча ломался.
alter table public.orders drop constraint if exists orders_status_valid;
alter table public.orders add constraint orders_status_valid check (
  status in ('open','in_progress','done','failed','cancelled')
);

create index if not exists orders_status_idx on public.orders (status, created_at desc);

-- Проставляем время завершения автоматически, чтобы фронт не мог соврать
create or replace function public.orders_touch_completed()
returns trigger
language plpgsql
as $$
begin
  if new.status in ('done','failed','cancelled') and old.status not in ('done','failed','cancelled') then
    new.completed_at := now();
  end if;
  if new.status = 'open' then
    new.completed_at := null;
  end if;
  return new;
end
$$;

drop trigger if exists orders_touch_completed_trg on public.orders;
create trigger orders_touch_completed_trg
  before update of status on public.orders
  for each row execute function public.orders_touch_completed();

-- ── СКОЛЬКО СДЕЛОК СОСТОЯЛОСЬ ───────────────────────────────────
-- Первая настоящая метрика площадки: не регистрации, а доведённые
-- до конца работы. По ней же видно, окупается ли мастеру подписка.
create or replace function public.deals_stats(p_days int default 30)
returns table (
  orders_total   bigint,
  with_responses bigint,
  in_progress    bigint,
  done           bigint,
  failed         bigint
)
language sql
security definer
set search_path = public
stable
as $$
  select
    count(*),
    count(*) filter (where exists (select 1 from public.responses r where r.order_id = o.id)),
    count(*) filter (where o.status = 'in_progress'),
    count(*) filter (where o.status = 'done'),
    count(*) filter (where o.status = 'failed')
  from public.orders o
  where o.created_at > now() - (coalesce(p_days,30) || ' days')::interval
$$;

revoke all on function public.deals_stats(int) from public;
grant execute on function public.deals_stats(int) to authenticated;

-- Проверка
select * from public.deals_stats(365);
