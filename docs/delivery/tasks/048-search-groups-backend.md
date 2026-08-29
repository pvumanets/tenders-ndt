---
id: "048"
type: task
status: done
phase: NEXT+
title: "Backend: search_groups + platforms.enabled + queue"
was: ""
---

# 048 — Backend: search_groups + platforms.enabled + queue

**route:** scout-architect → scout-backend → scout-qa → scout-documentation-writer

## Проблема

Runtime = `searches` × `platform_id`. Нужна схема групп, enable площадок, разворот очереди.

## Решение

По [`../search-groups-api.md`](../search-groups-api.md): Alembic `0015_search_groups`, CRUD `/api/search-groups*` + `/api/platforms*`, expand group×platform в runner, сиды 5 групп, cookie sync → `platform_settings.enabled`. `/api/searches*` — shim до 049.

## Acceptance

- [x] Schema + идемпотентные сиды A–E (5 групп)
- [x] Queue = in_queue groups × enabled platforms
- [x] Один `runs` row на шаг; ingest `search_group_id`
- [x] pytest зелёный; docs sync

## Файлы

- `app/db/models.py`, `alembic/versions/0015_search_groups.py`
- `app/api/search_groups.py`, `platforms.py`, `searches.py` (shim), `search_queue_sync.py`, `runner.py`, `main.py`
- `app/worker/search_seeds.py`, `ingest.py`
- `tests/test_search_groups_unit.py`, `test_searches_smoke.py`, …

## Out of scope

- React UI ([049](./049-search-groups-ui.md))
- Wipe прода / VPS deploy без 049

## Links

- Canon: [`../../discovery/search-groups.md`](../../discovery/search-groups.md)
- Index: [README](./README.md)
