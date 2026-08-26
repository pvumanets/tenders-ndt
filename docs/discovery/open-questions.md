# Открытые вопросы

**status:** accepted  
**last-review-date:** 2026-08-19  
**owner fill:** [`owner-flight-worksheet-2026-08-12.md`](./owner-flight-worksheet-2026-08-12.md) — **filled**; design P5.0 **accepted** (2026-08-13); runtime lock: [`../delivery/platform-phases.md`](../delivery/platform-phases.md)

| # | Вопрос | Статус |
| --- | --- | --- |
| Q1 | Объём прогона | **closed** — пул 1000 + fit L1–L3 ([fit-tiers](../delivery/fit-tiers.md)) |
| Q2 | Вторые запросы (РК, ВИК, …) | **closed** — строки запроса живут в именованном поиске (`queries[]`); сид rostender = «неразрушающий»; Tender.Pro сид = ВИК/ПВК/УЗК/РК ([named-searches](./named-searches.md)) |
| Q27 | Прошлое / закрытые в пуле | **closed** — не ищем; P1 = Приём заявок + срок ≥ сегодня МСК ([019](../delivery/tasks/019-open-upcoming-only.md)) |
| Q3 | Капча / без ввода владельцем | **closed** — cookies-файл площадки |
| Q4 | UI vs API/Bitrix | **closed** — UI; Bitrix API out; в демо Bitrix **не** в приёмке |
| Q5 | Частота | **closed** — разово до P7; **NEXT+** — cron (Q16) |
| Q6 | Consumer кроме выгрузки | **closed** — Sales Inbox + Tech из **Postgres**; Bitrix — later |
| Q7 | Предфильтр региона/НМЦ | **closed** — вся РФ |
| Q8 | Docs download | **closed** — демо **must**; том + `DOWNLOAD_DOCS` для **score ≥ 4** (P5.5) |
| Q9 | Где код / runtime | **closed** — **VPS + Docker** (прод); ПК = тот же compose (дев); Cursor не runner |
| Q10 | Уровни fit | **closed** — L1/L2/L3 в engine; карточки только у них |
| Q11 | Ярлыки sales-UI | **closed** — Горячие / Сильные / Смотреть |
| Q12 | Непросмотренные | **closed** — must; пул **score ≥ 4**; `lot_state` в Postgres |
| Q13 | Ручная смена приоритета | **closed** — must; L1/L2/L3 + «вручную»; сброс к движку; тот же `lot_state` |
| Q14 | Bitrix в UI | **closed** — не в демо; default responsible когда API = **N071** |
| Q15 | Excel / CSV daily | **closed** — не daily; вкладка Excel = **NEXT+** |
| Q16 | Cron + 10–12 площадок | **split:** cron / роли / остальные ЭТП — NEXT+. Именованные поиски + очередь — [023](../delivery/tasks/023-named-searches.md); первый чужой адаптер Tender.Pro — [024](../delivery/tasks/024-tender-pro-adapter.md). Lock: [`named-searches.md`](./named-searches.md). СИБУР / OnlineContract — зонды, кода нет |
| Q17 | Визуал | **closed** — personal kit (blurple); P5.0 accepted |
| Q18 | Вид списка | **closed** — Карточки / Таблица |
| Q19 | Панель деталей | **closed** — personal drawer (mock ~400px) |
| Q20 | Docker | **closed** — **P5.1** (не откладывать после UI) |
| Q21 | Темп | **closed** — канон фаз → код по [`../delivery/platform-phases.md`](../delivery/platform-phases.md) |
| Q22 | VPS + доступ директора | **closed** — VPS **в ship** (P7); две учётки без ролей; HTTPS; роли/multi-tenant = NEXT+ |
| Q23 | Фильтры дат | **closed** — must: срок подачи + `ingested_at`; пресеты в UI |
| Q24 | GPT / LLM для скрейпа | **closed** — **не нужен**; worker = httpx + cookies |
| Q25 | Tech Start/Stop в React | **closed** — кнопки в Tech ([022](../delivery/tasks/022-tech-start-stop.md) **done**). Query/limit **не** на кнопке: после 023 — в карточке именованного поиска; Старт читает очередь `in_queue` |
| Q26 | Экран входа | **closed** — must P5.2; Scout login ≠ rostender cookies |

Закрытые ответы отражены в [`../delivery/`](../delivery/) (tech-architecture, sales-inbox-api, platform-phases, acceptance).
