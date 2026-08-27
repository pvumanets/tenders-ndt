# Техархитектура — ndt-tender-scout

**status:** accepted  
**last-review-date:** 2026-08-27  
**код + канон:** этот репозиторий (`docs/`)  
**Sales Inbox API:** [`sales-inbox-api.md`](./sales-inbox-api.md) (P12 sync lock 2026-08-27)  
**Фазы P0–P5.0:** [`code-phases.md`](./code-phases.md)  
**Фазы P5.1–P7:** [`platform-phases.md`](./platform-phases.md) (`accepted`; P5.1–P7 **done**)  
**Фазы NEXT+:** [`next-phases.md`](./next-phases.md)

Owner lock 2026-08-13: дизайн P5.0 **accepted**; runtime **VPS + Docker**; ПК = тот же compose; SoT inbox = **Postgres**; две учётки без ролей. P5.1–P7 **done**. Именованные поиски ([023](./tasks/023-named-searches.md)) и Tender.Pro ([024](./tasks/024-tender-pro-adapter.md)) **done**. Lock 2026-08-27: пул доски L1–L3, update-on-diff, без must limit 1000 — канон API [032](./tasks/032-api-canon-sync.md); код 028/029/030.

---

## Целевое репо

| Параметр | Значение |
| --- | --- |
| Путь | `C:\Users\NDT\Documents\ndt-tender-scout` |
| Git | **GitHub SoT:** [pvumanets/tenders-ndt](https://github.com/pvumanets/tenders-ndt) · ветка `main` · [git-workflow.md](./git-workflow.md) |
| Runtime **prod** | **VPS** `77.91.94.111` + Caddy TLS · [https://tenders.ndtexam.ru](https://tenders.ndtexam.ru) ([`vps.md`](./vps.md)) |
| Runtime **dev** | тот же compose на ПК владельца (без Caddy, HTTP `:8765`) |
| Не runtime | Cursor-агент как исполнитель прогона; GPT/LLM API для скрейпа |

Канон scope, L1–L3, acceptance — в **`docs/` этого репо**. Business-proc хранит только статус эпика.

## Стек (зафиксирован)

| Слой | Технология |
| --- | --- |
| Язык | Python 3.12 |
| Сбор списка (P1) | **httpx + BeautifulSoup**; адаптер по `platform_id` поиска (023/024). Playwright — WAF 403 на rostender; Tender.Pro список без Playwright |
| Карточки (P3+) | httpx + BeautifulSoup |
| Документы (P5.5) | httpx download → том `docs/{tender_id}/` для лотов **на доске** (`tier ∈ {L1,L2,L3}`); метаданные в Postgres. AS-IS до 029: score ≥ 4 |
| SoT inbox | **Postgres 16** (`lots`, `lot_state`, `runs`, `users`, `sessions`, `documents`; 023: `searches`) |
| API | FastAPI (`/api/auth*`, `/api/status`, `/api/run/*`, `/api/searches*` (023), `/api/results*`, `/api/inbox*`) |
| Экран оператора **AS-IS** | static HTML (`app/static/`) — не корень `/`; hotfix / legacy на деве |
| Экран оператора **TO-BE** | **React** SPA в `app/web/` — P5.0 mock **accepted**; **P6 done** (живой `/api/*`); за Scout-логином с P5.2 |
| Упаковка | Docker Compose: `db` + `api` (worker-поток внутри api); prod + Caddy |
| Секреты | `.env` / `.env.vps` (gitignore) + Netscape cookies-файл. Пароли не в git и не в skills. |
| Выгрузка P4 | том прогона: CSV + MD + JSON (inbox их **не** читает) |

Вне текущего ship: Bitrix lead sync, роли, cron, Excel-вкладка, СИБУР / OnlineContract / остальные ЭТП кроме Tender.Pro. Поиски + Tender.Pro — **done** (023/024); lock [`../discovery/named-searches.md`](../discovery/named-searches.md).

## FAQ — стек, скрейп, VPS (обновлено 2026-08-13)

| Вопрос | Ответ |
| --- | --- |
| Кто ходит по rostender? | **Python worker** (`httpx` + BeautifulSoup) с **cookies-файлом**. Не Cursor, не браузер-агент ChatGPT. |
| Нужен ли GPT / OpenAI API? | **Нет** для скрейпа и скоринга L1–L3. |
| Где крутится прод? | **VPS + Docker**. |
| Что такое дев-стенд? | Тот же compose на ПК: analog прода, HTTP, без публичного интернета. |
| Кто открывает UI? | Директор с любого компьютера (HTTPS + логин) и digital на деве. |
| Шаринг / роли | Две учётки, **одинаковый** inbox, без ролей. Роли — NEXT+. |
| Где лоты и «просмотрено»? | **Postgres**. Не `operator-state.json`. |
| Стек UI | **React** → FastAPI `/api/*` за сессией. AS-IS HTML не `/`. |
| Cursor | Редактор/агент для кода и docs — **не** runtime прогона. |

## Поток данных

```text
cookies.{platform}.txt         # Netscape; rostender обязателен; tender-pro список публичный
    → httpx worker (адаптер по platform_id поиска)
        → список (без must limit 1000), score, карточки L1–L3
        → ingest Postgres (runs, lots) — tier ∈ {L1,L2,L3}; update-on-diff
        → docs download для лотов на доске → том + documents meta
        → выгрузка P4 на том (tenders.md, priority-fit.md)
    ← FastAPI (session Scout)
        /api/auth/*             (логин двух учёток)
        /api/searches*          (именованные поиски, 023)
        /api/status, /api/run/* (очередь in_queue; Стоп рвёт хвост)
        /api/results*           (legacy HTML на деве)
        /api/inbox*             (Sales Inbox ← Postgres, пул L1–L3)

Director  --HTTPS--> Caddy --> React+API
Digital   --HTTP---> compose на ПК
```

## Компоненты

```text
ndt-tender-scout/
  AGENTS.md
  README.md
  docker-compose.yml             # db + api (P5.1); profile prod = Caddy (P7)
  .env.example
  alembic.ini
  cookies.rostender.txt          # gitignore; bind на api
  cookies.tender-pro.txt         # gitignore; 024; список публичный
  app/
    api/                         # FastAPI + health + Scout session (P5.2); ingest P5.3; inbox P5.4
    db/                          # SQLAlchemy models, bootstrap users
    worker/                      # scrape + artifacts + ingest (P5.3) + docs (P5.5)
    scoring/                     # L1–L3 (синхрон с docs/)
    static/                      # AS-IS HTML (/legacy)
    web/                         # React (P5.0 accepted; в image P5.1; P6 done)
  docs/                          # canon
  .cursor/skills/
```

Том данных на VPS ≠ «папка на ноутбуке Павла». На деве том просто лежит на ПК.

## Связь репозиториев

| Что | Где |
| --- | --- |
| Product / discovery / delivery | **этот репо** `docs/` |
| Эпик / редкий статус | `ndt-buisness-proc` stub `docs/projects/tender-monitoring/` |
| Код + Docker | этот репо ([GitHub](https://github.com/pvumanets/tenders-ndt); P7 клонирует origin, не папку с ПК) |

## Decisions (lightweight ADR)

### Decision: inbox pool = tier L1∪L2∪L3 (amended 2026-08-27)

**Context:** Нужен канон пула Sales Inbox / «непросмотренных». Было: score ≥ 4 (= L1∪L2), авто-L3 out.  
**Options:** (A) L1∪L2∪L3 по `tier`; (B) score ≥ 6; (C) score ≥ 4.  
**Choice (было 2026-08-13):** **C**.  
**Choice (lock 2026-08-27 / P12):** **A** — на доске Горячие / Сильные / **Смотреть** заполняет система (`tier ∈ {L1,L2,L3}`).  
**Consequences:** Ingest, `/api/inbox` и docs download согласованы на пул доски. Код догоняет в 028/029. ADR supersedes «inbox score ≥ 4».

### Decision: Postgres is inbox SoT (замена operator-state.json)

**Context:** 2026-08-12 SoT был `runs/YYYY-MM-DD/operator-state.json` на localhost. Owner 2026-08-13: прод = VPS, данные не «папка на ПК», нужен вход директора с любого компьютера.  
**Options:** (A) JSON на томе; (B) Postgres (лоты + state); (C) выкинуть worker.  
**Choice:** **B**. Worker и выгрузка P4 остаются. `viewed` / `manual_tier` в `lot_state` по `tender_id` глобально.  
**Consequences:** [`sales-inbox-api.md`](./sales-inbox-api.md); фазы [`platform-phases.md`](./platform-phases.md). JSON-state **не** SoT.

### Decision: VPS prod, PC analog, HTTPS for director

**Context:** Директор заходит с любого ПК с логином/паролем.  
**Choice:** один compose; dev = HTTP на ПК; prod = VPS + Caddy/Let's Encrypt. Без домена P7 не закрываем (пароль по открытому HTTP в интернет — fail).  
**Consequences:** две учётки без ролей; Scout session ≠ rostender cookies.

### Decision: P5.0 mock then platform phases (не P6-before-React)

**Context:** Ранее: JSON API → docs → Docker → wire React; VPS = NEXT+. React mock уже принят.  
**Choice:** P5.0 accepted → P5.1 Platform → P5.2 Auth → P5.3 Ingest → P5.4 Inbox API → P5.5 Docs → P6 Wire → P7 VPS.  
**Consequences:** Docker не «после UI», а **с P5.1**. Wire — P6. VPS в ship, не NEXT+.

### Decision: P5.5 docs = volume + session download, not run_dir

**Context:** Демо директору must с файлами. Байты не в Postgres. Старый output-schema клал файлы в `runs/YYYY-MM-DD/docs/`.  
**Options:** (A) папка прогона; (B) том `SCOUT_DOCS_DIR` + таблица `documents` + API за сессией.  
**Choice:** **B**. `DOWNLOAD_DOCS=0` — kill switch (новые не качать). Имена файлов — basename без traversal. Потолок 50 МиБ.  
**Consequences:** [`sales-inbox-api.md`](./sales-inbox-api.md) § Документы; drawer бьёт в `/api/inbox/{id}/documents*`.

### Decision: P5.3 ingest = tier L1–L3 + update-on-diff (amended 2026-08-27)

**Context:** Inbox SoT = Postgres. Worker P1–P4 остаётся; файлы прогона — выгрузка, не inbox. `lot_state` глобален по `tender_id`.  
**Options:** (A) писать все scored-строки; (B) только score ≥ 4, всегда ON CONFLICT UPDATE; (C) отдельный ingest-сервис; (D) `tier ∈ {L1,L2,L3}` + update-on-diff.  
**Choice (было P5.3):** **B**.  
**Choice (lock 2026-08-27 / P12):** **D** — в `lots` строки с `tier ∈ {L1,L2,L3}`; повторный `tender_id`: без diff на площадке → skip UPDATE («Уже были»); с diff → UPDATE полей («Обновлено с площадки»). `lot_state` / AI-флаги **не** трогаем. Реализация: [028](./tasks/028-run-idempotent-report.md) / [029](./tasks/029-tier-rules-and-ai.md).  
**Consequences:** P5.4 читает пул L1–L3; повторный прогон не сбрасывает viewed/manual_tier. **P9/028 done** (update-on-diff + `run_report`). AS-IS пул до 029: score ≥ 4.

### Decision: named searches + queue (2026-08-19)

**Context:** Нужны настройки поисков под разные ЭТП в продукте, не хардкод «неразрушающий» на Старте.  
**Options:** (A) одна карточка на площадку; (B) именованные поиски; (C) поля только на кнопке Старт.  
**Choice:** **B** + очередь `in_queue` на одном Старте. Первый чужой адаптер — Tender.Pro.  
**Consequences:** [`../discovery/named-searches.md`](../discovery/named-searches.md); API `/api/searches*`; `tender_id` prefix с 024.

## Риски / откат

- Rostender cookies протухают; ToS — [../discovery/risks-compliance.md](../discovery/risks-compliance.md). Обрезка limit 1000 — **не** канон продукта (P11/030); AS-IS в коде до 030.  
- Docs: для лотов на доске (`tier ∈ {L1,L2,L3}`); `DOWNLOAD_DOCS`; стоп при ошибке сессии площадки. **P10/029 done.**
- Дубли `tender_id`: update-on-diff (**P9/028 done**); `viewed` / AI-поля не сбрасываются. С 024 ключ = `{platform_id}:{native_id}`. Пул **tier L1–L3** (**P10/029 done**).
- ИИ: `POST /api/inbox/ai-review` по кнопке; `lot_state` AI-поля; прогон без авто-ИИ.
- Пароль Scout в git/чат — смена паролей обеих учёток.  
- Откат UI: AS-IS HTML не публичный `/`; React inbox читает Postgres (P6).
