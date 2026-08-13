---
id: "014"
type: task
status: done
phase: P5.3
title: "Ingest: worker upsert lots/runs в Postgres"
was: ""
---

# 014 — Ingest: worker upsert lots/runs в Postgres

**route:** scout-architect → scout-backend → scout-qa → scout-documentation-writer

## Проблема

Прогон пишет файлы, inbox должен читать БД. Нужен upsert, не выкидывание worker.

## Решение

[`../platform-phases.md`](../platform-phases.md) § P5.3. После P1–P4 — запись `runs` + `lots`. Выгрузка MD/CSV остаётся. `lot_state` не затирается.

## Acceptance

- [x] после прогона в `lots` есть score≥4 с полями карточки (location, url, source_platform_id, ingested_at)
- [x] повторный ingest того же tender_id обновляет карточку, не дублирует PK
- [x] MD/CSV на томе
- [x] viewed / manual_tier после повторного ingest на месте

## Файлы

- `app/worker/ingest.py`, `app/api/runner.py`, `app/worker/cli.py`

## Out of scope

- Inbox GET/PUT (015), docs download (016), новый UI

## Links

- Output: [`../../discovery/output-schema.md`](../../discovery/output-schema.md)
- Index: [README](./README.md)
