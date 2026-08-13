---
id: "002"
type: task
status: done
phase: P5.0
title: "Fluid колонки доски на всю ширину"
was: "B"
---

# 002 — Fluid колонки доски на всю ширину

**route:** scout-designer → scout-frontend → scout-documentation-writer

## Проблема

Справа на доске оставалась пустота: колонки фиксированной ширины не заполняли контент.

## Решение

Колонки и карточки **fluid** на ширину области Лотов; `minWidth` personal сохранён.

## Acceptance

- [x] Доска заполняет ширину контента без пустого правого края при типичном viewport
- [x] Карточки `width: 100%` внутри колонки

## Файлы

- `app/web/src/components/scout/LotBoard.tsx`
- `app/web/src/vendor/personal/dispatch/BoardColumn.tsx`
- `app/web/src/components/scout/LotMiniCard.tsx`

## Out of scope

- Изменение числа столбцов приоритета

## Links

- Index: [README](./README.md)
