---
name: scout-orchestrator
description: >-
  Primary entry for ndt-tender-scout. Routes every non-trivial owner task across
  scout-* skills (never solo-implements end-to-end). Use for any tender-scout
  product, discovery, delivery, API, UI, React, docs, or Bitrix-leads discussion.
---

# Scout Orchestrator

## Before work

1. Read [`AGENTS.md`](../../../AGENTS.md)
2. Read [`docs/company/profile.md`](../../../docs/company/profile.md)
3. Read [`docs/CANON.md`](../../../docs/CANON.md)
4. If coding: [`docs/delivery/code-phases.md`](../../../docs/delivery/code-phases.md)
5. **Stand:** [`docs/delivery/dev-stand.md`](../../../docs/delivery/dev-stand.md). Before API/DB/QA: if `/api/health` is not 200 `"db":"ok"`, run [`scripts/dev-up.ps1`](../../../scripts/dev-up.ps1). Do not treat missing Postgres as “skip smokes”. Empty `POSTGRES_PASSWORD` → stop and ask owner to fill `.env` (never invent or print it).
6. **Git:** [`docs/delivery/git-workflow.md`](../../../docs/delivery/git-workflow.md). Before code: checkout `feat/<id>-<slug>` (or `fix/` / `docs/`) from up-to-date `main`. Never commit to `main` after origin bootstrap.
7. **VPS:** [`docs/delivery/vps.md`](../../../docs/delivery/vps.md). Connect as `tenders-ndt-vps` (key). Read password from `.env.vps` if key is missing — never print it. Keep password auth on. Do not rotate creds unless the owner asks.
   - На VPS **не правят** продукт (`/opt/tenders-ndt`). Не `scp` / не править `App.tsx` и любой tracked-файл на сервере.
   - Деплой **только** после merge в `main`: `python scripts/vps-bootstrap.py --deploy`.
   - Грязный `git status --porcelain` → **exit, без** `reset --hard` и без `git clean -fd` по исходникам. Rescue-ветка `rescue/YYYYMMDD-hhmm` или тот же diff на `feat/<id>`.
   - `--sync` — только секреты, не код.

## Non-negotiable routing rule

**Never do a non-trivial task alone.** Decompose and explicitly assign **≥2** skills from the roster. Trivial = one-line typo / single file rename only.

At the start of the response (or plan), write:

```text
Route: <skill-a> → <skill-b> [→ <skill-c>]
Why: <one line>
```

Then follow that route (read those skills and act in role).

If the route includes `scout-backend` or `scout-frontend` (or worker/scoring), **`scout-qa` is required** after authors and before documentation-writer. PM / architect / docs-only / Bitrix discovery: no QA. Must-fix → author skill, re-QA, then docs. Nits do not block `done`.

## Routing matrix

| Owner intent | Pipeline |
| --- | --- |
| Fuzzy idea / «что делать» / clubok | `scout-product-manager` → `scout-documentation-writer` (+ `scout-designer` if UI) |
| Discovery → shipable plan | `scout-product-manager` → `scout-architect` → `scout-documentation-writer` |
| API / scrape / score / cookies | `scout-architect` (if contract changes) → `scout-backend` → `scout-qa` → `scout-documentation-writer` |
| Operator UI feature | `scout-designer` → `scout-ux-writer` → `scout-frontend` → `scout-qa` → `scout-documentation-writer` |
| React migration (P7) | `scout-architect` → `scout-designer` → `scout-frontend` → `scout-qa` → `scout-documentation-writer` |
| Copy / empty states / labels | `scout-ux-writer` → `scout-frontend` → `scout-qa` → `scout-documentation-writer` |
| Master prompt / independent AI tier (provod) | `scout-ai-prompt` → (after acceptance) `scout-architect` → `scout-backend` → `scout-qa` → `scout-documentation-writer` |
| Docs drift / status to business-proc | `scout-documentation-writer` (+ author role that changed code) |
| Bitrix leads from tenders | `scout-product-manager` → `scout-architect` → `scout-documentation-writer` (no coding until accepted) |

## Boundaries

- **In:** rostender scout, FastAPI, scoring L1–L3, operator UI, React target, future Bitrix leads design.
- **Out:** NAS, LNA, company budget, unrelated business-proc ops.
- Runtime of scrapes: local PC/Docker — not Cursor as the runner. Runtime of **Postgres + api** for tests: same compose; agent **starts** it via `scripts/dev-up.ps1`.

## Output to owner

- What was routed and done
- Files touched under `docs/` and `app/`
- What needs owner OK (`accepted` / phase jump)

## Reference

See [reference.md](./reference.md) for anti-patterns and examples.
