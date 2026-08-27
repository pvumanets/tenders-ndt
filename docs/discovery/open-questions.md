# Открытые вопросы

**status:** accepted  
**last-review-date:** 2026-08-27  
**решения владельца (простой язык):** [`owner-decisions.md`](./owner-decisions.md)
**owner fill:** [`owner-flight-worksheet-2026-08-12.md`](./owner-flight-worksheet-2026-08-12.md) — **filled**; design P5.0 **accepted** (2026-08-13); runtime lock: [`../delivery/platform-phases.md`](../delivery/platform-phases.md)

| # | Вопрос | Статус |
| --- | --- | --- |
| Q1 | Объём прогона | **amended 2026-08-27** — **без лимита 1000**; только открытые (срок ≥ сегодня); ~30–60 на запрос. Lock: [`owner-decisions.md`](./owner-decisions.md) · [`search-keywords.md`](./search-keywords.md) |
| Q2 | Вторые запросы (РК, ВИК, …) | **amended 2026-08-27** — строки в `queries[]`; целевые сиды = уровни **A–E** ([`search-keywords.md`](./search-keywords.md)); AS-IS seed «неразрушающий» — до sync кода |
| Q27 | Прошлое / закрытые в пуле | **closed** — не ищем; P1 = Приём заявок + срок ≥ сегодня МСК ([019](../delivery/tasks/019-open-upcoming-only.md)) |
| Q3 | Капча / без ввода владельцем | **closed** — cookies-файл площадки |
| Q4 | UI vs API/Bitrix | **closed** — UI; Bitrix API out; в демо Bitrix **не** в приёмке |
| Q5 | Частота | **closed** — разово до P7; **NEXT+** — cron (Q16) |
| Q6 | Consumer кроме выгрузки | **closed** — Sales Inbox + Tech из **Postgres**; Bitrix — later |
| Q7 | Предфильтр региона/НМЦ | **closed** — вся РФ |
| Q8 | Docs download | **amended 2026-08-27 / P12** — демо **must**; том + `DOWNLOAD_DOCS` для лотов **на доске** (`tier ∈ {L1,L2,L3}`). AS-IS код до 029: score ≥ 4 |
| Q9 | Где код / runtime | **closed** — **VPS + Docker** (прод); ПК = тот же compose (дев); Cursor не runner |
| Q10 | Уровни fit | **closed** — L1/L2/L3 в engine; карточки только у них |
| Q11 | Ярлыки sales-UI | **closed** — Горячие / Сильные / Смотреть |
| Q12 | Непросмотренные | **amended 2026-08-27 / P12** — must; пул **L1+L2+L3** на доске (Горячие / Сильные / **Смотреть** системой); `lot_state` в Postgres. Канон API синхронизирован ([032](../delivery/tasks/032-api-canon-sync.md)); код 028/029 |
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
| Q28 | Повторный прогон — трогаем карточку? | **closed 2026-08-27** — **обновляем**, если на площадке изменились данные (срок, цена, текст, документы); «просмотрено» и ручной приоритет не сбрасываем. [`owner-decisions.md`](./owner-decisions.md) |
| Q29 | ИИ когда? | **closed 2026-08-27** — **отдельный шаг** после прогона по правилам; раздел «Разобрано с помощью ИИ»; журнал ошибок. Не при каждой загрузке. [`ai-tier-review.md`](../delivery/ai-tier-review.md) |
| Q30 | Ключевые слова поиска | **closed 2026-08-27** — канон фраз и уровни A–C в [`search-keywords.md`](./search-keywords.md); D только в правилах |
| Q31 | Порядок запросов | **closed 2026-08-27** — несколько именованных поисков; **сначала длинные/точные, потом короткие**; без лимита 1000 |
| Q32 | Страховка широкими query | **closed 2026-08-27** — пакет E («контроль сварн», «диагностирование»…); мусор чистит ИИ. [`owner-decisions.md`](./owner-decisions.md) |
| Q33 | Wipe после 027–029 | **closed 2026-08-27** — **всё**: lots + lot_state + documents + том docs; без экспорта triage. [`inbox-lifecycle.md`](./inbox-lifecycle.md) |
| Q34 | Усечения в keywords | **closed 2026-08-27** — `дефект.`, `нераз.`, `ультр.` и т.п. **вместе** с полными словами |
| Q35 | Четыре контроля в поиске | **closed 2026-08-27** — принимающий / приёмочный / входной / строительный — пакет D в очереди |

Закрытые ответы отражены в [`../delivery/`](../delivery/) (tech-architecture, sales-inbox-api, platform-phases, acceptance). Lock 2026-08-27 + P12 ([032](../delivery/tasks/032-api-canon-sync.md)): accepted API = целевой контракт; AS-IS runtime score≥4 / limit 1000 до кода 028/029/030.
