---
id: "040"
type: task
status: done
phase: NEXT+
title: "Адаптер Росэлторг CORP"
was: ""
---

# 040 — Адаптер Росэлторг CORP

**route:** scout-architect → scout-backend → scout-qa → scout-documentation-writer

**зависит от:** зонд [`../../discovery/roseltorg-probe.md`](../../discovery/roseltorg-probe.md)

## Проблема

Площадка `roseltorg` в реестре и с учёткой, но worker умеет только rostender / tender-pro.

## Решение

Адаптер CORP: httpx-логин ELK (`ROSELTORG_USER` / `ROSELTORG_PASSWORD`) → Bearer → `GET /api/v1/procedures?query=`. Open-only по `acceptanceApplicationsDateEnd`. Docs в v1 не качаем. DEV-стенд; VPS deploy — отдельно после merge.

Ветка `feat/040-roseltorg-adapter` от `main`.

## Acceptance

- [x] `platform_id=roseltorg` в очереди собирает список по `queries[]` (union + дедуп + `limit_n`)
- [x] open-only: срок приёма ≥ сегодня MSK (клиентский фильтр; `visibility=active` как UI)
- [x] карточка `/api/v1/procedures/{id}` для score≥порога; скоринг L1–L3 тот же
- [x] ingest `source_platform_id=roseltorg`; `tender_id=roseltorg:{id}`
- [x] без USER/PASSWORD поиск roseltorg не в очереди (sync + seeds `in_queue`)
- [x] unit-тесты маппинга/open-filter; DEV health ok; live probe + list (open лотов на CORP сейчас может быть 0)

## Файлы

- `app/worker/roseltorg.py`
- `app/api/runner.py`, `searches.py`, `search_queue_sync.py`
- `app/worker/search_seeds.py`, `platform_ids.py`
- `alembic/versions/0013_roseltorg_seeds.py`
- UI copy / platform label
- docs: зонд, platforms, auth-cookies, tasks README

## Out of scope

- B2B / OilB2B / Северсталь
- Скачивание файлов лота
- Playwright в worker
- VPS `--deploy`

## Links

- Зонд: [`../../discovery/roseltorg-probe.md`](../../discovery/roseltorg-probe.md)
- Index: [README](./README.md)
