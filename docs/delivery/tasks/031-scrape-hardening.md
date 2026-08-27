---
id: "031"
type: task
status: backlog
phase: NEXT+
title: "Укрепление скрейпа: меньше тихих пропусков"
was: ""
---

# 031 — Укрепление скрейпа: меньше тихих пропусков

**route:** scout-architect → scout-backend → scout-qa → scout-documentation-writer

**фаза:** [`../next-phases.md`](../next-phases.md) **P14**  
**depends on:** желателен чистый прогон после P13; можно начать после P11  
**порядок:** после [030](./030-search-coverage.md) / P13; **не** блокирует первый wipe-прогон

## Проблема

Даже с широкими keywords лоты пропадают молча: score только по title; пагинация обрывается на пустой filtered page; cookies = «файл есть»; нет retry 429/5xx; soft-stop выбрасывает scored pool.

Evidence: [`../../discovery/decision-risks-review.md`](../../discovery/decision-risks-review.md) S1, S3–S6.

## Решение

1. **Re-score** после обогащения карточки / goods (хотя бы borderline + Tender.Pro).
2. Пагинация: отличать «нет строк HTML» vs «все отфильтрованы»; не stop на первой пустой filtered page.
3. **Probe** сессии cookies (не только existence); overall run `partial` при skip/error шагов.
4. Bounded **HTTP retry** на 429/5xx.
5. Soft-stop после P2: всё же ingest кандидатов на доску (tier L1–L3 / актуальный порог).

## Acceptance

- [ ] Unit/smoke на pagination «filtered empty ≠ end»
- [ ] Re-score path покрыт тестом (mock card text)
- [ ] Cookie missing/expired → явный step status; overall не всегда «done»
- [ ] Retry счётчик в логе/Tech (без секретов)
- [ ] Soft-stop не обнуляет scored кандидатов доски

## Файлы (ожидаемые при коде)

- `app/worker/list_scrape.py`, `tender_pro.py`, `card_scrape.py`
- `app/api/runner.py`, scoring pipeline
- тесты

## Out of scope

- Новые ЭТП
- Сиды A–E ([030](./030-search-coverage.md))
- ИИ ([029](./029-tier-rules-and-ai.md))
- Колонка просроченных ([027](./027-expired-column.md))

## Links

- [`../../discovery/decision-risks-review.md`](../../discovery/decision-risks-review.md)
- [`../next-phases.md`](../next-phases.md)
- Index: [README](./README.md)
