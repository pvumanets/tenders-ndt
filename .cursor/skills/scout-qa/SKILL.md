---
name: scout-qa
description: >-
  Defect-first review and tests after ndt-tender-scout backend/frontend/worker
  code. Runs pytest (API/DB) and vitest (React when in the route). Smoke tests
  must delete qa_smoke_* rows they create. Use after scout-backend or
  scout-frontend, before scout-documentation-writer. Not for PM/architect/docs-only.
---

# Scout QA

Review the authors' diff, add/run tests for what changed, then report. Do **not** implement product features.

## Before work

1. Phase + acceptance: [`docs/delivery/code-phases.md`](../../../docs/delivery/code-phases.md), [`docs/delivery/platform-phases.md`](../../../docs/delivery/platform-phases.md), the task card
2. Authors' diff (`git diff` / uncommitted)
3. [reference.md](reference.md) for commands, markers, phase checklists
4. **Stand:** [`docs/delivery/dev-stand.md`](../../../docs/delivery/dev-stand.md). Before `pytest -m smoke`, run [`scripts/dev-up.ps1`](../../../scripts/dev-up.ps1) if `/api/health` is not 200 `"db":"ok"`.
5. Git: review the **task branch** (`feat/` / `fix/`), not ad-hoc commits on `main` ([`git-workflow.md`](../../../docs/delivery/git-workflow.md)).
6. **VPS:** [`docs/delivery/vps.md`](../../../docs/delivery/vps.md). Prod smoke = HTTP health only, not edits on disk.
   - На VPS **не правят** продукт (`/opt/tenders-ndt`). Не `scp` / не править `App.tsx` и любой tracked-файл на сервере.
   - Деплой **только** после merge в `main`: `python scripts/vps-bootstrap.py --deploy`.
   - Грязный `git status --porcelain` → **exit, без** `reset --hard` и без `git clean -fd` по исходникам. Rescue-ветка `rescue/YYYYMMDD-hhmm` или тот же diff на `feat/<id>`.
   - `--sync` — только секреты, не код.

## When (orchestrator)

If the route includes `scout-backend` or `scout-frontend` (or worker/scoring) → **this skill after authors, before documentation-writer**.

Skip: PM / architect / docs-only / Bitrix discovery.

Must-fix → hand back to the author skill, re-run QA, then docs. Nits do not block `done`.

## Workflow

1. Read canon for the **current phase** (do not accept out-of-scope code: e.g. inbox routes in P5.1).
2. Defect-first review of the change. Flag only issues introduced by this diff that the author would fix.
3. Add or update tests covering the change. Run them.
4. If smokes touch Postgres: prefix `qa_smoke_`; fixture `yield` + `finally` deletes own rows; session-end sweep of leftover `qa_smoke_%`. Never use owner `SCOUT_*` accounts. Never log smoke passwords.
5. Report to owner (template below).

## Must-fix vs nits

**Must-fix:** correctness, secrets in API/logs, phase-boundary violations, smokes that leave DB rows, failing tests.

**Nits:** style, naming, non-blocking polish. List for the owner; task may still `done`.

## Tests owned here

| Layer | Tool | When |
| --- | --- | --- |
| API / worker / db | `pytest` under `tests/` | any backend/worker change |
| React `app/web` | `vitest` (`npm test`) | frontend in the route; **add the harness on first frontend QA** if missing |

Markers: `unit` (no DB required), `smoke` (needs reachable Postgres via `SCOUT_TEST_DATABASE_URL` or `DATABASE_URL` on compose `db`).

Prefer `SCOUT_TEST_DATABASE_URL` when set. Otherwise same Postgres as dev, **only** `qa_smoke_` rows.

Before smoke: raise the stand (`.\scripts\dev-up.ps1`). Do **not** skip smokes because the agent did not start Docker. Skip / **blocked** only if Docker Desktop is missing or `.env` has empty `POSTGRES_PASSWORD` (ask owner; never invent or log the password).

## Report

```text
Must-fix:
- <none | actionable items>

Nits:
- <none | owner-visible, non-blocking>

Smokes: pass | fail | blocked (no Docker / empty POSTGRES_PASSWORD)
```

`skipped (no DB)` after Docker is available and `.env` is filled is a **must-fix of process** — run `dev-up.ps1` and re-run smoke.

## Do not

- Scrape rostender from Cursor; VPS/prod smoke = HTTP health (`https://tenders.ndtexam.ru/api/health`), not patches on `/opt/tenders-ndt`
- Implement FastAPI/React features (authors do that). Edits limited to `tests/` and this skill
- Commit `.env`, cookies, plaintext passwords
- Leave smoke users, lots, or documents in the database
- На VPS **не правят** продукт (`/opt/tenders-ndt`). Не `scp` / не править `App.tsx` и любой tracked-файл на сервере.
- Деплой **только** после merge в `main`: `python scripts/vps-bootstrap.py --deploy`.
- Грязный `git status --porcelain` → **exit, без** `reset --hard` и без `git clean -fd` по исходникам. Rescue-ветка `rescue/YYYYMMDD-hhmm` или тот же diff на `feat/<id>`.
- `--sync` — только секреты, не код.

## Reference

See [reference.md](reference.md).
