# tenders-ndt

Operator UI for monitoring NDT-related tenders (Rostender and other platforms).

**Live:** [https://tenders.ndtexam.ru](https://tenders.ndtexam.ru)

## Stack

- FastAPI + Postgres + worker (httpx)
- React operator UI (Scout login)
- Docker Compose (dev and production)

## Quick start (dev)

1. Copy `.env.example` → `.env` and set secrets locally (never commit them).
2. Run `.\scripts\dev-up.ps1` (Windows) or `docker compose up --build`.
3. Open [http://localhost:8765/](http://localhost:8765/).

## License / contact

Private product for ООО СВАРКА / НДТ. Source on GitHub for portfolio and code collaboration.
