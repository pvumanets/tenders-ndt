---
id: "001"
type: task
status: done
phase: P5.0
title: "Поиск full-width под command bar"
was: "A"
---

# 001 — Поиск full-width под command bar

**route:** scout-designer → scout-ux-writer → scout-frontend → scout-documentation-writer

## Проблема

Поиск был зажат справа в одной полосе с чипами, датами и toggle — toolbar перегружен.

## Решение

1-я полоса = `ViewCommandBar` без search (фильтры + вид).  
2-я полоса сразу под ним = полноширинный поиск на всю ширину контента Лотов.

## Acceptance

- [x] Поиск на отдельной полной ширине под command bar
- [x] Copy `search_placeholder` актуален

## Файлы

- `app/web/src/components/scout/InboxCommandBar.tsx`
- `app/web/src/copy.ts`

## Out of scope

- Меню «Фильтры» (см. [004](./004-filters-menu.md))

## Links

- Index: [README](./README.md)
