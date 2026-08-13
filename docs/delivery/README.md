# Delivery — ndt-tender-scout

**status:** active canon in this repo  
**last-review-date:** 2026-08-13  
**площадка:** rostender.info (UI)  
**юрлицо:** ООО СВАРКА  

Документация + код в одном репо. Runtime: VPS + Docker (прод), тот же compose на ПК (дев). Не Cursor.

## Оглавление

| Файл | Зачем |
| --- | --- |
| [**code-phases.md**](./code-phases.md) | Обзор P0–P5.0 |
| [**platform-phases.md**](./platform-phases.md) | Подробно P5.1–P7 |
| [tech-architecture.md](./tech-architecture.md) | Стек, Postgres, два auth |
| [sales-inbox-api.md](./sales-inbox-api.md) | Inbox + session |
| [operator-ui.md](./operator-ui.md) | HTML AS-IS / React TO-BE |
| [fit-tiers.md](./fit-tiers.md) | L1 / L2 / L3 |
| [scope-v0.md](./scope-v0.md) | In / out |
| [acceptance.md](./acceptance.md) | Приёмка |
| [runbook-agent-v0.md](./runbook-agent-v0.md) | Сценарий прогона (обновить на P7) |
| [auth-cookies.md](./auth-cookies.md) | Scout login + cookies площадки |
| [ideal-priority-spec.md](./ideal-priority-spec.md) | **deprecated** → fit-tiers |

## Опора discovery

- [../discovery/relevance-rules.md](../discovery/relevance-rules.md)
- [../discovery/output-schema.md](../discovery/output-schema.md)
- [../discovery/rostender-ui-map.md](../discovery/rostender-ui-map.md)
- [../discovery/risks-compliance.md](../discovery/risks-compliance.md)

## Agents

Root [`AGENTS.md`](../../AGENTS.md) · entry skill **`scout-orchestrator`**
