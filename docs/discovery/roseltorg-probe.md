# Зонд Росэлторг — corp (КОРП)

**status:** ship ready for adapter  
**date:** 2026-08-28  
**ship:** as-is · адаптер [040](../delivery/tasks/040-roseltorg-adapter.md) merged  
**slug:** `roseltorg` ([platforms.md](./platforms.md))  
**ресёрч API:** [`../platform-api-research.md`](../platform-api-research.md) § 9–10  
**cookies (файл, не этот md):** `./cookies.roseltorg.txt` · `ROSELTORG_COOKIES_FILE` (опц.)  
**учётка:** `ROSELTORG_USER` / `ROSELTORG_PASSWORD` только в `.env`  
**auth-правила:** [`../delivery/auth-cookies.md`](../delivery/auth-cookies.md)

Живой зонд 2026-08-28: вход **Росэлторг.ID** (`lk.roseltorg.ru`) → секция **КОРП** (`corp.roseltorg.ru/#procedures/all`). Не `com.roseltorg.ru`. Сырьё — `runs/_probe/roseltorg/` (gitignore). Значения cookie / Bearer **не** в этот md.

Скрин владельца: поиск `неразруш` → процедура № `32616262401` (приборы НК — **поставка**); приём уже истёк.

---

## Факт / гипотеза / пробел

| Тег | Утверждение |
| --- | --- |
| **fact** | `lk` — React SPA (логин email/password / Госуслуги / ЭП). `corp` — **ExtJS Sencha** (`classic.json` → `classic/app.js`). Hash `#procedures/all`. |
| **fact** | REST CORP: **`/api/v1/`**. Без Bearer реестр → `401 Authentication Required`. Утилиты вроде `/api/v1/utils/time` доступны без auth. |
| **fact** | Список: **`GET /api/v1/procedures`** → JSON `{ items, count, limit, offset }`. Reader UI: `items` / `count`, пагинация **`offset`**, `limit` (pageSize 25). |
| **fact** | Поиск по строке UI: query-param **`query`**. Параметры `name` / `search` / Sencha `filter` JSON **не** сужают выдачу так же. |
| **fact** | Поля строки: `id`, `registrationNumber`, `name`, `organizator`, `acceptanceApplicationsDateEnd` (ISO+03), `status`, `state`, `summ`, `isSumVisible`, … |
| **fact** | Карточка: **`GET /api/v1/procedures/{id}`**. |
| **fact** | Auth httpx (адаптер): `POST …/auth/v1/token` `grant_type=password` + публичный SPA client `lk`/`elk` → cookie сессии → `grant_type=auth_token` + `client_id=platform_223_corp` → **Bearer** для CORP. |
| **fact** | Netscape cookies alone (без ELK login) **недостаточны** для списка. |
| **fact** | Open-only: клиентский отбор `acceptanceApplicationsDateEnd >= сегодня MSK`; UI-параметр `visibility=active` сужает выдачу, но **не** равен open-by-deadline. API-фильтр `acceptanceApplicationsDateEnd::gte` в зонде выдачу по сроку не закрыл. |
| **gap** | Надёжный серверный open-only / сортировка по сроку приёма. |
| **gap** | Скачивание файлов лота (v1 адаптера — только log skip). |

---

## Стек площадки

```text
ROSELTORG_USER / ROSELTORG_PASSWORD  (.env)
  → POST lk.../auth/v1/token  (password, client lk/elk)
  → POST lk.../auth/v1/token  (auth_token, client platform_223_corp)
        → Authorization: Bearer …
  → GET corp.../api/v1/procedures?query=…&limit=&offset=[&visibility=active]
  → GET /api/v1/procedures/{id}
```

- Cookies Netscape — опциональны; **канон сессии API = ELK Bearer после password grant**.
- Адаптер = httpx JSON (`app/worker/roseltorg.py`), не HTML-скрейп и не Playwright.

---

## Почему не копировать rostender / tender-pro

| | РосТендер | Tender.Pro | Росэлторг CORP |
| --- | --- | --- | --- |
| Транспорт | httpx HTML | httpx HTML | httpx **JSON** + Bearer |
| Поиск | query списка | `good_name` | **`query`** на `/api/v1/procedures` |
| Сессия | Netscape cookies | cookies опц. для списка | **логин ELK → Bearer** |
| UI | серверный HTML | серверный HTML | ExtJS SPA |

---

## Адаптер

Таск [040](../delivery/tasks/040-roseltorg-adapter.md): worker + runner + seeds. Ingest `source_platform_id=roseltorg`, `tender_id=roseltorg:{id}`. Скоринг L1–L3; минус поставок. DEV-стенд; VPS deploy — после merge в `main`.

## Out of scope зонда / v1

- Секции com / zakupki / Inter RAO  
- Playwright в worker  
- Просьбы «пришлите cookie `aut`» — в jar владельца её нет; token flow выше
