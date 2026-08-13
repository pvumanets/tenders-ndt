---
id: "017"
type: task
status: done
phase: P6
title: "Wire React: снять моки, inbox читает API"
was: ""
---

# 017 — Wire React: снять моки, inbox читает API

**route:** scout-architect → scout-ux-writer → scout-frontend → scout-qa → scout-documentation-writer

## Проблема

Принятый visual сидит на mocks. Директору нужны живые лоты после логина.

## Решение

[`../platform-phases.md`](../platform-phases.md) § P6. Тот же inbox; 401 → логин; пресеты дат на клиенте.

## Acceptance

- [x] список не из inbox.json как SoT
- [x] непросмотренные / приоритет / поиск / даты → API
- [x] 401 → экран входа
- [x] Tech read-only status
- [x] без новой доски и без Start/Stop

## Файлы

- `app/web/src/lib/inbox.ts`, `App.tsx`, `copy.ts`, `TenderDrawer.tsx`; mocks остаются фикстурами тестов

## Out of scope

- Перерисовка inbox; Bitrix; TLS; Start/Stop в React

## Links

- UI: [`../operator-ui.md`](../operator-ui.md)
- Index: [README](./README.md)
