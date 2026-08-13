# Runbook прогона v0.1

**status:** draft  
**last-review-date:** 2026-08-13  
**код:** репо `ndt-tender-scout` по [`code-phases.md`](./code-phases.md) · хвост [`platform-phases.md`](./platform-phases.md)  
**runtime:** VPS + Docker (прод); тот же compose на ПК (дев); не Cursor

Сценарий логики прогона. Deploy на VPS — деталь P7 / [018](./tasks/018-vps-tls.md). Inbox SoT = Postgres, не JSON.

## 0. Подготовка

1. [`scope-v0.md`](./scope-v0.md), [`acceptance.md`](./acceptance.md), [`fit-tiers.md`](./fit-tiers.md).
2. Cookies: [`auth-cookies.md`](./auth-cookies.md) в **ndt-tender-scout**.
3. `runs/YYYY-MM-DD/`, `DOWNLOAD_DOCS=0`.

## 1–3. Сессия → поиск → пул 1000

Как раньше: cookies → `неразрушающий` → новые → до 1000 строк списка (**P1**).

## 4. Score + tiers (**P2**)

По [`../discovery/relevance-rules.md`](../discovery/relevance-rules.md) и [`fit-tiers.md`](./fit-tiers.md):  
`tier` ∈ L1 | L2 | L3 | noise | pool.

## 5. Карточки (**P3**)

Открывать **только L1–L3**. Не весь пул 1000.

## 6. Артефакты (**P4**)

- `tenders.xlsx`/`csv` + `tenders.md`
- **`priority-fit.md`** (секции L1–L3)
- README прогона

## 7. Operator UI (**P5**, если поднят)

Смотреть ход на HTML ([operator-ui](./operator-ui.md)).

## 8. Завершение

Acceptance; отчёт: pool / L1 / L2 / L3 / noise. Секреты не коммитить.
