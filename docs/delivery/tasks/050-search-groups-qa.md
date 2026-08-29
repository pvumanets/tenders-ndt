---
id: "050"
type: task
status: backlog
phase: NEXT+
title: "QA: группы × площадки + notes wipe/seeds"
was: ""
---

# 050 — QA: группы × площадки + notes wipe/seeds

**route:** scout-qa → scout-documentation-writer

**blocked:** после [048](./048-search-groups-backend.md) + [049](./049-search-groups-ui.md). **Не начинать** до acceptance 044–047 и кода.

## Проблема

Нужна приёмка модели групп и UI без регрессии inbox/ingest.

## Решение

pytest + vitest; смоук Старт с 1 группой × 2 площадки; пустая очередь (нет группы / нет площадки); минус v2 эталоны; краткие ops notes по seeds/wipe в карточке или `dev-stand` при необходимости.

## Acceptance

- [ ] Тесты 048/049 зелёные
- [ ] empty_queue оба случая
- [ ] Нет регрессии tender_id / L1–L3 ingest
- [ ] Docs/tasks статус done

## Файлы

- `tests/`, `app/web` tests, при необходимости `docs/delivery/dev-stand.md`

## Out of scope

- Самостоятельный wipe прода без команды владельца

## Links

- Index: [README](./README.md)
