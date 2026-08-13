---
id: "009"
type: task
status: done
phase: P5.0
title: "Drawer: Switch «Просмотрено» + иконки файлов"
was: ""
---

# 009 — Drawer: Switch «Просмотрено» + иконки файлов

**route:** scout-designer → scout-ux-writer → scout-frontend → scout-documentation-writer  
**код:** mock P5.0 (2026-08-13)

## Проблема

Футер drawer: filled pill «Просмотрено» — не паттерн personal (там `FormControlLabel` + `Switch`). Список документов — только текст, без сигнала типа файла.

## Решение

1. Просмотренность = Switch + лейбл **«Просмотрено»** (состояние, не смена двух кнопок).
2. `FileTypeIcon` 16–18px слева от имени: цвет по расширению (pdf / doc / xls / image / zip / generic).

## Acceptance

- [x] В футере нет filled Chip/Button «Просмотрено»
- [x] Switch small, blurple, как personal
- [x] У файлов маленькая цветная иконка по расширению
- [x] Specs/copy синхронизированы

## Файлы

- `app/web/src/components/scout/TenderDrawer.tsx`
- `app/web/src/components/scout/FileTypeIcon.tsx`
- `docs/discovery/design/sales-inbox-component-specs.md`

## Out of scope

- P5.1 реальное скачивание; Bitrix в футере

## Links

- Personal: `PersonComplianceCard` Switch
- Index: [README](./README.md)
