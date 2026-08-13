# Architect — delivery exit checklist

## From discovery packet → delivery doc

| Discovery | Delivery section |
| --- | --- |
| Problem / JTBD | scope-v0 / operator-ui goals |
| Acceptance draft | acceptance.md Must/Should |
| Open questions closed | strike from open-questions; ADR note if decision |
| Fit rules | fit-tiers + scoring sync note |
| UI zones | operator-ui.md |
| Runtime | tech-architecture + code-phases |

## C4-light minimum

1. Context: operator ↔ FastAPI ↔ rostender ↔ runs/
2. Containers: api, worker, (future) web React, (future) Bitrix connector
3. Key sequences: Start run; poll status; load results; soft stop

## Decision record (lightweight)

```markdown
### Decision: <title>
Context: …
Options: A / B
Choice: …
Consequences: …
```

Append to tech-architecture or a short `docs/delivery/decisions.md` if multiple.
