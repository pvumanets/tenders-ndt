# Owner flight worksheet — Sales Inbox (~40 мин)

**status:** filled (исторический полёт 2026-08-12)  
**date:** 2026-08-12  
**superseded runtime:** 2026-08-13 — VPS+Docker+Postgres+логин, см. [`../delivery/platform-phases.md`](../delivery/platform-phases.md). Ниже текст полёта **не** править; Q9/Q22 в [`open-questions.md`](./open-questions.md) уже новые.

**цель (было):** в полёте прогнать design-пакет и закрыть дыры.  
**офлайн:** этот файл.  
**не решать заново:** Q1 пул 1000, Q3 cookies, Q5 разово, Q7 вся РФ, Q10 L1–L3, Q11 ярлыки, Q15 Excel не daily, Q20 P6 отложен.

```text
Таймер: 3 + 12 + 8 + 8 + 6 + 3 ≈ 40 мин
Роли: Doc → Designer+PM → UX writer → Architect → PM+Bitrix → PM demo
```

---

## 0. Как пользоваться (3 мин) — Doc

- [x] Прочитал шапку и «не решать заново»
- [x] Понял: сейчас только docs/дизайн; HTML/React после accept

---

## 1. Gate приёмки design-пакета (12 мин) — Designer + PM

### 1.1 Чеклист gate

- [x] Вкладки **Лоты** (default) / **Прогон**
- [x] Переключатель **Карточки / Таблица**
- [ ] Правый overlay-drawer ~380–400px → **note:** шире → канон **520px**
- [x] Секция **Документы**
- [x] Bitrix **«Скоро»**
- [x] Каталог + спеки + wireframes + copy
- [x] Accent teal `#0F766E`

### 1.2 IA

| # | Утверждение | Вердикт |
| --- | --- | --- |
| A | Default «Лоты» | ок |
| B | Непросмотренные + **даты** (срок / попало к нам) | правка → must в каноне |
| C | Без L1 в sales-UI | ок |
| D | Viewed/override между сессиями | **must** (уточнено post-flight) |
| E | Excel не daily | ок; вкладка Excel = NEXT+ |

**Визуал:** drawer шире → **520px**; иконки важны.

---

## 2. Микрокопия (8 мин) — UX writer

Строки product/chips/Bitrix/empty/docs/session — **ок**. Note: иконка + подпись.

---

## 3. Хранение (8 мин) — Architect

- Storage preference в полёте: VPS — **переопределено:** ship A = localhost local JSON; VPS = NEXT+.
- Порядок API → React — **согласен**.
- P6 отложить — **да**.

---

## 4. Bitrix (6 мин)

- Default responsible: **N071**
- Dedup: architect после демо
- API: не сейчас
- Q16 backlog ok; Q2 после первого run

---

## 5. Демо директора

Три сценария — готово (верно). Cut: Auth/ЭЦП out; также out NEXT: Bitrix API, DOWNLOAD_DOCS worker, cron (подтверждено post-flight).

---

## 6. Вердикт

- [x] **accepted with notes**

Notes (зафиксированы в каноне):

```
1. Drawer 520px; icon+label; фильтры срок подачи + ingested_at
2. Viewed/override must; ship A = local JSON на одном ПК
3. VPS+шаринг = NEXT+ после демо; Bitrix API не сейчас; default N071
```

**После посадки (done):** notes → `accepted-with-notes` → architect packet.

Имя / дата: Уманец Павел / 2026-08-12 (flight + post-flight answers)

---

## Architect lock (post-flight, 2026-08-12)

Владелец уточнил после flight (канон в delivery):

- Inbox / непросмотренные: **score ≥ 4** по всем `runs/`
- State: JSON **на каждый прогон**
- Документы с файлами — **must** на демо
- **P6 Docker → P7 React** (отмена «P6 отложить» из §3)
- Tech Start/Stop в UI — later; Bitrix не в приёмке демо
- NEXT+: VPS/multi-user + cron

## Handoff (done)

Discovery **accepted**. Architect packet в `docs/delivery/` (tech-architecture, sales-inbox-api, code-phases, acceptance). Следующий запрос владельца: **реализация P5.1+**.
