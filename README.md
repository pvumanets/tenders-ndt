# ndt-tender-scout

UI-мониторинг тендеров [rostender.info](https://rostender.info) для **ООО СВАРКА**.

**GitHub:** [pvumanets/tenders-ndt](https://github.com/pvumanets/tenders-ndt) · ветка `main` · [git workflow](./docs/delivery/git-workflow.md)

**Phases:** P0–P6 done · **P7** VPS + TLS next.

## Canon (this repo)

| | |
| --- | --- |
| Map | [docs/README.md](./docs/README.md) |
| Index | [docs/CANON.md](./docs/CANON.md) |
| Dev stand | [docs/delivery/dev-stand.md](./docs/delivery/dev-stand.md) |
| Agents | [AGENTS.md](./AGENTS.md) |
| Entry skill | **`scout-orchestrator`** (always multi-routes `scout-*`) |

Business-proc keeps only an epic stub — do not edit product rules there.

## Dev stand (P5.1, Docker)

Тот же compose, что потом на VPS (без Caddy). Канон: [docs/delivery/dev-stand.md](./docs/delivery/dev-stand.md).

1. Скопируйте `.env.example` → `.env` (или допишите новые переменные, если `.env` уже есть) и заполните `POSTGRES_PASSWORD` и две пары Scout (значения не в git и не в чат). Если пароль Postgres содержит `@` или `:`, URL-кодируйте его в `DATABASE_URL` на хосте; в compose для api пароль подставляется отдельно.
2. Поднять стенд (создаст пустой `cookies.rostender.txt`, если файла нет):

```powershell
.\scripts\dev-up.ps1
```

Эквивалент вручную: `docker compose up --build` (скрипт ещё ждёт health).

- React (живой API, P6): [http://localhost:8765/](http://localhost:8765/)
- AS-IS техпанель: [http://localhost:8765/legacy](http://localhost:8765/legacy)
- Health: [http://localhost:8765/api/health](http://localhost:8765/api/health)

Агент перед `pytest -m smoke` сам гоняет `dev-up.ps1`, если health не 200. Пароль из `.env` не выдумывает.

## Operator UI без Docker (venv)

Нужен тот же Postgres (`db` на :5433). Стенд `db` всё равно поднимайте скриптом. API с хоста:

```powershell
.\.venv\Scripts\Activate.ps1
python -m app.api
# → http://127.0.0.1:8765/  (React dist, если собран; иначе AS-IS HTML)
```

Start / Stop · phases · L1–L3 — на `/legacy`.  
**TO-BE:** React SPA за Scout-логином (P5.2 / P6) — `docs/delivery/operator-ui.md`.

## CLI

```powershell
python -m app.worker run --limit 1000 --out runs/YYYY-MM-DD
python -m app.worker run --from-score --out runs/2026-08-11
```

## Secrets

`cookies.rostender.txt` + `.env` — gitignore. Rules: `docs/delivery/auth-cookies.md`.

## Transport

httpx + cookies (Playwright → WAF 403 in current env).
