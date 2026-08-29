---
id: "043"
type: task
status: done
phase: NEXT+
title: "Росэлторг www-поиск вместо CORP"
was: ""
---

# 043 — Росэлторг www-поиск вместо CORP

**route:** scout-architect → scout-backend → scout-frontend (logo) → scout-qa → scout-documentation-writer

**зависит от:** [040](./040-roseltorg-adapter.md) (CORP retired)

## Проблема

Адаптер 040 ходил в `corp.roseltorg.ru` (ELK Bearer). Лоты ATOM/COM (напр. ATOM28082600172 — капиллярный контроль) живут в сводном поиске `www.roseltorg.ru` и в CORP API не видны.

## Решение

- Worker: HTML-поиск `www.roseltorg.ru/procedures/search` + карточка `/procedure/{id}/1`
- Auth: Netscape `cookies.roseltorg.txt` (очередь без файла — off)
- Docs: парсим `.lot-docs__list` / `file/get`, качаем при `DOWNLOAD_DOCS=1` (skip CORP-запрета)
- Twin: при ingest Росэлторга скрываем rostender-twin с тем же № процедуры (`board_hidden`)
- CORP / ELK Bearer удалены из runtime
- Логотип `platforms/roseltorg.png` обновлён

Ветка `feat/043-roseltorg-www`.

## Acceptance

- [x] Зонд www; CORP retired в probe
- [x] Очередь A–E при cookies
- [x] Список www; ingest `roseltorg:ATOM…`
- [x] Вложения скачиваются при наличии ссылок + `DOWNLOAD_DOCS=1`
- [x] Дубль rostender↔roseltorg: Росэлторг главный
- [x] Живой смоук капиллярный / ATOM (локально)
- [x] Нет CORP Bearer в runtime
- [x] Логотип 32×32; unit-тесты

## Файлы

- `app/worker/roseltorg.py`, `app/worker/etp_twins.py`
- `app/api/runner.py`, `search_queue_sync.py`, `app/worker/ingest.py`, `card_scrape.py`
- `app/deadline.py`, `.env.example`, `scripts/vps-bootstrap.py`
- `app/web/public/platforms/roseltorg.png`, `app/web/src/copy.ts`
- `tests/test_roseltorg_unit.py`, `tests/test_etp_twins_unit.py`
- docs: probe, platforms, auth-cookies, tasks

## Out of scope

- B2B / OilB2B / Северсталь
- Playwright
- Twin с Tender.Pro
- VPS deploy без команды

## Links

- Зонд: [`../../discovery/roseltorg-probe.md`](../../discovery/roseltorg-probe.md)
- Index: [README](./README.md)
