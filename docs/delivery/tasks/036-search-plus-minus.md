---
id: "036"
type: task
status: ready
phase: NEXT+
title: "Поиск v2: плюс/минус по пакетам (docs → code)"
was: ""
---

# 036 — Поиск v2: плюс/минус по пакетам

**route:** scout-product-manager → scout-architect → scout-documentation-writer → (позже) scout-backend → scout-frontend → scout-qa

**фаза:** [`../next-phases.md`](../next-phases.md) **P17** — сейчас **docs only**  
**канон:** [`../../discovery/search-system-v2.md`](../../discovery/search-system-v2.md)

## Owner lock (2026-08-28)

Плюс-фразы A–E оставляем. У каждого поиска свой `exclude[]`. Минус режет **на списке**. Tech UI правит плюс и минус. Соц/кровля-минусы — в основном на пакете D; A/B без них (детсад + радиограф = тема). «Строительный контроль» без НК — **не** минус. Hard L3 из [035](./035-no-build-control-hot.md) — **откатить при коде**.

## Сейчас (этот срез)

Только документация. Код / VPS / wipe — **не** в этом PR.

## Acceptance (docs)

- [x] [`search-system-v2.md`](../../discovery/search-system-v2.md) со схемой и таблицами A–E
- [x] Связки: search-keywords, named-searches, fit-tiers, README, next-phases
- [ ] Owner OK на таблицы plus/minus

## Acceptance (code — follow-up)

- [ ] Поле `exclude` + миграция + сиды D с минусами; plus D снова с «строительный контроль»
- [ ] Фильтр title на list scrape до score/ingest
- [ ] Tech drawer: блок Минус
- [ ] Откат `is_construction_watch` / hard L3
- [ ] Unit: ЗАГС/кровля drop в D; детсад+радиограф keep в B

## Out of scope (docs)

Код, wipe, ИИ, глобальный один минус на все пакеты.
