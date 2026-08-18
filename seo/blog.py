#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BUDUJ.BY · генератор блога.

Запуск из корня репозитория:
    python3 seo/blog.py

Создаёт:
    blog/index.html                — список статей
    blog/<slug>/index.html         — статьи
и дописывает адреса в sitemap.xml.

Чтобы добавить статью — допиши запись в ARTICLES и запусти скрипт.

Формат тела статьи (список блоков):
    ("h2",   "Заголовок раздела")
    ("p",    "Абзац текста")
    ("ul",   ["пункт", "пункт"])
    ("table",[("строка","значение"), ...])
    ("note", "Выделенная врезка")
    ("cta",  ("Текст кнопки", "/minsk/elektrik/"))
"""

import os
import json
import html
from datetime import date

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = "https://buduj.by"
TODAY = "2026-08-18"

ARTICLES = {
    # ─────────────────────────────────────── для заказчиков
    "remont-vannoy-skolko-stoit": {
        "audience": "Заказчикам",
        "title": "Сколько стоит ремонт ванной под ключ в Беларуси",
        "seo_title": "Ремонт ванной под ключ: сколько стоит в Беларуси в 2026",
        "desc": "Разбираем смету ремонта ванной по частям: демонтаж, "
                "сантехника, плитка, электрика. С ценами за метр и примером "
                "расчёта для типовой ванной 3 м².",
        "date": "2026-08-18",
        "lead": "Цифра «от 1500 рублей» ничего не говорит, пока не понятно, "
                "из чего она складывается. Разберём смету по частям — и вы "
                "сможете проверить любую, которую вам принесут.",
        "body": [
            ("h2", "Из чего вообще состоит эта работа"),
            ("p", "Ремонт ванной — не одна услуга, а пять разных работ подряд, "
                  "и делают их обычно разные люди. Сначала демонтаж, потом "
                  "черновая сантехника и электрика, затем выравнивание "
                  "и гидроизоляция, потом плитка, в конце — чистовая "
                  "установка сантехники."),
            ("p", "Когда бригада называет цену «под ключ», она складывает "
                  "именно эти пять этапов. Если в смете нет какого-то из них, "
                  "это не значит, что работа не понадобится: значит, её "
                  "предъявят отдельным счётом посреди ремонта."),
            ("h2", "Цены по этапам"),
            ("p", "Ниже — расценки, по которым работают мастера на площадке. "
                  "Это нижняя граница: конкретная сумма зависит от состояния "
                  "помещения и сложности раскладки."),
            ("table", [
                ("Демонтаж старой плитки", "от 8 BYN/м²"),
                ("Замена труб", "от 20 BYN/м"),
                ("Электрика, точка", "от 15 BYN"),
                ("Гидроизоляция", "от 15 BYN/м²"),
                ("Укладка плитки в ванной", "от 20 BYN/м²"),
                ("Установка унитаза", "от 40 BYN"),
                ("Монтаж ванны", "от 60 BYN"),
                ("Установка смесителей", "от 20 BYN"),
                ("Вывоз строймусора", "от 60 BYN"),
            ]),
            ("h2", "Пример расчёта: типовая ванная 3 м²"),
            ("p", "Возьмём санузел в панельном доме: пол 3 м², стены "
                  "примерно 17 м² при высоте 2,5 метра. Считаем только "
                  "работу, без материалов."),
            ("table", [
                ("Демонтаж плитки, 20 м²", "160 BYN"),
                ("Замена труб, 6 м", "120 BYN"),
                ("Электрика, 4 точки", "60 BYN"),
                ("Гидроизоляция, 8 м²", "120 BYN"),
                ("Плитка, 20 м²", "400 BYN"),
                ("Унитаз, ванна, смеситель", "120 BYN"),
                ("Вывоз мусора", "60 BYN"),
                ("Итого работа", "около 1040 BYN"),
            ]),
            ("note", "Это стоимость работы. Материалы — плитка, клей, "
                     "затирка, трубы, сантехника — считаются отдельно "
                     "и обычно сопоставимы с работой или дороже её."),
            ("h2", "Почему сметы так сильно отличаются"),
            ("p", "Две сметы на одну и ту же ванную могут различаться вдвое, "
                  "и чаще всего дело не в жадности, а в том, что в них "
                  "заложены разные объёмы."),
            ("ul", [
                "Выравнивание стен. В панельном доме перепад в два-три "
                "сантиметра — норма. Плитка его не скрывает, а повторяет. "
                "Одна бригада заложила выравнивание, вторая — нет.",
                "Гидроизоляция. Стоит немного, экономят на ней часто, "
                "а обнаруживается это через пару лет у соседей снизу.",
                "Перенос коммуникаций. Сдвинуть унитаз на полметра — "
                "это работа со стояком, а не «мелочь».",
                "Формат плитки. Крупноформатный керамогранит и мозаика "
                "укладываются дольше обычной плитки, и цена за метр выше.",
            ]),
            ("h2", "Как проверить смету за пять минут"),
            ("p", "Задайте три вопроса, и станет понятно, с кем вы имеете "
                  "дело. Входит ли выравнивание стен и пола. Входит ли "
                  "гидроизоляция мокрых зон. Что произойдёт с ценой, если "
                  "после демонтажа обнаружится, что стены хуже, чем "
                  "казалось."),
            ("p", "Мастер, который работает честно, ответит на это спокойно "
                  "и конкретно. Мастер, который планировал добрать деньги "
                  "по ходу, начнёт уходить от ответа."),
            ("cta", ("Найти плиточника", "/minsk/plitochnik/")),
        ],
        "related": ["/minsk/plitochnik/", "/minsk/santehnik/"],
    },

    "pochemu-vybivaet-avtomat": {
        "audience": "Заказчикам",
        "title": "Почему выбивает автомат: шесть причин",
        "seo_title": "Почему выбивает автомат в квартире — 6 причин и что делать",
        "desc": "Разбираем, почему срабатывает автомат или УЗО: перегрузка, "
                "короткое замыкание, утечка, старая проводка. Что можно "
                "проверить самому и когда нужен электрик.",
        "date": "2026-08-18",
        "lead": "Автомат выбивает не «просто так». Он делает ровно то, для "
                "чего поставлен: отключает линию, пока она не начала гореть. "
                "Вопрос только в том, что именно он нашёл.",
        "body": [
            ("h2", "Сначала определите, что именно сработало"),
            ("p", "В щитке обычно стоят устройства двух типов, и они "
                  "защищают от разного. Автомат реагирует на слишком "
                  "большой ток: перегрузку или короткое замыкание. УЗО "
                  "или дифавтомат реагирует на утечку тока — когда часть "
                  "его уходит мимо провода, например через воду или через "
                  "человека."),
            ("p", "Понять, что сработало, важно: это две разные истории. "
                  "Перегрузка — бытовая ситуация. Утечка — почти всегда "
                  "неисправность, и её игнорировать нельзя."),
            ("h2", "Шесть причин, от частой к редкой"),
            ("ul", [
                "Перегрузка. Включили чайник, микроволновку и стиральную "
                "машину на одной линии. Самая частая причина в старых "
                "квартирах, где все розетки сидят на одном кабеле.",
                "Неисправный прибор. Что-то одно пробивает на корпус. "
                "Проверяется отключением всего и поочерёдным включением.",
                "Влага. Залило розетку, попала вода в подрозетник, "
                "отсырела линия на балконе. Обычно срабатывает УЗО.",
                "Старая проводка. Алюминий в скрутках со временем "
                "окисляется, контакт греется, изоляция сохнет и начинает "
                "пропускать ток.",
                "Ошибка монтажа. Пережатый при установке кабель, "
                "закушенный саморезом провод, перепутанные ноль и земля.",
                "Неисправный автомат. Случается реже всего, но бывает: "
                "автомат отработал ресурс и срабатывает от нормального тока.",
            ]),
            ("h2", "Что можно проверить самому"),
            ("p", "Безопасно и без инструментов можно сделать вот что. "
                  "Отключите от розеток всё, что подключено на проблемной "
                  "линии. Включите автомат. Если он держит — подключайте "
                  "приборы по одному, и виновник найдётся."),
            ("p", "Если автомат не включается вообще, при пустой линии, — "
                  "дальше самостоятельно лучше не идти. Это означает "
                  "замыкание в самой проводке, и искать его нужно "
                  "приборами."),
            ("note", "Никогда не ставьте автомат большего номинала, чтобы "
                     "«перестало выбивать». Автомат подобран под сечение "
                     "кабеля. Более мощный не защитит провод — он позволит "
                     "ему нагреваться до тех пор, пока не загорится изоляция."),
            ("h2", "Когда это признак того, что пора менять проводку"),
            ("p", "Есть несколько сигналов, при которых разговор идёт уже "
                  "не про один автомат, а про линии целиком: розетка "
                  "или щиток тёплые на ощупь, есть запах горелого пластика, "
                  "автомат выбивает всё чаще без видимой причины, в квартире "
                  "алюминиевая проводка и вы добавили мощную технику."),
            ("p", "В домах до девяностых стоит алюминий сечением 1,5 мм². "
                  "Он рассчитан на телевизор и лампочку, а не на духовку "
                  "с посудомойкой. Такая линия не «сломалась» — она просто "
                  "работает на пределе, для которого её делали."),
            ("cta", ("Вызвать электрика", "/minsk/elektrik/")),
        ],
        "related": ["/minsk/elektrik/"],
    },

    "kak-proverit-mastera": {
        "audience": "Заказчикам",
        "title": "Как проверить мастера до начала работ",
        "seo_title": "Как проверить мастера по ремонту — 7 способов не ошибиться",
        "desc": "Практическая проверка исполнителя: фото работ, документы, "
                "предоплата, договор. Признаки, по которым видно проблемного "
                "подрядчика ещё до начала ремонта.",
        "date": "2026-08-18",
        "lead": "Проверять мастера имеет смысл ровно до того, как он начал "
                "работу. После — выбор сводится к тому, доделывать с ним "
                "или переделывать за ним.",
        "body": [
            ("h2", "Смотрите фотографии, а не отзывы"),
            ("p", "Отзыв написать легко, фотографию работы — нет. Причём "
                  "смотреть надо не на общий вид «красивой ванной», "
                  "а на детали, которые видно только вблизи."),
            ("ul", [
                "Плитка: ровность швов, углы, стыки у труб и розеток.",
                "Электрика: как собран щиток, подписаны ли автоматы, "
                "как уложен кабель в штробе.",
                "Сантехника: доступ к соединениям, аккуратность подводки.",
            ]),
            ("p", "Если на всех фото объект снят издалека и под удачным "
                  "углом — это тоже информация."),
            ("h2", "Попросите телефон прошлого заказчика"),
            ("p", "Нормальный мастер даёт его без раздумий: у него есть "
                  "довольные клиенты, и они не против. Отказ под предлогом "
                  "«не могу давать чужие контакты» звучит вежливо, но "
                  "означает, что таких клиентов может не быть."),
            ("h2", "Проверьте, с кем вы имеете дело юридически"),
            ("p", "Мастер может работать как ИП, как самозанятый или "
                  "по трудовому договору в фирме. Любой вариант нормален, "
                  "ненормально другое: когда на вопрос о статусе человек "
                  "начинает нервничать."),
            ("p", "От статуса зависит, к кому вы предъявите претензию, "
                  "если работа окажется бракованной."),
            ("h2", "Обсудите деньги до начала, а не в процессе"),
            ("ul", [
                "Предоплата за работу — красный флаг. За материалы — норма, "
                "их действительно надо купить.",
                "Оплата по этапам — здоровая схема: закончили черновую, "
                "рассчитались, пошли дальше.",
                "Стопроцентная предоплата «по скидке» — способ потерять "
                "и деньги, и время.",
            ]),
            ("h2", "Требуйте договор"),
            ("p", "Договор нужен не чтобы судиться, а чтобы обе стороны "
                  "одинаково поняли объём. Большая часть конфликтов "
                  "в ремонте — не про обман, а про то, что заказчик считал "
                  "какую-то работу входящей, а мастер нет."),
            ("p", "Что в нём должно быть, разобрано отдельно: "
                  "перечень работ, сроки, цена и порядок её изменения."),
            ("h2", "Тревожные признаки"),
            ("ul", [
                "Называет цену не глядя на объект.",
                "Соглашается на любой ваш срок, даже нереальный.",
                "Резко снижает цену, если вы сомневаетесь.",
                "Отказывается от договора: «мы же по-человечески».",
                "Не может объяснить, почему делает именно так.",
            ]),
            ("cta", ("Смотреть мастеров с фото работ", "/masters.html")),
        ],
        "related": ["/minsk/elektrik/", "/minsk/santehnik/", "/minsk/plitochnik/"],
    },

    "dogovor-s-masterom": {
        "audience": "Заказчикам",
        "title": "Что должно быть в договоре с мастером",
        "seo_title": "Договор с мастером на ремонт: что в нём обязательно",
        "desc": "Разбор пунктов договора подряда на ремонт: объём работ, "
                "сроки, цена, порядок изменения сметы, гарантия, приёмка. "
                "Что проверить перед подписью.",
        "date": "2026-08-18",
        "lead": "Договор в ремонте нужен не для суда. Он нужен, чтобы "
                "через месяц вы и мастер одинаково помнили, о чём "
                "договорились.",
        "body": [
            ("h2", "Перечень работ — самое важное"),
            ("p", "Не «ремонт ванной», а список: демонтаж плитки, замена "
                  "труб, гидроизоляция, укладка плитки, установка "
                  "сантехники. С объёмами в метрах и штуках."),
            ("p", "Именно здесь возникает большинство конфликтов. Заказчик "
                  "считал, что вынос мусора входит. Мастер считал, что нет. "
                  "Оба правы, потому что не написано."),
            ("h2", "Цена и порядок её изменения"),
            ("p", "Цена фиксируется до начала. Но в ремонте почти всегда "
                  "вскрываются вещи, которых не было видно: гнилая труба "
                  "под плиткой, стена хуже, чем казалась."),
            ("p", "Поэтому важнее самой цены пункт о том, что происходит "
                  "при изменении объёма. Нормальная формулировка: "
                  "дополнительные работы выполняются только после "
                  "письменного согласования с заказчиком. Тогда вас "
                  "не поставят перед фактом."),
            ("h2", "Сроки"),
            ("ul", [
                "Дата начала и дата окончания.",
                "Что считается уважительной причиной задержки — например, "
                "отсутствие материалов, которые закупает заказчик.",
                "Что происходит при просрочке.",
            ]),
            ("h2", "Материалы: кто покупает и кто отвечает"),
            ("p", "Обычно материалы покупает заказчик — так прозрачнее "
                  "по деньгам. Тогда в договоре стоит зафиксировать, что "
                  "мастер даёт список с характеристиками заранее, а не "
                  "по ходу дела."),
            ("p", "Если материалы закупает мастер, пропишите, что чеки "
                  "передаются заказчику. Это нормальная практика, и "
                  "адекватного исполнителя такой пункт не оскорбит."),
            ("h2", "Приёмка и гарантия"),
            ("p", "Приёмка — это момент, когда вы осматриваете работу "
                  "и подписываете, что претензий нет. До подписи имеет "
                  "смысл проверить всё внимательно: после — доказывать "
                  "сложнее."),
            ("p", "Гарантия на работы — обычная практика. Срок стороны "
                  "определяют сами; важно, чтобы он был написан, а не "
                  "подразумевался."),
            ("note", "Договор подписывается в двух экземплярах. Экземпляр "
                     "без подписи второй стороны — просто бумага."),
            ("cta", ("Разместить заказ", "/orders.html")),
        ],
        "related": ["/masters.html"],
    },

    # ─────────────────────────────────────── для мастеров
    "skolko-zarabatyvaet-master": {
        "audience": "Мастерам",
        "title": "Сколько зарабатывает мастер по ремонту: считаем по расценкам",
        "seo_title": "Сколько зарабатывает мастер по ремонту в Беларуси — расчёт",
        "desc": "Считаем доход плиточника, электрика и сантехника исходя "
                "из реальных расценок за работу и загрузки. Честная "
                "арифметика без обещаний.",
        "date": "2026-08-18",
        "lead": "Ниже — не результат опроса и не средняя температура "
                "по рынку. Это арифметика: берём расценки, по которым "
                "работают мастера, умножаем на реальный объём за месяц "
                "и вычитаем то, что обычно забывают вычесть.",
        "body": [
            ("h2", "Откуда цифры"),
            ("p", "В расчёте используются расценки за работу, по которым "
                  "мастера выставляют цены на BUDUJ.BY. Это нижняя граница "
                  "рынка: опытный мастер с портфолио берёт выше, новичок "
                  "иногда ниже."),
            ("p", "Важная оговорка: всё, что ниже, — это модель, а не "
                  "гарантия. Реальный доход зависит от загрузки, а загрузка "
                  "у всех разная."),
            ("h2", "Плиточник"),
            ("p", "Укладка плитки в ванной — от 20 BYN/м². Ванная 3 м² "
                  "с учётом стен — это около 20 м² плитки и примерно "
                  "неделя работы с выравниванием и затиркой."),
            ("table", [
                ("Один санузел, работа", "около 400 BYN"),
                ("Плюс выравнивание и гидроизоляция", "около 250 BYN"),
                ("Итого за объект", "около 650 BYN"),
                ("Четыре объекта в месяц", "около 2600 BYN"),
            ]),
            ("h2", "Электрик"),
            ("p", "Монтаж проводки — от 15 BYN за точку. Двухкомнатная "
                  "квартира — это 40–60 точек и три-пять дней работы."),
            ("table", [
                ("Разводка в двушке, 50 точек", "около 750 BYN"),
                ("Щиток", "от 80 BYN"),
                ("Четыре-пять квартир в месяц", "около 3300 BYN"),
            ]),
            ("p", "Плюс аварийные вызовы: от 35 BYN за выезд, и они "
                  "заполняют промежутки между крупными объектами."),
            ("h2", "Что нужно вычесть"),
            ("p", "Эти суммы — оборот, а не доход. Из них уходит:"),
            ("ul", [
                "Налоги: ИП или самозанятость, ставка зависит от режима.",
                "Инструмент и расходники: диски, буры, мешки, ведра. "
                "Расходуется постоянно.",
                "Транспорт: перевозка инструмента между объектами.",
                "Простои. Это главная статья, и её всегда недооценивают. "
                "Между объектами бывают пустые недели.",
            ]),
            ("h2", "Простои решают больше, чем ставка"),
            ("p", "Разница между мастером, который зарабатывает нормально, "
                  "и мастером, который еле выходит в ноль, — обычно не "
                  "в цене за метр. Она в том, сколько дней в месяце он "
                  "работает."),
            ("p", "Мастер со ставкой 18 BYN за метр и полной загрузкой "
                  "зарабатывает больше, чем мастер со ставкой 25, "
                  "работающий две недели из четырёх. Поэтому вопрос "
                  "«где брать заказы» важнее вопроса «сколько брать "
                  "за метр»."),
            ("cta", ("Получать заказы", "/for-masters.html")),
        ],
        "related": ["/for-masters.html"],
    },

    "kak-poluchat-zakazy": {
        "audience": "Мастерам",
        "title": "Как получать заказы, когда сарафанное радио закончилось",
        "seo_title": "Как мастеру получать заказы на ремонт — рабочие каналы",
        "desc": "Каналы, откуда мастеру идут заказы: рекомендации, "
                "площадки, объявления, карты. Что работает, что нет "
                "и почему фото работ важнее описания.",
        "date": "2026-08-18",
        "lead": "Сарафанное радио — лучший источник заказов и худший "
                "способ планировать месяц. Оно работает, пока работает, "
                "и молчит именно тогда, когда нужнее всего.",
        "body": [
            ("h2", "Почему одного канала мало"),
            ("p", "Рекомендации приходят волнами: сделал ремонт в подъезде — "
                  "месяц звонков от соседей, потом тишина. Проблема не в "
                  "том, что канал плохой, а в том, что он один и вы им "
                  "не управляете."),
            ("p", "Задача — не заменить сарафан, а добавить рядом два-три "
                  "источника, которые дают заявки ровно."),
            ("h2", "Что реально работает"),
            ("ul", [
                "Площадки с заявками. Заказчик описывает задачу, вы "
                "откликаетесь. Плюс в том, что человек уже решил делать "
                "ремонт — его не надо убеждать.",
                "Карты. Карточка в Яндекс.Бизнесе бесплатна, а по запросам "
                "«вызвать электрика» карты показываются выше сайтов.",
                "Доски объявлений. Дают поток, но качество заявок ниже: "
                "много тех, кто просто узнаёт цену.",
                "Свои фотографии в соцсетях. Медленно, но со временем "
                "работает лучше всего: люди видят результат, а не текст.",
            ]),
            ("h2", "Фотографии решают больше, чем описание"),
            ("p", "Заказчик не может оценить вашу квалификацию по словам. "
                  "«Качественно и в срок» пишут все, включая тех, кто "
                  "работает плохо. Единственное, что нельзя подделать, — "
                  "фотография собственной работы."),
            ("p", "Снимайте каждый объект. Не только общий вид: углы, швы, "
                  "щиток, стыки. Именно эти кадры отличают вас от "
                  "объявления без картинок."),
            ("note", "Три хорошие фотографии одного объекта работают лучше, "
                     "чем двадцать размытых с десяти. Снимайте днём, "
                     "не через плечо, без мусора в кадре."),
            ("h2", "Отвечайте быстро"),
            ("p", "В ремонте выигрывает не самый дешёвый, а самый первый. "
                  "Заказчик, у которого течёт труба, напишет пятерым "
                  "и договорится с тем, кто ответил через десять минут, "
                  "а не через день."),
            ("p", "Поэтому уведомления о новых заявках имеет смысл "
                  "подключить сразу, а не «потом разберусь»."),
            ("h2", "Считайте, откуда пришёл каждый заказ"),
            ("p", "Простая привычка, которая экономит деньги: спрашивайте "
                  "у каждого нового клиента, откуда он вас нашёл, "
                  "и записывайте. Через три месяца станет видно, какой "
                  "канал кормит, а какой только отнимает время."),
            ("cta", ("Создать профиль мастера", "/for-masters.html")),
        ],
        "related": ["/for-masters.html"],
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
</script><noscript><div><img src="https://mc.yandex.ru/watch/110231398" style="position:absolute; left:-9999px;" alt="" /></div></noscript>"""

CSS = """
*{margin:0;padding:0;box-sizing:border-box}
:root{--bg:#1C1512;--bg2:#241B14;--bg3:#2E2219;--gold:#F5A623;--white:#fff;
--t2:#C4A882;--t3:#9C8272;--border:rgba(245,166,35,0.25);--r:12px;--r2:8px}
body{background:var(--bg);color:var(--white);font-family:'Inter',system-ui,sans-serif;
font-size:17px;line-height:1.72;-webkit-font-smoothing:antialiased}
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
.wrap{max-width:760px;margin:0 auto;padding:0 22px}
.crumbs{font-size:13px;color:var(--t3);padding:20px 0 0}
.crumbs a{color:var(--t3)}
.tag{display:inline-block;font-size:12px;letter-spacing:1.5px;text-transform:uppercase;
color:var(--gold);border:1px solid var(--border);border-radius:20px;padding:4px 12px;
margin-bottom:16px}
h1{font-family:'Plus Jakarta Sans',sans-serif;font-size:36px;line-height:1.2;
font-weight:800;letter-spacing:-1px;margin:8px 0 14px}
.lead{color:var(--t2);font-size:19px;margin-bottom:8px}
.meta{color:var(--t3);font-size:14px;padding-bottom:26px;border-bottom:1px solid var(--border);
margin-bottom:8px}
h2{font-family:'Plus Jakarta Sans',sans-serif;font-size:24px;font-weight:800;
margin:38px 0 12px;letter-spacing:-0.5px}
p{color:var(--t2);margin-bottom:16px}
table{width:100%;border-collapse:collapse;margin:10px 0 18px;font-size:16px}
td{padding:12px 4px;border-bottom:1px solid rgba(245,166,35,0.13);color:var(--t2)}
td.p{text-align:right;color:var(--white);font-weight:600;white-space:nowrap}
ul{list-style:none;margin-bottom:18px}
li{color:var(--t2);padding-left:22px;position:relative;margin-bottom:10px}
li::before{content:"";position:absolute;left:4px;top:12px;width:6px;height:6px;
border-radius:50%;background:var(--gold)}
.note{background:var(--bg2);border:1px solid var(--border);border-left:3px solid var(--gold);
border-radius:var(--r);padding:18px 22px;color:var(--t2);font-size:16px;margin:20px 0}
.cta-box{margin:34px 0;background:var(--bg2);border:1px solid var(--border);
border-radius:var(--r);padding:24px;text-align:center}
.other{margin-top:44px;padding-top:22px;border-top:1px solid rgba(245,166,35,0.15)}
.other h3{font-size:15px;color:var(--t3);font-weight:600;margin-bottom:10px}
.other-links{display:flex;flex-wrap:wrap;gap:9px;margin-bottom:20px}
.other-links a{background:var(--bg2);border:1px solid var(--border);border-radius:20px;
padding:7px 15px;font-size:14px;color:var(--t2)}
.card-list{display:flex;flex-direction:column;gap:14px;margin:26px 0}
.acard{display:block;background:var(--bg2);border:1px solid var(--border);
border-radius:var(--r);padding:22px 24px}
.acard h3{font-family:'Plus Jakarta Sans',sans-serif;font-size:20px;font-weight:800;
color:var(--white);margin:6px 0 8px;letter-spacing:-0.4px}
.acard p{font-size:15px;margin:0;color:var(--t2)}
footer{border-top:1px solid var(--border);margin-top:56px;padding:26px 22px 40px;
text-align:center;color:var(--t3);font-size:13px}
footer a{color:var(--t3);margin:0 7px}
@media(max-width:640px){h1{font-size:28px}.nav-links{display:none}.wrap{padding:0 16px}
body{font-size:16px}}
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


def esc(t):
    return html.escape(t, quote=False)


def render_body(blocks):
    out = []
    for kind, val in blocks:
        if kind == "h2":
            out.append(f"  <h2>{esc(val)}</h2>")
        elif kind == "p":
            out.append(f"  <p>{esc(val)}</p>")
        elif kind == "note":
            out.append(f'  <div class="note">{esc(val)}</div>')
        elif kind == "ul":
            items = "".join(f"\n    <li>{esc(x)}</li>" for x in val)
            out.append(f"  <ul>{items}\n  </ul>")
        elif kind == "table":
            rows = "".join(
                f'\n    <tr><td>{esc(a)}</td><td class="p">{esc(b)}</td></tr>'
                for a, b in val
            )
            out.append(f"  <table>{rows}\n  </table>")
        elif kind == "cta":
            label, href = val
            out.append(
                f'  <div class="cta-box"><a class="btn" href="{href}">{esc(label)}</a></div>'
            )
    return "\n".join(out)


def plain_text(blocks):
    """Текст без разметки — для подсчёта объёма."""
    parts = []
    for kind, val in blocks:
        if kind in ("h2", "p", "note"):
            parts.append(val)
        elif kind == "ul":
            parts += val
        elif kind == "table":
            parts += [f"{a} {b}" for a, b in val]
    return " ".join(parts)


def build_article(slug, a):
    url = f"{SITE}/blog/{slug}/"
    ld = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "Article",
                "headline": a["title"],
                "description": a["desc"],
                "datePublished": a["date"],
                "dateModified": a["date"],
                "inLanguage": "ru-BY",
                "mainEntityOfPage": url,
                "author": {"@type": "Organization", "name": "BUDUJ.BY", "url": SITE},
                "publisher": {
                    "@type": "Organization",
                    "name": "BUDUJ.BY",
                    "url": SITE,
                    "logo": {"@type": "ImageObject", "url": f"{SITE}/apple-touch-icon.png"},
                },
            },
            {
                "@type": "BreadcrumbList",
                "itemListElement": [
                    {"@type": "ListItem", "position": 1, "name": "BUDUJ.BY", "item": SITE + "/"},
                    {"@type": "ListItem", "position": 2, "name": "Блог", "item": f"{SITE}/blog/"},
                    {"@type": "ListItem", "position": 3, "name": a["title"], "item": url},
                ],
            },
        ],
    }

    rel = "".join(
        f'<a href="{h}">{esc(label_for(h))}</a>' for h in a.get("related", [])
    )
    others = "".join(
        f'<a href="/blog/{s}/">{esc(x["title"])}</a>'
        for s, x in ARTICLES.items() if s != slug
    )

    return f"""<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{esc(a["seo_title"])} | BUDUJ.BY</title>
<meta name="description" content="{esc(a["desc"])}">
<link rel="canonical" href="{url}">
<link rel="icon" type="image/x-icon" href="/favicon.ico">
<link rel="icon" href="/favicon.svg">
<meta property="og:type" content="article">
<meta property="og:url" content="{url}">
<meta property="og:title" content="{esc(a["seo_title"])}">
<meta property="og:description" content="{esc(a["desc"])}">
<meta property="og:image" content="{SITE}/og.jpg">
<meta property="og:locale" content="ru_BY">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Plus+Jakarta+Sans:wght@700;800&display=swap" rel="stylesheet">
<style>{CSS}</style>
<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>
</head>
<body>
{NAV}
<div class="wrap">
  <div class="crumbs"><a href="/index.html">BUDUJ.BY</a> → <a href="/blog/">Блог</a></div>
  <span class="tag">{esc(a["audience"])}</span>
  <h1>{esc(a["title"])}</h1>
  <p class="lead">{esc(a["lead"])}</p>
  <div class="meta">Обновлено 18 августа 2026</div>

{render_body(a["body"])}

  <div class="other">
    <h3>По теме</h3>
    <div class="other-links">{rel}</div>
    <h3>Другие статьи</h3>
    <div class="other-links">{others}</div>
  </div>
</div>
{FOOTER}
{METRIKA}
</body>
</html>
"""


LABELS = {
    "/minsk/elektrik/": "Электрик в Минске",
    "/minsk/santehnik/": "Сантехник в Минске",
    "/minsk/plitochnik/": "Плиточник в Минске",
    "/masters.html": "Все мастера",
    "/orders.html": "Разместить заказ",
    "/for-masters.html": "Для мастеров",
}


def label_for(href):
    return LABELS.get(href, href)


def build_index():
    url = f"{SITE}/blog/"
    cards = ""
    for slug, a in ARTICLES.items():
        cards += (
            f'    <a class="acard" href="/blog/{slug}/">'
            f'<span class="tag">{esc(a["audience"])}</span>'
            f'<h3>{esc(a["title"])}</h3>'
            f'<p>{esc(a["desc"])}</p></a>\n'
        )
    ld = {
        "@context": "https://schema.org",
        "@type": "Blog",
        "name": "Блог BUDUJ.BY",
        "url": url,
        "inLanguage": "ru-BY",
        "blogPost": [
            {
                "@type": "BlogPosting",
                "headline": a["title"],
                "url": f"{SITE}/blog/{s}/",
                "datePublished": a["date"],
            }
            for s, a in ARTICLES.items()
        ],
    }
    desc = ("Как выбрать мастера, сколько стоят работы, что писать "
            "в договоре. Разборы для заказчиков и материалы для мастеров.")
    return f"""<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Блог о ремонте — цены, договор, выбор мастера | BUDUJ.BY</title>
<meta name="description" content="{esc(desc)}">
<link rel="canonical" href="{url}">
<link rel="icon" type="image/x-icon" href="/favicon.ico">
<link rel="icon" href="/favicon.svg">
<meta property="og:type" content="website">
<meta property="og:url" content="{url}">
<meta property="og:title" content="Блог о ремонте | BUDUJ.BY">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:image" content="{SITE}/og.jpg">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Plus+Jakarta+Sans:wght@700;800&display=swap" rel="stylesheet">
<style>{CSS}</style>
<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>
</head>
<body>
{NAV}
<div class="wrap">
  <div class="crumbs"><a href="/index.html">BUDUJ.BY</a> → Блог</div>
  <h1>Блог о ремонте</h1>
  <p class="lead">Разборы без воды: сколько стоит работа, как проверить
  мастера, что должно быть в договоре. И отдельно — материалы для тех,
  кто ремонтом зарабатывает.</p>
  <div class="card-list">
{cards}  </div>
</div>
{FOOTER}
{METRIKA}
</body>
</html>
"""


def update_sitemap(paths):
    sp = os.path.join(ROOT, "sitemap.xml")
    s = open(sp, encoding="utf-8").read()
    block, added = "", 0
    for p, prio in paths:
        loc = SITE + p
        if loc in s:
            continue
        block += (f"  <url>\n    <loc>{loc}</loc>\n"
                  f"    <lastmod>{TODAY}</lastmod>\n"
                  f"    <changefreq>monthly</changefreq>\n"
                  f"    <priority>{prio}</priority>\n  </url>\n")
        added += 1
    if added:
        s = s.replace("</urlset>", block + "</urlset>")
        open(sp, "w", encoding="utf-8").write(s)
    print(f"sitemap.xml: добавлено адресов — {added}")


def main():
    os.makedirs(os.path.join(ROOT, "blog"), exist_ok=True)
    with open(os.path.join(ROOT, "blog", "index.html"), "w", encoding="utf-8") as f:
        f.write(build_index())
    print("создано: blog/index.html")

    paths = [("/blog/", "0.8")]
    for slug, a in ARTICLES.items():
        d = os.path.join(ROOT, "blog", slug)
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, "index.html"), "w", encoding="utf-8") as f:
            f.write(build_article(slug, a))
        words = len(plain_text(a["body"]).split())
        print(f"создано: blog/{slug}/index.html  ({words} слов)")
        paths.append((f"/blog/{slug}/", "0.7"))

    update_sitemap(paths)
    print(f"\nвсего статей: {len(ARTICLES)}")


if __name__ == "__main__":
    main()
