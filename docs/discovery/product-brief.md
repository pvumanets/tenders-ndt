# Product brief — мониторинг тендеров

**status:** accepted  
**last-review-date:** 2026-08-13  
**юрлицо:** ООО СВАРКА  
**площадка (AS-IS):** rostender.info  
**код:** `ndt-tender-scout` · обзор [`../delivery/code-phases.md`](../delivery/code-phases.md) · хвост [`../delivery/platform-phases.md`](../delivery/platform-phases.md)  
**UI NEXT:** [`sales-inbox.md`](./sales-inbox.md) (**accepted**; visual P5.0 **accepted**)  
**Design package:** [`design/`](./design/)  
**Architect:** [`../delivery/tech-architecture.md`](../delivery/tech-architecture.md) · [`../delivery/sales-inbox-api.md`](../delivery/sales-inbox-api.md)  
**Runtime:** VPS + Docker (прод); ПК = тот же compose (дев). Cron / роли / Bitrix = NEXT+.

---

## Проблема

Продажи и директор не видят быстро **новые сильные** лоты НК без техграмоты: MVP-экран — техническая панель прогона; Excel/MD как daily path — архаизм. Итог — пропуск релевантных тендеров и ручной хаос.

## Пользователи

| Роль | Экран | Задача |
| --- | --- | --- |
| **Директор** (первый пользователь NEXT), продажи | **Sales Inbox** (вкладка «Лоты», default) | Непросмотренные + приоритет; фирма; drawer с деталями и **файлами документов**; ручная смена приоритета |
| Digital (владелец продукта) | **Tech** (вкладка «Прогон») | Статус прогона, cookies площадки, Старт/Стоп |

Внутренний скоринг остаётся L1/L2/L3 в engine ([`../delivery/fit-tiers.md`](../delivery/fit-tiers.md)). В sales-UI — **человеческие** ярлыки: Горячие / Сильные / Смотреть (не «L1»).

**Пул inbox:** лоты с **score ≥ 4** в Postgres (= L1∪L2 по текущему движку). Авто-L3 в список по умолчанию не входят; ярлык «Смотреть» — для **ручной** смены приоритета.

## Решение

### AS-IS (MVP принят)

1. Репо + runtime ПК/Docker.  
2. Cookies → UI rostender → пул 1000.  
3. Score → L1/L2/L3; карточки только у них.  
4. Excel/MD + static operator HTML (техпанель).  
5. Docs: флаг; worker download — P5.5.

### NEXT / ship (lock 2026-08-13)

1. **Sales Inbox** — принятый visual; **документы с файлами**; просмотренность; ручная смена приоритета.  
2. **Tech-вкладка** — статус + Старт/Стоп (022).  
3. UI = **vendored kit `ndt-personal`**.  
4. Порядок: [`../delivery/platform-phases.md`](../delivery/platform-phases.md) — P5.1 Platform → … → P7 VPS.  
5. Storage: **Postgres**; вход: две учётки без ролей.  
6. Excel/CSV — не daily; вкладка = NEXT+. Bitrix не в приёмке.

Спека: [`sales-inbox.md`](./sales-inbox.md). Дизайн: [`design/`](./design/). UI: `app/web/`. API: [`../delivery/sales-inbox-api.md`](../delivery/sales-inbox-api.md).

### Сейчас (активный этап)

Канон платформы **accepted**. **P5.1–P6 done** (compose + Postgres + Scout login + ingest + inbox API + docs на томе + React на живом API). Следующая фаза — P7 VPS (нужен домен). P5.0 visual **accepted**.

## Готово (док / код MVP)

- Пакет [`../delivery/`](../delivery/) + design package + visual `app/web`.  
- Код P0–P6 (React inbox на живом API).

## Out of scope / демо директора

- Роли и cron.  
- Реальный Bitrix API.  
- 10–12 площадок, GPT/LLM для скрейпа, ~17k dump, ЭЦП.
