# Acceptance — прогон и ship

**status:** accepted  
**last-review-date:** 2026-08-13  
**фазы P0–P5.0:** [`code-phases.md`](./code-phases.md)  
**фазы P5.1–P7:** [`platform-phases.md`](./platform-phases.md)  
**inbox API:** [`sales-inbox-api.md`](./sales-inbox-api.md)

Прогон / продукт: артефакты (P4) → **visual P5.0 accepted** → platform (Postgres, auth, ingest, inbox, docs) → wire → **VPS+TLS**.

---

## Must (P5.0 — визуальный Sales Inbox на моках) ✅

Owner 2026-08-13: **дизайн ок целиком**.

- [x] `npm run dev` в `app/web` открывает светлый Sales Inbox
- [x] Вкладки **Лоты** (default) / **Прогон**
- [x] Фильтры: непросмотренные; Горячие/Сильные/Смотреть; срок; «попало к нам»; поиск
- [x] Доска Горячие / Сильные / Смотреть + вид Таблица
- [x] Toolbar: **Непросмотренные** (кнопка+чекбокс) + отдельные меню; поиск full-width
- [x] На карточке нет chip приоритета и «новое»; unread = left bar
- [x] Колонки доски **fluid**
- [x] **Где работать** (`location`)
- [x] Drawer personal shell: фирма, поля, документы из мока, просмотрено, приоритет
- [x] Visual = vendored personal; Tech read-only; без Bitrix
- [x] **Owner gate:** «дизайн ок»

### UI backlog P5.0

См. [`tasks/README.md`](./tasks/) — 001–011 **done**.

---

## Must (артефакты, с P4)

- [x] Сессия площадки через cookies; владелец не вводил капчу/логин mid-run
- [x] Поиск `неразрушающий`, «сначала новые», только **приём заявок**, срок ≥ сегодня МСК
- [x] Пул до **1000** лотов в реестре
- [x] `tenders.md` + табличный реестр с колонкой `tier`
- [x] Есть **`priority-fit.md`** с секциями L1 / L2 / L3
- [x] Карточки открывались **только** для L1–L3
- [ ] УЗК/УК как услуга не отброшены
- [ ] Приборы → `noise`
- [ ] Cookies / `.env` / пароли Scout не в git и не в MD

## Must (P5.1 — platform) ✅

- [x] `docker compose` на ПК поднимает Postgres + api
- [x] миграции создают таблицы канона
- [x] bootstrap двух учёток из env (пароли не в логах)

## Must (P5.2 — вход) ✅

- [x] login / logout / me
- [x] без сессии inbox и status — 401
- [x] экран входа (personal kit, RU)

## Must (P5.3 — ingest) ✅

- [x] конец прогона upsert в `lots` / `runs`
- [x] выгрузка P4 на томе сохраняется
- [x] повторный ingest не затирает `lot_state`

## Must (P5.4 — inbox API) ✅

- [x] `GET /api/inbox` только **score ≥ 4** из Postgres
- [x] viewed и manual_tier переживают перезапуск api
- [x] сброс приоритета (`tier: null`) возвращает оценку движка
- [x] поля списка включают `location`, `source_platform_id`, `url`

## Must (P5.5 — документы) ✅

- [x] Для score ≥ 4 файлы на томе `docs/{tender_id}/`
- [x] `GET /api/inbox/{id}/documents` + скачивание за сессией
- [x] При `DOWNLOAD_DOCS=0` новые файлы не качаются

## Must (P6 — wire) ✅

- [x] React без mock как источника списка
- [x] тот же inbox, что P5.0

## Must (P7 — демо директору на VPS)

- [x] HTTPS (валидный сертификат); домен `tenders.ndtexam.ru`
- [ ] логин с другого компьютера
- [ ] за ≤1 мин видны **непросмотренные** score≥4 **без** жаргона L1/L2/L3
- [ ] фильтры: непросмотренные; приоритет; срок; ingested; поиск
- [ ] Карточки / Таблица; drawer; фирма; **документы с файлами**
- [ ] отметить просмотренным; сменить приоритет; state в БД
- [ ] вкладка «Прогон» — статус + Старт/Стоп (022)
- [ ] **Не** требуется: Bitrix, cron, Excel-вкладка, роли

## Should

- [ ] У L1–L3 заполнены `fit_reason` и `methods`
- [ ] README прогона: pool / L1 / L2 / L3 / noise
- [ ] Контакты/ИНН с карточек

## Could

- [ ] Excel-листы по уровням
- [ ] Bitrix «Скоро» в UI (не Must)

## Fail

- Капча/логин площадки требуют владельца без стопа с ошибкой
- Нет `priority-fit.md`
- Карточки на весь пул 1000
- Cookies / пароли Scout в git
- Bitrix «заодно»
- Демо без реальных документов при заявленном must
- Пароль директора по HTTP в интернет
- Выкинутый worker / пустой inbox без ingest
