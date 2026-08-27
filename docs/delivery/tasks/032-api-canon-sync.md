---
id: "032"
type: task
status: done
phase: NEXT+
title: "P12: синхрон канона API с lock 2026-08-27"
was: ""
---

# 032 — P12: синхрон канона API с lock 2026-08-27

**route:** scout-product-manager → scout-architect → scout-documentation-writer

**depends on:** [`../../discovery/owner-decisions.md`](../../discovery/owner-decisions.md) · [`../next-phases.md`](../next-phases.md) P12

**порядок:** **до** кода [027](./027-expired-column.md)–[029](./029-tier-rules-and-ai.md), чтобы backend не брал устаревший score≥4.

## Проблема

Accepted API и ADR всё ещё описывают пул **score ≥ 4**, всегда UPDATE при ingest и limit 1000. Owner lock 2026-08-27 уже другой — код P9/P10 иначе гадает по старому канону (G2).

## Решение

Docs-only: переписать целевой контракт в accepted-доках. Runtime AS-IS score≥4 до кода 028/029; снятие лимита — 030. Код worker **не** в scope.

## Acceptance

- [x] `sales-inbox-api` описывает пул `tier ∈ {L1,L2,L3}`, update-on-diff, без must limit 1000
- [x] Q8/Q12 и ADR согласованы с owner-decisions
- [x] `platform-phases` целевой пул обновлён
- [x] P12 в `next-phases` = done
- [x] Код / worker **не** в scope

## Файлы

- `docs/delivery/sales-inbox-api.md`
- `docs/delivery/tech-architecture.md`
- `docs/delivery/platform-phases.md`
- `docs/discovery/open-questions.md`
- `docs/discovery/sales-inbox.md`
- `docs/discovery/owner-decisions.md`
- `docs/discovery/named-searches.md`
- `docs/discovery/output-schema.md`
- `docs/delivery/acceptance.md`
- `docs/delivery/scope-v0.md`
- `docs/discovery/decision-risks-review.md`
- `docs/delivery/next-phases.md`
- `docs/CANON.md`
- `docs/delivery/tasks/README.md`

## Out of scope

- Реализация worker/ingest/UI (027–031)
- Wipe / deploy / VPS

## Links

- Фаза: [`../next-phases.md`](../next-phases.md) § P12
- Index: [README](./README.md)
