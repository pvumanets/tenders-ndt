---
id: "007"
type: task
status: done
phase: P5.0
title: "Даты в фильтрах: пресеты вместо 4 input"
was: ""
---

# 007 — Даты в фильтрах: пресеты вместо 4 input

**route:** scout-product-manager → scout-designer → scout-ux-writer → scout-documentation-writer  
**код:** в mock P5.0 (2026-08-13); UI дат — отдельные меню, не чипы в общем popover → [008](./008-filters-personal-list.md)

## Проблема

AS-IS: в toolbar **4** поля `type="date"` (срок from–to + «попало к нам» from–to). Это перебор для daily-работы директора. Перенос тех же 4 полей в popover ([004](./004-filters-menu.md) as-was) проблему не снимает.

## Ресёрч

| Источник | Вывод |
| --- | --- |
| `InboxCommandBar.tsx` | 4 native date input в центре bar |
| [`sales-inbox.md`](../../discovery/sales-inbox.md) | must: фильтры **срок подачи** и **`ingested_at`** |
| Flight worksheet | даты = must |
| 004 (ранняя формулировка) | from–to × 2 в меню = те же 4 поля |
| Personal / inbox UX | пресеты + FilterTrigger; free range — редкий путь |
| Job директора | «что горит по сроку» vs «что недавно попало» — две оси; произвольный диапазон редок |

## Варианты

| # | Вариант | Вердикт |
| --- | --- | --- |
| 1 | Оставить 2× from–to в меню | **отвергнуть** — тот же перебор |
| 2 | Только срок; ingested убрать из UI | **отвергнуть** — конфликт с product must |
| 3 | Одна ось (segment) + from–to без пресетов | слабее для daily |
| 4 | Пресеты на обеих осях; from–to только у «Свой» | **принято** |

## Решение (design accepted)

Оба измерения остаются. UI = **пресеты first**. В bar дат нет.

### Срок подачи (главная ось)

- `Любой` (default)
- `≤ 7 дней`
- `≤ 14 дней`
- `≤ 30 дней`
- `Свой период` → раскрывает **одну** пару from–to (≤2 input)

Семантика пресета N дней: `deadline_msk` ∈ [сегодня .. сегодня+N] (МСК).

### Попало к нам

- `Любое` (default)
- `Сегодня`
- `За 3 дня`
- `За 7 дней`
- `Свой период` → своя пара from–to

Семантика: `ingested_at` ≥ сегодня−(N−1) (включительно). «Сегодня» = N=1.

### Правила плотности

- В popover по умолчанию **0** date input — только пресеты.
- Оба «Свой» одновременно — допустимо, редкий путь; default оба = Любой / Любое.
- Badge «Фильтры»: +1 если срок ≠ Любой; +1 если попало ≠ Любое (плюс приоритет — по правилам 004).

## Acceptance

- [x] В bar нет date input
- [x] В меню «Фильтры» по умолчанию нет четырёх пустых дат — пресеты
- [x] «Свой период» раскрывает from–to только для выбранной оси
- [x] Оба измерения (срок + попало) доступны
- [x] Copy keys пресетов в [`sales-inbox-copy.md`](../../discovery/design/sales-inbox-copy.md)
- [x] Specs `InboxFilters` ссылаются на эту таску

## Файлы (когда делать код)

- `app/web/src/components/scout/InboxCommandBar.tsx` (+ filter state в `App.tsx`)
- `app/web/src/copy.ts`

## Out of scope

- Реализация до команды на 004+007
- P5.1 query params API
- Обязательный MUI DatePicker (можно при коде)
- Удаление `ingested_at` из продукта

## Links

- Depends: реализуется внутри UI [004](./004-filters-menu.md)
- Product: [`sales-inbox.md`](../../discovery/sales-inbox.md) — фильтры дат must
- Index: [README](./README.md)
