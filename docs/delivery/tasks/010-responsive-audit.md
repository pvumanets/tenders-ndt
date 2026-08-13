---
id: "010"
type: task
status: done
phase: P5.0
title: "Адаптив: косяки узких экранов"
was: ""
---

# 010 — Адаптив: косяки узких экранов

**route:** scout-designer → scout-frontend → scout-documentation-writer  
**код:** mock P5.0 (2026-08-13), owner scope **3** (phone + tablet + laptop)

## Контекст

Owner выбрал телефон в приёмке mock. Канон desktop `md+` (900+) без смены IA.

## Решение

| Ширина | Поведение |
| --- | --- |
| **&lt; sm** | AppBar: баннер второй строкой |
| **&lt; md** | Command bar Start **2×2**; Доска/Таблица отдельной строкой; доска — **столбик** трёх колонок; таблица `minWidth: 720` + H-scroll |
| **md+** | Один ряд bar, три fluid-колонки как раньше |
| Прогон | Путь + «Копировать» столбиком на xs |

Touch 44px / safe-area — не в этом фиксе.

## Acceptance

- [x] Owner выбрал scope 3 (phone в приёмке)
- [x] Title не выдавлен баннером на xs
- [x] Command bar 2×2 без сироты ниже md
- [x] Доска: стек столбцов &lt; md; три колонки md+
- [x] Specs обновлены

## Файлы

- `app/web/src/App.tsx`
- `app/web/src/components/scout/InboxCommandBar.tsx`
- `app/web/src/components/scout/LotBoard.tsx`
- `app/web/src/vendor/personal/dispatch/BoardColumn.tsx`
- `app/web/src/components/scout/LotTable.tsx`
- `app/web/src/components/scout/TechRunPanel.tsx`

## Out of scope

- Touch 44px; P5.1 API; новый визуал карточки

## Links

- Specs: [`sales-inbox-component-specs.md`](../../discovery/design/sales-inbox-component-specs.md)
- Index: [README](./README.md)
