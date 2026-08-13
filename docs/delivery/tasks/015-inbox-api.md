---
id: "015"
type: task
status: done
phase: P5.4
title: "Inbox API из Postgres + поля mock"
was: ""
---

# 015 — Inbox API из Postgres + поля mock

**route:** scout-architect → scout-backend → scout-qa → scout-documentation-writer

## Проблема

Контракт `/api/inbox*` должен читать БД и отдавать то, что уже рисует mock.

## Решение

[`../sales-inbox-api.md`](../sales-inbox-api.md). GET/PUT viewed/priority; query unread/tier/q/дат; поля location, source_platform_id, url, контакты.

## Acceptance

- [x] GET /api/inbox только score≥4, с сессией
- [x] viewed и manual_tier переживают перезапуск
- [x] сброс tier null → оценка движка
- [x] 401/404/400 по контракту; секреты не в JSON

## Файлы

- `app/api/inbox.py`, `app/api/main.py`

## Out of scope

- Снятие моков React (017); docs download (016); новый UI

## Links

- Phases: [`../platform-phases.md`](../platform-phases.md)
- Index: [README](./README.md)
