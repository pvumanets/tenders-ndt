---
id: "005"
type: task
status: done
phase: P5.0
title: "Чипы карточки: без приоритета и «новое»"
was: "E"
---

# 005 — Чипы карточки: без приоритета и «новое»

**route:** scout-designer → scout-ux-writer → scout-frontend → scout-documentation-writer  
**код:** в mock P5.0 (2026-08-13), вместе с [004](./004-filters-menu.md)

## Проблема

На карточке ряд «Сильные» + «вручную» + «новое» шумит.

- **«новое»** дублирует левый blurple-бар непросмотренного.
- **«Горячие / Сильные / Смотреть»** дублируют заголовок столбца на доске (и колонку «Приоритет» в таблице).

## Решение (design accepted)

| Элемент | На карточке (Доска) | В таблице |
| --- | --- | --- |
| Чип приоритета (Горячие/…) | **убрать** | оставить колонку/chip |
| Текст «новое» | **убрать** | точка/маркер непросмотрен |
| Чип «вручную» | **оставить** только если `manual_tier != null` | optional suffix у приоритета |

Иерархия: **слева** (опц. «вручную») → title → заказчик → где работать → срок / НМЦ → «Открыть»; **справа** PlatformIcon в рейле ([006](./006-platform-icons.md), [011](./011-platform-icon-rail.md)).  
Unread = left bar.

## Acceptance

- [x] На доске нет chip Горячие/Сильные/Смотреть и нет текста «новое»
- [x] «вручную» только при `manual_tier != null`
- [x] Таблица сохраняет колонку/chip приоритета
- [x] Specs/copy синхронизированы

## Файлы (когда делать)

- `app/web/src/components/scout/LotMiniCard.tsx`
- `app/web/src/components/scout/LotTable.tsx` (при необходимости)
- `docs/discovery/design/sales-inbox-component-specs.md`

## Out of scope

- Смена столбцов доски; P5.1

## Links

- Specs: LotMiniCard / PriorityChip в [`sales-inbox-component-specs.md`](../../discovery/design/sales-inbox-component-specs.md)
- Wireframe W1: [`sales-inbox-wireframes.md`](../../discovery/design/sales-inbox-wireframes.md)
- Copy: Priority chips (Task E) в [`sales-inbox-copy.md`](../../discovery/design/sales-inbox-copy.md)
- Index: [README](./README.md)
