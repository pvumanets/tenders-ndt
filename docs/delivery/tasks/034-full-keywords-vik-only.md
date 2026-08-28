---
id: "034"
type: task
status: doing
phase: NEXT+
title: "Полные keywords Rostender + только ВИК + cookies admin956"
was: ""
---

# 034 — Полные keywords Rostender + только ВИК + cookies admin956

**route:** scout-product-manager → scout-architect → scout-backend → scout-qa → scout-documentation-writer → ops (VPS)

**фаза:** [`../next-phases.md`](../next-phases.md) **P16**  
**depends on:** P15 (033)  
**PR:** `feat/034-full-keywords-vik-only`

## Owner lock (2026-08-28)

- Wipe прода → убрать **все** усечения и аббревиатуры в query Rostender **кроме ВИК**
- Убрать: `диагностирование`, `техническое диагностирование`, `ультр.` и прочие усечения
- Пакет E: `контроль сварных соединений`, `сварных соединений`
- Cookies сессии **admin956** на VPS (`--sync`, не в git)
- Прогон **только Rostender A–E**; Tender.Pro не трогаем

## Решение

1. [`app/worker/search_seeds.py`](../../app/worker/search_seeds.py) — RT A–E только полные фразы; C = `["ВИК"]`
2. Alembic `0009_full_keywords_vik_only` — UPDATE `searches.queries` для `rt-a` … `rt-e`
3. Scoring без изменений

## Acceptance

- [x] Unit: нет усечений/аббрев (кроме ВИК) в RT seeds
- [ ] Deploy + миграция 0009 на prod
- [ ] Wipe #3 + cookies admin956 + RT-only прогон
- [ ] Sanity: `customer_name` на выборке L1

## Out of scope

- Tender.Pro seeds / прогон
- Scoring / ИИ

## Links

- [`../../discovery/search-keywords.md`](../../discovery/search-keywords.md)
- [`../../discovery/inbox-lifecycle.md`](../../discovery/inbox-lifecycle.md)
