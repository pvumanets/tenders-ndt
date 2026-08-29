# Зонд Росэлторг — www (сводный поиск)

**status:** ship ready for adapter  
**date:** 2026-08-29  
**ship:** as-is · адаптер [043](../delivery/tasks/043-roseltorg-www.md)  
**slug:** `roseltorg` ([platforms.md](./platforms.md))  
**cookies (файл, не этот md):** `./cookies.roseltorg.txt` · `ROSELTORG_COOKIES_FILE`  
**auth-правила:** [`../delivery/auth-cookies.md`](../delivery/auth-cookies.md)

Живой зонд 2026-08-29: сводный **«Поиск закупок»** на `https://www.roseltorg.ru/procedures/search` (владелец залогинен в ЛК). Сырьё — `runs/_probe/roseltorg-www/` (gitignore). Значения cookie / JWT **не** в этот md.

**CORP (`corp.roseltorg.ru` + ELK Bearer)** — retired (040). ATOM/COM в CORP API не находятся.

Кейс владельца: `ATOM28082600172` (капиллярный контроль, мониторинг цен, Железногорск) — есть в www-поиске по `капиллярный контроль`, нет в CORP.

---

## Факт / гипотеза / пробел

| Тег | Утверждение |
| --- | --- |
| **fact** | Список: `GET /procedures/search?sale=1&query_field=…&status[]=5&status[]=0&status[]=1&currency=all&page=N` (page 0-based). |
| **fact** | Карточки: `.js-etp-procedure-grid-item` + `data-feature-favorite-lots-procedure-number` (ATOM… / COM… / …). |
| **fact** | Страница лота: `/procedure/{id}/1` — этапы («Приём заявок до DD.MM.YY»), блок `#documents` / `.lot-docs__list`. |
| **fact** | Документы COM и др.: ссылки `https://{section}.roseltorg.ru/file/get/t/LotDocuments|ProcedureDocuments/id/…`. |
| **fact** | У части ATOM на агрегаторe сейчас «Документов пока нет» — файлы живут в секции atom2; www пустой. |
| **fact** | Список открывается и без cookies; канон worker = Netscape jar (единый паттерн + скачивание). |
| **fact** | Twin: № процедуры на РосТендере («Участие» / ATOM…) = ключ; Росэлторг главный → rostender `board_hidden`. |
| **gap** | Надёжный скачивание вложений ATOM с atom2 без аккредитации секции (ExtJS). Пока — links с www, когда появятся. |

---

## Стек площадки

```text
cookies.roseltorg.txt
  → GET www.../procedures/search?query_field=…&status[]=…&page=
  → GET www.../procedure/{NATIVE}/1
  → doc_links (.lot-docs__list a[href*=file/get])
  → download_inbox_docs (DOWNLOAD_DOCS=1)
```

Адаптер = httpx HTML (`app/worker/roseltorg.py`), не Playwright, не CORP JSON.

---

## Почему не CORP

| | CORP (040, retired) | www (043) |
| --- | --- | --- |
| Хост | corp.roseltorg.ru | www.roseltorg.ru |
| Auth | ELK Bearer `platform_223_corp` | Netscape cookies |
| Охват | 223 CORP MSP | сводный (ATOM, COM, KIM, …) |
| Docs | out of scope | `.lot-docs` + file/get |

---

## Адаптер

Таск [043](../delivery/tasks/043-roseltorg-www.md): worker + runner + twin hide + docs. Ingest `source_platform_id=roseltorg`, `tender_id=roseltorg:{NATIVE}`.

## Out of scope зонда

- Playwright  
- Полный atom2 ExtJS API без аккредитации  
- B2B / OilB2B / Северсталь  
