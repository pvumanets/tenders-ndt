---
id: "050"
type: task
status: done
phase: NEXT+
title: "QA: группы × площадки + notes wipe/seeds"
was: ""
---

# 050 — QA: группы × площадки + notes wipe/seeds

**route:** scout-qa → scout-documentation-writer

## Проблема

Нужна приёмка модели групп и UI без регрессии inbox/ingest.

## Решение

pytest + vitest; empty_queue оба случая (нет групп в очереди / нет площадок); минус v2 и tender_id покрыты существующими suites; ops notes ниже.

## Acceptance

- [x] Тесты 048/049 зелёные
- [x] empty_queue оба случая
- [x] Нет регрессии tender_id / L1–L3 ingest
- [x] Docs/tasks статус done

## Ops notes (seeds / wipe)

- Схема: Alembic `0015_search_groups` → таблицы `search_groups`, `platform_settings`; `runs.search_group_id`.
- Сиды: 5 групп A–E, **insert-only** при boot (`ensure_group_seeds`) — не перезаписывают queries/exclude оператора.
- Cookie sync TP/RE: только **enable** при наличии файлов; не гасит `enabled` оператора при старте.
- **Wipe / полный прогон прода** — только по явной команде владельца (не часть 050). Локально: `dev-up.ps1` + migrate; см. [`../dev-stand.md`](../dev-stand.md).

## Файлы

- `tests/test_search_groups_unit.py`, `app/web/.../TechRunPanel.test.tsx`
- эта карточка + [`README`](./README.md)

## Out of scope

- Самостоятельный wipe прода без команды владельца

## Links

- Index: [README](./README.md)
