---
id: "033"
type: task
status: done
phase: NEXT+
title: "Без УК/РК в keywords и scoring + wipe #2"
was: ""
---

# 033 — Без УК/РК в keywords и scoring + wipe #2

**route:** scout-product-manager → scout-architect → scout-backend → scout-qa → scout-documentation-writer → ops (VPS)

**фаза:** [`../next-phases.md`](../next-phases.md) **P15** — wipe #2 после deploy  
**depends on:** P14 (031 scrape hardening)  
**PR:** `feat/033-no-uk-rk-keywords`

## Проблема

После P13 wipe + полный прогон A–E на проде в **Горячих (L1)** попал СМР Воронеж (РОСВОДОКАНАЛ): regex `\bук\b` в `RE_UZK` ловит **«ООО УК»** (управляющая компания), не ультразвук. Аналогично `\bрк\b` даёт ложные срабатывания на госномера и аббревиатуры вне радиографии.

**Owner lock 2026-08-28:** убрать **УК** и **РК** из query и regex; ультразвук — только **УЗК / ультразвуков / УЗТ**; радиография — **полные слова** (радиограф, рентген, гаммаграф, ЦР). **ИИ не подключаем** — доска только по правилам; `PROVOD_API_KEY` на VPS пустой.

## Решение

1. **`app/scoring/rules.py`:** убрать `\bук\b` из `RE_UZK`; убрать `\bрк\b` из `RE_SERVICE_NDT` / `RE_RK`; добавить `рентген`.
2. **`app/worker/card_scrape.py`:** те же правки в `METHOD_PATTERNS` (P3 re-score).
3. **`app/worker/search_seeds.py`:** пакет C — `["НК","УЗК","ВИК","ПВК"]` (RT), `["ВИК","ПВК","УЗК","НК"]` (TP).
4. **Alembic `0008_no_uk_rk_keywords`:** UPDATE `searches.queries` для stable UUID `rt-c`, `tp-abbr`.
5. **Ops P15:** wipe + полный прогон A–E (как P13).

## Acceptance

- [x] СМР Воронеж (эталон owner) → **не L1** (`tests/test_no_uk_rk_unit.py`)
- [x] «УЗК сварных швов» → fit-tier сохранён
- [x] «радиографический контроль» → сигнал есть; «…РК» в госномере без radiograph → нет RK
- [x] В abbr seeds нет УК/РК; есть УЗК
- [x] Deploy на prod + alembic 0008
- [x] P15 wipe + прогон; sanity: нет СМР Воронеж в Горячих (0 L1 с РОСВОДОКАНАЛ)

## Файлы

- `app/scoring/rules.py`, `app/worker/card_scrape.py`, `app/worker/search_seeds.py`
- `alembic/versions/0008_no_uk_rk_keywords.py`
- `tests/test_no_uk_rk_unit.py`

## Out of scope

- ИИ / provod.ai (отдельная задача по запросу owner)
- Сужение пакетов D/E
- Bitrix, новые ЭТП

## Links

- [`../../discovery/search-keywords.md`](../../discovery/search-keywords.md)
- [`../../discovery/inbox-lifecycle.md`](../../discovery/inbox-lifecycle.md) — P15 wipe #2
- [`../fit-tiers.md`](../fit-tiers.md)
