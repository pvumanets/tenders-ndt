---
id: "016"
type: task
status: done
phase: P5.5
title: "Docs: download score≥4 на том + routes"
was: ""
---

# 016 — Docs: download score≥4 на том + routes

**route:** scout-architect → scout-backend → scout-qa → scout-documentation-writer

## Проблема

Демо директору must с файлами в drawer. Байты на томе, не в Postgres.

## Решение

[`../platform-phases.md`](../platform-phases.md) § P5.5. `DOWNLOAD_DOCS`; метаданные в `documents`; download за сессией. Байты в `{SCOUT_DOCS_DIR}/{tender_id}/`.

## Acceptance

- [x] при флаге вкл. файлы на томе для score≥4
- [x] список + download в API
- [x] флаг 0 — новые файлы не появляются
- [x] 401 без сессии

## Файлы

- `app/worker/docs.py`, `app/worker/card_scrape.py`, `app/api/inbox.py`, `app/api/main.py`, `app/api/runner.py`, `app/worker/cli.py`, `docker-compose.yml`

## Out of scope

- Качать пул 1000; публичные URL без сессии; wire React (017)

## Links

- Index: [README](./README.md)
