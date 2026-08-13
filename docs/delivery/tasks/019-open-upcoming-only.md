---
id: "019"
type: task
status: done
phase: P1
title: "P1: только приём заявок, срок с сегодня"
was: ""
---

# 019 — P1: только приём заявок, срок с сегодня

**route:** scout-product-manager → scout-architect → scout-backend → scout-qa → scout-documentation-writer

## Проблема

Простой поиск rostender по умолчанию включает завершённые и отменённые. Пул 1000 засоряется прошлым; директор не ищет закрытое.

## Решение

Расширенный поиск: `states[]=10` (Приём заявок), `dte_from` = сегодня МСК, сортировка «Сначала новые». На разборе строки — отсев `.dtend` < сегодня и статусов Завершён/Отменён.

## Acceptance

- [x] POST поиска не берёт этап «Завершён» / «Отменён»
- [x] в `raw-list` нет строк с дедлайном раньше сегодняшнего дня МСК
- [x] сортировка «Сначала новые»

## Файлы

- `app/worker/list_scrape.py`

## Out of scope

- Inbox API (015), смена UI фильтров

## Links

- Index: [README](./README.md)
