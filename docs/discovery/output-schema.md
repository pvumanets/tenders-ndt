# Схема выходных артефактов прогона

**status:** accepted  
**last-review-date:** 2026-08-13  
**тиры:** [`../delivery/fit-tiers.md`](../delivery/fit-tiers.md)  
**inbox SoT:** Postgres — [`../delivery/sales-inbox-api.md`](../delivery/sales-inbox-api.md)  
**фазы:** [`../delivery/platform-phases.md`](../delivery/platform-phases.md)

Inbox **не** читает файлы прогона. Файлы = выгрузка P4 + том документов. Конец прогона (P5.3) пишет `runs` + `lots` (score ≥ 4) в Postgres.

---

## SoT vs выгрузка

| Данные | Где |
| --- | --- |
| Лоты inbox, viewed, manual_tier | Postgres (`lots`, `lot_state`, `runs`) |
| Файлы документов score≥4 | том `{SCOUT_DOCS_DIR}/{tender_id}/` (compose `/data/docs`) + таблица `documents` |
| Реестр / priority-fit для людей и приёмки P4 | том прогона (ниже) |

Путь тома на деве может выглядеть как `runs/YYYY-MM-DD/` на ПК. На VPS это **том сервера**, не продукт «папка на ноутбуке».

## Выгрузка P4 (том)

```text
runs/YYYY-MM-DD/          # или эквивалент на томе
  README.md
  raw-list.json           # после P1
  scored-list.json        # отладка / выгрузка; не SoT inbox
  tier-summary.json
  tenders.xlsx | .csv
  tenders.md
  priority-fit.md         # ОБЯЗАТЕЛЬНО: секции L1 L2 L3
```

Документы лотов **не** здесь: том `SCOUT_DOCS_DIR` (P5.5), не папка прогона.

`operator-state.json` **не** создаём как SoT (устарело 2026-08-13).

## Колонки реестра (выгрузка + поля `lots`)

| Колонка | Обязательность |
| --- | --- |
| `rank` | да |
| `score` | да |
| `tier` | да: L1 \| L2 \| L3 \| noise \| pool |
| `fit_reason` | для L1–L3 |
| `tender_id`, `title`, `url` | да |
| `status`, `price_rub`, `location`, `customer_name` | желательно |
| `customer_inn`, `deadline_msk`, `source_etp` / `source_platform_id` | с карточки (L1–L3); в inbox — `source_platform_id` |
| `methods` | желательно для L1–L3 |
| `contact_*` | если есть |
| `docs_path` | если скачано |
| `notes` | опционально |

## Markdown

- `tenders.md` — таблица пула 1000.
- `priority-fit.md` — секции L1 / L2 / L3; см. fit-tiers.

## Документы

Скачивание **must** для **score ≥ 4** в `{SCOUT_DOCS_DIR}/{tender_id}/` на томе.  
`DOWNLOAD_DOCS=1`/`true`/`yes` — качать новые; иначе (в т.ч. `0`) — kill switch.  
Карточки P3 — только L1–L3; docs — подмножество score≥4.

## Operator state

Таблица `lot_state` в Postgres. Схема полей — [`../delivery/sales-inbox-api.md`](../delivery/sales-inbox-api.md).
