---
id: "041"
type: task
status: done
phase: NEXT+
title: "Общие слова поиска A–E на все площадки"
was: ""
---

# 041 — Общие слова поиска A–E на все площадки

**route:** scout-product-manager → scout-architect → scout-backend → scout-qa → scout-documentation-writer

**канон:** Ростендер A–E ([`../../discovery/search-keywords.md`](../../discovery/search-keywords.md) · [`../../discovery/search-system-v2.md`](../../discovery/search-system-v2.md))

## Проблема

Tender.Pro и Росэлторг жили своим словарём (нет пакета A, усечённые методы, ПВК/УЗК/НК, «диагностирование»). Ростендер — полный A–E.

## Решение

Один SoT пакетов A–E в [`app/worker/search_seeds.py`](../../../app/worker/search_seeds.py); фабрика `seeds_for_platform` для каждой ЭТП. Отличаются только `platform_id`, имя, UUID, `sort_order`, `in_queue`.

Миграция [`0014_shared_search_packages.py`](../../../alembic/versions/0014_shared_search_packages.py) — upsert всех seed UUID.

## Acceptance

- [x] Один SoT A–E; TP/РЭ/RT не дублируют разные списки фраз
- [x] На TP и РЭ есть пакет A; C = только ВИК; E без диагностирование/усечений
- [x] exclude: supply на A/B/C/E; D = social+supply
- [x] Миграция идемпотентна по UUID
- [x] Docs + README
- [x] pytest seeds зелёный

## Файлы

- `app/worker/search_seeds.py`
- `alembic/versions/0014_shared_search_packages.py`
- `docs/discovery/search-keywords.md`, `named-searches.md`
- `tests/test_shared_search_packages_unit.py` (+ coverage / roseltorg / no_uk_rk)

## Out of scope

- Новые ЭТП (B2B…) — только готовность фабрики
- Wipe / полный прогон
- `COPY_ENV_KEYS` ROSELTORG — в том же PR как мелкий ops-fix (`vps-bootstrap.py`)

## Links

- Index: [README](./README.md)
- 036/037: плюс/минус · supply exclude
