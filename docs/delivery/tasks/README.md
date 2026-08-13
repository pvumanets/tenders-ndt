# Tasks / backlog

**status:** active  
**last-review-date:** 2026-08-13  

Владелец смотрит **эту таблицу**. Карточка = детали и acceptance. Cursor Plans ≠ канон.

**Id:** числа `001`, `002`, … (без буквенных префиксов).  
**Статусы:** `backlog` · `ready` · `doing` · `done` · `drop`.  
**Типы:** `task` · `story` (user story — тот же числовой ряд).

Правило: новый пункт = файл `{id}-{slug}.md` **и** строка ниже. Смена статуса = таблица + frontmatter карточки.

Шаблоны: [`_template-task.md`](./_template-task.md) · [`_template-story.md`](./_template-story.md)

Фазы хвоста: [`../platform-phases.md`](../platform-phases.md) (`accepted`). Не перескакивать фазы.

## Индекс

| id | что | тип | статус | фаза | было | карточка |
| --- | --- | --- | --- | --- | --- | --- |
| 001 | Поиск full-width под command bar | task | done | P5.0 | A | [001-search-fullwidth.md](./001-search-fullwidth.md) |
| 002 | Fluid колонки доски на всю ширину | task | done | P5.0 | B | [002-fluid-board.md](./002-fluid-board.md) |
| 003 | «Где работать» на карточке и в таблице | task | done | P5.0 | C | [003-location-on-card.md](./003-location-on-card.md) |
| 004 | Меню «Фильтры» (popover) в toolbar | task | done | P5.0 | D | [004-filters-menu.md](./004-filters-menu.md) |
| 005 | Чипы карточки: без приоритета и «новое» | task | done | P5.0 | E | [005-card-chips.md](./005-card-chips.md) |
| 006 | PlatformIcon + реестр площадок | task | done | P5.0 | F | [006-platform-icons.md](./006-platform-icons.md) |
| 007 | Даты в фильтрах: пресеты вместо 4 input | task | done | P5.0 | | [007-date-filters.md](./007-date-filters.md) |
| 008 | Фильтры: personal-список, даты отдельно, непросмотренные — кнопка | task | done | P5.0 | | [008-filters-personal-list.md](./008-filters-personal-list.md) |
| 009 | Drawer: Switch «Просмотрено» + иконки файлов | task | done | P5.0 | | [009-drawer-switch-file-icons.md](./009-drawer-switch-file-icons.md) |
| 010 | Адаптив: косяки узких экранов | task | done | P5.0 | | [010-responsive-audit.md](./010-responsive-audit.md) |
| 011 | PlatformIcon — фиксированный правый рейл карточки | task | done | P5.0 | | [011-platform-icon-rail.md](./011-platform-icon-rail.md) |
| 012 | Platform: compose db+api, Alembic, bootstrap users | task | done | P5.1 | | [012-platform-compose.md](./012-platform-compose.md) |
| 013 | Auth: session login + экран входа | task | done | P5.2 | | [013-auth-login.md](./013-auth-login.md) |
| 014 | Ingest: worker upsert в Postgres | task | done | P5.3 | | [014-ingest-postgres.md](./014-ingest-postgres.md) |
| 015 | Inbox API из Postgres + поля mock | task | done | P5.4 | | [015-inbox-api.md](./015-inbox-api.md) |
| 016 | Docs: download на том + routes | task | done | P5.5 | | [016-docs-volume.md](./016-docs-volume.md) |
| 017 | Wire React: снять моки | task | done | P6 | | [017-react-wire.md](./017-react-wire.md) |
| 018 | VPS: Caddy+TLS | task | doing | P7 | | [018-vps-tls.md](./018-vps-tls.md) |
| 019 | P1: только приём заявок, срок с сегодня | task | done | P1 | | [019-open-upcoming-only.md](./019-open-upcoming-only.md) |
| 020 | Дев-стенд: скрипт подъёма + агенты не скикают БД | task | done | P5.1 | | [020-dev-stand.md](./020-dev-stand.md) |
| 021 | GitHub origin + git workflow | task | done | P6 | | [021-github-origin.md](./021-github-origin.md) |

### Очередь

- **001–011** — done в mock; P5.0 **accepted** (2026-08-13).
- **012** — done (P5.1). **013** — done (P5.2). **014** — done (P5.3). **015** — done (P5.4). **016** — done (P5.5). **017** — done (P6). **019** — done (P1 hotfix: только открытые). **020** — done (P5.1 DX: `dev-up.ps1`). **021** — done (GitHub origin). **018** — doing (HTTPS https://tenders.ndtexam.ru; Owner OK — логин с другого ПК).
