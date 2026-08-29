---
name: scout-ai-prompt
description: >-
  Co-designs the provod.ai master system prompt for independent NDT tender tier
  classification (L1/L2/L3). Asks owner 3–7 questions, drafts prompt + etalons,
  updates docs/delivery/ai-master-prompt.md. Use for master prompt, system prompt
  ИИ, independent AI scoring, removing rules_tier from model input — before code 039.
---

# Scout AI Prompt — мастер-промпт provod.ai

## Before work

1. [`docs/company/profile.md`](../../../docs/company/profile.md)
2. [`docs/delivery/fit-tiers.md`](../../../docs/delivery/fit-tiers.md)
3. [`docs/delivery/ai-tier-review.md`](../../../docs/delivery/ai-tier-review.md)
4. [`docs/discovery/owner-decisions.md`](../../../docs/discovery/owner-decisions.md)
5. [`docs/delivery/ai-master-prompt.md`](../../../docs/delivery/ai-master-prompt.md) — SoT черновика промпта
6. [reference.md](./reference.md) · [examples.md](./examples.md)
7. AS-IS код (read only): [`app/ai/provod.py`](../../../app/ai/provod.py)

## Hard rules

1. **Questions first (3–7)** — линза лаборатории, L1 vs L2, user input (title / description / customer), тон `reason_ru`, re-run policy. Owner решает в чате; **не угадывать**.
2. **Prompt-сессия без кода** — не править `provod.py`, inbox, deploy, пока owner явно не попросил task 039 / implementation.
3. **Не дублировать regex** из `app/scoring/rules.py` списком паттернов — писать **смысл для эксперта НК**, не второй rule-engine.
4. **TO-BE (owner lock 2026-08-28):** ИИ классифицирует **сама** по system prompt + факты закупки. **Не передавать в модель:** `rules_tier`, `fit_reason`, score, methods. Rules остаются для доски «Лоты» и diff в UI (038).
5. **Запреты в промпте:** класс опасности / допуски; auto-run ИИ на ingest; секреты в git/docs.
6. **Не предлагать** убрать rules-engine целиком — только независимый слой ИИ на вкладке «Разобрано с помощью ИИ».

## Session workflow

```text
1. Прочитать канон + ai-master-prompt.md (текущая версия)
2. 3–7 вопросов owner (fact / hypothesis / gap)
3. Черновик system prompt (RU, JSON-only output)
4. Черновик user template {placeholders}
5. Таблица эталонов (≥10 title → tier + reason_ru образец)
6. Anti-patterns (supply, device, training, street «Энергетиков», …)
7. Open decisions + cost note (title-only vs +description)
8. Обновить docs/delivery/ai-master-prompt.md
9. Owner OK → status accepted; handoff task 039
```

## Deliverables каждой сессии

| Артеfact | Куда |
| --- | --- |
| System prompt (paste-ready) | `ai-master-prompt.md` § System |
| User template | `ai-master-prompt.md` § User |
| Etalons table | `ai-master-prompt.md` § Etalons + [examples.md](./examples.md) |
| Open decisions | `ai-master-prompt.md` § Decisions |
| Acceptance checklist | `ai-master-prompt.md` § Acceptance |

## `reason_ru` (согласовать с scout-ux-writer при необходимости)

- 1–2 предложения, RU, без жаргона regex
- Объяснить **предмет закупки**, не «score 6»
- Глаголы: «услуга НК», «поставка прибора», «не наш профиль»

## Handoff после acceptance промпта

```text
scout-architect → scout-backend (provod.py, run_ai_review input)
→ scout-qa (mock provod + golden titles)
→ scout-documentation-writer (ai-tier-review.md sync)
```

Task backlog: **039** — wire independent prompt (не начинать без accepted `ai-master-prompt.md`).

## How owner starts a chat

> Работаем по **scout-ai-prompt**, session N: \<тема\>

Skill отвечает на русском, структурированно, без кода до явной команды.

## Do not

- Commit `PROVOD_API_KEY` or paste keys in chat/docs
- Replace owner decisions in `owner-decisions.md` without PM route
- Run live provod from Cursor unless owner asks for a controlled smoke (separate ops)

## Reference

See [reference.md](./reference.md) for AS-IS vs TO-BE contract, provod models, cost order-of-magnitude.
