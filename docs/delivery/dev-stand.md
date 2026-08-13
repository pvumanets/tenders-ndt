# Дев-стенд — Docker db + api

**status:** accepted  
**last-review-date:** 2026-08-13  
**фаза:** P5.1 DX ([020](./tasks/020-dev-stand.md))  
**compose:** [`../../docker-compose.yml`](../../docker-compose.yml)

Единственный Postgres продукта — контейнер `db`. На Windows Postgres мимо Docker не ставим. Cursor-агент **не** скикает smoke «потому что БД нет»: если стенд лежит — поднимает скриптом.

## Порты

| Снаружи (ПК) | Внутри compose | Что |
| --- | --- | --- |
| `localhost:5433` | `db:5432` | Postgres |
| `localhost:8765` | `api:8765` | FastAPI + собранный React |

`DATABASE_URL` на хосте (pytest, psql) — `localhost:5433`. Если в `.env` задан только `POSTGRES_PASSWORD` (без `DATABASE_URL`), Python на ПК **собирает** DSN сам (`app/db/config.py`). В контейнере `api` compose подставляет `db:5432`.

## Подъём

```powershell
.\scripts\dev-up.ps1
```

Скрипт: Docker Desktop; `.env` с непустым `POSTGRES_PASSWORD`; `cookies.rostender.txt` как **файл**; `docker compose up -d --build`; ждёт `db` healthy и `GET /api/health` 200 с `"db":"ok"`.

Проверки без секретов: [http://localhost:8765/api/health](http://localhost:8765/api/health) · UI [http://localhost:8765/](http://localhost:8765/).

## Fail-closed

- Нет `.env` или пустой `POSTGRES_PASSWORD` — стоп. Заполнить `.env` (имена в `.env.example`). Пароль **не** выдумывать, не писать в чат/git/логи.
- Нет Docker — стоп, поставить Docker Desktop.
- `cookies.rostender.txt` оказался директорией — стоп (Windows bind). Скрипт создаёт пустой **файл**, если пути нет.

## Агенты

Перед кодом API/DB и перед `pytest -m smoke`: если health не 200 — `.\scripts\dev-up.ps1`. Pytest docker **не** стартует сам. `skipped (no DB)` при живом Docker и заполненном `.env` — ошибка процесса (не зелёный отчёт). Скип допустим только если Docker нет или `.env` не заполнен — тогда отчёт **blocked**, owner заполняет `.env`.

Smoke бьёт в тот же Postgres (или `SCOUT_TEST_DATABASE_URL`); только ряды `qa_smoke_*`.
