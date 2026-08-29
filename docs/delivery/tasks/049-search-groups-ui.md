---
id: "049"
type: task
status: done
phase: NEXT+
title: "Frontend: Прогон по 4 секциям + группы"
was: ""
---

# 049 — Frontend: Прогон по 4 секциям + группы

**route:** scout-designer → scout-ux-writer → scout-frontend → scout-qa → scout-documentation-writer

## Проблема

`TechRunPanel` — монолит MVP (cookies-сырец, 15 поисков, путь прогона).

## Решение

Shell по W-run (**порядок:** Управление → Группы → Площадки → Диагностика): sticky controls + `RunQueueSummary`; `SearchGroupList`/`SearchGroupDrawer`; `PlatformEnableList`; `TechDiagnostics` (auto-expand on error). Copy из [`../../discovery/design/sales-inbox-copy.md`](../../discovery/design/sales-inbox-copy.md) → `copy.ts`. Lock config while running; RunReport только @done. Клиент на `/api/search-groups*` + `/api/platforms*` (без shim `/api/searches*`).

## Acceptance

- [x] 4 секции; диагностика collapsed
- [x] Нет platform select в drawer группы
- [x] Primary статусы без имён cookie-файлов
- [x] Путь прогона не в основном потоке
- [x] vitest зелёный

## Файлы

- `app/web/src/components/scout/TechRunPanel.tsx` (+ RunControls, RunQueueSummary, SearchGroupList/Drawer, PlatformEnableList, TechDiagnostics)
- `app/web/src/copy.ts`, `app/web/src/lib/inbox.ts`, `app/web/src/App.tsx`, `app/web/src/types.ts`

## Out of scope

- Новые ЭТП; Bitrix

## Links

- Design: W-run in wireframes
- Index: [README](./README.md)
