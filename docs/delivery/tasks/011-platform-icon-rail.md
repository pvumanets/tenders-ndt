---
id: "011"
type: task
status: done
phase: P5.0
title: "PlatformIcon — фиксированный правый рейл карточки"
was: ""
---

# 011 — PlatformIcon — фиксированный правый рейл карточки

**route:** scout-designer → scout-ux-writer → scout-frontend → scout-documentation-writer

## Проблема

Иконка площадки сидела в отдельной строке над заголовком (рядом с опц. «вручную»). На карточках разной высоты / с чипом и без она **скакала** — не было постоянного правого блока.

Owner (2026-08-13): иконки должны жить в правом столбце карточки, не в потоке заголовка.

## Решение (design)

`LotMiniCard` = две колонки:

| Колонка | Содержимое |
| --- | --- |
| **Слева** (`flex: 1`, `minWidth: 0`) | опц. «вручную» → title → заказчик → где работать → срок / НМЦ → «Открыть» |
| **Справа** (рейл **24px**, `flexShrink: 0`) | только `PlatformIcon` 18px, **top-aligned**, без подписи |

Рейл без фона и бордера (красная рамка на скрине — аннотация, не хром). Иконка не делит ряд с чипом и не занимает строку над title. Таблица / drawer — без изменений (там уже своя колонка / ряд «На площадке»).

**Copy:** новых строк нет. Tooltip / `aria-label` остаются «Площадка: {name}». На рейле текста нет.

## Acceptance

- [x] На доске иконка всегда в правом рейле, top-right, одна и та же X-позиция на карточках одной ширины
- [x] Длина title / наличие «вручную» не двигают иконку
- [x] Title clamp не заезжает под иконку (левая колонка `minWidth: 0`)
- [x] Таблица и drawer не трогали
- [ ] **Owner gate:** визуально ок ли рейл / плотность (вместе с [006](./006-platform-icons.md))

## Файлы

- `app/web/src/components/scout/LotMiniCard.tsx`
- `docs/discovery/design/sales-inbox-component-specs.md`
- `docs/discovery/design/sales-inbox-components.md`
- `docs/discovery/design/sales-inbox-wireframes.md`
- `docs/discovery/platforms.md`

## Out of scope

- Новые строки copy; смена размера ассетов 32×32; scrape других ЭТП

## Links

- Follow-up [006](./006-platform-icons.md)
- Specs: LotMiniCard / PlatformIcon
- Index: [README](./README.md)
