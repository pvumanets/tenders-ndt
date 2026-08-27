---
id: "030"
type: task
status: backlog
phase: NEXT+
title: "Покрытие поиска: сиды A–E + без лимита 1000"
was: ""
---

# 030 — Покрытие поиска: сиды A–E + без лимита 1000

**route:** scout-architect → scout-backend → scout-frontend → scout-qa → scout-documentation-writer

**фаза:** [`../next-phases.md`](../next-phases.md) **P11**  
**depends on:** [`../../discovery/search-keywords.md`](../../discovery/search-keywords.md) · [`../../discovery/owner-decisions.md`](../../discovery/owner-decisions.md)  
**порядок:** после [028](./028-run-idempotent-report.md) (можно параллельно с [029](./029-tier-rules-and-ai.md)); **обязательно до wipe/чистого прогона (P13)**

## Проблема

В коде один seed «неразрушающий», `limit_n ≤ 1000`, Tender.Pro не в очереди. После wipe+прогона снова узкая сеть — lock 2026-08-27 не выполняется.

## Решение

1. Снять продуктовый/кодовый потолок `limit_n` (API validation, worker scrape, UI если показывает лимит как must).
2. Сиды именованных поисков по [`search-keywords.md`](../../discovery/search-keywords.md): rostender **A→B→C→D→E** (усечения + контроли + страховка); Tender.Pro — методы / аббревиатуры / контроли / страховка.
3. Включить Tender.Pro в очередь при валидных cookies (иначе `skipped` явно).
4. [`platforms.md`](../../discovery/platforms.md): `tender-pro` — не backlog (024 done).

## Acceptance

- [ ] Нет обязательного потолка 1000 в продукте/коде прогона
- [ ] Сиды A–E на rostender; порядок очереди слож→прост→страховка
- [ ] Tender.Pro пакеты + `in_queue` при cookies OK
- [ ] `platforms.md` отражает 024 done
- [ ] unit/smoke: scrape_queries без ранней обрезки по старому cap (или cap снят)

## Файлы (ожидаемые при коде)

- alembic seed / миграция searches
- `app/api/searches.py`, worker list scrape / tender_pro
- `docs/discovery/platforms.md`
- тесты

## Out of scope

- ИИ ([029](./029-tier-rules-and-ai.md))
- Re-score / retry / pagination harden ([031](./031-scrape-hardening.md))
- Wipe на проде (P13 ops)

## Links

- [`../../discovery/search-keywords.md`](../../discovery/search-keywords.md)
- [`../next-phases.md`](../next-phases.md)
- Index: [README](./README.md)
