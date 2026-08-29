# Tasks / backlog

**status:** active  
**last-review-date:** 2026-08-29  
**P17:** [036](./036-search-plus-minus.md) **done** · [037](./037-score-no-inject.md) **done** · [038](./038-ai-reviewed-tab.md) **done** · [039](./039-ai-master-prompt.md) **done** · [040](./040-roseltorg-adapter.md) **done** · [041](./041-shared-search-packages.md) **done**  
**Прогон группы (docs):** [044](./044-search-groups-discovery.md)–[047](./047-run-ux-copy.md) **done** · код [048](./048-search-groups-backend.md) **done** · UI [049](./049-search-groups-ui.md)–[050](./050-search-groups-qa.md) **backlog**

Владелец смотрит **эту таблицу**. Карточка = детали и acceptance. Cursor Plans ≠ канон.

**Id:** числа `001`, `002`, … (без буквенных префиксов).  
**Статусы:** `backlog` · `ready` · `doing` · `done` · `drop`.  
**Типы:** `task` · `story` (user story — тот же числовой ряд).

Правило: новый пункт = файл `{id}-{slug}.md` **и** строка ниже. Смена статуса = таблица + frontmatter карточки.

Шаблоны: [`_template-task.md`](./_template-task.md) · [`_template-story.md`](./_template-story.md)

Фазы хвоста: [`../platform-phases.md`](../platform-phases.md) (`accepted`) · **NEXT+ детально:** [`../next-phases.md`](../next-phases.md) (`draft`). Не перескакивать фазы.

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
| 018 | VPS: Caddy+TLS | task | done | P7 | | [018-vps-tls.md](./018-vps-tls.md) |
| 019 | P1: только приём заявок, срок с сегодня | task | done | P1 | | [019-open-upcoming-only.md](./019-open-upcoming-only.md) |
| 020 | Дев-стенд: скрипт подъёма + агенты не скикают БД | task | done | P5.1 | | [020-dev-stand.md](./020-dev-stand.md) |
| 021 | GitHub origin + git workflow | task | done | P6 | | [021-github-origin.md](./021-github-origin.md) |
| 022 | Tech: Старт/Стоп прогона в React | task | done | NEXT+ | Q25 | [022-tech-start-stop.md](./022-tech-start-stop.md) |
| 023 | Именованные поиски + очередь прогонов | task | done | NEXT+ | Q16/Q25 | [023-named-searches.md](./023-named-searches.md) |
| 024 | Адаптер Tender.Pro | task | done | NEXT+ | Q16 | [024-tender-pro-adapter.md](./024-tender-pro-adapter.md) |
| 025 | Чистый customer_name на карточке | task | done | NEXT+ | | [025-customer-name.md](./025-customer-name.md) |
| 026 | Drawer настроек поиска (Править) | task | done | NEXT+ | | [026-search-settings-drawer.md](./026-search-settings-drawer.md) |
| 027 | Колонка «Просроченные» + архив | task | done | NEXT+ | P8 | [027-expired-column.md](./027-expired-column.md) |
| 028 | Прогон: уже был + отчёт счётчиков | task | done | NEXT+ | | [028-run-idempotent-report.md](./028-run-idempotent-report.md) |
| 029 | Тиры: услуги vs поставка + ИИ отдельным шагом | task | done | NEXT+ | | [029-tier-rules-and-ai.md](./029-tier-rules-and-ai.md) |
| 030 | Покрытие поиска: сиды A–E + без лимита 1000 | task | done | NEXT+ | | [030-search-coverage.md](./030-search-coverage.md) |
| 031 | Укрепление скрейпа: меньше тихих пропусков | task | done | NEXT+ | P14 | [031-scrape-hardening.md](./031-scrape-hardening.md) |
| 032 | P12: синхрон канона API с lock | task | done | NEXT+ | P12 | [032-api-canon-sync.md](./032-api-canon-sync.md) |
| 033 | Без УК/РК в keywords и scoring + wipe #2 | task | done | NEXT+ | P15 | [033-no-uk-rk-keywords.md](./033-no-uk-rk-keywords.md) |
| 034 | Полные keywords Rostender + только ВИК | task | done | NEXT+ | P16 | [034-full-keywords-vik-only.md](./034-full-keywords-vik-only.md) |
| 035 | Строительный контроль не в Горячих | task | done | NEXT+ | | [035-no-build-control-hot.md](./035-no-build-control-hot.md) |
| 036 | Поиск v2: плюс/минус по пакетам | task | done | NEXT+ | P17 | [036-search-plus-minus.md](./036-search-plus-minus.md) |
| 037 | Скоринг: supply-минусы + без methods inject | task | done | NEXT+ | P18 | [037-score-no-inject.md](./037-score-no-inject.md) |
| 038 | Вкладка «Разобрано с помощью ИИ» | task | done | NEXT+ | | [038-ai-reviewed-tab.md](./038-ai-reviewed-tab.md) |
| 039 | Мастер-промпт ИИ + wire provod | task | done | NEXT+ | | [039-ai-master-prompt.md](./039-ai-master-prompt.md) |
| 040 | Адаптер Росэлторг CORP | task | done | NEXT+ | | [040-roseltorg-adapter.md](./040-roseltorg-adapter.md) |
| 041 | Общие слова поиска A–E на все площадки | task | done | NEXT+ | | [041-shared-search-packages.md](./041-shared-search-packages.md) |
| 042 | provod.ai: timeout→fallback + commit per lot | task | done | NEXT+ | | [042-provod-resilience.md](./042-provod-resilience.md) |
| 043 | Росэлторг www-поиск вместо CORP | task | done | NEXT+ | | [043-roseltorg-www.md](./043-roseltorg-www.md) |
| 044 | Discovery: группы поиска × площадки | task | done | NEXT+ | | [044-search-groups-discovery.md](./044-search-groups-discovery.md) |
| 045 | Delivery: API контракт групп и площадок | task | done | NEXT+ | | [045-search-groups-api.md](./045-search-groups-api.md) |
| 046 | Design: IA Прогон + компоненты W-run | task | done | NEXT+ | | [046-run-ia-design.md](./046-run-ia-design.md) |
| 047 | UX copy: площадки, группы, диагностика | task | done | NEXT+ | | [047-run-ux-copy.md](./047-run-ux-copy.md) |
| 048 | Backend: search_groups + platforms.enabled | task | done | NEXT+ | | [048-search-groups-backend.md](./048-search-groups-backend.md) |
| 049 | Frontend: Прогон 4 секции + группы | task | backlog | NEXT+ | | [049-search-groups-ui.md](./049-search-groups-ui.md) |
| 050 | QA: группы × площадки + wipe/seeds notes | task | backlog | NEXT+ | | [050-search-groups-qa.md](./050-search-groups-qa.md) |

### Очередь

- **001–011** — done в mock; P5.0 **accepted** (2026-08-13).
- **012** — done (P5.1). **013** — done (P5.2). **014** — done (P5.3). **015** — done (P5.4). **016** — done (P5.5). **017** — done (P6). **019** — done (P1 hotfix: только открытые). **020** — done (P5.1 DX: `dev-up.ps1`). **021** — done (GitHub origin). **018** — done (P7 HTTPS). **022** — done (Start/Stop в React). **023** — done (именованные поиски + очередь). **024** — done (Tender.Pro adapter + prefix `tender_id`). **025** — done (clean customer_name). **026** — done (search settings drawer).
- **032** — P12 канон API **done**; docs-only.
- **027** — P8 просрочка + архив **done**. **028** — P9 update-on-diff + Tech отчёт **done**. **029** — P10 тиры + ИИ **done**. **030** — P11 покрытие поиска (сиды A–E, без лимита) **done**.
- **031** — P14 hardening скрейпа — **done**.
- **033** — P15 без УК/РК + wipe #2 — **done** (2026-08-28).
- **034** — P16 полные keywords + ВИК + cookies admin956 — **done** (2026-08-28).
- **035** — строительный контроль → L3, убрать из сидов — **done** (2026-08-28); **deprecated** при коде 036 — см. [`search-system-v2.md`](../../discovery/search-system-v2.md).
- **036** — поиск v2 плюс/минус — **done** (2026-08-28); wipe #4 RT-only.
- **037** — supply exclude + no methods inject — **done** (P18 wipe #5, 2026-08-28).
- **038** — вкладка ИИ вместо галочки — **done** (2026-08-28).
- **039** — мастер-промпт ИИ + wire независимого provod — **done** (2026-08-29); wipe+AI на проде — после merge/deploy (D4).
- **040** — адаптер Росэлторг CORP — **done** (merge `feat/040-roseltorg-adapter`); VPS deploy — `--sync` + `--deploy` по команде.
- **041** — общие слова A–E на все ЭТП (канон Ростендер) — **done** (2026-08-29).
- **042** — provod resilience (timeout→fallback, commit per lot, 3-model chain) — **done** (2026-08-29; smoke 3/0).
- **043** — Росэлторг www вместо CORP (+ docs + twin prefer) — **done** (2026-08-29; live ATOM28082600172).
- **044–047** — docs: группы поиска × площадки + IA/copy Прогон — **done** (2026-08-29); канон [`../../discovery/search-groups.md`](../../discovery/search-groups.md).
- **048** — backend search_groups + platform_settings + queue expand — **done** (2026-08-29). UI **049–050** — backlog.
- **ЭТП учётки:** канон [`../../discovery/platforms.md`](../../discovery/platforms.md) + [`../auth-cookies.md`](../auth-cookies.md). Следующие адаптеры: B2B → OilB2B → Северсталь.
- Порядок фаз: [`../next-phases.md`](../next-phases.md). **P13 wipe + полный прогон** — **done** (2026-08-27).
