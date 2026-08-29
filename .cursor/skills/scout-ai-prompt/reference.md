# Reference — scout-ai-prompt

## Canon links

| Doc | Use |
| --- | --- |
| [`docs/delivery/fit-tiers.md`](../../../docs/delivery/fit-tiers.md) | L1/L2/L3 meaning, owner etalons, supply always L3 |
| [`docs/delivery/ai-tier-review.md`](../../../docs/delivery/ai-tier-review.md) | provod step, UI tab 038, fields `ai_*` |
| [`docs/delivery/ai-master-prompt.md`](../../../docs/delivery/ai-master-prompt.md) | **SoT** draft/accepted master prompt |
| [`docs/discovery/owner-decisions.md`](../../../docs/discovery/owner-decisions.md) | ИИ отдельный шаг; широкие query + ИИ чистит мусор |
| [`docs/company/profile.md`](../../../docs/company/profile.md) | ООО СВАРКА, Moscow+region, radiography/VIK/PVK strength |
| [`docs/company/ndt-methods.md`](../../../docs/company/ndt-methods.md) | Terminology — do not invent methods |

## Architecture (two engines)

```text
Run (rules) → board "Лоты"     columns = rules_tier / tier
Button "Разобрать с ИИ"      provod → ai_tier + reason_ru
Tab "Разобрано с помощью ИИ" columns = ai_tier; chip L2→L3
```

Rules and AI are **different lenses**. AI must not receive rules output as input (anchoring).

## Code (after 039) — [`app/ai/provod.py`](../../../app/ai/provod.py)

**Models:** `claude-sonnet-4-6` → fallback `openai-gpt-5-4` on same `api.provod.ai`.

**System (`_SYSTEM`):** paste-ready from accepted [`ai-master-prompt.md`](../../../docs/delivery/ai-master-prompt.md).

**User (`build_user_prompt`), from `run_ai_review`:**

- `title` (required)
- `customer` — if non-empty (`clean_customer_name`)
- `description` — if `lot.raw["description"]` is a non-empty string (truncated 800)

**Never send:** `rules_tier`, `fit_reason`, `score`, `methods`, `platform_id`

**Output:** `{"tier":"L1"|"L2"|"L3","reason_ru":"..."}`

**Trigger:** `POST /api/inbox/ai-review` — manual only; queue = board lots without `ai_reviewed_at`.

## Contract (owner lock 2026-08-28)

| Layer | Content |
| --- | --- |
| **System** | Role: NDT service lab director; L1/L2/L3 in plain RU; in-prompt examples; JSON-only; forbid hazard class / допуски |
| **User** | Purchase facts only: `title`; optional `customer_name`, `description` |
| **Never send** | `rules_tier`, `fit_reason`, `score`, `methods`, regex tags |
| **Output** | Same JSON schema |
| **Storage** | `rules_tier` in DB for UI diff only — not model input |

## L1 / L2 / L3 — prompt vocabulary (align with fit-tiers)

| Tier | Board name | Prompt should say |
| --- | --- | --- |
| L1 | Горячие | Clear **service/work** NDT: conduct control, welds, pipelines, wall thickness **as a job** |
| L2 | Сильные | NDT service visible but weaker signal or mixed wording |
| L3 | Смотреть | Supply/device/calibration/consumables/training; borderline non-NDT; not our job |

**Always L3 (anti-patterns):** поставка/закупка приборов, дефектоскоп, расходники, поверка/калибровка СИ without NDT service, обучение/аттестация as subject.

**Not in model scope:** `noise` / `pool` — inbox API only sends L1–L3 board lots to AI review.

## Provod ops (not secrets)

- Key: `PROVOD_API_KEY` in `.env` / VPS `--sync`
- Cost order: ~35 lots title-only ≈ 5–7 ₽ (Sonnet 4.6 via provod); +description ≈ +30–50% tokens
- Sequential one request per lot; typical ~2 min for 35 lots

## Owner forbids in prompt

- Filtering by **класс опасности** or допуски (manual director judgment)
- Auto AI on every ingest
- Keys in git, md, skills, chat canon

## Tests to align with after code 039

- [`tests/test_provod_unit.py`](../../../tests/test_provod_unit.py) — mock HTTP
- [`tests/test_score_037_unit.py`](../../../tests/test_score_037_unit.py) — title etalons (rules side; AI etalons may differ by design)

## Task handoff

**039** (future): implement TO-BE in `provod.py` + `inbox.run_ai_review`; golden set for AI independent of rules tier.
