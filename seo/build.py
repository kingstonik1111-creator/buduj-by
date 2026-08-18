#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BUDUJ.BY · генератор посадочных страниц под связку «услуга + город».

Запуск из корня репозитория:
    python3 seo/build.py

Создаёт файлы вида  minsk/elektrik/index.html  — то есть адрес
https://buduj.by/minsk/elektrik/ без параметров и без .html

Чтобы добавить новую страницу, достаточно дописать город в CITIES
или услугу в SERVICES и запустить скрипт заново. Ничего вручную
править не нужно.
"""

import os
import json
import html
from datetime import date

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = "https://buduj.by"
PHONE = "+375259138172"
PHONE_HUMAN = "+375 25 913-81-72"

# ─────────────────────────────────────────────────────────────
# ГОРОДА
# name      — именительный падеж, для заголовков-перечислений
# loc       — предложный падеж с предлогом: «в Минске»
# gen       — родительный: «Минска»
# ─────────────────────────────────────────────────────────────
CITIES = {
    "minsk": {
        "name": "Минск", "loc": "в Минске", "gen": "Минска",
        "context": (
            "Минск — самый большой рынок ремонта в стране, и самый разный. "
            "Панельные микрорайоны шестидесятых-восьмидесятых годов соседствуют "
            "с новостройками последних лет, и требования к работе в них "
            "отличаются принципиально."
        ),
    },
    "brest": {
        "name": "Брест", "loc": "в Бресте", "gen": "Бреста",
        "context": (
            "В Бресте довоенная застройка центра соседствует с панельными "
            "микрорайонами. Дома старого фонда — это толстые стены, "
            "нестандартные размеры проёмов и коммуникации, которые "
            "перекладывали не по одному разу."
        ),
    },
    "grodno": {
        "name": "Гродно", "loc": "в Гродно", "gen": "Гродно",
        "context": (
            "Гродно — город с сохранившимся историческим центром и обширными "
            "панельными районами вокруг. Работа в старом доме почти всегда "
            "требует больше времени: планировки нестандартные, а что скрыто "
            "в стенах, выясняется по ходу."
        ),
    },
    "vitebsk": {
        "name": "Витебск", "loc": "в Витебске", "gen": "Витебска",
        "context": (
            "Витебск был почти полностью разрушен в войну и отстроен заново, "
            "поэтому основная масса жилья здесь — послевоенная и панельная "
            "застройка. Планировки типовые, и это скорее плюс: мастер "
            "заранее понимает, с чем столкнётся."
        ),
    },
    "gomel": {
        "name": "Гомель", "loc": "в Гомеле", "gen": "Гомеля",
        "context": (
            "Гомель — второй по величине город страны, и основной его жилой "
            "фонд построен в семидесятые и восьмидесятые. Это значит типовые "
            "планировки и коммуникации, которым по сорок-пятьдесят лет."
        ),
    },
    "mogilev": {
        "name": "Могилёв", "loc": "в Могилёве", "gen": "Могилёва",
        "context": (
            "В Могилёве сталинская застройка центра соседствует с панельными "
            "районами шестидесятых-восьмидесятых. Дом довоенной или сталинской "
            "постройки почти всегда означает более трудоёмкую работу."
        ),
    },
}


# ─────────────────────────────────────────────────────────────
# УСЛУГИ
# cat        — категория в базе, попадает в ссылку на каталог мастеров
# prices     — реальные ценники с главной страницы, менять только вместе с ней
# includes   — что входит в работу
# timing     — сколько занимает
# mistakes   — типичные ошибки, ради которых страницу и читают
# faq        — вопрос-ответ, уходит в разметку FAQPage
# ─────────────────────────────────────────────────────────────
SERVICES = {
    "elektrik": {
        "old_stock": (
            "Для электрики возраст дома решает почти всё. В домах, построенных до девяностых, обычно стоит алюминиевая проводка сечением 1,5 мм². Она рассчитана на телевизор и лампочку, а не на духовку, стиральную машину и кондиционер одновременно. Алюминий со временем становится хрупким, а в местах скруток греется. Поэтому в старом фонде разговор почти всегда заканчивается заменой линий целиком, а не заменой одной розетки."
        ),
        
        "title_word": "Электрик",
        "cat": "Электрика",
        "lead": "от 15 BYN за точку",
        "lead_short": "от 15 BYN/точка",
        "intro": (
            "Электрика — единственная работа в квартире, где ошибка стоит не денег, "
            "а пожара. Поэтому здесь важнее не цена за точку, а то, видно ли, "
            "что человек делал раньше: как уложены линии в штробе, как собран щиток, "
            "подписаны ли автоматы."
        ),
        "prices": [
            ("Монтаж проводки", "от 15 BYN/точка"),
            ("Розетки и выключатели", "от 8 BYN/шт"),
            ("Замена электрощитка", "от 80 BYN"),
            ("Монтаж освещения", "от 10 BYN/точка"),
            ("Тёплый пол электрический", "от 25 BYN/м²"),
            ("Замена счётчика", "от 50 BYN"),
            ("Аварийный вызов", "от 35 BYN"),
            ("Заземление дома", "от 120 BYN"),
        ],
        "includes": [
            "выезд и осмотр объекта, замер и расчёт до начала работ",
            "штробление стен под кабель, если разводка скрытая",
            "прокладка кабеля, установка подрозетников, монтаж точек",
            "сборка и подключение щитка, маркировка автоматов",
            "проверка линий под нагрузкой и уборка за собой",
        ],
        "timing": (
            "Замена розетки или выключателя — от получаса. Щиток в квартире — "
            "день. Полная разводка в двухкомнатной квартире — от трёх до пяти дней, "
            "в зависимости от количества точек и того, штробятся стены или нет."
        ),
        "mistakes": [
            (
                "Считать по количеству розеток, а не точек",
                "Точка — это любой вывод: розетка, выключатель, светильник, вывод "
                "под технику. В смете их обычно вдвое больше, чем кажется на глаз. "
                "Просите посчитать точки до начала, а не после.",
            ),
            (
                "Экономить на сечении кабеля",
                "Кабель на розеточную группу тоньше 2,5 мм² — это не экономия, "
                "а отложенная проблема. Разница в цене на квартиру измеряется "
                "десятками рублей, последствия — заменой всей линии.",
            ),
            (
                "Не требовать схему щитка",
                "Через год вы не вспомните, какой автомат за что отвечает, "
                "а следующий мастер потратит час на прозвонку. Подписанный щиток "
                "и схема на бумаге — норма, а не любезность.",
            ),
        ],
        "faq": [
            (
                "Сколько стоит вызвать электрика {loc}?",
                "Аварийный выезд — от 35 BYN. Стоимость самих работ считается "
                "по точкам: монтаж проводки от 15 BYN за точку, установка розетки "
                "от 8 BYN. Точную сумму мастер называет после осмотра.",
            ),
            (
                "Нужно ли покупать материалы самому?",
                "Как правило, кабель, автоматы и подрозетники покупает заказчик — "
                "так прозрачнее по деньгам. Мастер составляет список с сечениями "
                "и количеством, с ним можно идти в магазин.",
            ),
            (
                "Даёт ли мастер гарантию?",
                "На платформе работа начинается с договора, где зафиксированы объём, "
                "сроки и цена. Гарантию на свои работы мастер несёт лично.",
            ),
            (
                "Как быстро приедет мастер?",
                "На аварийные заявки мастера обычно откликаются в течение дня. "
                "Плановые работы согласуются на удобную дату.",
            ),
        ],
    },
    "santehnik": {
        "old_stock": (
            "В домах советской постройки стояки чугунные, а разводка стальная. Чугун за полвека зарастает изнутри, сталь ржавеет по резьбе. Отсюда главное правило работы в старом фонде: трогать стояк без готовности заменить его целиком — плохая идея, потому что резьба на соседнем участке может не выдержать. В новостройках разводка полипропиленовая, и там задача обычно проще и дешевле."
        ),
        
        "title_word": "Сантехник",
        "cat": "Сантехника",
        "lead": "от 20 BYN за метр трубы",
        "lead_short": "от 20 BYN/м",
        "intro": (
            "Сантехника делится на две разные истории. Первая — авария: течёт, "
            "и нужно сейчас. Вторая — замена стояка или разводки, когда есть время "
            "выбрать и сравнить. Цена и требования к мастеру в этих случаях "
            "отличаются сильно."
        ),
        "prices": [
            ("Замена труб", "от 20 BYN/м"),
            ("Установка унитаза", "от 40 BYN"),
            ("Монтаж ванны", "от 60 BYN"),
            ("Установка душевой кабины", "от 80 BYN"),
            ("Установка смесителей", "от 20 BYN"),
            ("Водяной тёплый пол", "от 35 BYN/м²"),
            ("Счётчики воды", "от 35 BYN"),
            ("Чистка канализации", "от 30 BYN"),
        ],
        "includes": [
            "выезд, осмотр, определение причины и расчёт стоимости",
            "перекрытие стояка и подготовка места работ",
            "демонтаж старого оборудования и вынос его из квартиры",
            "монтаж, подключение, опрессовка и проверка под давлением",
            "проверка на протечки после запуска воды",
        ],
        "timing": (
            "Установка смесителя — час. Унитаз или ванна — полдня. Полная замена "
            "разводки в санузле — два-три дня. Замена стояка требует согласования "
            "с ЖЭС и отключения воды по подъезду, это отдельная история по срокам."
        ),
        "mistakes": [
            (
                "Ставить дешёвую подводку",
                "Гибкая подводка — самое частое место протечки в квартире. "
                "Разница между дешёвой и нормальной в пределах десяти рублей, "
                "разница в последствиях — ремонт у соседей снизу.",
            ),
            (
                "Прятать соединения в стену наглухо",
                "Любое резьбовое соединение когда-нибудь потребует доступа. "
                "Если его замуровали в плитку, добираться придётся через плитку.",
            ),
            (
                "Менять трубы без счётчиков и обратных клапанов",
                "Пока стены открыты, поставить всё сразу дешевле. Возвращаться "
                "к этому через год — значит снова вскрывать отделку.",
            ),
        ],
        "faq": [
            (
                "Сколько стоит вызвать сантехника {loc}?",
                "Чистка канализации — от 30 BYN, установка смесителя — от 20 BYN, "
                "унитаза — от 40 BYN. Замена труб считается по метрам, от 20 BYN. "
                "Точную сумму мастер называет после осмотра.",
            ),
            (
                "Кто перекрывает стояк?",
                "Если работы требуют отключения стояка, это согласуется с ЖЭС. "
                "Мастер подскажет порядок, но заявку подаёт собственник.",
            ),
            (
                "Работают ли мастера в выходные?",
                "Аварийные заявки закрываются в том числе в выходные. Плановые "
                "работы мастера обычно согласуют на будни.",
            ),
            (
                "Что делать при протечке прямо сейчас?",
                "Перекрыть воду на вводе в квартиру и разместить срочную заявку. "
                "На аварии мастера откликаются быстрее всего.",
            ),
        ],
    },
    "plitochnik": {
        "old_stock": (
            "В панельных домах стены ровными не бывают: перепад в два-три сантиметра на стену — обычное дело. Плитка этот перепад не скрывает, она его повторяет, поэтому выравнивание основания в смете почти неизбежно. В новостройках со свежей штукатуркой этой статьи расходов может не быть — но проверять ровность всё равно нужно до закупки плитки."
        ),
        
        "title_word": "Плиточник",
        "cat": "Плитка",
        "lead": "от 18 BYN за квадратный метр",
        "lead_short": "от 18 BYN/м²",
        "intro": (
            "Плитка — работа, где качество видно невооружённым глазом и через "
            "десять лет. Ровность шва, совпадение рисунка на углах, отсутствие "
            "пустот под плиткой — по этим трём вещам и стоит смотреть фотографии "
            "прошлых работ, а не по общему виду ванной."
        ),
        "prices": [
            ("Плитка в ванной", "от 20 BYN/м²"),
            ("Плитка на кухне", "от 18 BYN/м²"),
            ("Керамогранит", "от 22 BYN/м²"),
            ("Мозаика и декор", "от 35 BYN/м²"),
            ("Гидроизоляция", "от 15 BYN/м²"),
            ("Демонтаж старой плитки", "от 8 BYN/м²"),
        ],
        "includes": [
            "замер помещения и расчёт количества плитки с запасом на подрезку",
            "демонтаж старого покрытия и вынос строительного мусора",
            "выравнивание основания, без него ровной укладки не бывает",
            "гидроизоляция мокрых зон в санузле",
            "укладка, подрезка, затирка швов и финальная уборка",
        ],
        "timing": (
            "Ванная комната под ключ — от пяти до десяти дней с учётом "
            "выравнивания и высыхания. Фартук на кухне — один-два дня. "
            "Пол в комнате керамогранитом — два-три дня."
        ),
        "mistakes": [
            (
                "Класть плитку на кривые стены",
                "Клеевой слой не выравнивает стену, он её повторяет. Если "
                "основание кривое, это будет видно на швах. Выравнивание "
                "стоит денег, но без него результат предсказуемо плохой.",
            ),
            (
                "Экономить на гидроизоляции",
                "В санузле она стоит от 15 BYN за метр и делается один раз. "
                "Без неё через пару лет протечка обнаружится у соседей, "
                "а вскрывать придётся всю готовую плитку.",
            ),
            (
                "Покупать плитку впритык",
                "На подрезку уходит от десяти процентов, а на сложной раскладке "
                "больше. Докупить из той же партии через месяц почти невозможно: "
                "оттенок будет отличаться.",
            ),
        ],
        "faq": [
            (
                "Сколько стоит положить плитку {loc}?",
                "Плитка на кухне — от 18 BYN/м², в ванной — от 20 BYN/м², "
                "керамогранит — от 22 BYN/м². Демонтаж старой плитки считается "
                "отдельно, от 8 BYN/м².",
            ),
            (
                "Входит ли выравнивание стен в цену укладки?",
                "Обычно нет, это отдельная работа. Уточняйте до начала: "
                "разница в итоговой смете может быть заметной.",
            ),
            (
                "Сколько плитки покупать?",
                "Площадь плюс десять процентов на подрезку. При укладке "
                "по диагонали или со сложным рисунком — плюс пятнадцать.",
            ),
            (
                "Как выбрать мастера по плитке?",
                "Смотрите фотографии его работ вблизи: ровность швов, углы, "
                "стыки у сантехники. На BUDUJ.BY фото работ есть у каждого мастера.",
            ),
        ],
    },
}

# ─────────────────────────────────────────────────────────────

METRIKA = r"""<script type="text/javascript">
    (function(m,e,t,r,i,k,a){
        m[i]=m[i]||function(){(m[i].a=m[i].a||[]).push(arguments)};
        m[i].l=1*new Date();
        for (var j = 0; j < document.scripts.length; j++) {if (document.scripts[j].src === r) { return; }}
        k=e.createElement(t),a=e.getElementsByTagName(t)[0],k.async=1,k.src=r,a.parentNode.insertBefore(k,a)
    })(window, document,'script','https://mc.yandex.ru/metrika/tag.js?id=110231398', 'ym');
    ym(110231398, 'init', {ssr:true, webvisor:true, clickmap:true, ecommerce:"dataLayer", referrer: document.referrer, url: location.href, accurateTrackBounce:true, trackLinks:true});
</script>
<noscript><div><img src="https://mc.yandex.ru/watch/110231398" style="position:absolute; left:-9999px;" alt="" /></div></noscript>"""

CSS = """
*{margin:0;padding:0;box-sizing:border-box}
:root{--bg:#1C1512;--bg2:#241B14;--bg3:#2E2219;--gold:#F5A623;--white:#fff;
--t2:#C4A882;--t3:#9C8272;--border:rgba(245,166,35,0.25);--r:12px;--r2:8px}
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
header.hero{padding:26px 0 40px}
h1{font-family:'Plus Jakarta Sans',sans-serif;font-size:38px;line-height:1.15;
font-weight:800;letter-spacing:-1px;margin-bottom:14px}
.lead{color:var(--t2);font-size:18px;max-width:640px}
.cta-box{margin-top:26px;background:var(--bg2);border:1px solid var(--border);
border-left:3px solid var(--gold);border-radius:var(--r);padding:22px 24px}
.cta-box p{color:var(--t2);font-size:15px;margin-bottom:16px}
.cta-row{display:flex;gap:12px;flex-wrap:wrap}
h2{font-family:'Plus Jakarta Sans',sans-serif;font-size:25px;font-weight:800;
margin:44px 0 14px;letter-spacing:-0.5px}
h3{font-size:17px;font-weight:700;margin-bottom:6px;color:var(--white)}
p{color:var(--t2);margin-bottom:14px}
table{width:100%;border-collapse:collapse;margin:6px 0 10px;font-size:15px}
td{padding:12px 4px;border-bottom:1px solid rgba(245,166,35,0.13);color:var(--t2)}
td.p{text-align:right;color:var(--white);font-weight:600;white-space:nowrap}
ul{list-style:none;margin-bottom:14px}
li{color:var(--t2);padding-left:22px;position:relative;margin-bottom:9px}
li::before{content:"";position:absolute;left:4px;top:11px;width:6px;height:6px;
border-radius:50%;background:var(--gold)}
.card{background:var(--bg2);border:1px solid var(--border);border-radius:var(--r);
padding:20px 22px;margin-bottom:12px}
.card p{margin:0;font-size:15px}
.faq dt{font-weight:700;margin-top:18px}
.faq dd{color:var(--t2);margin-top:5px}
.note{color:var(--t3);font-size:14px;font-style:italic}
.other{margin-top:44px;padding-top:22px;border-top:1px solid rgba(245,166,35,0.15)}
.other h3{font-size:15px;color:var(--t3);font-weight:600;margin-bottom:10px}
.other-links{display:flex;flex-wrap:wrap;gap:9px;margin-bottom:20px}
.other-links a{background:var(--bg2);border:1px solid var(--border);border-radius:20px;
padding:7px 15px;font-size:14px;color:var(--t2)}
footer{border-top:1px solid var(--border);margin-top:56px;padding:26px 22px 40px;
text-align:center;color:var(--t3);font-size:13px}
footer a{color:var(--t3);margin:0 7px}
@media(max-width:640px){h1{font-size:29px}.nav-links{display:none}.wrap{padding:0 16px}}
"""


def esc(t):
    return html.escape(t, quote=False)


def build_page(city_slug, city, svc_slug, svc):
    loc = city["loc"]
    word = svc["title_word"]
    url = f"{SITE}/{city_slug}/{svc_slug}/"

    title = f"{word} {loc} — вызов на дом, {svc['lead_short']} | BUDUJ.BY"
    desc = (
        f"{word} {loc}: {svc['lead']}. Мастера с фото выполненных работ, "
        f"договор до начала работ, без комиссии платформе. "
        f"Оставьте заявку — откликнутся исполнители рядом."
    )

    price_rows = "\n".join(
        f'      <tr><td>{esc(n)}</td><td class="p">{esc(p)}</td></tr>'
        for n, p in svc["prices"]
    )
    inc = "\n".join(f"      <li>{esc(x)}</li>" for x in svc["includes"])
    mist = "\n".join(
        f'    <div class="card"><h3>{esc(h)}</h3><p>{esc(b)}</p></div>'
        for h, b in svc["mistakes"]
    )
    faq_pairs = [(q.format(loc=loc), a) for q, a in svc["faq"]]
    faq = "\n".join(
        f"      <dt>{esc(q)}</dt>\n      <dd>{esc(a)}</dd>" for q, a in faq_pairs
    )

    ld = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "Service",
                "name": f"{word} {loc}",
                "serviceType": svc["cat"],
                "areaServed": {"@type": "City", "name": city["name"]},
                "provider": {
                    "@type": "Organization",
                    "name": "BUDUJ.BY",
                    "url": SITE,
                    "telephone": PHONE,
                },
                "url": url,
                "offers": [
                    {
                        "@type": "Offer",
                        "name": n,
                        "priceCurrency": "BYN",
                        "description": p,
                    }
                    for n, p in svc["prices"]
                ],
            },
            {
                "@type": "BreadcrumbList",
                "itemListElement": [
                    {"@type": "ListItem", "position": 1, "name": "BUDUJ.BY",
                     "item": SITE + "/"},
                    {"@type": "ListItem", "position": 2, "name": city["name"],
                     "item": f"{SITE}/{city_slug}/"},
                    {"@type": "ListItem", "position": 3,
                     "name": f"{word} {loc}", "item": url},
                ],
            },
            {
                "@type": "FAQPage",
                "mainEntity": [
                    {
                        "@type": "Question",
                        "name": q,
                        "acceptedAnswer": {"@type": "Answer", "text": a},
                    }
                    for q, a in faq_pairs
                ],
            },
        ],
    }

    other_cities = "".join(
        f'<a href="/{cs}/{svc_slug}/">{esc(c["name"])}</a>'
        for cs, c in CITIES.items() if cs != city_slug
    )
    other_svcs = "".join(
        f'<a href="/{city_slug}/{ss}/">{esc(sv["title_word"])} {esc(loc)}</a>'
        for ss, sv in SERVICES.items() if ss != svc_slug
    )

    return f"""<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<link rel="canonical" href="{url}">
<link rel="icon" type="image/x-icon" href="/favicon.ico">
<link rel="icon" href="/favicon.svg">
<meta property="og:type" content="website">
<meta property="og:url" content="{url}">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:image" content="{SITE}/og.jpg">
<meta property="og:locale" content="ru_BY">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Plus+Jakarta+Sans:wght@700;800&display=swap" rel="stylesheet">
<style>{CSS}</style>
<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>
</head>
<body>
<nav>
  <div class="nav-inner">
    <a href="/index.html" class="logo">BUDUJ<span>.BY</span></a>
    <div class="nav-links">
      <a href="/masters.html">Мастера</a>
      <a href="/jobs.html">Заказы</a>
      <a href="/for-masters.html">Для мастеров</a>
    </div>
    <a class="btn" href="/orders.html">Разместить заказ</a>
  </div>
</nav>

<div class="wrap">
  <div class="crumbs">
    <a href="/index.html">BUDUJ.BY</a> → {esc(city["name"])} → {esc(word)}
  </div>

  <header class="hero">
    <h1>{esc(word)} {esc(loc)} с фото выполненных работ</h1>
    <p class="lead">{esc(svc["intro"])}</p>
    <div class="cta-box">
      <p>Опишите задачу — заявку увидят мастера {esc(loc)}, которые работают
      по этому направлению. Размещение бесплатное, платформа не берёт процент
      с заказа.</p>
      <div class="cta-row">
        <a class="btn" href="/orders.html?cat={esc(svc["cat"])}&city={esc(city["name"])}">Разместить заказ</a>
        <a class="btn btn-ghost" href="tel:{PHONE}">{PHONE_HUMAN}</a>
      </div>
    </div>
  </header>

  <h2>Цены {esc(loc)}</h2>
  <table>
{price_rows}
  </table>
  <p class="note">Все цены указаны как нижняя граница. Точную сумму мастер
  называет после осмотра: объём и сложность на месте всегда видны лучше,
  чем по описанию.</p>

  <h2>Что входит в работу</h2>
  <ul>
{inc}
  </ul>

  <h2>Сколько занимает</h2>
  <p>{esc(svc["timing"])}</p>

  <h2>Особенности жилого фонда {esc(city["name"])}</h2>
  <p>{esc(city["context"])}</p>
  <p>{esc(svc["old_stock"])}</p>

  <h2>Типичные ошибки</h2>
{mist}

  <h2>Как это работает на BUDUJ.BY</h2>
  <p>Вы описываете задачу — мастера {esc(loc)} видят заявку и откликаются.
  Вы смотрите фотографии их прошлых работ, рейтинг и отзывы, выбираете
  и договариваетесь напрямую. Платформа не участвует в расчётах и не берёт
  процент: мастер платит только за доступ к заявкам.</p>
  <p>До начала работ подписывается договор, где зафиксированы объём, сроки
  и цена. Оплата — мастеру и после выполнения.</p>

  <h2>Вопросы и ответы</h2>
  <dl class="faq">
{faq}
  </dl>

  <div class="other">
    <h3>{esc(word)} в других городах</h3>
    <div class="other-links">{other_cities}</div>
    <h3>Другие услуги {esc(loc)}</h3>
    <div class="other-links">{other_svcs}</div>
  </div>

  <div class="cta-box" style="margin-top:40px">
    <p>Нужен {esc(word.lower())} {esc(loc)}? Опишите задачу — это займёт минуту.</p>
    <div class="cta-row">
      <a class="btn" href="/orders.html?cat={esc(svc["cat"])}&city={esc(city["name"])}">Разместить заказ бесплатно</a>
      <a class="btn btn-ghost" href="/masters.html?cat={esc(svc["cat"])}&city={esc(city["name"])}">Смотреть мастеров</a>
    </div>
  </div>
</div>

<footer>
  © 2026 BUDUJ.BY · Маркетплейс строительных услуг в Беларуси<br>
  <a href="/oferta.html">Публичная оферта</a>
  <a href="/oplata.html">Оплата и возврат</a>
  <a href="/privacy.html">Конфиденциальность</a>
</footer>
{METRIKA}
</body>
</html>
"""


def main():
    made = []
    for city_slug, city in CITIES.items():
        for svc_slug, svc in SERVICES.items():
            d = os.path.join(ROOT, city_slug, svc_slug)
            os.makedirs(d, exist_ok=True)
            path = os.path.join(d, "index.html")
            with open(path, "w", encoding="utf-8") as f:
                f.write(build_page(city_slug, city, svc_slug, svc))
            made.append(f"/{city_slug}/{svc_slug}/")
            print("создано:", os.path.relpath(path, ROOT))

    update_sitemap(made)
    print(f"\nвсего страниц: {len(made)}")


def update_sitemap(paths):
    """Дописывает новые адреса в sitemap.xml, не трогая существующие."""
    sp = os.path.join(ROOT, "sitemap.xml")
    s = open(sp, encoding="utf-8").read()
    today = date.today().isoformat()
    added = 0
    block = ""
    for p in paths:
        loc = SITE + p
        if loc in s:
            continue
        block += (
            f"  <url>\n    <loc>{loc}</loc>\n"
            f"    <lastmod>{today}</lastmod>\n"
            f"    <changefreq>weekly</changefreq>\n"
            f"    <priority>0.9</priority>\n  </url>\n"
        )
        added += 1
    if added:
        s = s.replace("</urlset>", block + "</urlset>")
        open(sp, "w", encoding="utf-8").write(s)
    print(f"sitemap.xml: добавлено адресов — {added}")


if __name__ == "__main__":
    main()
