# Scope v0 / ship — UI-прототип rostender + платформа

**status:** accepted  
**last-review-date:** 2026-08-27  
**Sales Inbox:** [`../discovery/sales-inbox.md`](../discovery/sales-inbox.md) · [`sales-inbox-api.md`](./sales-inbox-api.md)  
**фазы хвоста:** [`platform-phases.md`](./platform-phases.md) · [`next-phases.md`](./next-phases.md)

## In scope (MVP P0–P5) — сделано

| Элемент | Решение |
| --- | --- |
| Юрлицо | ООО СВАРКА |
| Площадка | rostender.info, **только UI** |
| Данные | **Реальные** лоты |
| Код | репо `ndt-tender-scout` |
| Auth площадки | Netscape cookies-файл |
| Запрос | `неразрушающий`, сортировка новые, **только приём заявок**, срок ≥ сегодня МСК |
| Пул | до **1000** открытых (не архив / не закрытые) *(факт MVP; с 2026-08-27 обрезка 1000 не канон — 030)* |
| География | вся РФ |
| Fit | **L1 / L2 / L3** ([fit-tiers](./fit-tiers.md)); карточки только у них |
| Выходы | реестр 1000 + `priority-fit.md` |
| Оператор AS-IS | HTML хода работы ([operator-ui](./operator-ui.md)) |
| УЗК | услуги УЗК/УК **забираем** |

## Ship (P5.0 accepted → P7) — кратко

| Элемент | Решение |
| --- | --- |
| UI visual | React mock **accepted** (`app/web/`) |
| Runtime prod | **VPS + Docker** |
| Runtime dev | тот же compose на ПК |
| Inbox | **`tier ∈ {L1,L2,L3}`** в **Postgres** (P12 канон; AS-IS код до 029: score ≥ 4) |
| State | `lot_state` (не JSON-файл) |
| Вход | две учётки, без ролей, session cookie |
| Документы | **must** на демо (лоты на доске L1–L3, том; AS-IS до 029: score ≥ 4) |
| Директор | любой ПК, **HTTPS** (P7 **done**) |
| Bitrix / cron / роли | **не** этот ship (NEXT+) |
| Поиски / Tender.Pro | lock [`../discovery/named-searches.md`](../discovery/named-searches.md); код 023/024 |

Worker и скоринг **в scope** — не выкидываем.

## Out of scope

- API РосТендер, Bitrix/amoCRM (этот ship)
- Другие ЭТП (кроме иконки/реестра в UI)
- Полный dump ~17k
- Подача заявок / ЭЦП
- Регулярный cron (NEXT+)
- Ручной ввод капчи владельцем
- Роли и мульти-тенант
- NAS / LNA / бюджет

## Риски

[../discovery/risks-compliance.md](../discovery/risks-compliance.md)
