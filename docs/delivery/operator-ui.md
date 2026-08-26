# Operator UI — экран хода работы и Sales Inbox

**status:** accepted  
**last-review-date:** 2026-08-26  
**AS-IS:** фаза P5 в [`code-phases.md`](./code-phases.md)  
**TO-BE фазы:** [`platform-phases.md`](./platform-phases.md)  
**стек:** [`tech-architecture.md`](./tech-architecture.md)  
**API:** [`sales-inbox-api.md`](./sales-inbox-api.md)

Экран для **человека** (директор / digital). Не путать с UI rostender (его автоматизирует worker).

Прод: React за **Scout-логином**, корень `/`. С P5.1 `/` отдаёт собранный React. **P6 done:** лоты из `/api/inbox`. Вход — P5.2 **done**. AS-IS HTML — `/legacy` (`SCOUT_LEGACY_HTML`), не публичный `/`.

---

## AS-IS (P5) — техпанель HTML

**Цель:** в одном браузере видеть ход прогона и приоритетные лоты без CSV.

### Зоны (спека, сделано)

1. **Шапка** — название прогона, дата, Start / Stop (Stop = мягкая остановка после карточки).
2. **Фаза** — шаг P1…P4: текст + индикатор.
3. **Прогресс списка** — `собрано N / 1000`.
4. **Счётчики fit** — L1 / L2 / L3 / noise.
5. **Прогресс карточек** — `карточек открыто K / (L1+L2+L3)`.
6. **Лог** — последние 50–100 строк; ошибки красным.
7. **Артефакты** — путь выгрузки прогона.
8. **Сессия площадки** — OK / cookies expired (без секретов).
9. **Результаты** — таблица L1/L2/L3; `/api/results`.

Hotfix only. На деве `/legacy`; **не** корень `/`.

### Чего нет в AS-IS

- Авторизация Scout (появится на React).
- Редактирование правил L1–L3.
- Bitrix.
- Просмотренность / ручной приоритет (Postgres + React).

### Done P5 ✅

- Смена фаз и счётчиков без F5 «наугад».
- После прогона — путь выгрузки и таблица; CSV/MD как файлы приёмки.

---

## TO-BE — Sales Inbox (React)

Спека: [`../discovery/sales-inbox.md`](../discovery/sales-inbox.md) + [`../discovery/design/`](../discovery/design/).  
API: [`sales-inbox-api.md`](./sales-inbox-api.md).

### P5.0 — визуальный прототип (моки) — **accepted**

- Код: `app/web/` (Vite + React + TS); kit `vendor/personal/` + `components/scout/`.
- Данные: `src/mocks/*.json` как фикстуры; SoT списка — API с **P6**.
- Toolbar: кнопка+чекбокс **Непросмотренные**; отдельные `FilterTriggerButton`; поиск full-width ([008](./tasks/008-filters-personal-list.md)).
- Карточка: без chip приоритета и «новое»; `PlatformIcon` в правом рейле ([011](./tasks/011-platform-icon-rail.md)).
- Drawer: Switch «Просмотрено»; `FileTypeIcon` ([009](./tasks/009-drawer-switch-file-icons.md)).
- Доска: 3 столбца fluid на `md+`; ниже `md` — столбик ([010](./tasks/010-responsive-audit.md)).

### P5.2 — экран входа

Полноэкранный вход (не вкладка inbox). Visual = personal kit: фон `surfaceSubtle`, карточка Paper по центру, blurple «Войти», плотность полей как command bar.

- Поля: логин, пароль; одна кнопка «Войти».
- Ошибка — один Alert: «Неверные логин или пароль» (без утечки существования логина).
- Нет «забыли пароль», регистрации, ролей.
- После успеха — живые лоты inbox. 401 / нет cookie → снова этот экран.
- В шапке inbox текстовая кнопка **«Выйти»** (не перерисовка доски и не новый фильтр).

### P6 — wire — **done**

| Зона | Поведение |
| --- | --- |
| Вход | `/api/auth/*` |
| **Лоты** (default) | тот же UI → `/api/inbox*` |
| **Прогон** | `GET /api/status` + `POST /api/run/start` / `stop`; CRUD `/api/searches*` ([023](./tasks/023-named-searches.md) **done**) |

Пресеты дат остаются в UI; на API уходят `deadline_*` / `ingested_*`. Viewed / приоритет — `PUT`. Документы в drawer — `GET /api/inbox/{id}` + same-origin download.

### NEXT+ — поиски на вкладке Прогон (023 **done**)

Третью вкладку не плодим. На «Прогоне»: список именованных поисков, Switch «в очереди», CRUD, Старт/Стоп. Query/limit только в карточке поиска. Канон: [`../discovery/named-searches.md`](../discovery/named-searches.md).
