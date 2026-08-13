---
id: "003"
type: task
status: done
phase: P5.0
title: "«Где работать» на карточке и в таблице"
was: "C"
---

# 003 — «Где работать» на карточке и в таблице

**route:** scout-ux-writer → scout-designer → scout-frontend → scout-documentation-writer

## Проблема

На карточке не было города/региона работы — директору не видно, где объект.

## Решение

Поле `location` на `LotMiniCard` и колонка в таблице. Copy: **«Где работать»** (`card_location` / `col_location`).

## Acceptance

- [x] Location виден на карточке доски
- [x] Колонка в таблице
- [x] Пустое значение → «Нет данных» / empty copy

## Файлы

- `app/web/src/components/scout/LotMiniCard.tsx`
- `app/web/src/components/scout/LotTable.tsx`
- `app/web/src/copy.ts`
- `docs/discovery/design/sales-inbox-copy.md`

## Out of scope

- Геофильтр в toolbar

## Links

- Index: [README](./README.md)
