# Product manager — discovery playbook

## Question bank (pick 3–7)

1. Who uses this weekly — operator, sales, director?
2. What decision does the screen/run unlock?
3. Must-have vs nice-to-have for v0?
4. What is explicitly out (Bitrix now? docs download? 17k dump?)
5. How do we know it worked (acceptance)?
6. What existing artifact/API must not break?
7. Risk if wrong (false L1, expired cookies, duplicate leads)?

## Output skeleton

```markdown
## Problem
## Users
## Facts / Hypotheses / Gaps
## Options
## Recommendation
## Scope in / out
## Acceptance
## Next skill: scout-architect | scout-designer | …
```

## Anti-solutioning

If owner says «просто сделай React», still ask: parity with AS-IS zones? Vite? auth later? Keep static until P7 accepted.

If a filter/toolbar mock uses wrapping chips, Chip toggles, or dumps dates+priority into one jumping popover — **reject**. Cite personal `DispatchFilterMenu`. Density defects fail acceptance.
