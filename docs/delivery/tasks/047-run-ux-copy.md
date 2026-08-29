---
id: "047"
type: task
status: done
phase: NEXT+
title: "UX copy: площадки, группы, диагностика"
was: ""
---

# 047 — UX copy: площадки, группы, диагностика

**route:** scout-ux-writer → scout-documentation-writer

## Проблема

Разные cookie-строки с именами файлов; «Путь прогона» в основном потоке; «Поиски» вместо групп.

## Решение

Единый словарь статусов сессии; секции/группы/диагностика в [`../../discovery/design/sales-inbox-copy.md`](../../discovery/design/sales-inbox-copy.md). Legacy keys помечены.

## Acceptance

- [x] Секции Управление / Площадки / Группы / Диагностика
- [x] Primary без `cookies.*.txt`
- [x] `run_error_empty_queue` = группа + площадка
- [x] `run_path_*` только диагностика / legacy
- [x] UX re-review 2026-08-29: без «cookies» в ошибках; «Папка прогона»; TP «вход для списка не нужен»; empty bodies; без «fit»

## Файлы

- `docs/discovery/design/sales-inbox-copy.md`

## Out of scope

- Правка `app/web/src/copy.ts` (код 049)

## Links

- Index: [README](./README.md)
