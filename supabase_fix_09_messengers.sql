-- BUDUJ.BY · мессенджеры мастера · 16.08.2026
--
-- Было: заказчику при открытии номера показывался WhatsApp — всем подряд,
-- без вопроса. Если у мастера его нет, заказчик пишет в пустоту, мастер
-- ничего не получает, и оба думают, что связались. Контакт теряется молча.
--
-- Стало: мастер сам отмечает, чем пользуется. Показываем только отмеченное.
-- Пусто — только кнопка «Позвонить»: лучше меньше, чем ложное обещание.
--
-- Выполнить в Supabase → SQL Editor → Run

alter table public.profiles
  add column if not exists messengers text[] default '{}';

-- Контакты мастера видны только вошедшим (колоночные гранты для anon
-- их не включают) — messengers анониму не открываем сознательно:
-- знать, чем пользуется мастер, нужно только после открытия контакта.
grant select (messengers) on public.profiles to authenticated;

-- Разрешаем только известные значения, чтобы фронт не рисовал мусор
alter table public.profiles
  drop constraint if exists profiles_messengers_valid;
alter table public.profiles
  add constraint profiles_messengers_valid check (
    messengers is null
    or messengers <@ array['whatsapp','viber','telegram']::text[]
  );

-- Проверка
select
  (select count(*) from information_schema.columns
    where table_name='profiles' and column_name='messengers') as "колонка есть",
  (select count(*) from public.profiles
    where role='master' and coalesce(array_length(messengers,1),0)=0) as "мастеров без выбора";
