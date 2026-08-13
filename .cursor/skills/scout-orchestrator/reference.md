# Orchestrator reference

## Anti-patterns

- Implementing FastAPI + React + docs in one breath without naming skills
- Skipping product-manager on ambiguous scope
- Closing a **code** task without `scout-qa` (review + tests) before documentation-writer
- Skipping `pytest -m smoke` as “no DB” instead of running `.\scripts\dev-up.ps1` ([`docs/delivery/dev-stand.md`](../../../docs/delivery/dev-stand.md))
- Editing business-proc discovery/delivery (moved — stub only)
- Committing cookies or inventing Bitrix field maps without discovery
- Working on `main` / `master` for a task (use `feat/<id>-<slug>` from [`git-workflow.md`](../../../docs/delivery/git-workflow.md))
- Force-pushing `main` or pushing without the owner asking
- Filter menus as wrapping Chip rows, or Chip as «Непросмотренные» — personal is FilterTriggerButton + vertical list; owner rejected the chip picker (2026-08-13)

## Example

Owner: «Сделай нормальный экран результатов и чтобы можно было лид в битрикс»

```text
Route: scout-product-manager → scout-architect → scout-designer → scout-documentation-writer
Why: UI exists; Bitrix leads are future — split discovery vs delivery vs design
```

PM clarifies lead auto vs button; architect notes future API; designer specs results; docs update `bitrix-and-leads.md` + operator-ui. Frontend/backend only after owner accepts scope.
