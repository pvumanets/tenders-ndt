---
id: "052"
type: task
status: done
phase: NEXT+
title: "Fix: не ingest/ИИ просроченный срок после enrich"
was: ""
---

# 052 — Fix: не ingest/ИИ просроченный срок после enrich

**route:** scout-backend → scout-qa → scout-documentation-writer

## Проблема

После wipe прогон всё равно наполнял «Просроченные». Росэлторг: в списке нет срока → open-фильтр по статусу → на карточке срок уже прошедший → ingest.

## Решение

`drop_past_deadline_rows` перед каждым ingest; ИИ пропускает `deadline_expired`.

## Acceptance

- [x] Past deadline не уходит в Postgres из runner
- [x] AI review не вызывает модель по просроченным
- [x] unit tests

## Файлы

- `app/deadline.py`, `app/api/runner.py`, `app/api/inbox.py`
- `tests/test_deadline_unit.py`
- `docs/discovery/inbox-lifecycle.md`

## Links

- Index: [README](./README.md)
