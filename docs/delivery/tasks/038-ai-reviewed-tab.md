---
id: "038"
type: task
status: done
phase: NEXT+
title: "Вкладка «Разобрано с помощью ИИ» вместо галочки"
was: ""
---

# 038 — Вкладка «Разобрано с помощью ИИ»

**route:** scout-frontend → scout-ux-writer → scout-qa → scout-documentation-writer

## Проблема

Галочка «Разобрано с помощью ИИ» фильтровала список, но `effectiveTier` подменял колонки на доске «Лоты» тиром ИИ — при снятии галочки rules-колонки не возвращались.

## Решение

- Вкладка **«Разобрано с помощью ИИ»** (`AppTab ai`): только `ai_reviewed=1`, колонки по `ai_tier`, chip `L2 → L3`, кнопка «Разобрать с ИИ».
- Вкладка **«Лоты»**: колонки по **rules** (`rules_tier` / `tier`); muted chip «ИИ: L3» если был перенос.
- Drawer: режим `rules` vs `ai` — «было по правилам» / «ИИ предложил».

## Acceptance

- [x] «Лоты» не сдвигают колонки после ИИ
- [x] Отдельная вкладка без галочки
- [x] «Разобрать с ИИ» только на вкладке ИИ + empty CTA
- [x] vitest board-buckets + InboxCommandBar

## Out of scope

- Backend `tier_basis` query param
- Передача `description` в provod prompt
