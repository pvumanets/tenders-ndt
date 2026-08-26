---
id: "024"
type: task
status: ready
phase: NEXT+
title: "Адаптер Tender.Pro"
was: "Q16"
---

# 024 — Адаптер Tender.Pro

**route:** scout-architect → scout-backend → scout-qa → scout-documentation-writer

**зависит от:** [023](./023-named-searches.md)

## Проблема

Поиск `tender-pro` в очереди нечем исполнить: worker умеет только rostender.

## Решение

Отдельный адаптер по [`../../discovery/tender-pro-probe.md`](../../discovery/tender-pro-probe.md) и [`../../discovery/named-searches.md`](../../discovery/named-searches.md): httpx+BS4, `good_name` из `queries[]`, `tender_state=1`, `country=1`. Не Playwright, не JSON-RPC. Список без cookies; файлы score≥4 — только с живым `cookies.tender-pro.txt`.

`tender_id` = `{source_platform_id}:{native_id}` для всех площадок; миграция существующих rostender-рядов / `lot_state` / том docs — в этом таске.

Ветка `feat/024-tender-pro-adapter` от `main` (после merge 023). Прогон — человек в UI, не Cursor. Cookies на VPS — `--sync`.

## Acceptance

- [ ] поиск с `platform_id=tender-pro` собирает список по каждой строке `queries` (union + дедуп + `limit_n`)
- [ ] карточки `/api/tender/{id}/view_public`; скоринг L1–L3 тот же
- [ ] без cookies список идёт; docs без ЛК не качаем
- [ ] ingest `source_platform_id=tender-pro`; inbox score≥4
- [ ] существующие rostender `tender_id` переезжают на префикс без потери `lot_state`

## Файлы

- новый worker-модуль (не копировать `list_scrape.py` вслепую)
- `app/api/runner.py`, ingest
- Alembic миграция `tender_id`
- [`../auth-cookies.md`](../auth-cookies.md)

## Out of scope

- СИБУР, OnlineContract, остальные 9 ЭТП
- JSON-RPC `_key`
- Cron, фильтр inbox по площадке
- Правки дерева на VPS

## Links

- Зонд: [`../../discovery/tender-pro-probe.md`](../../discovery/tender-pro-probe.md)
- Поиски: [`../../discovery/named-searches.md`](../../discovery/named-searches.md)
- Index: [README](./README.md)
