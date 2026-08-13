# Bitrix24 and future tender → lead pipeline

**status:** draft (UX contract closed; API not coded)  
**last-review-date:** 2026-08-12  
**portal:** single Bitrix24 box on **ООО СВАРКА**; НДТ-Консалтинг = обособленное подразделение (ADR-002 in business-proc).  
**UI product:** [`../discovery/sales-inbox.md`](../discovery/sales-inbox.md)

---

## Today (AS-IS)

- Tender scout produces `runs/` + operator UI results (L1/L2/L3).
- **No** Bitrix CRM write from this repo.
- Bitrix exists as company CRM/tasks; adoption historically low — keep lead UX simple when we build it.

## Product decisions (owner 2026-08-12)

| Topic | Decision |
| --- | --- |
| Trigger | Кнопка **«Отправить в Битрикс»** с карточки / drawer лота в Sales Inbox — **не** batch auto после прогона в NEXT |
| Visibility | В UI виден статус лида; **до API** — подпись **«Скоро»** (disabled / stub), не обещать создание лида |
| Stub label | Пользователь видит **«Скоро»** на кнопке или рядом (не «Ошибка») |
| Audience | Директор (первый пользователь NEXT) + продажи; digital не обязателен для create |
| Default responsible (когда API) | **N071** Зюганов К.М. (продажи); не N013 |
| Engine tiers | Автоотправка по L1-only и т.п. — **не** в NEXT; человек выбирает лот |
| API code | **Не реализовывать**, пока нет explicit owner switch + architect ADR |

## Target (TO-BE)

```text
Fit lot in Sales Inbox (Горячие / Сильные / Смотреть)
    → operator: «Отправить в Битрикс»
    → Bitrix CRM lead (ООО СВАРКА portal)
    → UI shows lead status (+ id when known)
    → assign owner (sales / lab) — mapping TBD architect
```

В NEXT UI до API: кнопка **disabled** + явная подпись **«Скоро»** (см. [`../discovery/design/sales-inbox-copy.md`](../discovery/design/sales-inbox-copy.md)).

## Still open (architect + PM)

1. Dedup key: `tender_id` / URL / INN+title? — owner: architect предложит после демо  
2. Bitrix field map from scored lot (title, price, deadline, customer, url, fit_reason, priority label).  
3. ~~Default responsible~~ → **closed: N071**  
4. Idempotent re-send / update existing lead.  
5. Stub shape in FastAPI vs wait for real webhook/REST.

## Agent rules

- Do **not** implement Bitrix API integration without explicit owner switch + discovery.  
- When discussing leads: `scout-product-manager` + `scout-architect`; document in `docs/discovery/` then `docs/delivery/`.  
- NAS / LNA / budget remain out of this repo.

## Related people

See [employees.md](./employees.md) — especially director (N013), sales (N071), digital owner (N070).
