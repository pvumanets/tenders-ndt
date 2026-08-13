# Зонд OnlineContract — onlinecontract.ru

**status:** draft  
**date:** 2026-08-13  
**ship:** backlog / NEXT+ (не текущие фазы P0–P7)  
**slug:** `onlinecontract` ([platforms.md](./platforms.md))  
**ресёрч API:** [`../platform-api-research.md`](../platform-api-research.md) § 3  
**cookies (файл, не этот md):** `./cookies.onlinecontract.txt` · имя переменной `ONLINECONTRACT_COOKIES_FILE`  
**учётка поставщика:** имена `ONLINECONTRACT_USER` / `ONLINECONTRACT_PASSWORD` в `.env` (не в этом файле)  
**auth-правила:** [`../delivery/auth-cookies.md`](../delivery/auth-cookies.md)

Живой HTTP-зонд 2026-08-13 с Netscape-сессией поставщика. **Код адаптера не пишем** до отдельного OK владельца после P7. Playwright для списка **не понадобился**.

---

## Факт / гипотеза / пробел

| Тег | Утверждение |
| --- | --- |
| **fact** | Cookies живые: `GET /otp/Zakupki` 200, в `window.APP_INITIAL_STATE` сессия `id=22938618`, компания ООО «НДТ-КОНСАЛТИНГ». |
| **fact** | Корень сайта — JS SPA («Загрузка приложения…»). Список закупок — Angular OTP (`/otp/assets/app/main.*.js`) + jQuery-оболочка. **Таблицы лотов в первом HTML нет.** |
| **fact** | Список не публичный REST. Грузится `GET /otp/ajaxnotm.php?sid={getProcedureListSID}` (SID из `otp.kzList` в initial state). Ответ JSON: `totalCount=10`, массив `procedureList` из 10 строк. Совпало со скрином поиска «контроль» (в т.ч. id `583187`, тип КЛП). |
| **fact** | Поля строки (фрагмент): `id`, `name`, `type.short`/`type.long`, `published`, `offerStop`, `price` / `startPrice`, `bidCount`, `status`, `owner`, `is223fz`. Даты ISO с офсетом `+03:00`. |
| **fact** | `GET /otp/ajaxnotm.php?sid={exportExcelSID}` → `application/vnd.ms-excel` (xlsx/zip). |
| **fact** | `POST /otp/ajax/TorgList/GetPublicTorg` с `IDA`+`Mode=Ok` — скачивание извещения (blob), **не** список. Без полей — 500 и протокол `1#!#CurTmSet#!#`. |
| **fact** | Карточка `GET /otp/Zakupki/583187` — ~100 КБ HTML, номер в теле есть, `APP_INITIAL_STATE` есть; не JSON. |
| **fact** | Angular `/api/ng/timeStamp`, `/api/feedback/check` отвечают; каталога тендеров там нет. |
| **hypothesis** | Смена поисковой строки — `applyFilterSID` + тело как `kzList.filters` (`SearchName`, `page`, `perpage`, …). Простой GET/POST только `SearchName=неразрушающий` вернул 0 байт. |
| **gap** | Как выставить фильтр «неразрушающий» без заранее сохранённого UI-поиска. Документы на карточке: одна download-ссылка в HTML, дерево файлов не разбиралось. Логин формой не вызывался (cookies хватило). |

---

## Стек площадки

```text
cookies.onlinecontract.txt + Bearer apiToken (из APP_INITIAL_STATE)
  → GET /otp/Zakupki                         # оболочка Angular, kzList.items пустой
  → GET /otp/ajaxnotm.php?sid=getProcedureListSID
        → JSON procedureList[]               # грид
  → GET /otp/Zakupki/{id}                    # карточка HTML
  → GET /otp/ajaxnotm.php?sid=exportExcelSID # xlsx
```

- Хост: `onlinecontract.ru`, раздел **Корпоративные закупки** `/otp/Zakupki`.
- Сессия PHP: `PHPSESSID`, `current_session`, `ONLC_*`.
- ИИ / GPT API **не нужны**.

SID и `apiToken` **сессионные**: каждый прогон читать из HTML, не хардкодить. Values SID/token в этот md **не писать**.

---

## Почему не копировать P1 `list_scrape.py` вслепую

| | РосТендер (as-is) | OnlineContract |
| --- | --- | --- |
| Список | HTML `article.tender-row` | JSON `procedureList` после SID-ajax |
| Поиск | POST формы на rostender | фильтры в `kzList`; смена query в зонде не доказана |
| Сессия | Netscape cookies | cookies **и** Bearer `apiToken` + SID из state |
| Excel | не канон списка | SID export — рабочий xlsx |

Ближе к httpx, чем СИБУР SRM (там POWL/JS-delta). Всё равно отдельный адаптер.

---

## Рецепт адаптера (когда NEXT+)

1. Netscape `cookies.onlinecontract.txt`; при протухании — учётка из `.env` (логин формой не в этом ship).
2. GET `/otp/Zakupki` → вытащить `otp.kzList.getProcedureListSID` и `otp.session.apiToken`.
3. GET `/otp/ajaxnotm.php?sid=…` + `Authorization: Bearer …` + `X-Requested-With: XMLHttpRequest`.
4. Запрос «неразрушающий»: разобрать `applyFilterSID` / `filters.SearchName` (сейчас gap).
5. Карточки `/otp/Zakupki/{id}`; файлы — отдельно.
6. Ingest: `source_platform_id=onlinecontract`; скоринг L1–L3 тот же.

Compose bind и код — **вне** этой заметки.

---

## Cookies и учётка (где лежат)

| Что | Где |
| --- | --- |
| Значения cookie | только `cookies.onlinecontract.txt` (gitignore `cookies*.txt`) |
| Логин/пароль поставщика | только локальный `.env` |
| Имена в env | `ONLINECONTRACT_COOKIES_FILE`, `ONLINECONTRACT_USER`, `ONLINECONTRACT_PASSWORD` (см. `.env.example`) |
| Этот markdown | **запрещены** values, SID, apiToken, пароль |

Имена cookie в дампе (без values): `PHPSESSID`, `current_session`, `ONLC_*`, `session-cookie`, `otpClient`. Также метрика: `_ym_*`, `tmr_*`, `lastEvent_*`.

Не путать со Scout login, `cookies.rostender.txt` и `cookies.sibur.txt`.

---

## Вне скоупа заметки

Код адаптера, bind в Docker, логин-скрипт в репо, смена фаз P0–P7, таск в очереди P6, повторный прогон из агента.
