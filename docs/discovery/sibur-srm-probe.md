# Зонд СИБУР SRM — srm.sibur.ru

**status:** draft  
**date:** 2026-08-13  
**ship:** backlog / NEXT+ (не текущие фазы P0–P7)  
**slug:** `sibur-srm` ([platforms.md](./platforms.md))  
**ресёрч API:** [`../platform-api-research.md`](../platform-api-research.md) § 5  
**cookies (файл, не этот md):** `./cookies.sibur.txt` · имя переменной `SIBUR_COOKIES_FILE`  
**auth-правила:** [`../delivery/auth-cookies.md`](../delivery/auth-cookies.md)

Живой HTTP-зонд 2026-08-13 с Netscape-сессией поставщика. **Код адаптера не пишем** до отдельного OK владельца после P7.

---

## Факт / гипотеза / пробел

| Тег | Утверждение |
| --- | --- |
| **fact** | Cookies открыли NWBC: HTTP 200, приветствие пользователя, меню «Поиск процедур». |
| **fact** | SAP Gateway на контуре **выключен**: `GET /sap/opu/odata/IWFND/CATALOGSERVICE;v=2/ServiceCollection?$format=json` → 500, код `/IWFND/CM_COS/003`, текст «SAP Gateway деактивирован». Публичного OData для мониторинга нет. |
| **fact** | Поиск процедур — Web Dynpro **POWL**, не HTML-таблица rostender-типа. |
| **fact** | Приложение поиска: `APPLID=ZSAPSRM_B_RFXANDAUCTIONS`, `WDCONFIGURATIONID=/SAPSRM/WDA_POWL`, `POWLDELTARENDERING=X`. |
| **fact** | Первый GET POWL = заглушка «Личный рабочий список» (Lightspeed SSR). Грид, «Применить», «Экспорт» в этом HTML нет. Номер процедуры `2138496` / «Строительный контроль» в ответе httpx не появился. |
| **fact** | Playwright Chromium `page.goto` на `/ui2/nwbc/?sap-nwbc-node=0000000037` не дождался `domcontentloaded` за 45 с. |
| **fact** | GET `/ui2/nwbc/?sap-nwbc-node=page_collection` без полного контекста вернул «Выход из системы выполнен успешно» (canvas), SSO-оболочка при этом ещё отвечала 200. |
| **hypothesis** | Кнопка «Экспорт» в UI даст Excel/CSV проще, чем разбор WDA-delta. Не проверено. |
| **gap** | Карточка процедуры и модалка «Документация» (скачивание с правого клика) не зондировались отдельным приложением. |

---

## Стек площадки

```text
Браузер директора/поставщика
  → SAP NWBC /ui2/nwbc/          # оболочка, меню
      → service map (папка «Поиск процедур»)
          → POWL ZSAPSRM_B_RFXANDAUCTIONS   # грид + фильтры
      → POWL ZSAPSRM_NOTIF                  # «Отчет по уведомлениям»
```

- UI: SAP NetWeaver Business Client + Web Dynpro ABAP (POWL).
- Client: `100`, language: `RU`.
- Хост: `srm.sibur.ru`.
- ИИ / GPT API **не нужны** (как Q24 для rostender).

### Узлы NWBC в сессии 2026-08-13

Не считать стабильными между логинами.

| node | Что увидели |
| --- | --- |
| `0000000026` | Карта сервисов «Поиск процедур» (плитки, не грид) |
| **`0000000037`** | Лист поиска → iframe POWL `ZSAPSRM_B_RFXANDAUCTIONS` |
| `0000000038` | «Отчет по уведомлениям» → POWL `ZSAPSRM_NOTIF` |

URL POWL поиска (шаблон, `sap-ext-sid` сессионный, не копировать в код как константу):

`/sap/bc/webdynpro/sap/powl;sap-ext-sid=…?APPLID=ZSAPSRM_B_RFXANDAUCTIONS&POWLDELTARENDERING=X&WDCONFIGURATIONID=%2fSAPSRM%2fWDA_POWL&sap-client=100&sap-language=RU`

---

## Почему не копировать P1 `list_scrape.py`

| | РосТендер (as-is) | СИБУР SRM |
| --- | --- | --- |
| Транспорт | httpx GET/POST, в HTML сразу строки | httpx: только оболочка; грид после JS delta |
| Разметка | `article.tender-row` | Lightspeed / динамические id |
| Сессия | Netscape cookies | cookies + `sap-contextid` + `sap-ext-sid`; лишний iframe может сбросить canvas |
| Поиск | поля формы в коде | «Применить» = событие Web Dynpro |
| Документы | ссылки (P5.5) | дерево + context menu |

---

## Рецепт адаптера (когда NEXT+)

Отдельный worker `sibur-srm`, не общий «робот по всем сайтам»:

1. Netscape-файл `cookies.sibur.txt` (как rostender).
2. Заход в POWL `ZSAPSRM_B_RFXANDAUCTIONS` — **Playwright** (или разбор WDA-delta; хрупче). Кнопка «Экспорт» — кандидат на чистый список.
3. Запрос / фильтр → грид открытых процедур.
4. Карточка и файлы — второй шаг.
5. Ingest в ту же Postgres: `source_platform_id=sibur-srm`; скоринг L1–L3 тот же.

Compose bind этого файла и код — **вне** этой заметки.

---

## Cookies (где лежат, что не писать сюда)

| Что | Где |
| --- | --- |
| Значения | только `cookies.sibur.txt` в корне репо (gitignore `cookies*.txt`) |
| Имя пути в env | `SIBUR_COOKIES_FILE` (см. `.env.example`) |
| Этот markdown | **запрещены** values, SSO-билет, `sap-contextid` целиком |

Имена, которые были в дампе (без values): `MYSAPSSO2`, `SAP_SESSIONID_SRP_100`, `SAP_SESSIONID_SRP_150`, `sap-contextid`, `sap-usercontext`, `sap-login-XSRF_SRP`, `session-cookie`. Также в файле: `_ym_*`, `mdd`, `sap-ext-sid-backup`, `sap-nwbc-*`.

Дамп 2026-08-13 записан в файл с чата. После зонда SSO светился в чате; httpx задевал `page_collection`. **Перед следующим заходом в ЛК — перелогин и свежий экспорт Netscape.**

Не путать с Scout login (P5.2) и `cookies.rostender.txt`.

---

## Вне скоупа заметки

Код адаптера, bind в Docker, смена фаз P0–P7, таск в очереди P6, повторный живой прогон из агента.
