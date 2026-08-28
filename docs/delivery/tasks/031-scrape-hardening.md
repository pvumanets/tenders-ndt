---
id: "031"
type: task
status: done
phase: NEXT+
title: "Укрепление скрейпа: меньше тихих пропусков"
was: ""
---

# 031 — Укрепление скрейпа: меньше тихих пропусков

**route:** scout-architect → scout-backend → scout-qa → scout-documentation-writer

**фаза:** [`../next-phases.md`](../next-phases.md) **P14** — **done** (2026-08-28)  
**depends on:** P13 wipe + полный прогон  
**PR:** `feat/031-scrape-hardening`

## Проблема

Даже с широкими keywords лоты пропадают молча: score только по title; пагинация обрывается на пустой filtered page; cookies = «файл есть»; нет retry 429/5xx; soft-stop выбрасывает scored pool.

Evidence: [`../../discovery/decision-risks-review.md`](../../discovery/decision-risks-review.md) S1, S3–S6.

## Решение (реализовано)

1. **Re-score** после P3 (`rescore_rows`: title + methods + snippet описания).
2. Пагинация: `raw_article_count == 0` → конец; filtered-empty streak до 3 страниц.
3. **Probe** cookies (`probe_rostender_cookies`, `probe_tender_pro_cookies`); overall `partial` при skip/error/cancelled шагов.
4. Bounded **HTTP retry** (`app/worker/http_retry.py`); счётчик `http_retries` в STATE/Tech.
5. Soft-stop после P2: ingest L1–L3 из scored.
6. Prod compose: mount `cookies.tender-pro.txt` + `TENDER_PRO_COOKIES_FILE`.

## Acceptance

- [x] Unit/smoke на pagination «filtered empty ≠ end»
- [x] Re-score path покрыт тестом (mock card text)
- [x] Cookie missing/expired → явный step status; overall не всегда «done»
- [x] Retry счётчик в логе/Tech (без секретов)
- [x] Soft-stop не обнуляет scored кандидатов доски

## Файлы

- `app/worker/http_retry.py`, `list_scrape.py`, `tender_pro.py`, `card_scrape.py`
- `app/scoring/pipeline.py` — `rescore_rows`
- `app/api/runner.py`, `app/api/state.py`
- `app/web` — phase `partial`, `http_retries` в Tech
- `docker-compose.yml`, `docker-compose.prod.yml`
- `tests/test_http_retry_unit.py`, `tests/test_scrape_hardening_unit.py`, `tests/test_queue_unit.py`

## Out of scope

- Новые ЭТП
- Сиды A–E ([030](./030-search-coverage.md))
- ИИ ([029](./029-tier-rules-and-ai.md))
- Колонка просроченных ([027](./027-expired-column.md))

## Links

- [`../../discovery/decision-risks-review.md`](../../discovery/decision-risks-review.md)
- [`../next-phases.md`](../next-phases.md)
- Index: [README](./README.md)
