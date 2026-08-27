# Фазы разработки NEXT+ (после P7)

**status:** draft  
**last-review-date:** 2026-08-27  
**решения владельца:** [`../discovery/owner-decisions.md`](../discovery/owner-decisions.md)  
**уже сделано:** [`code-phases.md`](./code-phases.md) · [`platform-phases.md`](./platform-phases.md) (P0–P7 **done**; 022–026 **done**)  
**таски:** [`tasks/README.md`](./tasks/README.md)  
**ревью рисков:** [`../discovery/decision-risks-review.md`](../discovery/decision-risks-review.md)

Этот файл — **как строим дальше**. Не код. Не перескакивать фазы без owner OK.

---

## Зачем отдельный документ

Платформа (P5.1–P7) и поиски (023/024) уже на проде. Lock 2026-08-27 изменил продукт: доска L1–L3, обновление карточек, без лимита 1000, широкие keywords, ИИ отдельным шагом, wipe всего.

Задач **027–029 мало**: без сидов A–E и hardening скрейпа после wipe снова «один запрос неразрушающий» и тихие пропуски.

---

## Обзор фаз

| Фаза | Название (просто) | Статус | Задача |
| --- | --- | --- | --- |
| **P8** | Доска: просрочка и архив | **done** | [027](./tasks/027-expired-column.md) |
| **P9** | Прогон: уже был / обновлено | **done** | [028](./tasks/028-run-idempotent-report.md) |
| **P10** | Тиры + ИИ отдельным шагом | **done** | [029](./tasks/029-tier-rules-and-ai.md) |
| **P11** | Покрытие поиска (сиды + без лимита) | **done** | [030](./tasks/030-search-coverage.md) |
| **P12** | Синхрон канона API с lock | **done** | [032](./tasks/032-api-canon-sync.md) |
| **P13** | Wipe прода + чистый прогон | backlog | ops после P8–P11 на `main` |
| **P14** | Укрепление скрейпа | backlog | [031](./tasks/031-scrape-hardening.md) |
| **P15+** | Дальний хвост | backlog | cron, ЭТП, Bitrix, роли, Excel |

```text
P12 (канон API)
  → P8 (027) → P9 (028) → P10 (029)
                 ↘         ↗
                   P11 (030)
                         ↓
                    P13 wipe + полный прогон
                         ↓
                    P14 (031)
                         ↓
                    P15+ …
```

### Жёсткие правила

1. Код **027 → 028 → 029** — **по одному PR**, не одним комком.
2. **P11 (сиды A–E) до wipe-прогона** — иначе чистый прогон снова узкий.
3. **P12** — **done** ([032](./tasks/032-api-canon-sync.md)); accepted API = lock. Код P9/P10 читает новый канон (не score≥4).
4. **P14** не блокирует первый чистый прогон, но нужен, чтобы **не пропускать лоты молча**.
5. Деплой на VPS — только после merge в `main` (`vps-bootstrap.py --deploy`).

---

## Узкие места, которые ещё болят (G1–G5)

| ID | Узкое место | Закрываем в |
| --- | --- | --- |
| **G1** | В коде: один query + лимит 1000; Tender.Pro не в очереди | **P11 done** |
| **G2** | Accepted API: score≥4, всегда UPDATE | **P12 done** (docs); код P9/P10 |
| **G3** | Скачивание документов только score≥4 → «Смотреть» без файлов | **P10** |
| **G4** | Title-only score; обрыв пагинации; cookies «файл есть»; нет retry; soft-stop пустой | **P14** |
| **G5** | `platforms.md`: tender-pro ещё «backlog» при 024 done | **P11 done** |

Подробности: [`decision-risks-review.md`](../discovery/decision-risks-review.md). Закрытые lock’ами M1/M3/M5 — там же.

---

## P8 — Доска: просрочка и архив

**Цель:** четвёртая колонка «Просроченные»; живые колонки без протухших.

| | |
| --- | --- |
| **Статус** | **done** (2026-08-27) — [027](./tasks/027-expired-column.md) |
| **Вход** | Lock lifecycle; доска L1–L3 ещё может быть на старом фильтре score≥4 |
| **Выход / Done** | Колонка справа; бейдж «Срок подачи вышел»; архив `board_hidden`; правило даты МСК **read-time** |
| **Задача** | [027](./tasks/027-expired-column.md) |
| **Риски** | S8 закрыт read-time (без cron) |
| **Out** | ИИ; сиды; wipe |

---

## P9 — Прогон: уже был / обновлено

**Цель:** повторный Старт не плодит копии; при изменениях на площадке — обновляем карточку; triage не сбрасываем.

| | |
| --- | --- |
| **Статус** | **done** (2026-08-27) — [028](./tasks/028-run-idempotent-report.md) |
| **Вход** | P8 желателен (счётчик «Ушли в просроченные»); **P12** контракт ingest |
| **Выход / Done** | Diff: без изменений → «Уже были»; с diff → «Обновлено с площадки»; `viewed` / ручной приоритет / AI-флаги живы; Tech — четыре полные фразы; `GET /api/status.run_report` |
| **Задача** | [028](./tasks/028-run-idempotent-report.md) |
| **Риски** | Пул доски ещё score≥4 до P10 |
| **Out** | ИИ; keywords |

---

## P10 — Тиры + ИИ отдельным шагом

**Цель:** правила кладут L1/L2/L3 на доску; ИИ — кнопка «Разобрать с ИИ»; мусор страховки не в Горячих.

| | |
| --- | --- |
| **Статус** | **done** (2026-08-27) — [029](./tasks/029-tier-rules-and-ai.md) |
| **Вход** | fit-tiers + ai-tier-review; P9 стабилен |
| **Выход / Done** | Ingest/inbox/docs по `tier ∈ {L1,L2,L3}`; поставка→L3; Inbox AI + фильтр + `ai_error`; Tech `ai_failures`; эталоны unit/mock |
| **Задача** | [029](./tasks/029-tier-rules-and-ai.md) |
| **Риски** | Без P11 широкий мусор E ещё не в выдаче |
| **Out** | Сиды A–E; снятие limit (это P11) |

---

## P11 — Покрытие поиска

**Цель:** искать по канону A–E; без потолка 1000; Tender.Pro в очереди (если cookies ок).

| | |
| --- | --- |
| **Статус** | **done** (2026-08-27) — [030](./tasks/030-search-coverage.md) |
| **Вход** | [`search-keywords.md`](../discovery/search-keywords.md); можно после P9 (форма API поисков) |
| **Выход / Done** | `limit_n` снят в продукте/коде; сиды rostender A–E + TP пакеты; `in_queue` для TP при валидных cookies; `platforms.md` tender-pro ≠ backlog |
| **Задача** | [030](./tasks/030-search-coverage.md) |
| **Риски** | Страховка E → много шума (ожидаемо; чистит ИИ в P10) |
| **Out** | Re-score / retry (P14) |

**Обязательно до P13.**

---

## P12 — Синхрон канона API

**Цель:** accepted-доки совпадают с owner-decisions, чтобы код не гадал.

| | |
| --- | --- |
| **Статус** | **done** (2026-08-27) — [032](./tasks/032-api-canon-sync.md) |
| **Вход** | Lock 2026-08-27 |
| **Выход / Done** | Обновлены [`sales-inbox-api.md`](./sales-inbox-api.md) (пул tier L1–L3; ingest update-on-diff; без обязательного limit 1000); Q8/Q12; ADR; `platform-phases` целевой пул |
| **Задача** | [032](./tasks/032-api-canon-sync.md) docs-only |
| **Риски** | Пропуск был бы G2 — закрыт на стороне docs; код догоняет в 028/029 |
| **Out** | Реализация worker |

---

## P13 — Wipe прода + чистый прогон

**Цель:** снести кривые старые карточки; набрать заново широкой сетью.

| | |
| --- | --- |
| **Вход** | P8–P11 **на `main` и задеплоены**; cookies площадок живые |
| **Выход / Done** | Снесены `lots` + `lot_state` + `documents` + том `docs/`; полный Старт очереди A–E (+ TP); отчёт Tech с счётчиками; доска осмысленна |
| **Задача** | ops (описание в [`inbox-lifecycle.md`](../discovery/inbox-lifecycle.md)); команда — в execute-плане кода, не здесь |
| **Риски** | Wipe без P11 = снова узкая сеть |
| **Out** | Точечный «починить старые тиры» |

---

## P14 — Укрепление скрейпа

**Цель:** меньше **тихих** пропусков после того, как доска уже живёт.

| | |
| --- | --- |
| **Вход** | Чистый прогон после P13 желателен (есть baseline) |
| **Выход / Done** | Re-score после карточки/товаров; пагинация не ломается на пустой filtered page; probe cookies / overall `partial`; HTTP retry 429/5xx; soft-stop сохраняет scored≥порог |
| **Задача** | [031](./tasks/031-scrape-hardening.md) |
| **Риски** | Сложность vs ценность — не блокирует P13 |
| **Out** | Новые ЭТП |

---

## P15+ — Дальний хвост

Не детализируем здесь:

- Полный cron прогонов (не только суточная просрочка)
- Остальные ЭТП (СИБУР, OnlineContract, …)
- Bitrix leads
- Роли
- Excel-вкладка

См. хвост в [`platform-phases.md`](./platform-phases.md).

---

## Что уже сделано (чтобы не путать)

| Блок | Статус |
| --- | --- |
| P0–P7 платформа + HTTPS | **done** |
| Tech Start/Stop, поиски, Tender.Pro adapter, customer_name, drawer поиска | **022–026 done** |
| Discovery lock 2026-08-27 | **docs done** |
| P12 канон API | **done** ([032](./tasks/032-api-canon-sync.md)) |
| P8 просрочка + архив | **done** ([027](./tasks/027-expired-column.md)) |
| P9 update-on-diff + Tech отчёт | **done** ([028](./tasks/028-run-idempotent-report.md)) |
| P10 тиры + ИИ | **done** ([029](./tasks/029-tier-rules-and-ai.md)) |
| P11 сиды A–E + без limit 1000 | **done** ([030](./tasks/030-search-coverage.md)); дальше P13 wipe |

---

## Acceptance документа

- [x] Фазы P8–P14 с целями и зависимостями
- [x] Узкие места G1–G5 привязаны к фазам
- [x] Задачи 027–031 связаны
- [ ] Owner: статус `accepted` после прочтения

## Owner must (не код)

- Прочитать [`owner-decisions.md`](../discovery/owner-decisions.md)
- Дать OK на порядок P8→…→P14 (или поправить)
- Перед P13: свежие cookies rostender (+ Tender.Pro если в очереди)
- `PROVOD_API_KEY` в `.env` / VPS `--sync` перед живым ИИ (P10)
