# Sales Inbox — каталог компонентов

**status:** accepted-with-notes  
**last-review-date:** 2026-08-13  
**product:** [`../sales-inbox.md`](../sales-inbox.md)  
**specs:** [`sales-inbox-component-specs.md`](./sales-inbox-component-specs.md)  
**wireframes:** [`sales-inbox-wireframes.md`](./sales-inbox-wireframes.md)  
**copy:** [`sales-inbox-copy.md`](./sales-inbox-copy.md)

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
| Прогон | `TechRunPanel`, `TechPhaseBar`, `TechCounters`, `TechLog`, `RunPathCopy`, `RunControls` |
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
| **Ответственность** | Сборка tech-блоков для digital |
| **In** | status API shape (логически) |
| **Out** | sales filters |
| **Состояния** | idle; running; done; stopped; error |

### `TechPhaseBar`

| | |
| --- | --- |
| **Ответственность** | Текущая фаза прогона + прогресс пула/карточек |
| **Состояния** | per phase P1–P4; done |

### `TechCounters`

| | |
| --- | --- |
| **Ответственность** | Счётчики fit; **здесь допустимы L1/L2/L3** |
| **Состояния** | zero; populated |

### `TechLog`

| | |
| --- | --- |
| **Ответственность** | Последние N строк лога; ошибки выделены |
| **Состояния** | empty; streaming; error line |

### `RunPathCopy`

| | |
| --- | --- |
| **Ответственность** | Путь `runs/…` + одно действие «Копировать» |
| **Состояния** | no run; has path; copied feedback |

### `RunControls`

| | |
| --- | --- |
| **Ответственность** | Start / Stop прогона (только Tech) |
| **Состояния** | can start; running (stop enabled); disabled missing cookies |

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
