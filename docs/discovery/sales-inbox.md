# Sales Inbox — продукт NEXT (discovery)

**status:** accepted  
**last-review-date:** 2026-08-19  
**платформа / фазы хвоста:** [`../delivery/platform-phases.md`](../delivery/platform-phases.md)  
**brief:** [`product-brief.md`](./product-brief.md)  
**AS-IS UI:** [`../delivery/operator-ui.md`](../delivery/operator-ui.md)  
**TO-BE API:** [`../delivery/sales-inbox-api.md`](../delivery/sales-inbox-api.md)  
**Bitrix:** [`../company/bitrix-and-leads.md`](../company/bitrix-and-leads.md)  
**Fit engine:** [`../delivery/fit-tiers.md`](../delivery/fit-tiers.md)  
**Design package:** [`design/`](./design/) — components → specs → wireframes → copy  
**Flight worksheet:** [`owner-flight-worksheet-2026-08-12.md`](./owner-flight-worksheet-2026-08-12.md)

---

## Problem

Техпанель MVP не объясняет продукт продажам: жаргон L1, лог, пути файлов. Нужен экран, где за минуту видны **новые непросмотренные сильные** лоты и ключевые поля заказчика.

## Users / JTBD

| Кто | Job |
| --- | --- |
| **Директор** (первый пользователь NEXT), продажи | Когда появились лоты после прогона, хочу сразу увидеть непросмотренные высокоприоритетные и понять фирму/суть — чтобы решить звонить / вести дальше |
| Digital | Когда сомневаюсь в прогоне, хочу на **отдельной** вкладке увидеть фазу, cookies, путь `runs/` — без смешивания с sales-workflow |

## Owner decisions (2026-08-12 + lock 2026-08-13)

| Тема | Решение | Tag |
| --- | --- | --- |
| Первый пользователь | Директор; digital — дев-стенд | fact |
| Design gate | P5.0 visual **accepted** целиком (2026-08-13) | fact |
| Пул inbox / непросмотренные | Лоты с **score ≥ 4** (L1∪L2); авто-L3 не в списке | fact |
| Список | Переключатель **Карточки / Таблица** | fact |
| Детали | Правый overlay-drawer (personal shell ~400px в mock; product note 520px) | fact |
| Документы | Имена **и файлы** на демо — **must** (`DOWNLOAD_DOCS` для score≥4) | fact |
| Bitrix в демо | **Не требуется**; API — out | fact |
| Bitrix default responsible (когда API) | **N071** | fact |
| Просмотренность | **must**; ключ `tender_id`; глобально | fact |
| Ручная смена приоритета | **must**; L1/L2/L3 + «вручную»; сброс к движку | fact |
| Storage | **Postgres** (`lots` + `lot_state`); не `operator-state.json` | fact |
| Runtime | **VPS + Docker** (прод); ПК = тот же compose (дев) | fact |
| Вход | две учётки, без ролей, один inbox; HTTPS на P7 | fact |
| Cron / роли / Excel-вкладка | NEXT+ | fact |
| Именованные поиски + очередь | lock 2026-08-19; код [023](../delivery/tasks/023-named-searches.md) / [024](../delivery/tasks/024-tender-pro-adapter.md) | fact |
| Порядок кода | [`../delivery/platform-phases.md`](../delivery/platform-phases.md) P5.1→P7 | fact |
| Фильтры дат | must: **срок подачи** + **`ingested_at`** (пресеты в UI) | fact |
| Tech вкладка | Статус + Старт/Стоп + поиски/очередь (**023 done**) | fact |

## Facts / Hypotheses / Gaps

| Claim | Tag |
| --- | --- |
| Без L1-жаргона в sales-UI; фильтры Горячие/Сильные; Смотреть — ручной приоритет | fact |
| Excel не daily path | fact |
| Visual SoT = скопированный kit `ndt-personal` (blurple, BoardColumn, mini-card) | fact |
| Tasks 004/005/007/008 | Toolbar: FilterTrigger + вертикальный список; даты отдельными меню; карточка без chip приоритета/«новое» | fact |
| Иконка + подпись на ключевых действиях | fact |
| REST `/api/inbox/*` из Postgres + `/api/auth/*` | fact → [`../delivery/sales-inbox-api.md`](../delivery/sales-inbox-api.md) |
| Cron / роли / остальные ЭТП | backlog NEXT+ |
| Поиски + Tender.Pro | [named-searches.md](./named-searches.md); код 023/024 |
| Реальный Bitrix API | out этого ship |

## Information architecture

Две вкладки одного приложения (default = **Лоты**). Третья вкладка Excel — **не** в ship A.

### Вкладка «Лоты» (Sales Inbox)

1. **Фильтры + поиск**  
   - Непросмотренные  
   - Приоритет: Горячие / Сильные / Смотреть (map на L1/L2/L3; Смотреть в основном после ручной смены)  
   - **Срок подачи** (filter/sort)  
   - **Попало к нам** (`ingested_at`)  
   - Текстовый поиск (название, заказчик, id)  
   - Bitrix-фильтр — **не** в приёмке демо  
2. **Переключатель вида** — **Карточки** | **Таблица** (иконка + подпись).  
3. **Список** — приоритет-чип, непросмотрен, название, фирма, срок/НМЦ.  
4. **Детали** — правый drawer **520px**:  
   - Название, ссылка на площадку  
   - Заказчик (фирма) — акцент  
   - НМЦ, срок, регион  
   - Почему подходит  
   - Контакты  
   - **Документы** (имена + скачивание файлов)  
   - Footer (иконка+подпись): просмотрено; изменить приоритет

### Вкладка «Прогон» (Tech)

- Фаза, прогресс, cookies площадки OK/expired, счётчики L1–L3, идентификатор/путь выгрузки.  
- Старт / Стоп (022 **done**). Query/limit — не на кнопке: именованные поиски + очередь на этой же вкладке ([023](../delivery/tasks/023-named-searches.md), [`named-searches.md`](./named-searches.md)). Третью вкладку не плодим.

## Mapping engine → UI

| Engine | Sales label |
| --- | --- |
| L1 | Горячие |
| L2 | Сильные |
| L3 | Смотреть |
| noise / pool | не в inbox |
| score &lt; 4 | не в inbox ship A |

Ручная смена приоритета пишет поверх тира движка в `lot_state` (см. API).

## Visual direction

- Светлая тема; accent teal `#0F766E`.  
- Drawer **520px**; icon+label.  
- Спеки: [`design/`](./design/).

## Scope

### In ship (демо директору на VPS)

- Sales Inbox + Tech (статус + Старт/Стоп) по принятому visual  
- Логин двух учёток (без ролей)  
- Просмотренность + ручная смена приоритета (Postgres)  
- Date filters (deadline + ingested_at)  
- DocumentsList **с файлами** (P5.5)  
- Docker на деве и на VPS; HTTPS на P7

### Out / backlog

- Bitrix UI / API в приёмке  
- Cron; СИБУР / OnlineContract / остальные ЭТП кроме Tender.Pro (024)  
- Роли  
- Excel как вкладка / daily UX  
- ЭЦП  
- GPT / LLM API для скрейпа (не нужен)

## Acceptance (product — демо директору)

- [ ] Директор за ≤1 мин видит непросмотренные лоты score≥4 **без** жаргона L1/L2/L3.  
- [ ] В drawer ≤3 с: фирма + ключевые поля; ширина ~520px.  
- [ ] Карточки / Таблица; **документы с файлами**; ручная смена приоритета.  
- [ ] Просмотренность и приоритет переживают перезапуск браузера и контейнера (БД жива).  
- [ ] Фильтры/сорт по сроку подачи и «попало к нам».  
- [x] Вкладка «Прогон» отдельно (статус + Старт/Стоп).  
- [x] Вход по логину; на P7 — HTTPS с другого компьютера.  
- [ ] **Не** требуется: Bitrix, роли.

## Acceptance (design package)

- [x] Каталог / спеки / wireframes / RU-copy  
- [x] Owner design **`accepted-with-notes`** → product **`accepted`**

См. [`design/README.md`](./design/README.md).

## Handoff

```text
Done: P5.0–P7 + поиски/очередь (023)
Now: адаптер Tender.Pro (024)
```

**Стоп кода 024:** не начинать, пока 023 не влит в `main` (или работать поверх `feat/023-named-searches`).
