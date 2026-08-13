---
id: "004"
type: task
status: done
phase: P5.0
title: "Меню «Фильтры» (popover) в toolbar"
was: "D"
---

# 004 — Меню «Фильтры» (popover) в toolbar

**route:** scout-designer → scout-ux-writer → scout-frontend → scout-documentation-writer  
**код:** в mock P5.0 (2026-08-13); визуал чип-пикера **отклонён** владельцем → [008](./008-filters-personal-list.md)

## Проблема

Полоса фильтров перегружена (чипы приоритета + две пары дат + вид). На доске приоритет уже выражен **столбцами**, поэтому дублирующие чипы «Горячие / Сильные / Смотреть» в тулбаре путают. Четыре date input — отдельная проблема → [007](./007-date-filters.md).

## Решение (design accepted)

1. **Всегда видимы в command bar:**
   - «Непросмотренные» (chip/toggle)
   - кнопка **«Фильтры»** (паттерн personal `FilterTriggerButton`) + badge «N активных»
   - toggle **Доска / Таблица**
2. **Внутри popover «Фильтры»:**
   - приоритет (Горячие / Сильные / Смотреть) — опциональный фильтр списка
   - **даты** — пресеты + опц. «Свой период» по [007](./007-date-filters.md) (не 4 голых input)
   - «Сбросить фильтры»
3. Поиск остаётся отдельной полной шириной под bar ([001](./001-search-fullwidth.md) — done).

## Acceptance

- [x] В bar нет чипов приоритета и нет date input
- [x] «Фильтры» открывает popover с приоритетом, датами (007), сбросом
- [x] Badge показывает число активных фильтров (приоритет + оси дат по 007; «Непросмотренные» / вид — по спеке copy)
- [x] Copy: `filter_menu`, сброс, пресеты дат — в [`sales-inbox-copy.md`](../../discovery/design/sales-inbox-copy.md)

## Файлы (когда делать)

- `app/web/src/components/scout/InboxCommandBar.tsx`
- `app/web/src/copy.ts`
- vendor personal `FilterTriggerButton` при необходимости

## Out of scope

- P5.1 API; Bitrix-фильтры
- Отдельный ship дат без меню — см. 007 (делается вместе с 004)

## Links

- Даты UX: [007](./007-date-filters.md)
- Specs: [`sales-inbox-component-specs.md`](../../discovery/design/sales-inbox-component-specs.md) — InboxFilters
- Wireframe: [`sales-inbox-wireframes.md`](../../discovery/design/sales-inbox-wireframes.md) — W1
- Copy: [`sales-inbox-copy.md`](../../discovery/design/sales-inbox-copy.md) — Filters & view
- Следом: [005](./005-card-chips.md)
- Index: [README](./README.md)
