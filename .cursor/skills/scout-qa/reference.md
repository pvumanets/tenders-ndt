# Scout QA — reference

## Commands

```text
.\scripts\dev-up.ps1
pytest
pytest -m unit
pytest -m smoke
```

Frontend (when vitest exists in `app/web`):

```text
npm test
```

If the route includes frontend and `npm test` is missing, add vitest in that QA pass (not in a Python-only change).

## DB cleanup contract

- Username / tender_id / filename prefix: `qa_smoke_`
- Create in a `try` / pytest fixture; delete in `finally` even on assertion failure
- Session fixture: sweep `User.username.startswith("qa_smoke_")` (and later lots/documents with the same prefix) at **start and end**
- Do not insert owner `SCOUT_DIGITAL_*` / `SCOUT_DIRECTOR_*` as smoke data
- Fail the review (must-fix) if a new smoke has no teardown

`SCOUT_TEST_DATABASE_URL` overrides `DATABASE_URL` for pytest (see `tests/conftest.py`).

Before smoke: [`scripts/dev-up.ps1`](../../../scripts/dev-up.ps1) ([`docs/delivery/dev-stand.md`](../../../docs/delivery/dev-stand.md)). Pytest does **not** start Docker itself. If ping still fails after `dev-up`, the skip message points at that script.

**Blocked** (not a green skip): Docker missing, or `.env` without `POSTGRES_PASSWORD`. Do not invent a second Postgres. Do not print secrets.

## Phase checklists (extend when a phase lands)

### P5.1 Platform

Covered by `tests/` (`pytest -m unit`; `pytest -m smoke` if Postgres is up):

- `GET /api/health` JSON is only `ok` + `db`; no DSN, password, cookie
- Status 200 (db up) or 503 (db down), never 500 for "db down"
- `/` is React dist when built; `/legacy` is AS-IS HTML
- Bootstrap hashes passwords; empty DB + missing env fails closed without logging secrets

### P5.2 Auth

Covered by `tests/test_auth_unit.py`, `tests/test_auth_smoke.py`, and `app/web` `npm test`:

- Login 401 `invalid_credentials` does not reveal whether the username exists
- Without cookie: `/api/me`, `/api/status`, `/api/inbox`, `/api/results` are 401 (inbox body is P5.4)
- Logout 204; session cookie cleared; `/api/health` stays public
- Smoke: login → `/api/me` `{username, display_name}` → logout; password rotation invalidates sessions
- Vitest: LoginScreen shows `login_error` on failed submit

### P5.3 Ingest

Covered by `tests/test_ingest_unit.py` and `tests/test_ingest_smoke.py`:

- Mapping: score ≥ 4 only; `source_platform_id=rostender`; location cleaned
- No `DATABASE_URL` → ingest skip; P4 MD/CSV still written
- DSN/password not in ingest error text
- Smoke: upsert same `tender_id` updates card; `lot_state.viewed` / `manual_tier` stay; prefix `qa_smoke_`

### P5.4 Inbox API

Covered by `tests/test_inbox_unit.py` and `tests/test_inbox_smoke.py`:

- Without cookie: `GET/PUT /api/inbox*` are 401; documents list/download are 401
- Query `tier=L9` / bad ISO date → 400 (`invalid_tier` / `invalid_date`)
- `deadline_msk` display `DD.MM.YYYY` serializes to ISO `YYYY-MM-DD`
- Smoke: list is score ≥ 4 only; PUT viewed/priority persist across a new client; `tier: null` restores engine `effective_tier`; 404 outside the pool; prefix `qa_smoke_`

### P5.5 Docs download

Covered by `tests/test_docs_unit.py` and `tests/test_docs_smoke.py`:

- `DOWNLOAD_DOCS=0` does not fetch or write files
- `DOWNLOAD_DOCS=1` writes score≥4 files to `SCOUT_DOCS_DIR/{tender_id}/`; lower scores skipped
- Card HTML: per-file links preferred; archive only as fallback
- Filename traversal rejected (`..`, `/`); download stays inside the volume
- Without cookie: documents list/download are 401
- Smoke: list `{items:[{name,size_kb,url}]}`; download returns bytes; 404 missing; prefix `qa_smoke_`

### P6 Wire React

Covered by `app/web` `npm test` (`lib/date-filters.test.ts`, `lib/inbox.test.ts`, `App.test.tsx`):

- Date presets map to `deadline_*` / `ingested_*`; `any` omits params
- Multi-tier: 0 or 2+ → query `tier=fit`; single selection sends that tier
- `GET /api/status`: `list_n`/`list_limit` → `list_done`/`list_total`; `missing_cookies` → `missing`
- 401 on inbox → login screen, no lots
- Mocks are fixtures only; App does not import `inbox.json` / `tech.json`

### P1 open/upcoming (019)

Covered by `tests/test_list_filter_unit.py`:

- List HTML: drop past `.dtend` and status Завершён/Отменён
- Keep deadline ≥ today MSK inclusive


## Review bar (defect-first)

Flag when all are true: introduced by this change; actionable; correctness / secrets / phase boundary / leftover smoke data; author would fix it.

Do not flag pre-existing issues, speculative nits as must-fix, or intentional phase deferrals.
