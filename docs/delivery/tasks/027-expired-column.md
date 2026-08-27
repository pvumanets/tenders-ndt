---
id: "027"
type: task
status: done
phase: NEXT+
title: "Колонка «Просроченные» + авто-перенос + архив"
was: ""
---

# 027 — Колонка «Просроченные» + авто-перенос + архив

**route:** scout-architect → scout-designer → scout-ux-writer → scout-backend → scout-frontend → scout-qa → scout-documentation-writer

**depends on:** канон [`../../discovery/inbox-lifecycle.md`](../../discovery/inbox-lifecycle.md)

**порядок:** первая в цепочке **027 → 028 → 029** (отдельный PR). **P8 done.**

## Проблема

Лоты с прошедшим сроком подачи остаются в Горячих/Сильных/Смотреть: скрейп режет прошлое только при сборе, уже сохранённые в БД не двигаются.

## Решение

1. Четвёртая колонка доски **справа** — **«Просроченные»**.
2. Лот со сроком подачи &lt; сегодня (МСК) не показывается в L1–L3; виден в Просроченных; карточку можно открыть; бейдж **«Срок подачи вышел»**.
3. **Read-time** правило даты в `list_inbox` / UI (crontab в P8 не вводили).
4. Сортировка: **свежие протухшие сверху**.
5. Горизонтальный скролл — **только у блока доски**.
6. **«В архив»** (`board_hidden`): убрать со всех колонок; строка в БД остаётся; из drawer можно вернуть.

## Acceptance

- [x] Четыре колонки; «Просроченные» справа
- [x] Срок вчера и ранее → не в Горячих/Сильных/Смотреть; бейдж «Срок подачи вышел»
- [x] Просроченную карточку можно открыть
- [x] Read-time согласование Inbox с правилом даты МСК (вместо отдельного cron)
- [x] «В архив» / вернуть на доску
- [x] Горизонтальный скролл только внутри блока доски
- [x] Свежие протухшие сверху
- [x] pytest/vitest на границу «сегодня / вчера» МСК

## Файлы

- `alembic/versions/0005_board_hidden.py`
- `app/db/models.py`, `app/api/inbox.py`, `app/api/main.py`
- `app/web` — LotBoard, LotMiniCard, TenderDrawer, App, copy, types, lib/inbox
- тесты: `tests/test_inbox_*.py`, `app/web/src/lib/board-*.test.ts`

## Out of scope

- Идемпотентный отчёт прогона ([028](./028-run-idempotent-report.md))
- Пересчёт тиров / ИИ ([029](./029-tier-rules-and-ai.md))
- Обновление полей живой карточки с площадки
- Ops wipe прода

## Links

- Discovery: [`../../discovery/inbox-lifecycle.md`](../../discovery/inbox-lifecycle.md)
- Index: [README](./README.md)
