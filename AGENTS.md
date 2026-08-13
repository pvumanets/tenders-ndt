# AGENTS — ndt-tender-scout

**Audience:** owner (digital development).  
**Entry skill:** always start with **`scout-orchestrator`**.

## Before any task

1. [`docs/company/profile.md`](./docs/company/profile.md)
2. [`docs/CANON.md`](./docs/CANON.md)
3. [`docs/delivery/code-phases.md`](./docs/delivery/code-phases.md) and [`docs/delivery/platform-phases.md`](./docs/delivery/platform-phases.md) when coding
4. Owner backlog (таблица): [`docs/delivery/tasks/README.md`](./docs/delivery/tasks/README.md)
5. **Dev stand:** [`docs/delivery/dev-stand.md`](./docs/delivery/dev-stand.md). If `http://127.0.0.1:8765/api/health` is not 200 with `"db":"ok"`, run `.\scripts\dev-up.ps1`. Do not skip Postgres smokes when Docker is up. Do not invent `.env` passwords.
6. **Git:** [`docs/delivery/git-workflow.md`](./docs/delivery/git-workflow.md). Origin [pvumanets/tenders-ndt](https://github.com/pvumanets/tenders-ndt). Before code: branch `feat/<id>-<slug>` (or `fix/` / `docs/`) from up-to-date `main`.

## Roster (project skills)

| Role | Skill | When |
| --- | --- | --- |
| Orchestrator | `scout-orchestrator` | **Every** non-trivial owner task |
| Product manager | `scout-product-manager` | Discovery, scope, JTBD, questions first |
| Architect | `scout-architect` | Discovery → delivery specs, API, phases |
| Backend | `scout-backend` | FastAPI, worker, scoring, cookies |
| Frontend | `scout-frontend` | **React** (target); static HTML hotfix only |
| QA | `scout-qa` | After **code** (backend/frontend/worker): review + pytest/vitest; before docs |
| Designer | `scout-designer` | IA / layout / visual for operator UI |
| UX writer | `scout-ux-writer` | RU microcopy, empty/error states |
| Documentation | `scout-documentation-writer` | Keep `docs/` + business-proc stub in sync |

## Hard rules

- Orchestrator **must** route ≥2 skills for non-trivial work (never solo-implement everything).
- Canon = this repo `docs/`. Business-proc = epic stub only.
- Work items = [`docs/delivery/tasks/`](./docs/delivery/tasks/) (числовые id + таблица). Cursor Plans ≠ owner SoT.
- Out of scope: NAS, LNA packs, budget.
- Bitrix leads = future; use PM + architect first ([`docs/company/bitrix-and-leads.md`](./docs/company/bitrix-and-leads.md)).
- Secrets never in git/docs (`.env`, `cookies*.txt`, `_probe_*`).
- Git: default `main`; work on `feat/<id>-<slug>` / `fix/<id>-<slug>` / `docs/<id>-<slug>`; merge via PR. Agent **does not** commit to `main` after origin bootstrap, **does not** force-push `main`, **does not** skip hooks, **does not** push unless the owner asked.
- Operator UI AS-IS = static HTML (не `/`); TO-BE = React за логином (P5.2 / P6).
