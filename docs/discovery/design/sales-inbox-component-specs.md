# Sales Inbox — спецификации компонентов

**status:** accepted-with-notes  
**last-review-date:** 2026-08-13  
**catalog:** [`sales-inbox-components.md`](./sales-inbox-components.md)  
**wireframes:** [`sales-inbox-wireframes.md`](./sales-inbox-wireframes.md)  
**notes:** drawer **520px**; icon+label на ключевых действиях; фильтры дат (срок / `ingested_at`) — пресеты в меню «Фильтры» ([007](../../delivery/tasks/007-date-filters.md), mock P5.0).

Визуал и поведение. Не код.

---

## Visual system

### Surfaces (Stripe-light, из `ndt-personal` palette)

| Token | Value | Use |
| --- | --- | --- |
| `surface` | `#FFFFFF` | App bg, drawer paper, cards |
| `surfaceSubtle` | `#F6F9FC` | Page wash behind content, table header |
| `border` | `#E3E8EE` | Hairline borders, dividers |
| `borderHover` | `#C1C9D2` | Hover outline |
| `text` | `#3C4257` | Body |
| `textMuted` | `#697386` | Labels, meta |
| `navy` | `#0A2540` | Product title, strong values, drawer title |

### Accent (как ndt-personal)

| Token | Value | Use |
| --- | --- | --- |
| `accent` / `stripe.blurple` | `#635BFF` | Primary CTA, tabs, focus |
| `accentSoft` | `rgba(99, 91, 255, 0.08)` | Selected/hover soft fills |
| `accentHover` | `#5851E5` | Hover on primary |

**SoT:** скопированный theme personal в `app/web/src/theme/`. Teal для scout **отменён**.

### Priority colors (chips)

| Label | Fill | Text |
| --- | --- | --- |
| Горячие | `rgba(198, 40, 40, 0.10)` | `#C62828` |
| Сильные | `rgba(239, 163, 47, 0.12)` | `#B45309` |
| Смотреть | `rgba(15, 118, 110, 0.10)` | `#0F766E` |

### Principles

- Одна композиция на вкладку Лоты: toolbar + список; drawer — overlay, не второй «дашборд».  
- Cards — только `LotCard` как контейнер клика; не оборачивать фильтры/статы в promo-cards.  
- Field rows: muted 12px label **над** 13–14px medium value.  
- Drawer paper: white, 1px border-left, **без** тяжёлой multi-shadow (как MUI Drawer override в personal).  
- **Иконки:** ключевые действия = **иконка + подпись** (не иконка alone): просмотрено, изменить приоритет, Bitrix stub, ViewToggle Карточки/Таблица; quiet line icons, без emoji.  
- Mobile (mock P5.0, [010](../../delivery/tasks/010-responsive-audit.md)): drawer full width на xs; ниже `md` — command bar 2×2, доска столбцами друг под другом; `md+` — desktop IA (один ряд bar, три колонки).

---

## Shared lot data (cards = table)

Одинаковый summary model для `LotCard` и `LotTableRow`:

| Field | UI |
| --- | --- |
| priority | `PriorityChip` |
| viewed | `UnreadMarker` |
| title | primary line, 1–2 lines clamp |
| customer | secondary, navy/medium |
| deadline | meta muted |
| price | meta muted |
| bitrix | `BitrixStatus` stub |

---

## Component specs

### `AppShell` / `AppTabs`

- Top bar: product name **Tender Scout** (или «Мониторинг тендеров») в `navy`, 18–20px semibold — brand-level, не мелкий eyebrow.  
- Tabs under bar: text tabs; active = `accent` underline 2px; inactive = `textMuted`.  
- Background page = `surfaceSubtle`; content panels = `surface` where needed.

### `InboxFilters` / command bar ([004](../../delivery/tasks/004-filters-menu.md) · [008](../../delivery/tasks/008-filters-personal-list.md))

**Видимы всегда (ViewCommandBar):**

- outlined **Button + чекбокс** «Непросмотренные» (не Chip);
- `FilterTriggerButton` **«Фильтры»** — только приоритет;
- `FilterTriggerButton` **«Срок подачи»**;
- `FilterTriggerButton` **«Попало к нам»**;
- toggle **Доска | Таблица** (иконка + подпись).

**Внутри меню (паттерн personal `DispatchFilterMenu`):**

- вертикальный список, одна опция = один ряд; Checkbox (приоритет) или Radio (даты);
- **запрещено:** wrapping Chip/pill как пикер опций;
- даты: пресеты [007](../../delivery/tasks/007-date-filters.md); from–to столбиком только при «Свой период»; в bar дат нет;
- сброс — caption-ссылка в том меню, где есть активный фильтр.

**Поиск:** отдельная полная ширина **под** command bar.  
Bitrix-фильтры — out приёмки демо.

### `ViewToggle`

- Segmented control: **Доска** | **Таблица**.  
- Active: personal toggle density; **иконка + текст**.

### `LotCard` / `LotMiniCard` (scout) — Task E accepted · Task F icon

- Border / density / fluid width как personal mini-card; unread = **только** left blurple bar (без текста «новое»).  
- **На доске не показывать** chip приоритета (Горячие/Сильные/Смотреть) — дубль заголовка столбца.  
- Единственный chip на карточке: **«вручную»** если `manual_tier != null`.  
- **`PlatformIcon`** 16–20px в **фиксированном правом рейле** карточки (не в потоке title): колонка ~24px, `flexShrink: 0`, иконка top-aligned; tooltip = `label_ru`; без текста домена и без подписи на рейле.  
- Layout: **слева** (опц. «вручную») → title → customer → **где работать** → срок / НМЦ → «Открыть»; **справа** — только рейл с иконкой. Длина title / чип не двигают иконку ([011](../../delivery/tasks/011-platform-icon-rail.md)).

### `PlatformIcon` — Task F · [011](../../delivery/tasks/011-platform-icon-rail.md)

- Атом: favicon/logo площадки из `source_platform_id` → `app/web/public/platforms/{id}.png`.  
- Display **16–20px**; канон файла **32×32**.  
- На карточке доски: только в **правом рейле** (не в строке title / не рядом с «вручную»).  
- Tooltip / `aria-label`: «Площадка: {name}» (`platform_icon_aria`). На рейле подписи нет.  
- On broken image: initials placeholder (не ломает карточку).  
- Реестр: [`../platforms.md`](../platforms.md).

### `LotTable` / `LotTableRow`

- Columns: ●/unread | **Площадка** (`PlatformIcon`) | **Приоритет** (chip/label) | Название | Заказчик | Где работать | Срок | НМЦ.  
- Приоритет в таблице **остаётся** (иначе нет сигнала). Optional: suffix «вручную» у приоритета.  
- Bitrix column — out демо.

### `PriorityChip`

- На **доске-карточке:** не использовать для авто-приоритета.  
- В **таблице / drawer header:** Горячие / Сильные / Смотреть; «вручную» — suffix или отдельный quiet chip.  
- Small rounded rect (radius 4–6, **не** pill-full), density.chip.

### `UnreadMarker`

- **Карточка доски:** только left bar (не текст «новое»).  
- **Таблица:** точка/маркер в первой колонке.

### `BitrixStatus`

- Stub: muted text «Скоро» or small quiet badge — **not** error red.  
- Future statuses use success/critical tokens; not in visual must for stub.

### `TenderDetailDrawer`

**Shell (как personal, шире по owner note):**

- Width **`400px`** desktop (personal DrawerShell); `100%` narrow.  
- Column: header (fixed) → body (scroll) → footer (fixed).  
- Close: X, Esc, backdrop.

**Header**

- Title (lot name), PriorityChip, **`PlatformIcon` +** link «На площадке» (external).  
- Customer name large under title (navy).

**Body sections** (order)

1. Ключевые поля — `TenderFieldRow`: НМЦ, срок, регион, статус закупки  
2. Почему подходит — short prose / methods  
3. Контакты — name, phone, email (or empty)  
4. **Документы** — `DocumentsList`

**Footer**

- `FormControlLabel` + **Switch** small (personal): лейбл всегда «Просмотрено»; не filled Chip/Button.  
- Secondary: «Изменить приоритет» (menu: Горячие/Сильные/Смотреть).  
- Primary disabled: «Отправить в Битрикс» + hint «Скоро» — out демо.

### `TenderFieldRow`

- Label `textMuted` 12px; value `text`/`navy` 13–14px.  
- Empty: «—» or copy «Нет данных».  
- Stack gap 12–16px between rows.

### `DocumentsList`

- Section title «Документы».  
- Empty-not-downloaded: one short line + muted (copy).  
- Populated: list rows — **`FileTypeIcon` 16–18px** (цвет по расширению) + file name + size optional + «Скачать».  
- Иконка: компактный бейдж (PDF/DOC/XLS/IMG/ZIP), не крупный MUI glyph.  
- No fake card gallery; simple list.

### `TechRunPanel` family

- Denser, still light theme (not AS-IS dark).  
- `TechPhaseBar`: phase label + progress text (`собрано N / 1000`).  
- `TechCounters`: L1 / L2 / L3 / noise as plain metrics — ok to show codes here.  
- `TechLog`: monospace 12px, error lines `#C62828`.  
- `RunPathCopy`: path in readonly field + button.  
- `RunControls`: Start = accent filled; Stop = outline critical/muted.

### Empty / error

- Centered in list area; one headline + one sentence; no illustration clutter.  
- See copy file for strings.

---

## Anti-patterns

- Purple/blurple gradients  
- Dark mode for Sales Inbox  
- Stats strip / promo chips in first viewport beyond filters  
- Modal dialog instead of drawer for lot detail  
- Showing L1/L2/L3 on Лоты tab  

## Handoff

→ [`sales-inbox-wireframes.md`](./sales-inbox-wireframes.md)
