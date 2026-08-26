---
id: "022"
type: task
status: done
phase: NEXT+
title: "Tech: Старт/Стоп прогона в React на VPS"
was: "Q25"
---

# 022 — Tech: Старт/Стоп прогона в React на VPS

**route:** scout-architect → scout-designer → scout-ux-writer → scout-frontend → scout-qa → scout-documentation-writer

## Проблема

Вкладка «Прогон» на https://tenders.ndtexam.ru read-only (Q25). Digital и директор не могут запустить rostender из UI. API `POST /api/run/start` и `POST /api/run/stop` уже есть.

## Решение

Limit/query в UI нет на кнопке — дефолты API до 023 (именованные поиски). На VPS `DOWNLOAD_DOCS=1`. Прогон стартует человек в браузере, не Cursor.

Dress rehearsal 2026-08-13: `limit=5` на VPS, сессия rostender ok, дедлайны 18–31.08.2026 (прошлого нет); inbox/runs/docs стёрты, api перезапущен. Директор жмёт Старт на 1000.

## Acceptance

- [x] на «Прогоне» кнопки Старт и Стоп; нет текста «отключены»
- [x] Старт disabled, если идёт прогон или нет cookies
- [x] Стоп disabled, если прогон не идёт
- [x] обе учётки могут стартовать (без ролей)
- [x] после прогона лоты score≥4 в inbox; файлы при `DOWNLOAD_DOCS=1` (Owner 2026-08-19: ок)

## Файлы

- `app/web/src/components/scout/TechRunPanel.tsx`, `copy.ts`, `lib/inbox.ts`, `App.tsx`
- [`../operator-ui.md`](../operator-ui.md), [`../../discovery/open-questions.md`](../../discovery/open-questions.md)
- Деплой на VPS: [`../vps.md`](../vps.md) — `python scripts/vps-bootstrap.py --deploy` (dirty tree → abort)

## Out of scope

- Cron, роли, Bitrix, Excel, другие ЭТП, запуск прогона агентом из Cursor

## Links

- API: [`../sales-inbox-api.md`](../sales-inbox-api.md)
- Index: [README](./README.md)
