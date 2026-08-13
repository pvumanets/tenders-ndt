---
id: "022"
type: task
status: doing
phase: NEXT+
title: "Tech: Старт/Стоп прогона в React на VPS"
was: "Q25"
---

# 022 — Tech: Старт/Стоп прогона в React на VPS

**route:** scout-architect → scout-designer → scout-ux-writer → scout-frontend → scout-qa → scout-documentation-writer

## Проблема

Вкладка «Прогон» на https://tenders.ndtexam.ru read-only (Q25). Digital и директор не могут запустить rostender из UI. API `POST /api/run/start` и `POST /api/run/stop` уже есть.

## Решение

Кнопки Старт/Стоп на том же экране Tech. Обе учётки, без ролей. Limit/query в UI нет — дефолты API (1000, «неразрушающий»). На VPS `DOWNLOAD_DOCS=1`. Прогон стартует человек в браузере, не Cursor.

## Acceptance

- [x] на «Прогоне» кнопки Старт и Стоп; нет текста «отключены»
- [x] Старт disabled, если идёт прогон или нет cookies
- [x] Стоп disabled, если прогон не идёт
- [x] обе учётки могут стартовать (без ролей)
- [ ] после прогона лоты score≥4 в inbox; файлы при `DOWNLOAD_DOCS=1` (Owner: нажать Старт на VPS)

## Файлы

- `app/web/src/components/scout/TechRunPanel.tsx`, `copy.ts`, `lib/inbox.ts`, `App.tsx`
- [`../operator-ui.md`](../operator-ui.md), [`../../discovery/open-questions.md`](../../discovery/open-questions.md)

## Out of scope

- Cron, роли, Bitrix, Excel, другие ЭТП, запуск прогона агентом из Cursor

## Links

- API: [`../sales-inbox-api.md`](../sales-inbox-api.md)
- Index: [README](./README.md)
