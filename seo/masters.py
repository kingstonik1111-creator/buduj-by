#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BUDUJ.BY · генератор персональных страниц мастеров.

Создаёт:
    master/index.html            — каталог мастеров со страницами
    master/<slug>/index.html     — личная страница мастера
и обновляет sitemap.xml.

Запуск (нужен интернет — берёт данные из Supabase):
    python3 seo/masters.py

Ключ и адрес Supabase читаются из masters.html, чтобы не хранить их
отдельно и не рассинхронизироваться. Ключ публичный по назначению —
он и так лежит в коде сайта.

ПОРОГ: страница создаётся мастеру, у которого не меньше MIN_PHOTOS
фотографий работ. Смысл двойной: мастеру не стыдно давать ссылку,
а поисковик не считает страницу пустышкой.

Папка master/ каждый раз пересобирается с нуля. Это важно: если мастер
удалил фотографии или ушёл, его страница должна исчезнуть, а не висеть.
"""

import os
import re
import json
import html
import shutil
import urllib.request
import urllib.parse
from datetime import date

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = "https://buduj.by"
OUT_DIR = os.path.join(ROOT, "master")
MIN_PHOTOS = 5
TODAY = date.today().isoformat()

FIELDS = ("id,name,spec,categories,city,rating,reviews_count,"
          "avatar_url,portfolio_urls,is_verified,verified_status,bio")

# ─────────────────────────────────────────────────────────────
# Данные
# ─────────────────────────────────────────────────────────────


def read_credentials():
    """Достаёт адрес проекта и публичный ключ из masters.html."""
    src = open(os.path.join(ROOT, "masters.html"), encoding="utf-8").read()
    url = re.search(r"https://[a-z0-9]+\.supabase\.co", src)
    key = re.search(r"sb_publishable_[A-Za-z0-9_-]+", src)
    if not url or not key:
        raise SystemExit("Не нашёл адрес Supabase или ключ в masters.html")
    return url.group(0), key.group(0)


def fetch_masters():
    base, key = read_credentials()
    q = urllib.parse.urlencode({
        "select": FIELDS,
        "role": "eq.master",
        "order": "rating.desc",
        "limit": "500",
    })
    req = urllib.request.Request(
        f"{base}/rest/v1/profiles?{q}",
        headers={"apikey": key, "Authorization": f"Bearer {key}"},
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))


# ─────────────────────────────────────────────────────────────
# Вспомогательное
# ─────────────────────────────────────────────────────────────

TRANSLIT = {
    'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'e',
    'ж': 'zh', 'з': 'z', 'и': 'i', 'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm',
    'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u',
    'ф': 'f', 'х': 'h', 'ц': 'c', 'ч': 'ch', 'ш': 'sh', 'щ': 'sch',
    'ъ': '', 'ы': 'y', 'ь': '', 'э': 'e', 'ю': 'yu', 'я': 'ya',
    'і': 'i', 'ў': 'u', 'ґ': 'g', 'є': 'e', 'ї': 'i',
}


def translit(text):
    out = []
    for ch in (text or "").lower():
        out.append(TRANSLIT.get(ch, ch if ch.isalnum() else "-"))
    s = re.sub(r"-+", "-", "".join(out)).strip("-")
    return re.sub(r"[^a-z0-9-]", "", s)


def make_slug(m, taken):
    parts = [translit(m.get("name") or "master")]
    spec = translit(m.get("spec") or (m.get("categories") or [""])[0] if m.get("categories") else "")
    if spec:
        parts.append(spec)
    city = translit(m.get("city") or "")
    if city:
        parts.append(city)
    slug = "-".join(p for p in parts if p)[:70].strip("-") or "master"
    if slug in taken:                       # тёзки в одном городе
        slug = f"{slug}-{str(m['id'])[:6]}"
    taken.add(slug)
    return slug


def esc(t):
    return html.escape(str(t or ""), quote=False)


def photos_of(m):
    p = m.get("portfolio_urls")
    return [u for u in p if u] if isinstance(p, list) else []


# ─────────────────────────────────────────────────────────────
# Разметка
# ─────────────────────────────────────────────────────────────

METRIKA = r"""<script type="text/javascript">
    (function(m,e,t,r,i,k,a){
        m[i]=m[i]||function(){(m[i].a=m[i].a||[]).push(arguments)};
        m[i].l=1*new Date();
        for (var j = 0; j < document.scripts.length; j++) {if (document.scripts[j].src === r) { return; }}
        k=e.createElement(t),a=e.getElementsByTagName(t)[0],k.async=1,k.src=r,a.parentNode.insertBefore(k,a)
    })(window, document,'script','https://mc.yandex.ru/metrika/tag.js?id=110231398', 'ym');
    ym(110231398, 'init', {ssr:true, webvisor:true, clickmap:true, ecommerce:"dataLayer", referrer: document.referrer, url: location.href, accurateTrackBounce:true, trackLinks:true});
</script><noscript><div><img src="https://mc.yandex.ru/watch/110231398" style="position:absolute; left:-9999px;" alt="" /></div></noscript>"""

CSS = """
*{margin:0;padding:0;box-sizing:border-box}
:root{--bg:#1C1512;--bg2:#241B14;--gold:#F5A623;--white:#fff;--t2:#C4A882;
--t3:#9C8272;--border:rgba(245,166,35,0.25);--r:12px;--r2:8px}
body{background:var(--bg);color:var(--white);font-family:'Inter',system-ui,sans-serif;
font-size:16px;line-height:1.65;-webkit-font-smoothing:antialiased}
a{color:var(--gold);text-decoration:none}
nav{position:sticky;top:0;z-index:100;background:rgba(28,21,18,0.97);
backdrop-filter:blur(16px);border-bottom:1px solid var(--border)}
.nav-inner{max-width:1140px;margin:0 auto;padding:14px 22px;display:flex;
align-items:center;justify-content:space-between;gap:16px}
.logo{font-family:'Plus Jakarta Sans',sans-serif;font-weight:800;font-size:21px;
color:var(--gold);letter-spacing:-0.5px}
.logo span{color:var(--white);opacity:0.45}
.nav-links{display:flex;gap:20px;font-size:14px}
.nav-links a{color:var(--t2)}
.btn{display:inline-block;background:var(--gold);color:#1C1512;font-weight:700;
font-size:15px;padding:14px 26px;border-radius:var(--r2);border:none;cursor:pointer}
.btn-ghost{background:transparent;color:var(--gold);border:1px solid var(--border)}
.wrap{max-width:900px;margin:0 auto;padding:0 22px}
.crumbs{font-size:13px;color:var(--t3);padding:20px 0 0}
.crumbs a{color:var(--t3)}
.head{display:flex;gap:22px;align-items:flex-start;padding:22px 0 8px}
.ava{width:92px;height:92px;border-radius:50%;object-fit:cover;flex:none;
border:2px solid var(--border);background:var(--bg2)}
h1{font-family:'Plus Jakarta Sans',sans-serif;font-size:32px;line-height:1.2;
font-weight:800;letter-spacing:-0.8px;margin-bottom:6px}
.sub{color:var(--t2);font-size:17px}
.badges{display:flex;flex-wrap:wrap;gap:8px;margin-top:12px}
.badge{font-size:13px;color:var(--t2);background:var(--bg2);border:1px solid var(--border);
border-radius:20px;padding:5px 13px}
.badge.gold{color:var(--gold)}
h2{font-family:'Plus Jakarta Sans',sans-serif;font-size:23px;font-weight:800;
margin:36px 0 12px;letter-spacing:-0.5px}
p{color:var(--t2);margin-bottom:14px}
.gallery{display:grid;grid-template-columns:repeat(auto-fill,minmax(230px,1fr));gap:12px}
.gallery img{width:100%;aspect-ratio:4/3;object-fit:cover;border-radius:var(--r);
border:1px solid var(--border);background:var(--bg2);display:block}
.cta-box{margin:32px 0;background:var(--bg2);border:1px solid var(--border);
border-left:3px solid var(--gold);border-radius:var(--r);padding:22px 24px}
.cta-box p{margin-bottom:14px;font-size:15px}
.cta-row{display:flex;gap:12px;flex-wrap:wrap}
.note{color:var(--t3);font-size:14px}
.card-list{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));
gap:14px;margin:24px 0}
.mcard{display:block;background:var(--bg2);border:1px solid var(--border);
border-radius:var(--r);padding:18px 20px}
.mcard h3{font-family:'Plus Jakarta Sans',sans-serif;font-size:18px;font-weight:800;
color:var(--white);margin-bottom:4px}
.mcard p{font-size:14px;margin:0;color:var(--t2)}
footer{border-top:1px solid var(--border);margin-top:56px;padding:26px 22px 40px;
text-align:center;color:var(--t3);font-size:13px}
footer a{color:var(--t3);margin:0 7px}
@media(max-width:640px){h1{font-size:25px}.nav-links{display:none}.wrap{padding:0 16px}
.head{gap:16px}.ava{width:68px;height:68px}}
"""

NAV = """<nav>
  <div class="nav-inner">
    <a href="/index.html" class="logo">BUDUJ<span>.BY</span></a>
    <div class="nav-links">
      <a href="/masters.html">Мастера</a>
      <a href="/jobs.html">Заказы</a>
      <a href="/blog/">Блог</a>
      <a href="/for-masters.html">Для мастеров</a>
    </div>
    <a class="btn" href="/orders.html">Разместить заказ</a>
  </div>
</nav>"""

FOOTER = """<footer>
  © 2026 BUDUJ.BY · Маркетплейс строительных услуг в Беларуси<br>
  <a href="/oferta.html">Публичная оферта</a>
  <a href="/oplata.html">Оплата и возврат</a>
  <a href="/privacy.html">Конфиденциальность</a>
</footer>"""

HEAD = """<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<link rel="icon" type="image/x-icon" href="/favicon.ico">
<link rel="icon" href="/favicon.svg">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Plus+Jakarta+Sans:wght@700;800&display=swap" rel="stylesheet">"""


def build_master(m, slug):
    url = f"{SITE}/master/{slug}/"
    name = m.get("name") or "Мастер"
    city = m.get("city") or "Беларусь"
    spec = m.get("spec") or ""
    cats = [c for c in (m.get("categories") or []) if c]
    pics = photos_of(m)
    reviews = int(m.get("reviews_count") or 0)
    rating = m.get("rating")

    what = spec or (cats[0] if cats else "Мастер по ремонту")
    title = f"{name} — {what}, {city} | BUDUJ.BY"[:70]
    desc = (f"{name}: {what} в городе {city}. "
            f"{len(pics)} фотографий выполненных работ, "
            f"{'отзывы заказчиков, ' if reviews else ''}"
            f"договор до начала работ. Профиль на BUDUJ.BY.")

    badges = ""
    if m.get("is_verified") or m.get("verified_status") == "verified":
        badges += '<span class="badge gold">Документы проверены</span>'
    if reviews:
        badges += f'<span class="badge">Отзывов: {reviews}</span>'
        if rating:
            badges += f'<span class="badge">Рейтинг {rating}</span>'
    badges += f'<span class="badge">Фото работ: {len(pics)}</span>'
    for c in cats[:6]:
        badges += f'<span class="badge">{esc(c)}</span>'

    gallery = "".join(
        f'<img src="{esc(u)}" alt="{esc(name)} — {esc(what)}, пример работы" loading="lazy">'
        for u in pics[:24]
    )

    bio = (m.get("bio") or "").strip()
    bio_html = f"  <h2>О мастере</h2>\n  <p>{esc(bio)}</p>\n" if bio else ""

    person = {
        "@type": "Person",
        "name": name,
        "jobTitle": what,
        "address": {"@type": "PostalAddress", "addressLocality": city,
                    "addressCountry": "BY"},
        "url": url,
        "worksFor": {"@type": "Organization", "name": "BUDUJ.BY", "url": SITE},
    }
    if pics:
        person["image"] = pics[0]
    # Рейтинг отдаём разметке только если отзывы реальные и их больше нуля
    if reviews and rating:
        person["aggregateRating"] = {
            "@type": "AggregateRating",
            "ratingValue": rating,
            "reviewCount": reviews,
            "bestRating": 5,
        }

    ld = {"@context": "https://schema.org", "@graph": [person, {
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "BUDUJ.BY", "item": SITE + "/"},
            {"@type": "ListItem", "position": 2, "name": "Мастера", "item": f"{SITE}/master/"},
            {"@type": "ListItem", "position": 3, "name": name, "item": url},
        ],
    }]}

    ava = m.get("avatar_url") or (pics[0] if pics else "")
    ava_html = f'<img class="ava" src="{esc(ava)}" alt="{esc(name)}">' if ava else ""

    return f"""<!DOCTYPE html>
<html lang="ru">
<head>
{HEAD}
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<link rel="canonical" href="{url}">
<meta property="og:type" content="profile">
<meta property="og:url" content="{url}">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:image" content="{esc(pics[0] if pics else SITE + '/og.jpg')}">
<meta property="og:locale" content="ru_BY">
<style>{CSS}</style>
<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>
</head>
<body>
{NAV}
<div class="wrap">
  <div class="crumbs"><a href="/index.html">BUDUJ.BY</a> → <a href="/master/">Мастера</a> → {esc(name)}</div>

  <div class="head">
    {ava_html}
    <div>
      <h1>{esc(name)}</h1>
      <div class="sub">{esc(what)} · {esc(city)}</div>
      <div class="badges">{badges}</div>
    </div>
  </div>

{bio_html}
  <h2>Фотографии выполненных работ</h2>
  <div class="gallery">{gallery}</div>
  <p class="note" style="margin-top:12px">Все фотографии загружены самим мастером.</p>

  <div class="cta-box">
    <p>Нужен {esc(what.lower())} в городе {esc(city)}? Напишите мастеру
    через платформу или опишите задачу — откликнутся и другие исполнители.</p>
    <div class="cta-row">
      <a class="btn" href="/profile.html?id={esc(m['id'])}">Связаться с мастером</a>
      <a class="btn btn-ghost" href="/orders.html?city={urllib.parse.quote(city)}">Разместить заказ</a>
    </div>
  </div>

  <h2>Как это работает</h2>
  <p>До начала работ подписывается договор, где зафиксированы объём, сроки
  и цена. Оплата — напрямую мастеру и после выполнения. Платформа не берёт
  процент с заказа.</p>
</div>
{FOOTER}
{METRIKA}
</body>
</html>
"""


def build_index(items):
    url = f"{SITE}/master/"
    cards = "".join(
        f'<a class="mcard" href="/master/{s}/"><h3>{esc(m.get("name"))}</h3>'
        f'<p>{esc(m.get("spec") or (m.get("categories") or ["Мастер"])[0])} · '
        f'{esc(m.get("city") or "")} · фото: {len(photos_of(m))}</p></a>'
        for s, m in items
    )
    desc = ("Мастера по ремонту и строительству с фотографиями выполненных "
            "работ. Личные страницы исполнителей на BUDUJ.BY.")
    return f"""<!DOCTYPE html>
<html lang="ru">
<head>
{HEAD}
<title>Мастера с фото работ — личные страницы | BUDUJ.BY</title>
<meta name="description" content="{esc(desc)}">
<link rel="canonical" href="{url}">
<meta property="og:type" content="website">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{SITE}/og.jpg">
<style>{CSS}</style>
</head>
<body>
{NAV}
<div class="wrap">
  <div class="crumbs"><a href="/index.html">BUDUJ.BY</a> → Мастера</div>
  <h1 style="margin-top:16px">Мастера с фотографиями работ</h1>
  <p>У каждого мастера — своя страница с портфолио. Личную страницу
  получает исполнитель, загрузивший не меньше {MIN_PHOTOS} фотографий
  выполненных работ.</p>
  <div class="card-list">{cards}</div>
  <div class="cta-box">
    <p>Вы мастер? Заполните профиль, загрузите фотографии работ —
    и получите такую же страницу. Бесплатно.</p>
    <div class="cta-row"><a class="btn" href="/for-masters.html">Создать профиль</a></div>
  </div>
</div>
{FOOTER}
{METRIKA}
</body>
</html>
"""


def update_sitemap(paths):
    """Переписывает раздел /master/ в карте сайта целиком."""
    sp = os.path.join(ROOT, "sitemap.xml")
    s = open(sp, encoding="utf-8").read()
    s = re.sub(r"\s*<url>\s*<loc>https://buduj\.by/master/[^<]*</loc>.*?</url>",
               "", s, flags=re.S)
    block = ""
    for p in paths:
        block += (f"  <url>\n    <loc>{SITE}{p}</loc>\n"
                  f"    <lastmod>{TODAY}</lastmod>\n"
                  f"    <changefreq>weekly</changefreq>\n"
                  f"    <priority>0.7</priority>\n  </url>\n")
    s = s.replace("</urlset>", block + "</urlset>")
    open(sp, "w", encoding="utf-8").write(s)
    print(f"sitemap.xml: адресов мастеров — {len(paths)}")


def main():
    data = fetch_masters()
    print(f"получено профилей мастеров: {len(data)}")
    if not data:
        print("ВНИМАНИЕ: база вернула пусто. Вероятная причина — RLS "
              "отдаёт анониму только мастеров с активной подпиской.")

    good = [m for m in data if len(photos_of(m)) >= MIN_PHOTOS]
    print(f"из них с {MIN_PHOTOS}+ фотографиями: {len(good)}")

    if os.path.isdir(OUT_DIR):
        shutil.rmtree(OUT_DIR)
    os.makedirs(OUT_DIR, exist_ok=True)

    taken, items, paths = set(), [], ["/master/"]
    for m in good:
        slug = make_slug(m, taken)
        d = os.path.join(OUT_DIR, slug)
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, "index.html"), "w", encoding="utf-8") as f:
            f.write(build_master(m, slug))
        items.append((slug, m))
        paths.append(f"/master/{slug}/")
        print(f"  создано: /master/{slug}/  ({len(photos_of(m))} фото)")

    if not items:
        # Пустой каталог публиковать нельзя: страница без содержимого
        # для поисковика мусор, а мусор тянет вниз весь сайт.
        shutil.rmtree(OUT_DIR, ignore_errors=True)
        update_sitemap([])
        print("\nстраниц мастеров: 0 — каталог не публикуем, пока пусто")
        return

    with open(os.path.join(OUT_DIR, "index.html"), "w", encoding="utf-8") as f:
        f.write(build_index(items))

    update_sitemap(paths)
    print(f"\nстраниц мастеров: {len(items)}")


if __name__ == "__main__":
    main()
