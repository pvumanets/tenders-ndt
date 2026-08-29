---
id: "042"
type: task
status: done
phase: NEXT+
title: "provod.ai: timeout→fallback + commit per lot + model chain"
was: ""
---

# 042 — provod.ai resilience

**route:** scout-architect → scout-backend → scout-qa → scout-documentation-writer

## Проблема

- «Разобрать с ИИ» на проде → **500** (`httpcore.ReadTimeout`); `ai_reviewed=0`, `ai_error` пусто.
- Timeout httpx **не** был `AiTierError` → fallback не стартовал.
- `commit` в конце пакета откатывал весь прогресс.
- Primary `claude-sonnet-4-6` ~55 с (smoke 2026-08-29) — упирается в старый timeout 60 с.

## Решение

1. [`app/ai/provod.py`](../../../app/ai/provod.py): `MODEL_CHAIN` (default 3 alias на `api.provod.ai`); `TimeoutException`/`TransportError` → `AiTierError`; timeout 120 с; env `PROVOD_MODEL_CHAIN`.
2. [`run_ai_review`](../../../app/api/inbox.py): **commit после каждого лота**.
3. Unit-тесты цепочки / timeout / all-fail.
4. Sync [`ai-tier-review.md`](../ai-tier-review.md).

## Диагностика (2026-08-29)

| Проверка | Результат |
| --- | --- |
| `PROVOD_API_KEY` local / VPS api | True / True |
| `GET /v1/models` | 200, 46 models |
| `claude-sonnet-4-6` chat | 200, ~55 s |
| `openai-gpt-5-4` chat | 200, ~1.5 s |
| `gemini-2.5-flash` chat | 200, ~0.9 s |
| Prod board | 37 lots, ai_ok=0, ai_err=0; recent ai-review 500 |

Default chain: `claude-sonnet-4-6` → `openai-gpt-5-4` → `gemini-2.5-flash` (все на том же хосте; третья из каталога).

## Acceptance

- [x] Timeout/transport на primary → следующая модель без сырого 500
- [x] Частичный успех пакета сохраняется (`commit` per lot)
- [x] Все модели fail → `ai_error` + `ai_failures`, tier правил на месте
- [x] pytest unit pass
- [x] Docs synced; deploy + smoke 1–3 лота на проде (2026-08-29: processed=3 failed=0)

## Файлы

- `app/ai/provod.py`, `app/api/inbox.py`, `tests/test_provod_unit.py`
- `docs/delivery/ai-tier-review.md`, эта карточка, `tasks/README.md`
- `.env.example` — `PROVOD_MODEL_CHAIN`

## Out of scope

- Другой провайдер / base URL вне `api.provod.ai`
- Переписывание мастер-промпта (039)
- Фоновая очередь ИИ
- Wipe без отдельной команды owner

## Links

- Canon ИИ: [`ai-tier-review.md`](../ai-tier-review.md)
- Prompt SoT: [`ai-master-prompt.md`](../ai-master-prompt.md)
- Prior: [039](./039-ai-master-prompt.md)
