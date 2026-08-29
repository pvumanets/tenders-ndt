# Реестр тендерных площадок (UI / иконки)

**status:** accepted  
**last-review-date:** 2026-08-28  
**источник списка:** учётки НДТ (владелец 2026-08-28); slug’и без учётки — parked (иконки для старых лотов)  
**API-ресёрч:** [`../platform-api-research.md`](../platform-api-research.md)  
**auth / cookies:** [`../delivery/auth-cookies.md`](../delivery/auth-cookies.md)  
**именованные поиски / очередь:** [`named-searches.md`](./named-searches.md)  
**зонд СИБУР SRM (parked):** [`sibur-srm-probe.md`](./sibur-srm-probe.md)  
**зонд OnlineContract (parked):** [`onlinecontract-probe.md`](./onlinecontract-probe.md)  
**зонд Tender.Pro (as-is):** [`tender-pro-probe.md`](./tender-pro-probe.md)  
**зонд Росэлторг www (as-is):** [`roseltorg-probe.md`](./roseltorg-probe.md)
**ассеты:** `app/web/public/platforms/{id}.png` (32×32)

Ship scrape = **rostender** + **tender-pro** + **roseltorg** (адаптер [040](../delivery/tasks/040-roseltorg-adapter.md)). Очередь следующих: **b2b-center → oilb2bcs → severstal**. Пароли и cookie values — только `.env` / `cookies*.txt`, не в этом md.

## Поля

| Поле | Смысл |
| --- | --- |
| `id` | стабильный slug в коде (`source_platform_id`) |
| `hosts` | домены / URL из перечня |
| `label_ru` | короткое имя (tooltip / drawer) |
| `ship` | `as-is` = адаптер в прогоне · `account` = есть учётка, адаптер позже · `parked` = нет учётки в актуальном перечне |
| `logo` | путь от корня web-приложения |

## Таблица

| id | label_ru | hosts | ship | logo |
| --- | --- | --- | --- | --- |
| `b2b-center` | B2B-Center | www.b2b-center.ru, b2b-center.ru | **account** | `/platforms/b2b-center.png` |
| `rostender` | РосТендер | rostender.info | **as-is** | `/platforms/rostender.png` |
| `onlinecontract` | OnlineContract | onlinecontract.ru | parked | `/platforms/onlinecontract.png` |
| `rts-rosatom` | РТС (Росатом) | www.rosatom.rts-tender.ru, rosatom.rts-tender.ru | parked | `/platforms/rts-rosatom.png` |
| `sibur-srm` | СИБУР SRM | srm.sibur.ru | parked | `/platforms/sibur-srm.png` |
| `tender-pro` | Tender.Pro | www.tender.pro, tender.pro | **as-is** | `/platforms/tender-pro.png` |
| `tektorg-kim` | ТЭК-Торг КИМ | kim.tektorg.ru | parked | `/platforms/tektorg-kim.png` |
| `astgoz` | АСТ ГОЗ | 223.astgoz.ru | parked | `/platforms/astgoz.png` |
| `roseltorg` | Росэлторг | www.roseltorg.ru (сводный поиск); lk.roseltorg.ru | **as-is** | `/platforms/roseltorg.png` |
| `oilb2bcs` | OilB2B | oilb2bcs.ru | **account** | `/platforms/oilb2bcs.png` |
| `gpb-etp` | ЭТП ГПБ | etp.gpb.ru | parked | `/platforms/gpb-etp.png` |
| `tmk` | ТМК закупки | zakupki.tmk-group.com | parked | `/platforms/tmk.png` |
| `severstal` | Северсталь | procurement.severstal.com | **account** | `/platforms/severstal.png` |

## Как обучить Scout новой площадке

Паттерн rostender / Tender.Pro. Scout **не** логинится в UI сам.

1. Владелец входит в браузере под учёткой из `.env`.
2. Экспорт Netscape → `cookies.{slug}.txt` в корне (gitignore). На VPS — `--sync`.
3. Зонд с агентом (1 площадка = 1 сессия) → `docs/discovery/{slug}-probe.md` **без** паролей/cookie values: URL списка, карточки, нужны ли cookies для поиска.
4. Таск адаптера → `feat/0XX-{slug}-adapter` → worker + `runner.py` → QA → docs. Прогон — человек в Tech.
5. Порядок следующих: B2B-Center → OilB2B → Северсталь SRM. Росэлторг www — [043](../delivery/tasks/043-roseltorg-www.md) / [`roseltorg-probe.md`](./roseltorg-probe.md) (cookies Netscape; CORP retired).

Не коммитить `.env` / `cookies*.txt`. Не править продукт на VPS руками. Не тащить все четыре адаптера одним PR.

## Иконки

- Канон файла: **32×32** PNG; в UI показывать **16–20px**.
- Сборка/обновление: [`scripts/fetch-platform-icons.py`](../../scripts/fetch-platform-icons.py).
- При отсутствии файла UI рисует placeholder с инициалами (не ломает карточку).
- Ассеты — локальный кэш для внутреннего операторского UI, не для перепродажи брендов.
- Slug’и `parked` **не удаляем** — иконки для исторических лотов в inbox.

## UI

- Поле лота: `source_platform_id`.
- Карточка: иконка в **фиксированном правом рейле** (не в строке title); таблица: колонка «Площадка»; drawer: рядом с «На площадке».
