---
id: "023"
type: task
status: ready
phase: NEXT+
title: "Именованные поиски + очередь прогонов"
was: "Q16/Q25"
---

# 023 — Именованные поиски + очередь прогонов

**route:** scout-architect → scout-designer → scout-ux-writer → scout-backend → scout-frontend → scout-qa → scout-documentation-writer

## Проблема

Старт гоняет один хардкод РосТендера. Нужно в системе хранить несколько поисков (имя, площадка, строки, лимит), отмечать очередь и одним Стартом прогонять их подряд.

## Решение

Lock: [`../../discovery/named-searches.md`](../../discovery/named-searches.md). Postgres `searches`; CRUD `/api/searches*`; Старт читает `in_queue`; Стоп рвёт хвост; `GET /api/status` — текущий шаг и cookies по площадке. Вкладка Прогон, без третьей вкладки. Сиды: «РосТендер НК» в очереди; «Tender.Pro НК» не в очереди.

Код — ветка `feat/023-named-searches` от `main`. Этот docs-срез адаптер не пишет.

## Acceptance

- [ ] таблица `searches` + сиды
- [ ] CRUD за сессией Scout; имя уникально; `queries` непустой
- [ ] Старт пустой очереди → 400 `empty_queue`; второй Старт → 409
- [ ] очередь: шаг = один `runs` (`search_id`, `source_platform_id`); ошибка шага не рвёт хвост
- [ ] Стоп рвёт текущий шаг и остаток очереди
- [ ] Tech: список поисков + чекбокс очереди + CRUD + Старт/Стоп; query/limit не на кнопке

## Файлы

- `app/db/models.py`, Alembic
- `app/api/main.py`, `app/api/runner.py`
- `app/web/src/components/scout/TechRunPanel.tsx`
- [`../sales-inbox-api.md`](../sales-inbox-api.md), [`../operator-ui.md`](../operator-ui.md)

## Out of scope

- Адаптер Tender.Pro ([024](./024-tender-pro-adapter.md))
- Prefix `tender_id` / миграция inbox (024)
- Cron, роли, Bitrix, СИБУР / OnlineContract
- Правки на VPS / `scp`

## Links

- Product: [`../../discovery/named-searches.md`](../../discovery/named-searches.md)
- Index: [README](./README.md)
