# Реестр тендерных площадок (UI / иконки)

**status:** accepted  
**last-review-date:** 2026-08-27  
**источник списка:** перечень отдела продаж (скрин владельца 2026-08-13)  
**API-ресёрч:** [`../platform-api-research.md`](../platform-api-research.md)  
**именованные поиски / очередь:** [`named-searches.md`](./named-searches.md)  
**зонд СИБУР SRM (NEXT+):** [`sibur-srm-probe.md`](./sibur-srm-probe.md)  
**зонд OnlineContract (NEXT+):** [`onlinecontract-probe.md`](./onlinecontract-probe.md)  
**зонд Tender.Pro (NEXT+):** [`tender-pro-probe.md`](./tender-pro-probe.md)  
**ассеты:** `app/web/public/platforms/{id}.png` (32×32)

Ship A scrape = **rostender** + **tender-pro** (адаптер [024](../delivery/tasks/024-tender-pro-adapter.md) done; сиды очереди — [030](../delivery/tasks/030-search-coverage.md)). Остальные строки — реестр UI «откуда тендер» и более поздние адаптеры.

## Поля

| Поле | Смысл |
| --- | --- |
| `id` | стабильный slug в коде (`source_platform_id`) |
| `hosts` | домены / URL из перечня |
| `label_ru` | короткое имя (tooltip / drawer) |
| `ship` | `as-is` = текущий scout · `backlog` = позже |
| `logo` | путь от корня web-приложения |

## Таблица

| id | label_ru | hosts | ship | logo |
| --- | --- | --- | --- | --- |
| `b2b-center` | B2B-Center | www.b2b-center.ru, b2b-center.ru | backlog | `/platforms/b2b-center.png` |
| `rostender` | РосТендер | rostender.info | **as-is** | `/platforms/rostender.png` |
| `onlinecontract` | OnlineContract | onlinecontract.ru | backlog | `/platforms/onlinecontract.png` |
| `rts-rosatom` | РТС (Росатом) | www.rosatom.rts-tender.ru, rosatom.rts-tender.ru | backlog | `/platforms/rts-rosatom.png` |
| `sibur-srm` | СИБУР SRM | srm.sibur.ru | backlog | `/platforms/sibur-srm.png` |
| `tender-pro` | Tender.Pro | www.tender.pro, tender.pro | **as-is** | `/platforms/tender-pro.png` |
| `tektorg-kim` | ТЭК-Торг КИМ | kim.tektorg.ru | backlog | `/platforms/tektorg-kim.png` |
| `astgoz` | АСТ ГОЗ | 223.astgoz.ru | backlog | `/platforms/astgoz.png` |
| `roseltorg` | Росэлторг | com.roseltorg.ru, lk.roseltorg.ru | backlog | `/platforms/roseltorg.png` |
| `oilb2bcs` | OilB2B | oilb2bcs.ru | backlog | `/platforms/oilb2bcs.png` |
| `gpb-etp` | ЭТП ГПБ | etp.gpb.ru | backlog | `/platforms/gpb-etp.png` |
| `tmk` | ТМК закупки | zakupki.tmk-group.com | backlog | `/platforms/tmk.png` |
| `severstal` | Северсталь | procurement.severstal.com | backlog | `/platforms/severstal.png` |

## Иконки

- Канон файла: **32×32** PNG; в UI показывать **16–20px**.
- Сборка/обновление: [`scripts/fetch-platform-icons.py`](../../scripts/fetch-platform-icons.py).
- При отсутствии файла UI рисует placeholder с инициалами (не ломает карточку).
- Ассеты — локальный кэш для внутреннего операторского UI, не для перепродажи брендов.

## UI

- Поле лота: `source_platform_id`.
- Карточка: иконка в **фиксированном правом рейле** (не в строке title); таблица: колонка «Площадка»; drawer: рядом с «На площадке».
