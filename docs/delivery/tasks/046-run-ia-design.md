---
id: "046"
type: task
status: done
phase: NEXT+
title: "Design: IA Прогон + компоненты W-run"
was: ""
---

# 046 — Design: IA Прогон + компоненты W-run

**route:** scout-designer → scout-documentation-writer

## Проблема

Вкладка «Прогон» — монолит без блоков; каталог обещал Tech* компоненты, код не разнёс.

## Решение

Четыре секции; каталог `PlatformStatusList`, `SearchGroupList`, `SearchGroupDrawer`, `TechDiagnostics`; deprecate `RunPathCopy` из основного UI; wireframe **W-run**.

## Acceptance

- [x] IA 4 блока в operator-ui / components
- [x] W-run ASCII + W6 marked historical
- [x] Component specs обновлены
- [x] Designer re-review 2026-08-29: порядок Группы→Площадки; sticky Управление; `RunQueueSummary`; split PlatformEnableList; RunReport@done; lock while running

## Файлы

- `docs/discovery/design/sales-inbox-components.md`
- `docs/discovery/design/sales-inbox-component-specs.md`
- `docs/discovery/design/sales-inbox-wireframes.md`
- `docs/delivery/operator-ui.md`

## Out of scope

- React реализация ([049](./049-search-groups-ui.md))

## Links

- Index: [README](./README.md)
