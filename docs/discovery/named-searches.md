# Именованные поиски и очередь прогонов

**status:** accepted  
**last-review-date:** 2026-08-27  
**owner lock:** 2026-08-19 (имена поисков + очередь Старта; первая чужая ЭТП = Tender.Pro) · **2026-08-27** (без лимита 1000; пакеты ключевых слов — [`search-keywords.md`](./search-keywords.md))  
**код:** [023](../delivery/tasks/023-named-searches.md) **done** → [024](../delivery/tasks/024-tender-pro-adapter.md) **done**. Этот файл — решения.  
**зонд Tender.Pro:** [`tender-pro-probe.md`](./tender-pro-probe.md)  
**реестр ЭТП:** [`platforms.md`](./platforms.md)  
**API:** [`../delivery/sales-inbox-api.md`](../delivery/sales-inbox-api.md)

---

## Problem

Сейчас в коде ещё хардкод: один seed «неразрушающий», limit 1000. **Продуктовый lock 2026-08-27:** лимит убираем; несколько поисков по [`search-keywords.md`](./search-keywords.md). Нужно в системе хранить **несколько поисков** под разные площадки и одним Стартом прогонять выбранные подряд.

## Users

| Кто | Job |
| --- | --- |
| Digital / директор (обе учётки, без ролей) | Настроить поиски (имя, площадка, строки), отметить очередь, нажать Старт |
| Продажи | Inbox: **L1+L2+L3** на доске (Горячие / Сильные / Смотреть); иконка площадки уже есть |

## Facts / Hypotheses / Gaps

| Claim | Tag |
| --- | --- |
| Worker as-is = только rostender, `httpx`, без ИИ (Q24) | fact |
| Tender.Pro список = HTML `good_name` + открыт + РФ; JSON-RPC без `_key` ленту по товару не даёт | fact (зонд 2026-08-13) |
| Именованные поиски, не одна карточка «на ЭТП» и не ad-hoc поля на кнопке Старт | fact (owner 2026-08-19) |
| Старт = очередь отмеченных поисков; один глобальный `running`; Стоп рвёт текущий шаг и хвост | fact (owner 2026-08-19) |
| Макет списка поисков на вкладке Прогон | gap — `scout-designer` / `scout-ux-writer` в 023, не этот lock |
| Живые cookies Tender.Pro после дампа 13.08 | gap — владелец: свежий Netscape до первого прогона 024 |

---

## Сущность «поиск»

Одна строка Postgres. Обе учётки видят одно и то же.

| Поле | Правило |
| --- | --- |
| `id` | UUID |
| `name` | человеческое; уникально в инстансе |
| `platform_id` | ровно одна ЭТП: сейчас `rostender` \| `tender-pro`; позже slug из [`platforms.md`](./platforms.md) |
| `queries` | массив строк, минимум 1; порядок **слож → прост** (см. search-keywords) |
| `limit_n` | **deprecated в продукте (2026-08-27)** — без потолка; в коде AS-IS ещё ≤1000 до отдельной задачи |
| `in_queue` | попадет в следующий Старт |
| `sort_order` | порядок в очереди |

Поиск **не** смешивает две площадки. Площадочные фильтры (открыт, РФ, поле «товар») **не** в UI — в адаптере.

Смысл `queries[]`:

- **rostender** — каждая строка = `keywords` (канон: [`search-keywords.md`](./search-keywords.md))
- **tender-pro** — каждая строка = `good_name` (уровни B→C из search-keywords)

Внутри одного поиска: все query → union → дедуп по native id площадки → **без обрезки limit** (lock 2026-08-27) → скоринг L1–L3 → ingest **tier ∈ {L1,L2,L3}** (не только score≥4).

Q25 **держим:** query и limit живут в карточке поиска, не на кнопке Старт. `POST /api/run/start` не принимает ad-hoc `query`/`limit` как способ настройки (после 023 body настроек игнорируется / убирается).

### Сиды (целевые после sync кода)

См. таблицы в [`search-keywords.md`](./search-keywords.md). Кратко очередь РосТендер:

1. **услуги НК** (A, + усечения)
2. **методы** (B, + усечения)
3. **аббревиатуры** (C)
4. **контроли** (D: принимающий / приёмочный / входной / строительный)
5. **страховка** (E: широкие — мусор чистит ИИ)

Tender.Pro: методы / аббревиатуры / контроли / страховка — включить в очередь когда cookies OK.

**AS-IS миграция 023:** один seed «неразрушающий» / limit 1000 — заменить при задаче sync keywords.

---

## Очередь и прогон

```text
Tech (in_queue=true, sort_order)
  → POST /api/run/start
      → шаг 1: адаптер поиска → ingest_run
      → шаг 2: …
```

- Один поиск в очереди = **один** ряд `runs` (`query` = имя + склеенные строки; плюс `source_platform_id`, `search_id`).
- Inbox (целевой пул): upsert `lots` по `tender_id`, **tier L1|L2|L3**, `lot_state` не сбрасывается. AS-IS код: score≥4 — см. owner-decisions.
- Параллельных воркеров нет. Второй Старт → 409 `already_running`.
- Пустая очередь (`in_queue` ни у кого) → 400 `empty_queue`.
- Ошибка шага / нет обязательных cookies: шаг `error` или `skipped`, **очередь идёт дальше**. Стоп — единственный полный обрыв (текущий soft-stop + drop хвоста).
- `GET /api/status`: текущий поиск, позиция i/N, статусы шагов; cookies **по площадке**, не одно поле rostender.

UI: всё на вкладке **Прогон** (третью вкладку не плодим): список поисков, чекбокс «в очереди», CRUD, Старт/Стоп.

---

## `tender_id`

Стабильный ключ inbox: `{source_platform_id}:{native_id}` для **всех** площадок, включая новые rostender-ingest. Иначе числовой id Tender.Pro столкнётся с РосТендером.

Существующие лоты / `lot_state` / том docs — **миграция в коде 024** (не в этом docs-срезе). До 024 rostender as-is оставляет голый native id.

---

## Tender.Pro (рецепт адаптера 024)

Канон HTTP: [`tender-pro-probe.md`](./tender-pro-probe.md).

- `httpx` + BeautifulSoup. **Не** Playwright. **Не** JSON-RPC (`_key` не нужен).
- Список: `GET /api/tenders/list` с `good_name` + `tender_state=1` + `country=1`.
- Карточка: `/api/tender/{id}/view_public`.
- Cookies: `cookies.tender-pro.txt` / `TENDER_PRO_COOKIES_FILE`. Список публичный — шаг списка идёт **без** файла. Файлы score≥4 без сессии ЛК не качаем.
- Перед живым прогоном: свежий Netscape (дамп 13.08 светился в чате). На VPS — `python scripts/vps-bootstrap.py --sync`, не правки `/opt/tenders-ndt`.
- ИИ не нужен.

Адаптер выбирается по `platform_id` поиска. Общего «робота по HTML» нет.

---

## Options (уже выбрали)

| Тема | A | B (lock) | C |
| --- | --- | --- | --- |
| Хранение | карточка на ЭТП | **именованные поиски** | поля только на Старте |
| Старт | один поиск за клик | **очередь отмеченных** | — |

## Scope

**In (lock):** сущность поиска, очередь, сиды, контракт API, Tender.Pro как первый чужой адаптер, prefix `tender_id`.

**Out:** код 023/024; cron; роли; Bitrix; Excel-вкладка; СИБУР / OnlineContract / остальные 9 ЭТП; фильтр inbox по площадке (иконка уже есть); правка продукта на VPS.

## Acceptance (docs)

- [x] Owner выбрал именованные поиски и очередь (2026-08-19)
- [x] Сиды и смысл `queries[]` по площадкам записаны
- [x] Tender.Pro не копирует `list_scrape.py` вслепую
- [x] Код 023 — ветка `feat/023-named-searches` (очередь + Tech)
- [x] Код 024 — `feat/024-tender-pro-adapter` (адаптер + prefix `tender_id`)

## Next skill

Дальше по бэклогу владельца; СИБУР / OnlineContract — отдельные зонды, не этот файл.
