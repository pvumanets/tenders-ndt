---
id: "045"
type: task
status: done
phase: NEXT+
title: "Delivery: API контракт групп и площадок"
was: ""
---

# 045 — Delivery: API контракт групп и площадок

**route:** scout-architect → scout-documentation-writer

## Проблема

AS-IS `/api/searches*` несёт `platform_id` на каждой строке. Нужен контракт групп + enable площадок без реализации.

## Решение

[`../search-groups-api.md`](../search-groups-api.md); зоны в [`../operator-ui.md`](../operator-ui.md); ссылки в [`../sales-inbox-api.md`](../sales-inbox-api.md).

## Acceptance

- [x] REST sketch `/api/search-groups*`, `/api/platforms*`
- [x] Разворот очереди и `runs` FK
- [x] Deprecate path для `/api/searches*`
- [x] Operator-ui 4 секции

## Файлы

- `docs/delivery/search-groups-api.md`
- `docs/delivery/operator-ui.md`
- `docs/delivery/sales-inbox-api.md`

## Out of scope

- Код FastAPI / Alembic

## Links

- Discovery: [`../../discovery/search-groups.md`](../../discovery/search-groups.md)
- Index: [README](./README.md)
