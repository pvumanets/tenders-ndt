# Фазы платформы — VPS + Docker + Postgres + вход

**status:** accepted  
**last-review-date:** 2026-08-27  
**owner lock:** 2026-08-13 (дизайн P5.0 accepted; runtime VPS+Docker; Postgres; две учётки без ролей)  
**owner OK:** 2026-08-13 (запрос «делаем P5.1»)  
**P12 канон API:** lock 2026-08-27 — целевой пул `tier ∈ {L1,L2,L3}`; см. [`sales-inbox-api.md`](./sales-inbox-api.md) · [032](./tasks/032-api-canon-sync.md)  
**обзор P0–P5.0:** [`code-phases.md`](./code-phases.md)  
**архитектура:** [`tech-architecture.md`](./tech-architecture.md)  
**API:** [`sales-inbox-api.md`](./sales-inbox-api.md)  
**приёмка:** [`acceptance.md`](./acceptance.md)  
**таски:** [`tasks/README.md`](./tasks/README.md) (012+)

Этот файл — **подробный план хвоста** после visual mock. **Код в этом документе не пишем** — только вход, выход, границы, Done. **Не перескакивать фазы.**

Документ **accepted**. P5.1 **done** — [012](./tasks/012-platform-compose.md). P5.2 **done** — [013](./tasks/013-auth-login.md). P5.3 **done** — [014](./tasks/014-ingest-postgres.md). P5.4 **done** — [015](./tasks/015-inbox-api.md). P5.5 **done** — [016](./tasks/016-docs-volume.md). P6 **done** — [017](./tasks/017-react-wire.md). P7 **done** — [018](./tasks/018-vps-tls.md).

---

## Lock (не переоткрывать)

| Тема | Решение |
| --- | --- |
| P5.0 Sales Inbox (visual) | **accepted** целиком (иконки / рейл включены) |
| Прод | VPS + Docker |
| Дев-стенд | тот же compose на ПК владельца |
| SoT inbox | **Postgres** (лоты + `viewed` + `manual_tier`) |
| Файлы документов | Docker-том |
| Вход | две учётки (digital + директор), **без ролей**, один inbox |
| Worker / scoring P1–P4 | **не выкидываем** |
| `operator-state.json` | больше **не** SoT |
| Директор с любого ПК | пароль только по **HTTPS** (домен — гейт P7) |
| Scout login vs rostender cookies | **два разных auth** |
| Bitrix / роли / cron / Excel-вкладка | NEXT+ |

---

## Обзор

| Фаза | Название | Статус | Таск |
| --- | --- | --- | --- |
| **P5.0** | Visual Sales Inbox (mock) | **accepted** | 001–011 done |
| **P5.1** | Platform (compose + Postgres) | **done** | [012](./tasks/012-platform-compose.md) |
| **P5.2** | Auth (login API + экран входа) | **done** | [013](./tasks/013-auth-login.md) |
| **P5.3** | Ingest (worker → Postgres) | **done** | [014](./tasks/014-ingest-postgres.md) |
| **P5.4** | Inbox API из БД | **done** | [015](./tasks/015-inbox-api.md) |
| **P5.5** | Docs download (том) | **done** | [016](./tasks/016-docs-volume.md) |
| **P6** | Wire mock → API | **done** | [017](./tasks/017-react-wire.md) |
| **P7** | VPS + TLS | **done** | [018](./tasks/018-vps-tls.md) |

```text
P0 … P5 → P5.0 accepted
              → P5.1 Platform → P5.2 Auth → P5.3 Ingest
              → P5.4 Inbox API → P5.5 Docs → P6 Wire → P7 VPS
                                                    ↓
                                              NEXT+: cron, Bitrix, роли,
                                              поиски 023, Tender.Pro 024
```

Без P5.1 нет P5.2. Без P5.3 таблица `lots` пустая — inbox нечем кормить.

---

## Контур (словами, на все фазы)

```text
Director browser  --HTTPS--> Caddy (prod) --> FastAPI (+ собранный React)
Digital PC        --HTTP---> api:8765 (dev, без Caddy)

FastAPI  --> Postgres (users, runs, lots, lot_state, documents meta)
         --> том docs_data  (байты файлов лотов на доске, tier L1–L3)
Worker   --> rostender.info (httpx + cookies.rostender.txt)
         --> Postgres upsert (update-on-diff после 028)
         --> том выгрузки P4 (tenders.md, priority-fit.md)
```

**Compose (один файл, профили):**

- `db` — Postgres 16
- `api` — FastAPI; worker **пока поток внутри API** (как нынешний `runner.py`); в образе — собранный React (multi-stage)
- том `docs_data` — `docs/{tender_id}/`
- bind/secret `cookies.rostender.txt` — **не** в image
- профиль `dev`: без Caddy, `http://localhost:8765`
- профиль `prod`: Caddy + Let's Encrypt

`/` отдаёт React. AS-IS HTML (`app/static/`) **не** корень; на деве `/legacy` (`SCOUT_LEGACY_HTML`).

---

## Схема Postgres (целевая)

Не SQL-миграция (это код P5.1). Колонки — контракт для API и ingest.

| Таблица | Смысл |
| --- | --- |
| `users` | username, password_hash, display_name. Две строки при bootstrap из `.env` (значения **не** в git/docs) |
| `sessions` | Scout login (P5.2): `user_id`, `token_hash` (sha256 opaque cookie), `expires_at`. Не JWT, не in-memory |
| `runs` | дата прогона, query, status, timestamps |
| `lots` | карточка; PK `tender_id`; score, `tier` движка, location, url, `source_platform_id`, контакты, jsonb сырых полей, `ingested_at`, ссылка на последний `run` |
| `lot_state` | PK `tender_id`; `viewed`, `viewed_at`, `manual_tier`, `manual_tier_at` — **глобально** по лоту |
| `documents` | метаданные файла (имя, size, путь на томе); байты не в БД |

Дубли `tender_id`: при update-on-diff (целевой контракт P9) без изменений карточку не переписываем; с diff — поля с площадки. `viewed` не сбрасывается новым прогоном. AS-IS до 028: last-wins UPDATE.

Эффективный приоритет: `manual_tier` если задан, иначе `tier` движка.

Пул inbox (норма с 2026-08-27 / P12): **`tier ∈ {L1, L2, L3}`** — Горячие / Сильные / Смотреть системой. AS-IS код до 029: score ≥ 4 (авто-L3 out).

---

## Два auth

| Контур | Что | Где |
| --- | --- | --- |
| **Scout** | логин/пароль двух учёток, HttpOnly cookie `scout_session` (opaque token → `sessions`; `Secure` если `SCOUT_COOKIE_SECURE=1`) | P5.2; директор и digital |
| **Rostender** | Netscape `cookies.rostender.txt` для worker | как сейчас; [`auth-cookies.md`](./auth-cookies.md) |

Путать нельзя. Пароли Scout и cookie-файл площадки в ответы API **не** попадают.

---

## Шаблон секции фазы

Каждая фаза ниже: статус, зависит от, вход, выход, контур, не делать, Done, owner OK, файлы потом.

---

## P5.0 — Visual Sales Inbox (React + mock)

**Статус:** **accepted** (owner 2026-08-13, целиком, включая иконки/рейл).  
**Зависит от:** P5 (AS-IS HTML).  
**Вход:** design package [`../discovery/design/`](../discovery/design/), [`../discovery/sales-inbox.md`](../discovery/sales-inbox.md).  
**Выход:** кликабельный inbox в `app/web/` на моках, vendored personal kit.

**Контур:** Vite + React; `src/mocks/`; viewed/priority в local state; без `/api/inbox`; без Bitrix.

**Не делать (уже закрыто):** новый визуал доски; P5.1+ код до accept этого документа.

**Done:** `npm run dev` показывает Лоты / Прогон, фильтры personal, доску, таблицу, drawer. Таски 001–011 `done`.

**Owner OK:** получено — «дизайн ок целиком».

**Файлы:** `app/web/` visual; с P6 список читает API (`src/mocks/` — фикстуры). Не перерисовывать экран.

---

## P5.1 — Platform

**Статус:** **done** (2026-08-13)  
**Зависит от:** P5.0 accepted + owner OK на этот документ  
**Таск:** [012](./tasks/012-platform-compose.md)  
**Вход:** этот файл + [`tech-architecture.md`](./tech-architecture.md)  
**Выход:** `docker compose` (dev) поднимает `db` + `api`; миграции Alembic применяются; healthcheck; bootstrap users из env (хеш в БД); том docs смонтирован; React собирается в image.

**Контур:** Postgres 16; FastAPI подключается по `DATABASE_URL`; multi-stage Dockerfile (node build `app/web` → python); cookies bind как сейчас в compose. `/` — собранный React; AS-IS HTML — `/legacy`.

**Не делать:** inbox routes из БД (P5.4); экран входа (P5.2); ingest (P5.3); Caddy/TLS (P7); Bitrix; выкидывание worker.

**Done:**

- [x] `docker compose` на ПК поднимает db+api без ручного Postgres
- [x] таблицы из схемы выше существуют
- [x] две учётки появляются из env при пустой БД (пароли не в логах)
- [x] `/api/health` (или аналог) 200, без секретов

**Owner OK:** нет отдельного гейта; digital проверяет стенд (`.\scripts\dev-up.ps1` — [`dev-stand.md`](./dev-stand.md)). Агент перед smoke сам поднимает compose, не скикает БД.

**Файлы:** `docker-compose.yml`, `Dockerfile`, Alembic, `.env.example` (имена переменных, не значения), `app/db`, `app/api/main.py`, `scripts/dev-up.ps1` ([020](./tasks/020-dev-stand.md)).

---

## P5.2 — Auth

**Статус:** **done** (2026-08-13)  
**Зависит от:** P5.1  
**Таск:** [013](./tasks/013-auth-login.md)  
**Route кода:** scout-backend → scout-designer → scout-ux-writer → scout-frontend  
**Вход:** две учётки в `users`; personal kit  
**Выход:** `POST /api/auth/login`, `POST /api/auth/logout`, `GET /api/me`; все прочие `/api/*` (кроме login и health) — только с сессией; React-экран входа.

**Контур:** сессия = строка `sessions` (не JWT, не RAM). Cookie `scout_session` (HttpOnly, SameSite Lax, Path `/`, TTL 7 суток с логина, без sliding). `Secure` только при `SCOUT_COOKIE_SECURE=1` (дев HTTP = 0; P7 = 1). `GET /api/me` → `{ username, display_name }`. 401 login: `invalid_credentials` без утечки «логин существует». Middleware: любой `/api/*` кроме `GET /api/health`, `POST /api/auth/login`, `POST /api/auth/logout` — только с живой сессией (несуществующий `/api/inbox` без cookie → 401). Ротация пароля: при старте сверка env с хешем по username; смена хеша гасит сессии пользователя. Смена username в env — не авто-rename. Нет ролей. Start/Stop в React — таск [022](./tasks/022-tech-start-stop.md) (после P6).

**Не делать:** Bitrix SSO; JWT в localStorage; роли; публичный inbox без логина; TLS (P7).

**Done:**

- [x] Неверный пароль → 401, без секретов
- [x] Верный логин → cookie; `GET /api/me` ок
- [x] Logout сбрасывает сессию
- [x] Без cookie `/api/inbox` и `/api/status` — 401
- [x] Экран: логин, пароль, «Войти», RU copy, personal kit

**Owner OK:** digital пробует обе учётки на дев HTTP (`docker compose up --build`, `:8765`).

**Файлы:** `app/api/auth.py`, `app/api/main.py`, `app/db` (`sessions`), Alembic `0002_sessions`, `app/web` LoginScreen, `copy.ts`, design W-login.

---

## P5.3 — Ingest

**Статус:** **done** (2026-08-13)  
**Зависит от:** P5.1 (таблицы); P5.2 не блокер для upsert, но API прогона уже за сессией  
**Таск:** [014](./tasks/014-ingest-postgres.md)  
**Вход:** текущий pipeline P1–P4 (`scrape` → score → cards → артефакты)  
**Выход:** конец прогона **upsert** `runs` + `lots` в Postgres. Выгрузка `tenders.md` / `priority-fit.md` / csv **остаётся** на томе (приёмка P4). Inbox эти файлы не читает.

**Контур:** worker-поток как сейчас; после score/cards — запись в БД. `tender_id` обновляет карточку последнего прогона. `lot_state` не затирается.

**Не делать:** читать inbox из JSON; удалять scoring; качать docs (P5.5); менять UI.

**Done:**

- [x] После прогона в `lots` есть строки score≥4 с title, location, url, `source_platform_id` (rostender), `ingested_at`
- [x] Повторный прогон того же `tender_id` обновляет карточку, не дублирует PK
- [x] MD/CSV прогона лежат на томе
- [x] `viewed` / `manual_tier` после повторного ingest на месте

*(Факт выкладки P5.3. Норма с 2026-08-27 / P12: ingest `tier ∈ {L1,L2,L3}` + update-on-diff — код 028/029.)*

**Owner OK:** нет отдельного гейта; digital — один прогон на дев-стенде (нужны живые rostender cookies).

**Файлы:** `app/worker/ingest.py`, `app/api/runner.py`, `app/worker/cli.py`.

---

## P5.4 — Inbox API

**Статус:** **done** (2026-08-13)  
**Зависит от:** P5.3 (данные в БД), P5.2 (сессия)  
**Таск:** [015](./tasks/015-inbox-api.md)  
**Вход:** контракт [`sales-inbox-api.md`](./sales-inbox-api.md)  
**Выход:** `GET/PUT /api/inbox*` читают/пишут Postgres, не `operator-state.json` и не `scored-list.json`.

**Контур:** целевой пул `tier ∈ {L1,L2,L3}` (P12); AS-IS выкладка — score≥4. Query `unread`, `tier`, `q`, `deadline_from/to`, `ingested_from/to`. Пресеты дат («≤7 дней», «сегодня») — **в UI**; API — абсолютные даты ISO `YYYY-MM-DD`. Поля списка как mock: `location`, `source_platform_id`, `url`, контакты, `fit_reason`. `PUT viewed` / `PUT priority` (`null` = сброс к движку) в `lot_state`.

**Не делать:** новый UI доски; Bitrix; снятие моков (P6); docs download (P5.5, meta может быть пустой).

**Done:**

- [x] `GET /api/inbox` только score≥4, с сессией
- [x] viewed и manual_tier переживают перезапуск api/db
- [x] сброс `tier: null` возвращает оценку движка
- [x] 404 вне пула; 400 валидация; секреты не в JSON

*(Факт выкладки P5.4. Норма с 2026-08-27 / P12: `GET /api/inbox` = пул L1–L3 — код 029.)*

**Owner OK:** curl/httpie с cookie сессии.

**Файлы:** `app/api/inbox.py`, `app/api/main.py`. AS-IS `/api/results` остаётся для legacy HTML на деве.

---

## P5.5 — Docs download

**Статус:** **done** (2026-08-13)  
**Зависит от:** P5.4  
**Таск:** [016](./tasks/016-docs-volume.md)  
**Вход:** лоты на доске (`tier ∈ {L1,L2,L3}`); AS-IS выкладка — score≥4; `DOWNLOAD_DOCS`  
**Выход:** файлы в томе `{SCOUT_DOCS_DIR}/{tender_id}/`; метаданные в `documents`; `GET /api/inbox/{id}/documents` + скачивание (за сессией).

**Контур:** httpx download после ingest; путь — том `SCOUT_DOCS_DIR` (compose `/data/docs`), не папка прогона. `DOWNLOAD_DOCS=0` — не качать новые. Ссылки файлов снимает P3 (`doc_links`).

**Не делать:** класть байты в Postgres; публичные URL без сессии; wire React (P6). Обрезка «пул 1000» — не канон продукта (P11).

**Done:**

- [x] при флаге вкл. файлы на томе для score≥4
- [x] список + download в API работают
- [x] флаг 0 — новые файлы не появляются
- [x] 401 без сессии

*(Факт выкладки P5.5. Норма с 2026-08-27 / P12: docs для лотов на доске L1–L3 — код 029.)*

**Owner OK:** API документов **done**; React drawer качает файлы (P6 **done**). Digital: `DOWNLOAD_DOCS=1` и прогон на дев-стенде (нужны живые rostender cookies).

**Файлы:** `app/worker/docs.py`, `app/worker/card_scrape.py`, `app/api/inbox.py`, `app/api/main.py`, `app/api/runner.py`, `app/worker/cli.py`.

---

## P6 — Wire React

**Статус:** **done**  
**Зависит от:** P5.4 и P5.5 (**done** — документы must на демо директору)  
**Таск:** [017](./tasks/017-react-wire.md)  
**Вход:** UI P5.0 + реальный `/api/inbox*` + `/api/auth*` + `/api/status`  
**Выход:** моки сняты; тот же inbox; экран входа; вкладка Прогон (статус; Start/Stop — 022).

**Контур:** после логина — текущие Лоты. Local state viewed/priority заменяется API. Пресеты дат считают `from/to` на клиенте.

**Не делать (тогда):** новая доска; Start/Stop в React (снято в 022); Bitrix; перерисовка под 520px vs personal 400px (остаётся personal shell ~400px, как accepted mock).

**Done:**

- [x] без мока inbox.json как источника списка
- [x] непросмотренные / приоритет / поиск / даты ходят в API
- [x] 401 → логин
- [x] Tech status (Start/Stop — 022)

**Owner OK:** digital на дев-стенде проходит сценарий директора (логин → непросмотренные → drawer; файлы, если был прогон с `DOWNLOAD_DOCS=1`).

**Файлы:** `app/web/src/lib/inbox.ts`, `App.tsx`; `src/mocks/*.json` — фикстуры тестов, не SoT.

---

## P7 — VPS + TLS

**Статус:** **done** (HTTPS [tenders.ndtexam.ru](https://tenders.ndtexam.ru); owner 2026-08-19: логин с другого ПК ок)  
**Зависит от:** P6; **домен** на A-запись VPS (owner)  
**Таск:** [018](./tasks/018-vps-tls.md)  
**Вход:** тот же compose, профиль `prod`  
**Выход:** директор открывает HTTPS URL с любого ПК, логин/пароль, тот же inbox. Cookies rostender и пароли Scout — только на сервере (env/secrets).

**Контур:** Caddy + Let's Encrypt на **https://tenders.ndtexam.ru**. `SCOUT_COOKIE_SECURE=1`. Дев-стенд на ПК остаётся HTTP analog. Код: GitHub + overlay prod compose/Caddyfile. Доступ: [`vps.md`](./vps.md). Публично только 80/443; `:8765` на loopback.

**Не делать:** роли; Bitrix; cron; открытый HTTP с паролем в интернет (fail); коммит секретов.

**Done:**

- [x] HTTPS без warning (валидный сертификат)
- [x] логин директора с другой машины
- [x] сессия переживает перезапуск контейнера api (БД жива)
- [x] cookies rostender не в git и не в UI

**Owner OK:** демо директору — открыть https://tenders.ndtexam.ru с другого ПК. Учётки и cookies rostender уже на сервере.

**Файлы:** [`docker-compose.prod.yml`](../../docker-compose.prod.yml), [`Caddyfile`](../../Caddyfile), [`vps.md`](./vps.md), [`runbook-agent-v0.md`](./runbook-agent-v0.md).

---

## После P7 (NEXT+)

Детальный план фаз **P8–P14** (просрочка, прогон, тиры/ИИ, сиды, wipe, hardening): [`next-phases.md`](./next-phases.md) (`draft`, lock 2026-08-27).

Краткий список хвоста:

- Именованные поиски + очередь — [023](./tasks/023-named-searches.md) (**done**); lock [`../discovery/named-searches.md`](../discovery/named-searches.md)
- Адаптер Tender.Pro — [024](./tasks/024-tender-pro-adapter.md) (**done**)
- Cron прогона
- Роли (если digital ≠ директор по правам)
- Bitrix leads
- Excel-вкладка
- Остальные ЭТП (реестр [`../discovery/platforms.md`](../discovery/platforms.md); зонды СИБУР / OnlineContract)

Start/Stop в Tech — [022](./tasks/022-tech-start-stop.md) (**done**, owner 2026-08-19).

---

## Owner must (не код)

- Домен для P7 (без него прод с паролем директора не принимаем)
- Два логина/пароля только в `.env` дев и VPS — не в чат, не в git
- `cookies.rostender.txt` на машине прогона (дев или VPS)

---

## Вне скоупа платформенных фаз

NAS / LNA / бюджет. Выкидывание worker. Новый визуал inbox.
