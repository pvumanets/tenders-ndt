---
id: "012"
type: task
status: done
phase: P5.1
title: "Platform: compose db+api, Alembic, bootstrap users"
was: ""
---

# 012 — Platform: compose db+api, Alembic, bootstrap users

**route:** scout-architect → scout-backend → scout-documentation-writer

## Проблема

Inbox SoT больше не JSON на ПК. Нужен одинаковый Docker-контур на деве и (потом) на VPS: Postgres, api, том docs.

## Решение

См. [`../platform-phases.md`](../platform-phases.md) § P5.1. Compose: `db` + `api`; миграции; bootstrap двух учёток из env; healthcheck; multi-stage React в image.

## Acceptance

- [x] `docker compose` на ПК поднимает db+api без ручного Postgres
- [x] таблицы канона существуют
- [x] две учётки из env при пустой БД; пароли не в логах
- [x] health 200 без секретов

## Файлы

- `docker-compose.yml`, `Dockerfile`, Alembic, `.env.example`, `app/db`, `app/api` (подключение к БД)

## Out of scope

- Login UI (013), ingest (014), inbox routes (015), Caddy/TLS (018)

## Links

- Phases: [`../platform-phases.md`](../platform-phases.md)
- Index: [README](./README.md)
