-- BUDUJ.BY · исправление №2 от 16.08.2026
-- Единый справочник категорий на весь проект.
--
-- Что было: четыре несовместимых списка.
--   orders.html (12) · dashboard-мастер заказа (10) · jobs.html (12) · masters.html (8)
-- Мастера искали по свободному тексту spec через .includes() — совпадало
-- 2 категории из 8. Заказ из кабинета с «Укладка полов» не находился
-- фильтром «Укладка ламината / полов».
--
-- Стало: 12 категорий, одинаковых везде. У мастера — массив categories.
--
-- Выполнить в Supabase → SQL Editor → Run

-- ── 1 · КОЛОНКА У МАСТЕРА ───────────────────────────────────────
alter table public.profiles
  add column if not exists categories text[] default '{}';

create index if not exists profiles_categories_idx
  on public.profiles using gin (categories);

-- ВАЖНО: у анонимов доступ к profiles выдан поколоночно
-- (supabase_step2_lock_contacts.sql). Новую колонку надо открыть явно,
-- иначе каталог мастеров сломается для незалогиненных посетителей.
grant select (categories) on public.profiles to anon;

-- ── 2 · ПРИВОДИМ КАТЕГОРИИ ЗАКАЗОВ К НОВЫМ НАЗВАНИЯМ ────────────
update public.orders set category = case
  when category in ('Укладка плитки','Плитка')                        then 'Плитка'
  when category in ('Укладка ламината / полов','Укладка полов','Полы') then 'Полы и ламинат'
  when category in ('Ремонт квартир под ключ','Ремонт квартир')        then 'Ремонт квартир под ключ'
  when category in ('Покраска и штукатурка','Маляр-штукатур')          then 'Покраска и штукатурка'
  when category in ('Кровельные работы','Кровельщик')                  then 'Кровля'
  when category in ('Сварочные работы','Сварщик')                      then 'Сварка'
  when category in ('Установка дверей и окон')                         then 'Двери и окна'
  else category
end
where category is not null;

-- ── 3 · РАСКЛАДЫВАЕМ spec МАСТЕРА ПО КАТЕГОРИЯМ ─────────────────
-- spec — свободный текст («Электрик», «Полы, ламинат, паркет»).
-- Разбираем по корням слов. Что не опознали — оставляем пустым,
-- мастер выберет сам в кабинете.
update public.profiles p
   set categories = (
     select coalesce(array_agg(distinct c), '{}')
     from (
       select unnest(array[
         case when p.spec ~* 'электр'                      then 'Электрика' end,
         case when p.spec ~* 'сантехн|водопров|отоплен'     then 'Сантехника' end,
         case when p.spec ~* 'плиточ|плитк|кафел'          then 'Плитка' end,
         case when p.spec ~* 'пол|ламинат|паркет|линолеум' then 'Полы и ламинат' end,
         case when p.spec ~* 'маляр|штукат|покрас|шпакл'   then 'Покраска и штукатурка' end,
         case when p.spec ~* 'кровел|кровл|крыш'           then 'Кровля' end,
         case when p.spec ~* 'сварщ|сварк|сварочн'         then 'Сварка' end,
         case when p.spec ~* 'потолк'                      then 'Натяжные потолки' end,
         case when p.spec ~* 'двер|окн|остеклен'           then 'Двери и окна' end,
         case when p.spec ~* 'мебел|сборк|кухн'            then 'Мебель и сборка' end,
         case when p.spec ~* 'ремонт кварт|под ключ|отделк' then 'Ремонт квартир под ключ' end
       ]) as c
     ) t
     where c is not null
   )
 where p.role = 'master'
   and (p.categories is null or p.categories = '{}');

-- ── 4 · ПРОВЕРКА ────────────────────────────────────────────────
select
  count(*)                                        as "мастеров всего",
  count(*) filter (where categories <> '{}')      as "категории проставлены",
  count(*) filter (where categories =  '{}')      as "надо выбрать вручную"
from public.profiles
where role = 'master';

-- Посмотреть, кто что получил:
-- select name, spec, categories from public.profiles where role='master';
