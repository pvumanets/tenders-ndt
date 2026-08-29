# Именованные поиски и очередь прогонов

**status:** superseded  
**last-review-date:** 2026-08-29  
**superseded by:** [`search-groups.md`](./search-groups.md) (owner lock 2026-08-29)  
**owner lock (historical):** 2026-08-19 (имена поисков + очередь Старта; первая чужая ЭТП = Tender.Pro) · **2026-08-27** (без лимита 1000; пакеты — [`search-keywords.md`](./search-keywords.md)) · **2026-08-28** (плюс/минус — [`search-system-v2.md`](./search-system-v2.md)) · **2026-08-29** (shared A–E на все ЭТП — [041](../delivery/tasks/041-shared-search-packages.md))  
**код AS-IS:** [023](../delivery/tasks/023-named-searches.md) **done** → [024](../delivery/tasks/024-tender-pro-adapter.md) **done** · [040](../delivery/tasks/040-roseltorg-adapter.md) **done** · [041](../delivery/tasks/041-shared-search-packages.md) shared lexicon.  
**зонд Tender.Pro:** [`tender-pro-probe.md`](./tender-pro-probe.md)  
**реестр ЭТП:** [`platforms.md`](./platforms.md)  
**API AS-IS:** [`../delivery/sales-inbox-api.md`](../delivery/sales-inbox-api.md) · **TO-BE:** [`../delivery/search-groups-api.md`](../delivery/search-groups-api.md)

---

## Supersede notice

**Новый канон операторской модели:** [`search-groups.md`](./search-groups.md).

| Было (этот файл / runtime до 048) | Стало (целевой канон) |
| --- | --- |
| Одна строка `searches` = одна площадка | **Группа** = плюс+минус без `platform_id` |
| 15 сидов A–E × 3 ЭТП | **5 групп** A–E |
| Вкл/выкл только `in_queue` на строке | Группы `in_queue` **и** площадки `enabled` отдельно |
| «Поиск не смешивает две площадки» | Группа на все **включённые** площадки |

Пока код 048 не в `main`, **runtime** остаётся per-platform `searches`. Этот файл — история + AS-IS контракт для адаптеров/`tender_id`.

---

## Problem (historical)

Сейчас в коде: сиды A–E + пакеты по площадкам ([030](../delivery/tasks/030-search-coverage.md)); `limit_n=0` без must-cap. Несколько поисков по [`search-keywords.md`](./search-keywords.md).

## Users

| Кто | Job |
| --- | --- |
| Digital / директор (обе учётки, без ролей) | Настроить поиски (имя, площадка, строки), отметить очередь, нажать Старт |
| Продажи | Inbox: **L1+L2+L3** на доске (Горячие / Сильные / Смотреть); иконка площадки уже есть |

## Facts / Hypotheses / Gaps

| Claim | Tag |
| --- | --- |
| Worker as-is = rostender / tender-pro / roseltorg adapters | fact |
| Tender.Pro список = HTML `good_name` + открыт + РФ; JSON-RPC без `_key` ленту по товару не даёт | fact (зонд 2026-08-13) |
| Именованные поиски, не одна карточка «на ЭТП» и не ad-hoc поля на кнопке Старт | fact (owner 2026-08-19); **superseded** группами 2026-08-29 |
| Старт = очередь отмеченных поисков; один глобальный `running`; Стоп рвёт текущий шаг и хвост | fact (owner 2026-08-19); шаги станут group×platform |
| Макет списка поисков на вкладке Прогон | closed → [`search-groups.md`](./search-groups.md) + W-run |
| Живые cookies Tender.Pro после дампа 13.08 | gap — владелец: свежий Netscape до первого прогона 024 |

---

## Сущность «поиск» (AS-IS runtime)

Одна строка Postgres. Обе учётки видят одно и то же.

| Поле | Правило |
| --- | --- |
| `id` | UUID |
| `name` | человеческое; уникально в инстансе |
| `platform_id` | ровно одна ЭТП: `rostender` \| `tender-pro` \| `roseltorg`; позже slug из [`platforms.md`](./platforms.md) |
| `queries` | массив строк, минимум 1; порядок **слож → прост**; **канон A–E общий** ([`search-keywords.md`](./search-keywords.md) · [041](../delivery/tasks/041-shared-search-packages.md)) |
| **`exclude`** | массив минус-фраз; режет title **на списке** до скоринга ([`search-system-v2.md`](./search-system-v2.md)); на одноимённом пакете одинаков для всех ЭТП |
| `limit_n` | optional soft stop; **`0` = без потолка** ([030](../delivery/tasks/030-search-coverage.md) done) |
| `in_queue` | попадет в следующий Старт |
| `sort_order` | порядок в очереди |

AS-IS: поиск **не** смешивает две площадки. TO-BE: см. [`search-groups.md`](./search-groups.md). Площадочные фильтры (открыт, РФ, поле «товар») **не** в UI — в адаптере.

Смысл `queries[]`:

- **все площадки** — одни и те же плюс-фразы пакетов A–E ([`search-keywords.md`](./search-keywords.md)); адаптер ЭТП подставляет поле поиска площадки (`keywords` / `good_name` / www `query` и т.д.)

Внутри одного поиска (v2): все query → union → дедуп → **`exclude` по title** → без обрезки limit → скоринг L1–L3 → ingest **tier ∈ {L1,L2,L3}**.

`exclude[]` действует **только** на выдачу **этого** поиска; другие поиски в очереди не наследуют минусы (детсад+радиограф через пакет B сохраняется).

Q25 **держим:** query, exclude и limit живут в карточке поиска/группы, не на кнопке Старт. `POST /api/run/start` не принимает ad-hoc настройки.

### Сиды (AS-IS)

Плюс/минус A–E: [`search-keywords.md`](./search-keywords.md) · [`search-system-v2.md`](./search-system-v2.md).  
**Сиды (041):** на rostender / tender-pro / roseltorg — полный A–E из одного SoT; TP/РЭ `in_queue` при cookies.  
**TO-BE сиды:** 5 групп — [`search-groups.md`](./search-groups.md).

## Очередь и прогон (AS-IS)

```text
Tech (in_queue=true, sort_order)
  → POST /api/run/start
      → шаг 1: адаптер поиска → ingest_run
      → шаг 2: …
```

- Один поиск в очереди = **один** ряд `runs` (`query` = имя + склеенные строки; плюс `source_platform_id`, `search_id`).
- Inbox (целевой пул, P12): `lots` по `tender_id`, **tier ∈ {L1,L2,L3}**, update-on-diff ([028](../delivery/tasks/028-run-idempotent-report.md)); `lot_state` не сбрасывается.
- Параллельных воркеров нет. Второй Старт → 409 `already_running`.
- Пустая очередь (`in_queue` ни у кого) → 400 `empty_queue`.
- Ошибка шага / нет обязательных cookies: шаг `error` или `skipped`, **очередь идёт дальше**. Стоп — единственный полный обрыв (текущий soft-stop + drop хвоста).
- `GET /api/status`: текущий поиск, позиция i/N, статусы шагов; cookies **по площадке**, не одно поле rostender.

UI AS-IS: вкладка **Прогон**, список поисков × площадка. TO-BE IA — [`design/sales-inbox-wireframes.md`](./design/sales-inbox-wireframes.md) W-run.

---

## `tender_id`

Стабильный ключ inbox: `{source_platform_id}:{native_id}` для **всех** площадок. Иначе числовой id Tender.Pro столкнётся с РосТендером.

Существующие лоты / `lot_state` / том docs — миграция в коде 024 (исторически). Префикс остаётся при модели групп.

---

## Tender.Pro (рецепт адаптера 024)

Канон HTTP: [`tender-pro-probe.md`](./tender-pro-probe.md).

- `httpx` + BeautifulSoup. **Не** Playwright. **Не** JSON-RPC (`_key` не нужен).
- Список: `GET /api/tenders/list` с `good_name` + `tender_state=1` + `country=1`.
- Карточка: `/api/tender/{id}/view_public`.
- Cookies: Netscape-файл / env (имена — [`../delivery/auth-cookies.md`](../delivery/auth-cookies.md)). Список публичный — шаг списка идёт **без** файла. Файлы лотов на доске без сессии ЛК не качаем.
- Перед живым прогоном: свежий Netscape. На VPS — `python scripts/vps-bootstrap.py --sync`, не правки `/opt/tenders-ndt`.
- ИИ не нужен.

Адаптер выбирается по `platform_id` шага (AS-IS: поиска; TO-BE: пары группа×площадка). Общего «робота по HTML» нет.

---

## Options (уже выбрали — historical)

| Тема | A | B (lock 2026-08-19) | C |
| --- | --- | --- | --- |
| Хранение | карточка на ЭТП | **именованные поиски** | поля только на Старте |
| Старт | один поиск за клик | **очередь отмеченных** | — |

Lock 2026-08-29: группы × площадки — [`search-groups.md`](./search-groups.md).

## Scope

**In (historical lock):** сущность поиска, очередь, сиды, контракт API, Tender.Pro как первый чужой адаптер, prefix `tender_id`.

**Out then / still out:** cron; роли; Bitrix; Excel-вкладка; фильтр inbox по площадке (иконка уже есть); правка продукта на VPS.

## Acceptance (docs)

- [x] Owner выбрал именованные поиски и очередь (2026-08-19)
- [x] Сиды и смысл `queries[]` по площадкам записаны
- [x] Tender.Pro не копирует `list_scrape.py` вслепую
- [x] Код 023 — ветка `feat/023-named-searches` (очередь + Tech)
- [x] Код 024 — `feat/024-tender-pro-adapter` (адаптер + prefix `tender_id`)
- [x] Supersede pointer → [`search-groups.md`](./search-groups.md) (2026-08-29)

## Next skill

Канон оператора — [`search-groups.md`](./search-groups.md). Адаптеры и `tender_id` правила ниже по тексту остаются валидны.
