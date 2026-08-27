---
id: "028"
type: task
status: backlog
phase: NEXT+
title: "Прогон: уже был / обновлено + отчёт счётчиков"
was: ""
---

# 028 — Прогон: уже был / обновлено + отчёт счётчиков

**route:** scout-product-manager → scout-architect → scout-backend → scout-frontend → scout-qa → scout-documentation-writer

**depends on:** [`../../discovery/inbox-lifecycle.md`](../../discovery/inbox-lifecycle.md) · [`../../discovery/owner-decisions.md`](../../discovery/owner-decisions.md)

**порядок:** после [027](./027-expired-column.md), перед [029](./029-tier-rules-and-ai.md).

## Проблема

Повторный Старт не объясняет, что лот с площадки уже в системе — и не показывает, **обновились** ли данные (срок, цена, документы).

## Решение (lock 2026-08-27)

При ingest для существующего `tender_id`:

- **Нет изменений** на площадке → **не** обновлять карточку; счётчик «**Уже были в системе**».
- **Есть изменения** (срок, НМЦ, title, docs meta) → **обновить** поля с площадки; счётчик «**Обновлено с площадки**».
- **`viewed` / `manual_tier` / `ai_reviewed`** — **не сбрасывать**.

В Tech после прогона — **полные фразы**:

- **Новые лоты**
- **Уже были в системе**
- **Обновлено с площадки**
- **Ушли в просроченные** — всех, кого система **впервые** отметила протухшими в окне прогона / суточного шага

Дымовой критерий: повторный Старт того же поиска → «Уже были» + «Обновлено» ≥ сумма пересечений; «Новые» ≈ 0.

## Acceptance

- [ ] Повторный прогон не создаёт вторую строку
- [ ] Diff с площадкой → обновление полей; без diff → skip update
- [ ] `viewed` / `manual_tier` / AI-статус не сбрасываются
- [ ] В Tech видны **четыре** счётчика (полные фразы)
- [ ] unit/smoke на already_exists / updated_from_platform

## Файлы (ожидаемые при коде)

- worker ingest / runner
- Tech UI статус прогона / copy
- тесты

## Out of scope

- UI колонки «Просроченные» ([027](./027-expired-column.md))
- ИИ отдельным шагом ([029](./029-tier-rules-and-ai.md))

## Links

- Discovery: [`../../discovery/inbox-lifecycle.md`](../../discovery/inbox-lifecycle.md)
- Index: [README](./README.md)
