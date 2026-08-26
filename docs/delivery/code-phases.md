# Фазы кода — ndt-tender-scout

**status:** accepted  
**last-review-date:** 2026-08-19  
**репо:** этот (`ndt-tender-scout`)  
**хвост P5.1–P7 (подробно):** [`platform-phases.md`](./platform-phases.md)  
**канон:** [`tech-architecture.md`](./tech-architecture.md) · [`sales-inbox-api.md`](./sales-inbox-api.md) · [`fit-tiers.md`](./fit-tiers.md) · [`acceptance.md`](./acceptance.md)

Этот файл — **обзор P0–P5.0** и таблица статусов. Реализация после visual mock — **не перескакивать**; детали только в platform-phases.

---

## Обзор

| Фаза | Название | Статус |
| --- | --- | --- |
| **P0** | Bootstrap репо | **done** |
| **P1** | List scrape | **done** |
| **P2** | Score + tiers | **done** |
| **P3** | Cards | **done** |
| **P4** | Artifacts | **done** |
| **P5** | Operator HTML | **done** |
| **P5.0** | Visual Sales Inbox (personal kit + mock) | **accepted** |
| **P5.1** | Platform (compose + Postgres) | **done** — см. [platform-phases](./platform-phases.md) |
| **P5.2** | Auth | **done** — см. [platform-phases](./platform-phases.md) |
| **P5.3** | Ingest → Postgres | **done** |
| **P5.4** | Inbox API из БД | **done** |
| **P5.5** | Docs на том | **done** |
| **P6** | Wire React | **done** |
| **P7** | VPS + TLS | **done** |

```text
P0 → … → P5 → P5.0 accepted
              → P5.1 → P5.2 → P5.3 → P5.4 → P5.5 → P6 → P7
                                                         ↓
                                                    NEXT+: cron, Bitrix, роли,
                                                    поиски 023, Tender.Pro 024
```

---

## P0 — Bootstrap репо

**Done:** репо существует.

---

## P1 — List scrape

**Done:** `raw-list.json` ≤1000; только **Приём заявок**, срок подачи ≥ сегодня МСК (таск [019](./tasks/019-open-upcoming-only.md)).

---

## P2 — Score + tiers

**Done:** score + L1–L3.

---

## P3 — Cards

**Done:** обогащение L1–L3.

---

## P4 — Artifacts

**Done:** tenders / priority-fit.

---

## P5 — Operator HTML ✅

**Выход:** техпанель AS-IS [`operator-ui.md`](./operator-ui.md).  
**Done:** static HTML + FastAPI.  
**Hotfix only** — не переписывать под Sales Inbox. После P5.2 не является корнем `/`.

---

## P5.0 — Visual Sales Inbox (React + mock) ✅

**Вход:** design package [`../discovery/design/`](../discovery/design/), [`../discovery/sales-inbox.md`](../discovery/sales-inbox.md).  
**Выход:** React SPA в `app/web/` на **моках**, UI из **скопированного** `ndt-personal` kit.

**Owner gate:** «дизайн ок» — **получено 2026-08-13** (целиком, включая иконки/рейл). Статус фазы **accepted**.

**Не делать в P5.0 (уже закрыто):** API inbox, Postgres, Docker platform.

Дальше — [`platform-phases.md`](./platform-phases.md) (`accepted`). **P5.1–P7 done.** NEXT+: [023](./tasks/023-named-searches.md) / [024](./tasks/024-tender-pro-adapter.md).

---

## P5.1–P7

Не дублировать здесь. Единственный подробный текст: [`platform-phases.md`](./platform-phases.md).

Кратко: Platform → Auth → Ingest → Inbox API → Docs → Wire (**done**) → VPS. Worker не выкидываем. SoT = Postgres. Две учётки без ролей.

---

## После P7 (NEXT+)

- Именованные поиски + очередь ([023](./tasks/023-named-searches.md)), адаптер Tender.Pro ([024](./tasks/024-tender-pro-adapter.md))
- Cron, роли, Bitrix, Excel-вкладка, остальные ЭТП
