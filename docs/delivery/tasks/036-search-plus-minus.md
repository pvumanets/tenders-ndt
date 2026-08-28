---
id: "036"
type: task
status: doing
phase: NEXT+
title: "Поиск v2: плюс/минус по пакетам"
was: ""
---

# 036 — Поиск v2: плюс/минус по пакетам

**route:** scout-architect → scout-backend → scout-frontend → scout-ux-writer → scout-qa → scout-documentation-writer → ops

**фаза:** [`../next-phases.md`](../next-phases.md) **P17**  
**канон:** [`../../discovery/search-system-v2.md`](../../discovery/search-system-v2.md)

## Owner lock (2026-08-28)

Плюс-фразы A–E оставляем. У каждого поиска свой `exclude[]`. Минус режет **на списке**. Tech UI правит плюс и минус. Соц/кровля-минусы — в основном на пакете D; A/B без них (детсад + радиограф = тема). «Строительный контроль» без НК — **не** минус. Hard L3 из [035](./035-no-build-control-hot.md) — **откатить**.

## Acceptance (docs)

- [x] [`search-system-v2.md`](../../discovery/search-system-v2.md) со схемой и таблицами A–E
- [x] Связки: search-keywords, named-searches, fit-tiers, README, next-phases
- [x] Owner OK на таблицы plus/minus (2026-08-28)

## Acceptance (code)

- [x] Поле `exclude` + миграция `0011` + сиды D с минусами; plus D снова с «строительный контроль»
- [x] Фильтр title на list scrape до score/ingest
- [x] Tech drawer: блок Минус
- [x] Откат `is_construction_watch` / hard L3
- [x] Unit: ЗАГС/кровля drop в D; детсад+радиограф keep при пустом exclude

## Acceptance (ops)

- [ ] Deploy + TP `in_queue=false`
- [ ] Wipe #4 + RT-only Start; sanity без ИИ

## Out of scope

ИИ, глубокая перепись TP plus, глобальный один минус на все пакеты.
