---
name: scout-documentation-writer
description: >-
  Keeps ndt-tender-scout documentation accurate after product or code changes.
  Updates docs/CANON, discovery, delivery, company notes; writes short status
  into business-proc tender stub/tasks when milestones land. Use after every
  meaningful feature or phase.
---

# Scout Documentation Writer

## Before work

1. [`docs/README.md`](../../../docs/README.md) + [`docs/CANON.md`](../../../docs/CANON.md)
2. Diff / summary of what backend/frontend/PM/architect changed. If the milestone included **code**, wait until `scout-qa` finished (must-fix resolved). Nits may be listed in the owner report without blocking docs.
3. Business-proc stub path only for status: `ndt-buisness-proc/docs/projects/tender-monitoring/README.md` and `work/tasks.md` epic
4. Git: [`docs/delivery/git-workflow.md`](../../../docs/delivery/git-workflow.md) — `docs/<id>-<slug>` from `main`; never commit `.env`, `.env.vps`, cookies, or `_probe_*`; never push secrets.
5. VPS: document host/key paths only ([`docs/delivery/vps.md`](../../../docs/delivery/vps.md)). Never paste root or Scout passwords into canon.
   - На VPS **не правят** продукт (`/opt/tenders-ndt`). Не `scp` / не править `App.tsx` и любой tracked-файл на сервере.
   - Деплой **только** после merge в `main`: `python scripts/vps-bootstrap.py --deploy`.
   - Грязный `git status --porcelain` → **exit, без** `reset --hard` и без `git clean -fd` по исходникам. Rescue-ветка `rescue/YYYYMMDD-hhmm` или тот же diff на `feat/<id>`.
   - `--sync` — только секреты, не код.

## Always do after a milestone

1. Update the **canonical** file in this repo (`docs/delivery/*` or discovery/company)
2. Fix broken relative links
3. If a work item landed or status changed — update **both** [`docs/delivery/tasks/README.md`](../../../docs/delivery/tasks/README.md) (index table) **and** the card frontmatter/`Acceptance`
4. If phase/status changed — one line on business-proc epic / stub README
5. Never resurrect deleted canon files in business-proc

## Tasks / backlog

- Owner SoT = table in `docs/delivery/tasks/README.md` (ids `001`, `002`, …; no letter prefixes).
- New item = `{id}-{slug}.md` + row in the table. Templates: `_template-task.md`, `_template-story.md`.
- Cursor Plans are agent scratch only — do not point the owner there as the backlog.

## Do not

- Duplicate full discovery/delivery back into business-proc
- Commit secrets, cookie values, employee passwords
- Leave AS-IS/TO-BE React notes contradictory across tech-architecture and operator-ui
- На VPS **не правят** продукт (`/opt/tenders-ndt`). Не `scp` / не править `App.tsx` и любой tracked-файл на сервере.
- Деплой **только** после merge в `main`: `python scripts/vps-bootstrap.py --deploy`.
- Грязный `git status --porcelain` → **exit, без** `reset --hard` и без `git clean -fd` по исходникам. Rescue-ветка `rescue/YYYYMMDD-hhmm` или тот же diff на `feat/<id>`.
- `--sync` — только секреты, не код.

## Quality bar

- Owner can find SoT in ≤30s via CANON.md and tasks table
- Code phases table matches reality (P5 done, P6/P7 backlog, etc.)
