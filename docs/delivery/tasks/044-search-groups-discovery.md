---
id: "044"
type: task
status: done
phase: NEXT+
title: "Discovery: группы поиска × площадки"
was: ""
---

# 044 — Discovery: группы поиска × площадки

**route:** scout-product-manager → scout-architect → scout-documentation-writer

## Проблема

Оператор видит 15 поисков (пакет × площадка) и включает каждый отдельно. Нужна модель как Директ: группа (плюс+минус) на все включённые площадки.

## Решение

Owner lock в [`../../discovery/search-groups.md`](../../discovery/search-groups.md). [`named-searches.md`](../../discovery/named-searches.md) → `superseded`. Правки [`search-system-v2.md`](../../discovery/search-system-v2.md), [`CANON.md`](../../CANON.md).

## Acceptance

- [x] Lock: end-state эпик; группа без выбора ЭТП; docs-first
- [x] Очередь = groups × platforms; минус v2 сохранён
- [x] Сиды TO-BE = 5 групп A–E
- [x] Pointer supersede + CANON

## Файлы

- `docs/discovery/search-groups.md`
- `docs/discovery/named-searches.md`
- `docs/discovery/search-system-v2.md`
- `docs/CANON.md`

## Out of scope

- Код, миграции, VPS

## Links

- Next: [045](./045-search-groups-api.md)
- Index: [README](./README.md)
