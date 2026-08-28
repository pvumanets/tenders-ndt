# Sales Inbox — API и storage

**status:** accepted  
**last-review-date:** 2026-08-27  
**канон:** lock [`../discovery/owner-decisions.md`](../discovery/owner-decisions.md) 2026-08-27; P12 [032](./tasks/032-api-canon-sync.md)  
**продукт:** [`../discovery/sales-inbox.md`](../discovery/sales-inbox.md)  
**поиски / очередь:** [`../discovery/named-searches.md`](../discovery/named-searches.md)  
**архитектура:** [`tech-architecture.md`](./tech-architecture.md)  
**фазы:** [`platform-phases.md`](./platform-phases.md) — P5.2–P7 **done**; поиски [023](./tasks/023-named-searches.md) **done**; Tender.Pro [024](./tasks/024-tender-pro-adapter.md) **done**; NEXT+ [`next-phases.md`](./next-phases.md)

Термины для владельца: **просмотренность**, **ручная смена приоритета**. Ключи JSON/API — на английском.

SoT: **Postgres**, не `operator-state.json`. Все `/api/*` кроме `GET /api/health`, `POST /api/auth/login`, `POST /api/auth/logout` — **с сессией Scout**.

**AS-IS runtime (после 030):** ingest/inbox/docs — пул **`tier ∈ {L1,L2,L3}`**; `limit_n=0` = без потолка (мягкий stop если задан >0). Update-on-diff + `run_report` — **done** ([028](./tasks/028-run-idempotent-report.md)). ИИ — отдельный шаг ([029](./tasks/029-tier-rules-and-ai.md)). Сиды A–E + TP пакеты — [030](./tasks/030-search-coverage.md).

---

## Пул inbox

- Кандидаты: лоты с **`tier ∈ {L1, L2, L3}`** в таблице `lots` (после ingest всех прогонов). Колонка «Смотреть» = **системный** L3, не только ручной перенос.
- При повторном ingest того же `tender_id` — см. § Ingest (update-on-diff); без изменений на площадке карточку **не** переписываем.
- Эффективный приоритет для UI: `manual_tier` > `ai_tier` (если был успешный ИИ) > `tier` / `rules_tier` движка.

## Storage

| Что | Где |
| --- | --- |
| Карточка лота | `lots` |
| viewed / manual_tier / board_hidden | `lot_state` (один ряд на `tender_id`, глобально) |
| Прогон | `runs` (`query`, `limit_n`, `status`; после 023: `source_platform_id`, `search_id`) |
| Именованный поиск (023) | `searches` (`name`, `platform_id`, `queries`, `limit_n`, `in_queue`, `sort_order`) |
| Учётки Scout | `users` (password_hash; bootstrap из `.env`) |
| Сессия Scout | `sessions` (`token_hash` = sha256 opaque cookie; TTL 7 суток) |
| Мета документов | `documents`; байты — том `docs/{tender_id}/` |
| Выгрузка P4 | том (MD/CSV/JSON) — inbox **не** читает |

`viewed` не сбрасывается новым прогоном. `PUT` пишет в `lot_state`, не в файл прогона.

**Ingest (P5.3 + P9/028 + P10/029):** конец **одного** поиска-шага очереди вызывает `ingest_run`. В `lots` попадают строки с **`tier ∈ {L1, L2, L3}`** (не порог score≥4).

Повтор того же `tender_id`:

| На площадке | Действие | Счётчик Tech (`run_report`) |
| --- | --- | --- |
| Нет изменений (срок, НМЦ, title, docs meta) | **не** UPDATE карточки | `already` — «Уже были в системе» |
| Есть diff | UPDATE полей с площадки | `updated` — «Обновлено с площадки» |
| Новый `tender_id` | INSERT | `new` — «Новые лоты» |

`lot_state` (`viewed`, `manual_tier`, AI-поля) ingest **не** создаёт и **не** сбрасывает. Без `DATABASE_URL` — skip. Детали: [`../discovery/inbox-lifecycle.md`](../discovery/inbox-lifecycle.md), [028](./tasks/028-run-idempotent-report.md).

«Ушли в просроченные» (`run_report.expired`): снимок протухших `tender_id` в начале очереди; в конце — текущие протухшие минус снимок (впервые протухшие в окне прогона).

После 024 `tender_id` = `{source_platform_id}:{native_id}`. Числовые rostender-ряды мигрируют на `rostender:{id}`; том docs на диске — `rostender__{id}/` (двоеточие в имени папки нельзя).

Поля `lot_state`: `viewed`, `viewed_at`, `manual_tier` (`L1` \| `L2` \| `L3` \| null), `manual_tier_at`, `board_hidden`, `board_hidden_at`, плюс ИИ (029): `rules_tier`, `ai_reviewed_at`, `ai_tier`, `ai_reason_ru`, `ai_error`, `ai_wrong_at`, `ai_wrong_note`.

## ИИ-разбор (P10 / 029)

Прогон **не** вызывает ИИ. Оператор на вкладке Лоты:

| Метод | Путь | Назначение |
| --- | --- | --- |
| `POST` | `/api/inbox/ai-review` | body `{ "tender_ids"?: string[] }` — пусто = очередь без успешного review; ответ `{ processed, failed, items }` |
| `POST` | `/api/inbox/{id}/ai-wrong` | body `{ "note"?: string }` — журнал «ИИ ошибся» |
| `GET` | `/api/inbox?ai_reviewed=1` | вкладка «Разобрано с помощью ИИ» (доска по `ai_tier`; «Лоты» — без этого фильтра, колонки по rules) |

Сбой → `ai_error`, tier правил не меняется. `GET /api/status` может нести `ai_failures` (накопитель сбоев с последнего review-батча / сессии UI). Docs download — для лотов пула L1–L3.

## Доска: просрочка и архив (P8 / 027)

- **Read-time:** `deadline_date(deadline_msk) < today_msk` → `deadline_expired: true`; в L1–L3 не рисуем; колонка «Просроченные». Срок **сегодня** — ещё живой. Без разбираемой даты — **вне** доски.
- Default `GET /api/inbox` не отдаёт `board_hidden=true`. GET one / PUT доступны для архивных (вернуть на доску).
- Сорт: живые — score DESC, ближайший срок; просроченные — `deadline` DESC (свежие протухшие сверху).
- Отдельный crontab в P8 **не** вводим: read-time = механизм переноса (закрывает S8).

## REST — Auth (P5.2)

| Метод | Путь | Назначение |
| --- | --- | --- |
| `POST` | `/api/auth/login` | body `{ "username", "password" }` → HttpOnly cookie `scout_session` |
| `POST` | `/api/auth/logout` | сброс сессии (идемпотентно, без обязательной cookie) |
| `GET` | `/api/me` | `{ "username", "display_name" }` — без id, хеша, ролей |

401 на неверный пароль (`detail`: `invalid_credentials`) и на защищённые маршруты без cookie (`unauthorized`). Текст login не различает «нет логина» / «неверный пароль». Cookie: HttpOnly, SameSite=Lax, Path `/`, TTL 7 суток; `Secure` только если `SCOUT_COOKIE_SECURE=1`. Ролей нет: обе учётки видят один inbox.

Публичные `/api/*` без сессии: `GET /api/health`, `POST /api/auth/login`, `POST /api/auth/logout`. Остальные `/api/*` (включая `GET /api/inbox`) без cookie — **401**, не 404.

## REST — существующие (Tech / legacy)

| Метод | Путь | Назначение |
| --- | --- | --- |
| `GET` | `/api/health` | liveness, без секретов (можно без сессии) |
| `GET` | `/api/status` | Фаза, прогресс, очередь поисков, cookies **по площадке**, путь выгрузки — **с сессией** |
| `POST` | `/api/run/start` | Старт **очереди** `in_queue` (023). Body `query`/`limit` не способ настройки |
| `POST` | `/api/run/stop` | Мягкая остановка текущего шага **и** drop хвоста очереди |
| `GET` | `/api/searches` | Список именованных поисков (023) |
| `POST` | `/api/searches` | Создать поиск |
| `PUT` | `/api/searches/{id}` | Правка (имя, площадка, `queries`, `limit_n`, `in_queue`, `sort_order`) |
| `DELETE` | `/api/searches/{id}` | Удалить |
| `GET` | `/api/results` | Legacy список по одному run (AS-IS HTML на деве) |
| `GET` | `/api/results/{tender_id}` | Legacy карточка |

### Именованные поиски (023 **done**)

Тело поиска (GET list item / POST / PUT):

```json
{
  "id": "uuid",
  "name": "РосТендер НК",
  "platform_id": "rostender",
  "queries": ["неразрушающий"],
  "limit_n": null,
  "in_queue": true,
  "sort_order": 0
}
```

`platform_id` сейчас: `rostender` \| `tender-pro`. `queries` — непустой массив строк. Имя уникально. Сиды — [`../discovery/named-searches.md`](../discovery/named-searches.md).

**`limit_n`:** optional soft stop; **`0` = без потолка** (lock 2026-08-27; код [030](./tasks/030-search-coverage.md)). Продуктового must-cap 1000 нет.

Очередь: `POST /api/run/start` без настроек в body. Один шаг очереди = один `runs` (`search_id`, `source_platform_id`). Ошибка шага → `skipped`/`error`, очередь дальше. Стоп рвёт хвост. Пусто → `empty_queue`.

## REST — Sales Inbox (P5.4)

| Метод | Путь | Назначение |
| --- | --- | --- |
| `GET` | `/api/inbox` | Список лотов пула на доске (не `board_hidden`; с датой срока) |
| `GET` | `/api/inbox/{tender_id}` | Карточка + effective tier + viewed + board_hidden + docs meta |
| `PUT` | `/api/inbox/{tender_id}/viewed` | body `{ "viewed": true \| false }` |
| `PUT` | `/api/inbox/{tender_id}/priority` | body `{ "tier": "L1" \| "L2" \| "L3" \| null }` — `null` = сброс к движку |
| `PUT` | `/api/inbox/{tender_id}/board-hidden` | body `{ "hidden": true \| false }` — архив / вернуть на доску |
| `GET` | `/api/inbox/{tender_id}/documents` | Список файлов `{ items: [{ name, size_kb, url }] }` |
| `GET` | `/api/inbox/{tender_id}/documents/{filename}` | Скачивание байтов, `Content-Disposition: attachment`, за сессией |

### Обёртки ответов

- `GET /api/inbox` → `{ "items": [ <элемент> ], "total": N }` (без `run_dir`).
- `GET /api/inbox/{tender_id}` и `PUT` (viewed / priority / board-hidden) → **сам объект лота** (поля элемента + `documents`).
- Сортировка списка: сначала живые (`score` ↓, ближайший `deadline_msk`, `tender_id`), затем просроченные (`deadline_msk` ↓).

### Query `GET /api/inbox`

| Param | Смысл |
| --- | --- |
| `unread` | `true` — только непросмотренные (нет `lot_state` или `viewed=false`) |
| `tier` | `L1` \| `L2` \| `L3` \| `fit` (default `fit` = весь пул L1–L3). `L1`/`L2`/`L3` — по **effective** тиру |
| `q` | поиск title / customer / id / location |
| `deadline_from` / `deadline_to` | срок подачи, ISO `YYYY-MM-DD`, границы включительно (пресеты — в UI) |
| `ingested_from` / `ingested_to` | попало к нам, ISO `YYYY-MM-DD`, границы включительно |

Невалидный `tier`, `unread` или дата → **400**.

### Элемент списка (минимум; паритет с mock)

`deadline_msk` и `ingested_at` в JSON — ISO дата `YYYY-MM-DD`. В таблице `lots.deadline_msk` может лежать display `DD.MM.YYYY[ HH:MM]` (ingest не нормализует) — API парсит при чтении. Неразобранный срок отдаём как есть и **не** включаем строку в выборку, если задан фильтр `deadline_*`.

`customer_name` — одно юрлицо (`clean_customer_name` при list/card/ingest и serialize; колонка списка Rostender без PUA / «Закупки…»).

```json
{
  "tender_id": "...",
  "title": "...",
  "customer_name": "...",
  "score": 7,
  "tier": "L1",
  "effective_tier": "L1",
  "manual_tier": null,
  "viewed": false,
  "board_hidden": false,
  "deadline_expired": false,
  "deadline_msk": "2026-08-20",
  "ingested_at": "2026-08-12",
  "price_rub": null,
  "fit_reason": "...",
  "location": "...",
  "status": "...",
  "url": "...",
  "source_platform_id": "rostender",
  "contact_name": null,
  "contact_phone": null,
  "contact_email": null
}
```

На карточке (GET one / PUT) дополнительно `documents`: массив `{ "name", "size_kb" }` из таблицы `documents` (паритет mock). Поле `url` — только у `GET …/documents`, не у карточки.

`run_dir` в ответе не обязателен (SoT не файловая папка). Для Tech можно отдать идентификатор `run` / дату.

### Ошибки

| Code | Когда |
| --- | --- |
| `400` | валидация body/query / `filename` (`..`, `/`, `\`) / `empty_queue` |
| `401` | нет / протухла сессия Scout |
| `404` | лот не найден в пуле L1–L3; файла нет в `documents` или на томе; поиск не найден |
| `409` | конфликт run (`already_running`) |

Секреты, cookie values площадки, пароли Scout в ответах **запрещены**.

## Документы (P5.5 + целевой контракт P10/029)

- Байты: `{SCOUT_DOCS_DIR}/{volume_dir}/{filename}` где `volume_dir` = `tender_id` с `:` → `__` (compose: `/data/docs/…`). **Не** `runs/YYYY-MM-DD/docs/` — это не SoT inbox.
- Мета: таблица `documents`; `volume_path` = относительный `{volume_dir}/{filename}`. Байты в Postgres **не** кладём.
- Worker: ссылки файлов снимает с HTML карточки (P3, `doc_links`); качает **после ingest** для лотов **на доске** (`tier ∈ {L1, L2, L3}`). Нет отдельных файлов — «Скачать одним архивом» как `{tender_id}-docs.zip`.
- `DOWNLOAD_DOCS=1`/`true`/`yes` — качать новые. Иначе (в т.ч. `0` и unset) — новые файлы не появляются; уже лежащие на томе и в `documents` остаются.
- Повтор: тот же `{tender_id, filename}` не качаем заново, если файл на томе есть; мета upsert. Старые файлы прогон не удаляет. При **update-on-diff** с новыми docs на площадке — докачать недостающие (028/029).
- Имя файла: basename, без `..` / `/` / `\`; ответ download не выходит за `SCOUT_DOCS_DIR`.
- Потолок одного файла: 50 МиБ (больше — skip, не 500).
- Стоп при `AuthError` сессии площадки (как карточки). Soft-stop между файлами.
- Публичных URL без сессии нет: байты только `GET /api/inbox/{id}/documents/{filename}`.

AS-IS до 029: download только для score ≥ 4.

## UI (P6) — зоны vs API

| Зона React | API |
| --- | --- |
| Экран входа | `/api/auth/*` |
| Вкладка «Лоты» | `/api/inbox*` |
| Вкладка «Прогон» | `GET /api/status`, `POST /api/run/start`, `POST /api/run/stop`; CRUD `/api/searches*` (023) |
| Bitrix | **не** в приёмке |

**Клиент (lock, без смены FastAPI):**

- Список: `GET /api/inbox` → `{ items, total }`. В элементах **нет** `documents`. Drawer открывает `GET /api/inbox/{id}` (карточка + `documents: [{ name, size_kb }]`).
- Пресеты дат считает UI; на API — абсолютные `deadline_*` / `ingested_*`. Пресет «любой» — параметры не слать.
- Мультивыбор приоритета в UI: 0 выбранных → `tier=fit`; ровно 1 → этот тир; 2+ → `tier=fit` и фильтр `effective_tier` на клиенте. Query `tier` не расширяем.
- «Скачать»: same-origin `GET /api/inbox/{id}/documents/{filename}` (cookie как у навигации).
- `GET /api/status` (as-is): `list_n` / `list_limit` / `phase` / `session` (`ok` \| `expired` \| `missing_cookies` \| `unknown`), без `phase_label`. UI: `list_done=list_n`, `list_total=list_limit`; `missing_cookies` и `unknown` → session `missing`; подпись фазы — из copy.
- `GET /api/status` (023): плюс текущий поиск, позиция i/N, статусы шагов очереди; cookies **по** `platform_id` (не одно поле rostender).
- `GET /api/status` (028 / P9): плюс `run_report: { new, already, updated, expired }` (накопительно по очереди; `expired` — впервые протухшие в окне прогона). Tech показывает полные RU-фразы.
- `POST /api/run/start` после 023: без body настроек; очередь = поиски с `in_queue=true` по `sort_order`. Пусто → 400 `empty_queue`.
- 401 на `/api/*` после входа → экран логина. Null-поля списка нормализовать в `""` / `[]`.

AS-IS HTML и `/api/results` — только дев/legacy, не публичный `/`.
