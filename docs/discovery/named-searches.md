# Именованные поиски и очередь прогонов

**status:** accepted  
**last-review-date:** 2026-08-19  
**owner lock:** 2026-08-19 (имена поисков + очередь Старта; первая чужая ЭТП = Tender.Pro)  
**код:** [023](../delivery/tasks/023-named-searches.md) (таблица + Tech + очередь) → [024](../delivery/tasks/024-tender-pro-adapter.md) (адаптер). Этот файл — решения, не реализация.  
**зонд Tender.Pro:** [`tender-pro-probe.md`](./tender-pro-probe.md)  
**реестр ЭТП:** [`platforms.md`](./platforms.md)  
**API:** [`../delivery/sales-inbox-api.md`](../delivery/sales-inbox-api.md)

---

## Problem

Сейчас один хардкод: РосТендер, query «неразрушающий», limit 1000, кнопка Старт без настроек (Q25 / [022](../delivery/tasks/022-tech-start-stop.md)). Нужно в системе хранить **несколько поисков** под разные площадки и одним Стартом прогонять выбранные подряд.

## Users

| Кто | Job |
| --- | --- |
| Digital / директор (обе учётки, без ролей) | Настроить поиски (имя, площадка, строки, лимит), отметить очередь, нажать Старт |
| Продажи | Inbox как сейчас: один пул score≥4; иконка площадки уже есть |

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
| `queries` | массив строк, минимум 1 |
| `limit_n` | пул после union/дедупа; default 1000; потолок как сейчас ≤1000 |
| `in_queue` | попадет в следующий Старт |
| `sort_order` | порядок в очереди |

Поиск **не** смешивает две площадки. Площадочные фильтры (открыт, РФ, поле «товар») **не** в UI — в адаптере.

Смысл `queries[]`:

- **rostender** — каждая строка = `keywords` (сегодня хардкод «неразрушающий»)
- **tender-pro** — каждая строка = `good_name` (канон зонда: ВИК, ПВК, УЗК, РК)

Внутри одного поиска: все query → union → дедуп по native id площадки → обрезка до `limit_n` → тот же скоринг L1–L3.

Q25 **держим:** query и limit живут в карточке поиска, не на кнопке Старт. `POST /api/run/start` не принимает ad-hoc `query`/`limit` как способ настройки (после 023 body настроек игнорируется / убирается).

### Сиды (при миграции 023)

- «РосТендер НК» — `rostender` / `["неразрушающий"]` / 1000 / **в очереди**
- «Tender.Pro НК» — `tender-pro` / `["ВИК","ПВК","УЗК","РК"]` / 1000 / **не в очереди**, пока 024 не в проде

---

## Очередь и прогон

```text
Tech (in_queue=true, sort_order)
  → POST /api/run/start
      → шаг 1: адаптер поиска → ingest_run
      → шаг 2: …
```

- Один поиск в очереди = **один** ряд `runs` (`query` = имя + склеенные строки; плюс `source_platform_id`, `search_id`).
- Inbox без изменений модели пула: upsert `lots` по `tender_id`, только score≥4, `lot_state` не сбрасывается.
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
- [ ] Код 023/024 — отдельные ветки `feat/023-…` / `feat/024-…` после этого lock

## Next skill

Код: `scout-architect` (уже в этом файле) → `scout-designer` + `scout-ux-writer` + `scout-backend` + `scout-frontend` → `scout-qa` → docs. Не начинать, пока этот файл `accepted` (уже).
