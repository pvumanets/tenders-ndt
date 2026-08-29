# Search groups API — контракт (группы × площадки)

**status:** accepted  
**last-review-date:** 2026-08-29  
**discovery:** [`../discovery/search-groups.md`](../discovery/search-groups.md)  
**AS-IS shim:** [`../discovery/named-searches.md`](../discovery/named-searches.md) · `/api/searches*` до 049  
**код:** [048](./tasks/048-search-groups-backend.md) **done**  
**auth / cookies:** [`auth-cookies.md`](./auth-cookies.md)

Реализация **048 done**. Runtime: `search_groups` × `platform_settings.enabled`.  
`/api/searches*` — compatibility shim (разворот group×platform) до UI [049](./tasks/049-search-groups-ui.md).

---

## Цель

1. CRUD **групп** (плюс/минус/очередь) без привязки к ЭТП.  
2. First-class **enable** площадок.  
3. Старт = разворот `{группы in_queue} × {площадки enabled}`.  
4. Сохранить один `runs` row на шаг (пара группа×площадка) и prefix `tender_id`.

---

## Данные

### `search_groups` (новая таблица / эволюция `searches`)

| Поле | Тип | Правило |
| --- | --- | --- |
| `id` | UUID PK | |
| `name` | string unique | без префикса «РосТендер —» |
| `queries` | JSONB list | ≥1 |
| `exclude` | JSONB list | default `[]` |
| `limit_n` | int | `0` = без потолка |
| `in_queue` | bool | в Старте |
| `sort_order` | int | порядок групп |
| `created_at` | timestamptz | |

**Нет** `platform_id` на группе.

### Площадки `enabled`

Рекомендация (048 выбирает одну):

| Вариант | Описание |
| --- | --- |
| **A (preferred)** | Таблица `platform_settings` (`platform_id` PK, `enabled` bool) |
| B | JSON/settings row в существующем settings store |

Сиды: `rostender` / `tender-pro` / `roseltorg`. Default enable при миграции: как сейчас у сидов (`in_queue` по cookies для TP/RE; rostender обычно on) — точная матрица в 048.

### `runs` / FK

- AS-IS: `runs.search_id` → `searches.id`.  
- TO-BE: `runs.search_group_id` → `search_groups.id` (+ `source_platform_id` как сейчас).  
- Миграция: схлопнуть 15 seed UUID → 5 group UUID; кастомные per-platform строки — слить по каноническому имени пакета или оставить одну группу с union queries (алгоритм в 048 acceptance).

Исторические `runs` со старыми `search_id` — nullable/legacy map или backfill; не блокировать inbox.

---

## REST (TO-BE)

Все пути за Scout-сессией (как `/api/searches*`).

| Метод | Путь | Назначение |
| --- | --- | --- |
| `GET` | `/api/search-groups` | `{ items: [...] }` по `sort_order` |
| `POST` | `/api/search-groups` | Создать группу |
| `PUT` | `/api/search-groups/{id}` | Правка (имя, queries, exclude, limit_n, in_queue, sort_order) |
| `DELETE` | `/api/search-groups/{id}` | Удалить |
| `GET` | `/api/platforms` | Список ЭТП: `platform_id`, display name, `enabled`, `session` |
| `PUT` | `/api/platforms/{platform_id}` | body `{ "enabled": bool }` |

### Тело группы

```json
{
  "id": "uuid",
  "name": "методы",
  "queries": ["ультразвуковой контроль", "ВИК"],
  "exclude": ["поставка", "закупка", "прибор"],
  "limit_n": 0,
  "in_queue": true,
  "sort_order": 1
}
```

Ошибки: duplicate name → 409; empty queries → 400; not found → 404.

### Тело площадки (list item)

```json
{
  "platform_id": "rostender",
  "name": "РосТендер",
  "enabled": true,
  "session": "ok"
}
```

`session`: `ok` \| `missing` \| `expired` \| `list_without_login` (Tender.Pro список) \| `unknown`.  
UI **не** показывает имена cookie-файлов в primary status (copy — [047](./tasks/047-run-ux-copy.md)).

### Старт / статус

| Метод | Поведение TO-BE |
| --- | --- |
| `POST /api/run/start` | Разворот очереди group×platform; body без ad-hoc настроек. `empty_queue` если нет групп **или** нет площадок. |
| `POST /api/run/stop` | Без смены смысла |
| `GET /api/status` | `queue[]` шаги с `group_name` + `platform_id`; `platforms` / `sessions` согласованы с `/api/platforms`; `run_dir` остаётся в API для диагностики, **не** обязателен в основном UI |

Шаг очереди (status):

```json
{
  "group_id": "uuid",
  "group_name": "методы",
  "platform_id": "tender-pro",
  "status": "pending"
}
```

Один шаг → один `runs` row (`search_group_id`, `source_platform_id`).

---

## Миграция с `/api/searches*`

| Фаза | Поведение |
| --- | --- |
| **048 done** | Новые routes; `/api/searches*` = shim (GET cartesian; PUT пишет в группу; **DELETE** → `in_queue=false`, без wipe группы) |
| 049 | UI только на `/api/search-groups` + `/api/platforms`; shim можно снять |

Cookie sync при boot: **только enable** TP/RE, если cookie-файлы есть. Не снимает `enabled=false` оператора при отсутствии cookies (list-without-login). Hard-delete группы — только `DELETE /api/search-groups/{id}`.

---

## Совместимость inbox

Без смены: `tender_id`, ingest L1–L3, update-on-diff, AI step. Меняется только источник шага прогона.

---

## Acceptance (docs)

- [x] Таблицы group / platform / queue expand  
- [x] REST sketch  
- [x] Миграция и deprecate searches отмечены  
- [x] Owner accepted → код 048 **done**

## Out of scope

- Реализация, pytest, wipe  
- Новые ЭТП сверх реестра  
- Глобальный минус  
