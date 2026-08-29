---
id: "049"
type: task
status: backlog
phase: NEXT+
title: "Frontend: Прогон по 4 секциям + группы"
was: ""
---

# 049 — Frontend: Прогон по 4 секциям + группы

**route:** scout-designer → scout-ux-writer → scout-frontend → scout-qa → scout-documentation-writer

**blocked:** после [048](./048-search-groups-backend.md) **done**. Можно начинать UI.

## Проблема

`TechRunPanel` — монолит MVP (cookies-сырец, 15 поисков, путь прогона).

## Решение

Shell по W-run (**порядок:** Управление → Группы → Площадки → Диагностика): sticky controls + `RunQueueSummary`; `SearchGroupList`/`SearchGroupDrawer`; `PlatformEnableList`/`PlatformSessionHint`; `TechDiagnostics` (auto-expand on error). Copy из [`../../discovery/design/sales-inbox-copy.md`](../../discovery/design/sales-inbox-copy.md) → `copy.ts`. Lock config while running; RunReport только @done.

## Acceptance

- [ ] 4 секции; диагностика collapsed
- [ ] Нет platform select в drawer группы
- [ ] Primary статусы без имён cookie-файлов
- [ ] Путь прогона не в основном потоке
- [ ] vitest зелёный

## Файлы

- `app/web/src/components/scout/TechRunPanel.tsx` (+ новые компоненты)
- `app/web/src/copy.ts`, `app/web/src/lib/inbox.ts`

## Out of scope

- Новые ЭТП; Bitrix

## Links

- Design: W-run in wireframes
- Index: [README](./README.md)
