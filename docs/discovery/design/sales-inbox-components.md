# Sales Inbox — каталог компонентов

**status:** accepted-with-notes  
**last-review-date:** 2026-08-29  
**product:** [`../sales-inbox.md`](../sales-inbox.md)  
**specs:** [`sales-inbox-component-specs.md`](./sales-inbox-component-specs.md)  
**wireframes:** [`sales-inbox-wireframes.md`](./sales-inbox-wireframes.md)  
**copy:** [`sales-inbox-copy.md`](./sales-inbox-copy.md)  
**группы / Прогон TO-BE:** [`../search-groups.md`](../search-groups.md) · [046](../../delivery/tasks/046-run-ia-design.md)

Каталог UI. **Реализация:** копируем kit из `ndt-personal` в `app/web/src/vendor/personal/` + адаптеры `components/scout/` (лоты, столбцы приоритета). Domain people/crew API не переносим.

---

## Карта зон → компоненты

| Зона экрана | Компоненты |
| --- | --- |
| App chrome | `AppShell`, `AppTabs` |
| Лоты — toolbar | `InboxFilters`, `ViewToggle` |
| Лоты — список | `LotCardGrid`, `LotCard`, `LotTable`, `LotTableRow` |
| Общие атомы списка | `PriorityChip`, `UnreadMarker`, `BitrixStatus` |
| Детали лота | `TenderDetailDrawer`, `TenderFieldRow`, `DocumentsList` |
| Прогон | `TechRunPanel` (shell) → `RunControls`, `RunQueueSummary`, `TechPhaseBar`, `TechCounters`, `RunReport` (done only), `SearchGroupList`, `SearchGroupDrawer`, `PlatformEnableList`, `PlatformSessionHint`, `TechDiagnostics` |
| Состояния | `InboxEmptyState`, `InboxErrorState` |

---

## Компоненты

### `AppShell`

| | |
| --- | --- |
| **Зона** | Весь viewport |
| **Ответственность** | Светлый каркас: шапка продукта + область вкладок + контент |
| **In** | title, active tab content |
| **Out** | rostender UI, auth |
| **Состояния** | default |

### `AppTabs`

| | |
| --- | --- |
| **Зона** | Шапка / под шапкой |
| **Ответственность** | Переключение **Лоты** (default) / **Прогон** |
| **In** | `activeTab`: `lots` \| `run` |
| **Out** | deep links, >2 вкладок |
| **Состояния** | lots active; run active |

### `InboxFilters` (+ `FilterTrigger` / popover)

| | |
| --- | --- |
| **Зона** | Лоты — toolbar ([004](../../delivery/tasks/004-filters-menu.md) · [008](../../delivery/tasks/008-filters-personal-list.md)) |
| **Ответственность** | Bar: кнопка+чекбокс Непросмотренные; **Фильтры** (приоритет); **Срок подачи**; **Попало к нам**; Доска/Таблица. Меню = вертикальный список Checkbox/Radio (personal). Поиск — row под bar |
| **In** | filter model; badge на каждом триггере |
| **Out** | Chip как контроль фильтра; wrapping chip-пикер; 4 date input в bar; дата «Старт» прогона; Bitrix в демо |
| **Состояния** | idle; menu open; filters applied; search empty → `InboxEmptyState` |

### `ViewToggle`

| | |
| --- | --- |
| **Зона** | Лоты — toolbar End |
| **Ответственность** | Режим **Доска** \| **Таблица** (иконка + подпись) |
| **In** | `view`: `cards` (доска) \| `table` |
| **Out** | третий layout |
| **Состояния** | board; table |

### `LotCardGrid`

| | |
| --- | --- |
| **Зона** | Лоты — body (view=cards) |
| **Ответственность** | Сетка/колонка карточек лотов; клик → открыть drawer |
| **In** | list of lot summaries |
| **Out** | infinite scroll spec (later) |
| **Состояния** | loading; populated; empty |

### `LotCard` / `LotMiniCard`

| | |
| --- | --- |
| **Зона** | Внутри столбца доски / grid |
| **Ответственность** | Карточка лота; Task E: без chip приоритета и без «новое»; опц. «вручную»; location; Task F/011: `PlatformIcon` в правом рейле |
| **In** | unread (bar), manual override flag, title, customer, location, deadline, price, `source_platform_id` |
| **Out** | chip Горячие/Сильные/Смотреть на доске; текст «новое»; домен площадки текстом; контакты (drawer) |
| **Состояния** | unread; read; selected; hover |

### `PlatformIcon`

| | |
| --- | --- |
| **Зона** | LotMiniCard (правый рейл), LotTable (колонка «Площадка»), TenderDrawer у «На площадке» |
| **Ответственность** | Сигнал «откуда тендер»; tooltip = label площадки |
| **In** | `source_platform_id` |
| **Out** | scrape других ЭТП; текст домена на карточке |
| **Состояния** | image ok; broken → initials placeholder |

### `LotTable`

| | |
| --- | --- |
| **Зона** | Лоты — body (view=table) |
| **Ответственность** | Таблица тех же полей, что у карточки + колонка площадки; клик по строке → drawer |
| **In** | same lot summaries + `source_platform_id` |
| **Out** | column resize / export |
| **Состояния** | loading; populated; empty |

### `LotTableRow`

| | |
| --- | --- |
| **Зона** | Внутри `LotTable` |
| **Ответственность** | Одна строка; те же атомы, что `LotCard` |
| **Состояния** | unread; read; selected; hover |

### `PriorityChip`

| | |
| --- | --- |
| **Зона** | Таблица, drawer header; **не** авто-приоритет на доске-карточке |
| **Ответственность** | Ярлык Горячие / Сильные / Смотреть; «вручную» на карточке доски если override |
| **In** | sales priority label; `overridden?: boolean` |
| **Out** | L1/L2/L3; chip приоритета на LotMiniCard при авто-тире |
| **Состояния** | hot; strong; watch; overridden-only-on-card |

### `UnreadMarker`

| | |
| --- | --- |
| **Зона** | Карточка = left bar; таблица = точка |
| **Ответственность** | Непросмотрен без текста «новое» |
| **In** | `viewed: boolean` |
| **Out** | label «новое» на карточке |
| **Состояния** | unread; read |

### `BitrixStatus`

| | |
| --- | --- |
| **Зона** | Список + drawer footer |
| **Ответственность** | Показ stub **«Скоро»**; позже — нет / создан / ошибка |
| **In** | `mode: stub` \| future statuses |
| **Out** | реальный API call |
| **Состояния** | soon (current); none; created; error (future) |

### `TenderDetailDrawer`

| | |
| --- | --- |
| **Зона** | Overlay справа над Лотами |
| **Ответственность** | Полная высота; header (title, close, chip); scroll body; footer actions (иконка+подпись). Аналог `PersonDetailDrawerShell` (**520px** desktop / full mobile) |
| **In** | lot detail model; open/onClose |
| **Out** | отдельный full-page route (можно later «Открыть полностью» — не must) |
| **Состояния** | closed; open+loading; open+ready; open+error |

### `TenderFieldRow`

| | |
| --- | --- |
| **Зона** | Внутри drawer body |
| **Ответственность** | Label над value (иерархия ADR-018) |
| **In** | label, value, optional link |
| **Out** | — |
| **Состояния** | with value; empty (прочерк / «Нет данных») |

### `DocumentsList`

| | |
| --- | --- |
| **Зона** | Секция drawer |
| **Ответственность** | Список файлов: `FileTypeIcon` + имя + размер + «Скачать»; empty пока worker не качает |
| **In** | files[] \| empty reason |
| **Out** | upload пользователем |
| **Состояния** | empty-not-downloaded; empty-none; populated; error |

### `TechRunPanel`

| | |
| --- | --- |
| **Зона** | Вкладка Прогон |
| **Ответственность** | Shell из **4 секций** в порядке: Управление · **Группы** · **Площадки** · Диагностика. Sticky Управление. |
| **In** | status API; search-groups; platforms |
| **Out** | sales filters; primary «Путь/папка прогона»; RunReport в idle/running |
| **Состояния** | idle; running (config locked); done; stopped; error |

### `RunControls`

| | |
| --- | --- |
| **Зона** | Секция «Управление» |
| **Ответственность** | Start / Stop |
| **Состояния** | can start; running (stop enabled); disabled empty queue / busy |

### `RunQueueSummary`

| | |
| --- | --- |
| **Зона** | Управление |
| **Ответственность** | Prefight: `N групп × M площадок → K шагов` / «очередь пуста»; running: `Шаг i/K · группа × площадка` |
| **Состояния** | empty; ready; running |

### `TechPhaseBar`

| | |
| --- | --- |
| **Зона** | Управление |
| **Ответственность** | Текущая фаза + прогресс списка/карточек + (opt) текущий шаг; **hero** text в секции |
| **Состояния** | per phase; done; idle |

### `TechCounters`

| | |
| --- | --- |
| **Зона** | Управление |
| **Ответственность** | Счётчики; L1–L3/noise; **L1 визуально доминирует**, L2/L3/noise muted |
| **Состояния** | zero; populated |

### `RunReport`

| | |
| --- | --- |
| **Зона** | Управление — **только** `done` / `stopped` (или collapse «Отчёт») |
| **Ответственность** | new / already / updated / expired |
| **Out** | idle и running primary row |
| **Состояния** | hidden; populated |

### `SearchGroupList`

| | |
| --- | --- |
| **Зона** | Секция «Группы поиска» (вторая, после Управления) |
| **Ответственность** | Список групп: имя · Switch «В очереди» · Править/Удалить · «Новая группа». Plus preview — не колонка (muted clamp / drawer). |
| **In** | `/api/search-groups` |
| **Out** | строки «РосТендер — …» × N; select площадки; chip-пикер |
| **Состояния** | empty; populated; locked while running |

### `SearchGroupDrawer`

| | |
| --- | --- |
| **Зона** | Overlay Прогон |
| **Ответственность** | CRUD группы: имя, плюс, минус, лимит, очередь. **Без** поля площадки. |
| **Состояния** | create; edit; locked while running |

### `PlatformEnableList`

| | |
| --- | --- |
| **Зона** | Секция «Площадки» (третья) |
| **Ответственность** | Строка на ЭТП: имя · Switch «Участвует» (FormControlLabel). Session — через `PlatformSessionHint`, не равный вес. |
| **In** | `/api/platforms` |
| **Out** | имена `cookies.*.txt` в primary |
| **Состояния** | enabled/disabled; locked while running |
| **Was** | часть `PlatformStatusList` (split 2026-08-29) |

### `PlatformSessionHint`

| | |
| --- | --- |
| **Зона** | Ряд площадки / quiet Alert под заголовком секции |
| **Ответственность** | Muted статус сессии (`session_status_*`); при missing/expired на **включённой** ЭТП — один quiet Alert; детали файлов — в Диагностике |
| **Out** | Chip как пикер; essay на каждую ЭТП |
| **Состояния** | ok; missing; expired; list_without_login |

### `PlatformStatusList`

| | |
| --- | --- |
| **Статус** | **deprecated** — заменить на `PlatformEnableList` + `PlatformSessionHint` |

### `TechDiagnostics`

| | |
| --- | --- |
| **Зона** | Секция «Диагностика» |
| **Ответственность** | Collapse **закрыт по умолчанию**; **авто-раскрытие** при `error` / stop-with-error. Лог + опционально папка прогона. |
| **Out** | path в основном потоке |
| **Состояния** | collapsed; expanded; empty log |

### `TechLog`

| | |
| --- | --- |
| **Ответственность** | Последние N строк лога; ошибки выделены |
| **Состояния** | empty; streaming; error line |
| **Parent** | только внутри `TechDiagnostics` |

### `RunPathCopy`

| | |
| --- | --- |
| **Ответственность** | Папка прогона + «Копировать» |
| **Статус** | **deprecate** из основного UI; только внутри `TechDiagnostics` |
| **Состояния** | no run; has path; copied |

### `InboxEmptyState`

| | |
| --- | --- |
| **Зона** | Лоты body |
| **Ответственность** | Нет лотов / нет по фильтру / нет непросмотренных |
| **Состояния** | no-data; no-match; no-unread |

### `InboxErrorState`

| | |
| --- | --- |
| **Ответственность** | Ошибка загрузки результатов / сессии (без секретов) |
| **Состояния** | generic; cookies-expired (если показываем на Tech/Лоты) |

---

## Вне каталога (сознательно)

- Редактор правил L1–L3  
- Bitrix API client  
- Документ-uploader  
- Мобильная навигация как цель v0  

## Handoff

→ [`sales-inbox-component-specs.md`](./sales-inbox-component-specs.md) (визуал) → wireframes → copy → frontend после `accepted-with-notes` (architect plan отдельно).
