---
id: "025"
type: task
status: done
phase: NEXT+
title: "Чистый customer_name на карточке"
was: ""
---

# 025 — Чистый customer_name на карточке

**route:** scout-backend → scout-frontend → scout-qa → scout-documentation-writer

## Проблема

Под заголовком карточки inbox «полоски» — не skeleton, а мусор Rostender (PUA + «Закупки…») в `customer_name`. WIP на `fix/023-customer-name` не влит; 023 ушёл под named searches.

## Решение

`clean_customer_name` на list/card/ingest и serialize inbox; clamp 2 строки на карточке; с карточки площадки чистое имя побеждает list-junk.

## Acceptance

- [x] PUA / «Закупки…» не попадают в inbox JSON и на карточку
- [x] пустой заказчик не рисует блок на `LotMiniCard`
- [x] unit на `clean_customer_name` + list parse

## Файлы

- `app/worker/customer_name.py`
- `app/worker/list_scrape.py`, `card_scrape.py`, `ingest.py`
- `app/api/inbox.py`
- `app/web/src/components/scout/LotMiniCard.tsx`

## Out of scope

- Полная SQL-миграция всех строк (serialize чистит на лету)

## Links

- Index: [README](./README.md)
