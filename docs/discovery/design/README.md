# Sales Inbox — design package

**status:** accepted-with-notes  
**last-review-date:** 2026-08-13  
**product:** [`../sales-inbox.md`](../sales-inbox.md) (**accepted**)  
**visual P5.0:** **accepted** (owner 2026-08-13, целиком)  
**worksheet:** [`../owner-flight-worksheet-2026-08-12.md`](../owner-flight-worksheet-2026-08-12.md)  
**Architect packet:** [`../../delivery/tech-architecture.md`](../../delivery/tech-architecture.md) · [`../../delivery/sales-inbox-api.md`](../../delivery/sales-inbox-api.md) · [`../../delivery/platform-phases.md`](../../delivery/platform-phases.md)  
**Стоп API снят:** дизайн ок. P5.1–P5.2 done. Экран входа — W-login (не перерисовка inbox).

## Порядок чтения

| # | Файл | Содержание |
| --- | --- | --- |
| 1 | [`sales-inbox-components.md`](./sales-inbox-components.md) | Каталог компонентов |
| 2 | [`sales-inbox-component-specs.md`](./sales-inbox-component-specs.md) | Визуал и поведение по компонентам |
| 3 | [`sales-inbox-wireframes.md`](./sales-inbox-wireframes.md) | IA / wireframes экранов |
| 4 | [`sales-inbox-copy.md`](./sales-inbox-copy.md) | RU-микрокопия |

## Owner gate

**Статус пакета:** `accepted-with-notes` (2026-08-12).  
**Product discovery:** `accepted`. Visual P5.0 **accepted**. Runtime: [`platform-phases.md`](../../delivery/platform-phases.md).

### Accepted checklist

- [x] Вкладки Лоты (default) / Прогон  
- [x] Toggle Карточки / Таблица (иконка + подпись)  
- [x] Правый drawer **520px** с секцией Документы  
- [x] Каталог + спеки + wireframes + copy  
- [x] Visual SoT = vendored `ndt-personal` (blurple); adapters в `app/web`

### Notes (вошли в пакет + architect)

1. Visual SoT: **скопированный** kit `ndt-personal` (theme, BoardColumn, mini-card, ViewCommandBar, drawer 400px).  
2. Столбцы приоритета Горячие / Сильные / Смотреть; доска **fluid** на ширину контента.  
3. Accent **blurple** `#635BFF` (как personal).  
4. Toolbar: command bar + **поиск отдельной полной шириной** под ним.  
5. На карточке: **где работать** (`location`).  
6. **[004](../../delivery/tasks/004-filters-menu.md)** + **[008](../../delivery/tasks/008-filters-personal-list.md)**: bar = кнопка+чекбокс Непросмотренные; отдельные FilterTrigger «Фильтры» / «Срок подачи» / «Попало к нам»; меню = вертикальный список (не чипы).  
7. **[005](../../delivery/tasks/005-card-chips.md)** (был E, `done` в mock): на карточке без chip приоритета и «новое»; опц. «вручную»; left bar = непросмотрен.  
8. **[006](../../delivery/tasks/006-platform-icons.md)** + **[011](../../delivery/tasks/011-platform-icon-rail.md):** `PlatformIcon` в правом рейле — **accepted** с пакетом.  
9. **[007](../../delivery/tasks/007-date-filters.md)** (`done` в mock): даты = пресеты.  
10. **[009](../../delivery/tasks/009-drawer-switch-file-icons.md)**: Switch «Просмотрено»; `FileTypeIcon`.  
11. P5.0 **accepted**. Дальше — [`platform-phases`](../../delivery/platform-phases.md). Bitrix не в приёмке.  
12. Excel / cron / роли = NEXT+. VPS = **P7** (в ship).

**Экран входа:** P5.2 **done** (W-login, personal kit); inbox не перерисовывать.

**Таблица тасков:** [`../../delivery/tasks/`](../../delivery/tasks/)

## Refs

- Код: `app/web/src/theme/`, `app/web/src/vendor/personal/`, `app/web/src/components/scout/`  
- Площадки: `app/web/public/platforms/`, `scripts/fetch-platform-icons.py`  
- Источник: `ndt-personal/apps/web`
