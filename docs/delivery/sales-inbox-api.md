# Sales Inbox — API и storage

**status:** accepted  
**last-review-date:** 2026-08-13  
**продукт:** [`../discovery/sales-inbox.md`](../discovery/sales-inbox.md)  
**архитектура:** [`tech-architecture.md`](./tech-architecture.md)  
**фазы:** [`platform-phases.md`](./platform-phases.md) — P5.2–P6 **done** → P7 VPS

Термины для владельца: **просмотренность**, **ручная смена приоритета**. Ключи JSON/API — на английском.

SoT: **Postgres**, не `operator-state.json`. Все `/api/*` кроме `GET /api/health`, `POST /api/auth/login`, `POST /api/auth/logout` — **с сессией Scout**.

---

## Пул inbox

- Кандидаты: лоты с **score ≥ 4** в таблице `lots` (после ingest всех прогонов).
- При повторном ingest того же `tender_id` — поля карточки из **последнего** прогона.
- Авто-L3 (score 2–3) в список **не** входят.
- Эффективный приоритет для UI: `manual_tier` из `lot_state`, иначе `tier` движка.

## Storage

| Что | Где |
| --- | --- |
| Карточка лота | `lots` |
| viewed / manual_tier | `lot_state` (один ряд на `tender_id`, глобально) |
| Прогон | `runs` |
| Учётки Scout | `users` (password_hash; bootstrap из `.env`) |
| Сессия Scout | `sessions` (`token_hash` = sha256 opaque cookie; TTL 7 суток) |
| Мета документов | `documents`; байты — том `docs/{tender_id}/` |
| Выгрузка P4 | том (MD/CSV/JSON) — inbox **не** читает |

`viewed` не сбрасывается новым прогоном. `PUT` пишет в `lot_state`, не в файл прогона.

**Ingest (P5.3):** конец прогона (runner и CLI `artifacts` / `run`) вызывает `ingest_run`. В `lots` попадают только строки **score ≥ 4**. Повтор того же `tender_id` — `INSERT … ON CONFLICT` (карточка обновляется). `lot_state` ingest не создаёт и не обновляет. Без `DATABASE_URL` — skip.

Поля `lot_state`: `viewed`, `viewed_at`, `manual_tier` (`L1` \| `L2` \| `L3` \| null = оценка движка), `manual_tier_at` (ISO-8601).

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
| `GET` | `/api/status` | Фаза, прогресс, счётчики, cookies площадки, путь выгрузки — **с сессией** |
| `POST` | `/api/run/start` | Старт (не в React; Q25) |
| `POST` | `/api/run/stop` | Мягкая остановка |
| `GET` | `/api/results` | Legacy список по одному run (AS-IS HTML на деве) |
| `GET` | `/api/results/{tender_id}` | Legacy карточка |

## REST — Sales Inbox (P5.4)

| Метод | Путь | Назначение |
| --- | --- | --- |
| `GET` | `/api/inbox` | Список score≥4 из Postgres |
| `GET` | `/api/inbox/{tender_id}` | Карточка + effective tier + viewed + docs meta |
| `PUT` | `/api/inbox/{tender_id}/viewed` | body `{ "viewed": true \| false }` |
| `PUT` | `/api/inbox/{tender_id}/priority` | body `{ "tier": "L1" \| "L2" \| "L3" \| null }` — `null` = сброс к движку |
| `GET` | `/api/inbox/{tender_id}/documents` | Список файлов `{ items: [{ name, size_kb, url }] }` |
| `GET` | `/api/inbox/{tender_id}/documents/{filename}` | Скачивание байтов, `Content-Disposition: attachment`, за сессией |

### Обёртки ответов

- `GET /api/inbox` → `{ "items": [ <элемент> ], "total": N }` (без `run_dir`).
- `GET /api/inbox/{tender_id}` и оба `PUT` → **сам объект лота** (поля элемента + `documents`).
- Сортировка списка: `score` по убыванию, затем ближайший `deadline_msk`, затем `tender_id`.

### Query `GET /api/inbox`

| Param | Смысл |
| --- | --- |
| `unread` | `true` — только непросмотренные (нет `lot_state` или `viewed=false`) |
| `tier` | `L1` \| `L2` \| `L3` \| `fit` (default `fit` = весь пул score≥4). `L1`/`L2`/`L3` — по **effective** тиру |
| `q` | поиск title / customer / id / location |
| `deadline_from` / `deadline_to` | срок подачи, ISO `YYYY-MM-DD`, границы включительно (пресеты — в UI) |
| `ingested_from` / `ingested_to` | попало к нам, ISO `YYYY-MM-DD`, границы включительно |

Невалидный `tier`, `unread` или дата → **400**.

### Элемент списка (минимум; паритет с mock)

`deadline_msk` и `ingested_at` в JSON — ISO дата `YYYY-MM-DD`. В таблице `lots.deadline_msk` может лежать display `DD.MM.YYYY[ HH:MM]` (ingest не нормализует) — API парсит при чтении. Неразобранный срок отдаём как есть и **не** включаем строку в выборку, если задан фильтр `deadline_*`.

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
| `400` | валидация body/query / `filename` (`..`, `/`, `\`) |
| `401` | нет / протухла сессия Scout |
| `404` | лот не найден в пуле score≥4; файла нет в `documents` или на томе |
| `409` | конфликт run (start) |

Секреты, cookie values площадки, пароли Scout в ответах **запрещены**.

## Документы (P5.5)

- Байты: `{SCOUT_DOCS_DIR}/{tender_id}/{filename}` (compose: `/data/docs/{tender_id}/`). **Не** `runs/YYYY-MM-DD/docs/` — это не SoT inbox.
- Мета: таблица `documents`; `volume_path` = относительный `{tender_id}/{filename}`. Байты в Postgres **не** кладём.
- Worker: ссылки файлов снимает с HTML карточки (P3, `doc_links`); качает **после ingest** только score ≥ 4. Нет отдельных файлов — «Скачать одним архивом» как `{tender_id}-docs.zip`. Пул 1000 не качаем.
- `DOWNLOAD_DOCS=1`/`true`/`yes` — качать новые. Иначе (в т.ч. `0` и unset) — новые файлы не появляются; уже лежащие на томе и в `documents` остаются.
- Повтор: тот же `{tender_id, filename}` не качаем заново, если файл на томе есть; мета upsert. Старые файлы прогон не удаляет.
- Имя файла: basename, без `..` / `/` / `\`; ответ download не выходит за `SCOUT_DOCS_DIR`.
- Потолок одного файла: 50 МиБ (больше — skip, не 500).
- Стоп при `AuthError` сессии площадки (как карточки). Soft-stop между файлами.
- Публичных URL без сессии нет: байты только `GET /api/inbox/{id}/documents/{filename}`.

## UI (P6) — зоны vs API

| Зона React | API |
| --- | --- |
| Экран входа | `/api/auth/*` |
| Вкладка «Лоты» | `/api/inbox*` |
| Вкладка «Прогон» (read-only) | `GET /api/status` |
| Start/Stop в UI | **не** в React |
| Bitrix | **не** в приёмке |

**Клиент (lock, без смены FastAPI):**

- Список: `GET /api/inbox` → `{ items, total }`. В элементах **нет** `documents`. Drawer открывает `GET /api/inbox/{id}` (карточка + `documents: [{ name, size_kb }]`).
- Пресеты дат считает UI; на API — абсолютные `deadline_*` / `ingested_*`. Пресет «любой» — параметры не слать.
- Мультивыбор приоритета в UI: 0 выбранных → `tier=fit`; ровно 1 → этот тир; 2+ → `tier=fit` и фильтр `effective_tier` на клиенте. Query `tier` не расширяем.
- «Скачать»: same-origin `GET /api/inbox/{id}/documents/{filename}` (cookie как у навигации).
- `GET /api/status` отдаёт `list_n` / `list_limit` / `phase` / `session` (`ok` \| `expired` \| `missing_cookies` \| `unknown`), без `phase_label`. UI: `list_done=list_n`, `list_total=list_limit`; `missing_cookies` и `unknown` → session `missing`; подпись фазы — из copy.
- 401 на `/api/*` после входа → экран логина. Null-поля списка нормализовать в `""` / `[]`.

AS-IS HTML и `/api/results` — только дев/legacy, не публичный `/`.
