# tenders-ndt

Operator product for **ООО СВАРКА / НДТ** — monitors NDT-related tenders across Russian procurement platforms, scores fit, and routes hot leads to the sales inbox and Bitrix24.

**Live:** [https://tenders.ndtexam.ru](https://tenders.ndtexam.ru) (Scout login is private; not a public demo.)

[![CI](https://github.com/pvumanets/tenders-ndt/actions/workflows/ci.yml/badge.svg)](https://github.com/pvumanets/tenders-ndt/actions/workflows/ci.yml)

## What it does

1. **Ingest** — scrapes open lots from configured ETPs (Rostender, Roseltorg, B2B-Center, RTS Rosatom, and others).
2. **Score** — rules + AI classify fit into L1 / L2 / L3 for NDT services.
3. **Operate** — React inbox for triage, documents, export, and schedule.
4. **Notify** — Bitrix24 leads and ops chat for actionable lots.

## Stack

- **API / worker:** FastAPI, httpx, Postgres, Alembic
- **UI:** React operator SPA (session auth)
- **Runtime:** Docker Compose (dev + production with Caddy TLS)

## Repository map

| Path | Role |
| --- | --- |
| `app/` | API, worker, scoring, Bitrix, React (`app/web`) |
| `alembic/` | DB migrations |
| `tests/` | pytest unit suite (+ smoke when DB is up) |
| `scripts/` | Dev stand (`dev-up.ps1`) and thin VPS deploy helper |
| `.github/workflows/` | CI: `pytest -m unit`, vitest, `tsc` |

## Quick start (dev)

1. Copy `.env.example` → `.env` and fill secrets locally (never commit them).
2. Run `.\scripts\dev-up.ps1` (Windows) or `docker compose up --build`.
3. Open [http://localhost:8765/](http://localhost:8765/).

## License

Private product. All rights reserved © ООО СВАРКА / НДТ.

Source on GitHub is for portfolio review and authorized collaboration. Product documentation is private and is not published in this repository.
