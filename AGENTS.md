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
7. **VPS:** [`docs/delivery/vps.md`](./docs/delivery/vps.md). Host `77.91.94.111`, key `tenders-ndt-vps`. Password in `.env.vps` — never print or commit. Do not rotate unless the owner asks. Password SSH stays on. Deploy = `--deploy` after `main`; never reset a dirty VPS tree.

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
| AI prompt | `scout-ai-prompt` | Master provod system prompt, etalons, co-design with owner (before code 039) |
| Documentation | `scout-documentation-writer` | Keep `docs/` + business-proc stub in sync |

## Hard rules

- Orchestrator **must** route ≥2 skills for non-trivial work (never solo-implement everything).
- Canon = this repo `docs/`. Business-proc = epic stub only.
- Work items = [`docs/delivery/tasks/`](./docs/delivery/tasks/) (числовые id + таблица). Cursor Plans ≠ owner SoT.
- Out of scope: NAS, LNA packs, budget.
- Bitrix leads = future; use PM + architect first ([`docs/company/bitrix-and-leads.md`](./docs/company/bitrix-and-leads.md)).
- Secrets never in git/docs (`.env`, `.env.vps`, `cookies*.txt`, `_probe_*`). VPS root password is local `.env.vps` only.
- Git: default `main`; work on `feat/<id>-<slug>` / `fix/<id>-<slug>` / `docs/<id>-<slug>`; merge via PR. Agent **does not** commit to `main` after origin bootstrap, **does not** force-push `main`, **does not** skip hooks, **does not** push unless the owner asked.
- VPS: do not disable password SSH; do not publish Scout login on public HTTP; do not treat owner-given VPS creds as compromised unless asked to rotate. Do not edit product files on the VPS or `scp` feature branches onto `/opt/tenders-ndt`. Deploy with `python scripts/vps-bootstrap.py --deploy` after merge to `main`. If `git status --porcelain` is dirty (tracked or untracked sources), **do not** `reset --hard` — rescue branch first.
- Operator UI AS-IS = static HTML (не `/`); TO-BE = React за логином (P5.2 / P6).
