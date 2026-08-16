-- BUDUJ.BY · исправление №1 от 16.08.2026
-- Отклик мастера теперь связывается с его профилем.
--
-- Что было: jobs.html писал responses.master_id, а весь остальной код
-- читает responses.master_user_id. Колонка master_user_id была пуста всегда.
-- Из-за этого не работали: чат заказчика с мастером, ссылка на профиль,
-- рейтинг в отклике, «Показать номер» с запоминанием и раздел
-- «Мои отклики» в кабинете мастера.
--
-- Код уже исправлен (jobs.html пишет master_user_id).
-- Здесь переливаем то, что накопилось раньше.
--
-- Выполнить в Supabase → SQL Editor → Run

-- ── 1 · СКОЛЬКО ОТКЛИКОВ ПОСТРАДАЛО ─────────────────────────────
-- (посмотреть до починки; можно выполнить отдельно)
select
  count(*) filter (where master_user_id is null and master_id is not null) as "потеряли связь",
  count(*) filter (where master_user_id is not null)                       as "уже в порядке",
  count(*) filter (where master_user_id is null and master_id is null)     as "без автора вовсе",
  count(*)                                                                 as "всего откликов"
from public.responses;

-- ── 2 · ПЕРЕЛИВАЕМ ──────────────────────────────────────────────
update public.responses
   set master_user_id = master_id
 where master_user_id is null
   and master_id is not null;

-- ── 3 · ЧТОБЫ НЕ ПОВТОРИЛОСЬ ────────────────────────────────────
-- Если фронт когда-нибудь снова запишет master_id вместо master_user_id,
-- триггер молча подставит правильную колонку.
create or replace function public.responses_sync_master()
returns trigger
language plpgsql
as $$
begin
  if new.master_user_id is null and new.master_id is not null then
    new.master_user_id := new.master_id;
  end if;
  return new;
end
$$;

drop trigger if exists responses_sync_master_trg on public.responses;
create trigger responses_sync_master_trg
  before insert or update on public.responses
  for each row execute function public.responses_sync_master();

-- ── 4 · ПРОВЕРКА ────────────────────────────────────────────────
-- Должно быть 0 в первой колонке:
-- select count(*) from public.responses
--  where master_user_id is null and master_id is not null;
