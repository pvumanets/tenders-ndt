---
id: "008"
type: task
status: done
phase: P5.0
title: "Фильтры как personal: список, даты отдельно, непросмотренные — кнопка"
was: ""
---

# 008 — Фильтры как personal: список, даты отдельно, непросмотренные — кнопка

**route:** scout-designer → scout-ux-writer → scout-frontend → scout-documentation-writer  
**код:** mock P5.0 (2026-08-13), после owner reject чипов в [004](./004-filters-menu.md)/[007](./007-date-filters.md)

## Проблема

Первая сборка 004+007: wrapping Chip-ряды в одном popover, «Свой период» сиротой на второй строке, скачущие отступы, «Непросмотренные» чипом. Это **не** паттерн ndt-personal (`FilterTriggerButton` + вертикальный список Switch).

## Решение (owner)

1. **Непросмотренные** — outlined Button с чекбоксом внутри (не Chip).
2. **Фильтры** — только приоритет: вертикальный список чекбоксов (как personal row + control справа).
3. **Срок подачи** и **Попало к нам** — отдельные `FilterTriggerButton` + radio-список вниз; from–to только при «Свой период», поля столбиком.
4. Popover chrome = personal: ширина ~280, `p: 1.5`, равные ряды, сброс ссылкой.

## Acceptance

- [x] В bar нет Chip как контроля фильтров
- [x] В меню нет wrapping Chip-опций
- [x] Даты не в одном popover с приоритетом
- [x] «Непросмотренные» = кнопка + чекбокс
- [x] Скиллы PM / designer / frontend запрещают чип-пикеры и скачущую плотность

## Файлы

- `app/web/src/components/scout/InboxCommandBar.tsx`
- `app/web/src/vendor/personal/shell/FilterTriggerButton.tsx`
- `.cursor/skills/scout-product-manager/SKILL.md`
- `.cursor/skills/scout-designer/SKILL.md`
- `.cursor/skills/scout-frontend/SKILL.md`

## Out of scope

- P5.1 API; Bitrix-фильтры

## Links

- Personal: `ndt-personal/apps/web/components/dispatch/DispatchFilterMenu.tsx`
- Index: [README](./README.md)
