---
id: "026"
type: task
status: done
phase: NEXT+
title: "Drawer настроек поиска (Править)"
was: ""
---

# 026 — Drawer настроек поиска (Править)

**route:** scout-frontend → scout-qa → scout-documentation-writer

**зависит от:** [023](./023-named-searches.md)

## Проблема

«Править» / «Новый поиск» открывают длинную inline-форму в Tech — неудобно; нужен тот же правый drawer, что у тендера.

## Решение

`SearchSettingsDrawer` на `DetailDrawerShell`: все поля (имя, площадка, queries, limit, in_queue). Список Tech остаётся компактным.

## Acceptance

- [x] Править / Добавить открывают drawer справа
- [x] Сохранить / Отмена / Escape закрывают; API searches без смены контракта
- [x] vitest: клик Править монтирует поля формы

## Файлы

- `app/web/src/components/scout/SearchSettingsDrawer.tsx`
- `app/web/src/components/scout/TechRunPanel.tsx`

## Out of scope

- Новые поля поиска, Bitrix

## Links

- Index: [README](./README.md)
