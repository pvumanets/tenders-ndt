---
id: "039"
type: task
status: done
phase: NEXT+
title: "Мастер-промпт ИИ: co-design + wire provod"
was: ""
---

# 039 — Мастер-промпт ИИ: co-design + wire provod

**route:** scout-ai-prompt → scout-architect → scout-backend → scout-qa → scout-documentation-writer

## Проблема

- ИИ **дублировала rules**: в user уходили `rules_tier` и `fit_reason` — модель видела «ответ regex».
- Нужен accepted master prompt + wire без якоря rules.

## Решение

### Фаза A — co-design — **done**

1. Owner Q1–Q5 / session 1 — **done** 2026-08-28.
2. SoT [`ai-master-prompt.md`](../ai-master-prompt.md) — **accepted** (owner «принято»).
3. Etalons + anti-patterns в skill `scout-ai-prompt`.

### Фаза B — wire — **done** (ветка `feat/039-ai-master-prompt`)

1. [`app/ai/provod.py`](../../../app/ai/provod.py): `_SYSTEM` из SoT; user = title ± customer ± description; **без** rules/fit_reason/score/methods.
2. `run_ai_review`: факты закупки; `rules_tier` в DB только для UI-diff (038).
3. `tests/test_provod_unit.py` — mock + golden titles.
4. [`ai-tier-review.md`](../ai-tier-review.md) synced.
5. Prod wipe + новый AI-разбор (D4) — **ops после merge/deploy**, не в коде.

## Discovery — session 1 (закрыт)

| ID | Краткий ответ owner |
| --- | --- |
| **D1** | Приличная лаб. услуг НК; ВИК/ПВК/УЗК/акустика/металлография/РК+ЦР; ж/д мягко L2 |
| **D2** | title + description (~800) если есть; опционально customer |
| **D3** | «наши = наши»; эталоны Комсомольск + Пакш |
| **D4** | Wipe + новый разбор после deploy |
| **D5** | Нейтральный `reason_ru`; diff rules только в UI |

## Acceptance

### A — prompt

- [x] Owner answered Q1–Q5 (D1–D5 filled)
- [x] System prompt accepted by owner
- [x] User template without rules/fit_reason/score/methods
- [x] ≥10 etalons with expected tier + sample `reason_ru`
- [x] Anti-patterns documented
- [x] Cost note (title vs +description)
- [x] `ai-master-prompt.md` status → `accepted`

### B — code

- [x] `provod.py` uses accepted prompts only
- [x] `run_ai_review` input matches D2
- [x] pytest mock + golden titles pass
- [x] `ai-tier-review.md` synced
- [ ] Prod re-run per D4 (ops после merge — отдельно)

## Файлы

- [`docs/delivery/ai-master-prompt.md`](../ai-master-prompt.md) — SoT промпта (**accepted**)
- [`.cursor/skills/scout-ai-prompt/SKILL.md`](../../../.cursor/skills/scout-ai-prompt/SKILL.md)
- `app/ai/provod.py`, `app/api/inbox.py`, `tests/test_provod_unit.py`

## Out of scope

- Удаление rules-engine (`app/scoring/`)
- Auto-run ИИ на ingest
- Класс опасности / допуски в промпте
- `PROVOD_API_KEY` в git/docs

## Links

- UI две доски: [038](./038-ai-reviewed-tab.md)
- ИИ канон: [`ai-tier-review.md`](../ai-tier-review.md) · [`fit-tiers.md`](../fit-tiers.md)
- Index: [README](./README.md)
