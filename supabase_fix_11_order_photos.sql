-- BUDUJ.BY · фото к заявке · 16.08.2026
--
-- Было: previewOrderPhotos() рисовал превью через createObjectURL и всё.
-- Ни одного вызова загрузки в хранилище, колонки под фото у orders тоже
-- не было. Заказчик прикладывал снимки объекта, видел их на экране,
-- отправлял заказ — и они пропадали. Мастер не видел ничего.
--
-- А именно фото позволяют мастеру оценить объём без выезда и назвать
-- цену сразу. Без них он либо едет смотреть бесплатно, либо не берётся.
--
-- Выполнить в Supabase → SQL Editor → Run

alter table public.orders
  add column if not exists photos text[] default '{}';

-- Витрина заказов открыта всем, фото — часть описания задачи
create or replace function public.orders_public(
  p_city     text default null,
  p_category text default null,
  p_limit    int  default 60
)
returns table (
  id            uuid,
  created_at    timestamptz,
  title         text,
  city          text,
  category      text,
  budget        text,
  timing        text,
  photos        text[],
  responses_cnt bigint
)
language sql
security definer
set search_path = public
stable
as $$
  select
    o.id, o.created_at, o.title, o.city, o.category, o.budget, o.timing,
    coalesce(o.photos, '{}'),
    (select count(*) from public.responses r where r.order_id = o.id)
  from public.orders o
  where o.status = 'open'
    and (p_city     is null or p_city     = '' or o.city     = p_city)
    and (p_category is null or p_category = '' or o.category = p_category)
  order by o.created_at desc
  limit least(coalesce(p_limit, 60), 200)
$$;

revoke all on function public.orders_public(text, text, int) from public;
grant execute on function public.orders_public(text, text, int) to anon, authenticated;

-- ── ХРАНИЛИЩЕ ───────────────────────────────────────────────────
insert into storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
values ('order-photos', 'order-photos', true, 5242880,
        array['image/jpeg','image/png','image/webp','image/heic','image/heif'])
on conflict (id) do update
  set public = true,
      file_size_limit = 5242880,
      allowed_mime_types = excluded.allowed_mime_types;

-- Смотреть может кто угодно: заказ и так открыт мастерам
drop policy if exists "order_photos_read" on storage.objects;
create policy "order_photos_read" on storage.objects
  for select using (bucket_id = 'order-photos');

-- Загружать может любой — заявку размещают и без регистрации.
-- Ограничения: размер и типы файлов заданы на самом бакете выше.
drop policy if exists "order_photos_insert" on storage.objects;
create policy "order_photos_insert" on storage.objects
  for insert to anon, authenticated
  with check (bucket_id = 'order-photos');

-- ── СОЗДАНИЕ ЗАКАЗА: ПРИНИМАЕМ ФОТО ─────────────────────────────
create or replace function public.create_order_public(
  p_title    text,
  p_city     text,
  p_phone    text,
  p_name     text default null,
  p_category text default null,
  p_email    text default null,
  p_timing   text default null,
  p_budget   text default null,
  p_photos   text[] default '{}'
) returns uuid
language plpgsql
security definer
set search_path = public
as $$
declare
  v_token uuid;
begin
  if coalesce(btrim(p_title), '') = '' then raise exception 'Опишите задачу'; end if;
  if coalesce(btrim(p_city), '')  = '' then raise exception 'Выберите город'; end if;
  if length(coalesce(btrim(p_phone), '')) < 6 then raise exception 'Введите телефон'; end if;

  insert into public.orders (
    title, city, phone, name, category, email, timing, budget, photos, status, owner_id
  ) values (
    left(btrim(p_title), 2000),
    btrim(p_city),
    btrim(p_phone),
    left(btrim(coalesce(p_name, '')), 200),
    coalesce(nullif(btrim(coalesce(p_category, '')), ''), 'Другое'),
    nullif(btrim(coalesce(p_email, '')), ''),
    nullif(btrim(coalesce(p_timing, '')), ''),
    coalesce(nullif(btrim(coalesce(p_budget, '')), ''), 'Нужна смета'),
    coalesce(p_photos, '{}'),
    'open',
    auth.uid()
  )
  returning claim_token into v_token;

  return v_token;
end
$$;

revoke all on function public.create_order_public(text,text,text,text,text,text,text,text,text[]) from public;
grant execute on function public.create_order_public(text,text,text,text,text,text,text,text,text[])
  to anon, authenticated;

-- Проверка
select
  (select count(*) from storage.buckets where id='order-photos')      as "бакет",
  (select count(*) from information_schema.columns
    where table_name='orders' and column_name='photos')               as "колонка";
