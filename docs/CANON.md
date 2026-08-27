# Product canon (local)

Code and product rules live **in this repo**. Do not duplicate scoring/scope rules only in business-proc.

## Key files

| Topic | Path |
| --- | --- |
| Code phases P0–P5.0 (обзор) | [delivery/code-phases.md](./delivery/code-phases.md) |
| Фазы P5.1–P7 (подробно) | [delivery/platform-phases.md](./delivery/platform-phases.md) (`accepted`; P5.1–P7 **done**) |
| Фазы NEXT+ (P8–P14) | [delivery/next-phases.md](./delivery/next-phases.md) (`draft`; P12 **done**; после lock 2026-08-27) |
| Dev stand (compose db+api) | [delivery/dev-stand.md](./delivery/dev-stand.md) · `scripts/dev-up.ps1` |
| Architecture / stack | [delivery/tech-architecture.md](./delivery/tech-architecture.md) |
| Sales Inbox API (Postgres + auth) | [delivery/sales-inbox-api.md](./delivery/sales-inbox-api.md) (`accepted`; **P12** sync lock 2026-08-27 — пул L1–L3, update-on-diff) |
| React UI (P5.0 accepted; в image с P5.1; **P6 done**) | `app/web/` (`theme/`, `vendor/personal/`, `components/scout/`) |
| Fit L1–L3 | [delivery/fit-tiers.md](./delivery/fit-tiers.md) (`draft` v0.2; услуги vs поставка; эталоны владельца) |
| ИИ подтверждение тира (provod.ai) | [delivery/ai-tier-review.md](./delivery/ai-tier-review.md) (`draft`; **отдельный шаг** после прогона; ключ только `.env`) |
| Inbox lifecycle (просрочка, архив, уже был, wipe) | [discovery/inbox-lifecycle.md](./discovery/inbox-lifecycle.md) (`accepted` P8+P9; 027/028 **done**; код 029) |
| Operator UI | [delivery/operator-ui.md](./delivery/operator-ui.md) |
| Acceptance | [delivery/acceptance.md](./delivery/acceptance.md) |
| Tasks / backlog | [delivery/tasks/](./delivery/tasks/) |
| Git / ветки (GitHub origin) | [delivery/git-workflow.md](./delivery/git-workflow.md) |
| VPS (SSH, HTTPS) | [delivery/vps.md](./delivery/vps.md) (`https://tenders.ndtexam.ru`) |
| Auth (Scout login + cookies площадок) | [delivery/auth-cookies.md](./delivery/auth-cookies.md) |
| Relevance rules | [discovery/relevance-rules.md](./discovery/relevance-rules.md) |
| Product brief | [discovery/product-brief.md](./discovery/product-brief.md) |
| Sales Inbox (product) | [discovery/sales-inbox.md](./discovery/sales-inbox.md) (`accepted`) |
| Sales Inbox design package | [discovery/design/](./discovery/design/) |
| Open questions | [discovery/open-questions.md](./discovery/open-questions.md) |
| Решения владельца (простой язык) | [discovery/owner-decisions.md](./discovery/owner-decisions.md) (`active`; lock 2026-08-27) |
| Ключевые слова поиска | [discovery/search-keywords.md](./discovery/search-keywords.md) (`active`) |
| Ревью решений: узкие места (пропуски + ИИ) | [discovery/decision-risks-review.md](./discovery/decision-risks-review.md) (`draft`; cross-skill review 2026-08-26) |
| Named searches + очередь (NEXT+) | [discovery/named-searches.md](./discovery/named-searches.md) (`accepted`; код 023/024 **done**) |
| Platforms registry | [discovery/platforms.md](./discovery/platforms.md) |
| СИБУР SRM зонд (NEXT+) | [discovery/sibur-srm-probe.md](./discovery/sibur-srm-probe.md) (`draft`; cookies = `cookies.sibur.txt`, не в md) |
| OnlineContract зонд (NEXT+) | [discovery/onlinecontract-probe.md](./discovery/onlinecontract-probe.md) (`draft`; cookies = `cookies.onlinecontract.txt`, не в md) |
| Tender.Pro зонд (NEXT+) | [discovery/tender-pro-probe.md](./discovery/tender-pro-probe.md) (`draft`; cookies = `cookies.tender-pro.txt`, не в md) |
| Platform API research | [platform-api-research.md](./platform-api-research.md) |
| Output schema (выгрузка + Postgres SoT) | [discovery/output-schema.md](./discovery/output-schema.md) |
| Agents / roster | [`../AGENTS.md`](../AGENTS.md) (`scout-qa` after code; not an owner backlog item) |
| Company profile | [company/profile.md](./company/profile.md) |
| Bitrix leads (future) | [company/bitrix-and-leads.md](./company/bitrix-and-leads.md) |

On rule drift: edit docs here first, then sync `app/scoring/`.

## Secrets

- Tracked: auth **rules** in `delivery/auth-cookies.md`, `.env.example` (имена переменных, в т.ч. будущий `PROVOD_API_KEY`)
- Never commit: `cookies*.txt` (в т.ч. `cookies.rostender.txt`, `cookies.sibur.txt`, `cookies.onlinecontract.txt`, `cookies.tender-pro.txt`), `.env`, `.env.vps`, passwords, cookie values, API keys (provod.ai и др.), `_probe_*`
- Heavy run artifacts / docs volume: gitignore
- Origin: [github.com/pvumanets/tenders-ndt](https://github.com/pvumanets/tenders-ndt) — ветки [delivery/git-workflow.md](./delivery/git-workflow.md)
- VPS: [tenders.ndtexam.ru](https://tenders.ndtexam.ru) · root password only `.env.vps`; host/key in [delivery/vps.md](./delivery/vps.md). Do not print. Owner: do not rotate unless asked.
