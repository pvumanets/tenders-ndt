# Auth: два контура

**status:** accepted  
**last-review-date:** 2026-08-19  
**архитектура:** [`tech-architecture.md`](./tech-architecture.md)  
**API Scout:** [`sales-inbox-api.md`](./sales-inbox-api.md)  
**фазы:** P5.2 (Scout login), worker cookies — как P1

Это **не** один механизм. Путать логин директора (Scout) и сессию ЭТП (rostender / СИБУР / OnlineContract / Tender.Pro) нельзя.

---

## 1. Scout — вход в продукт (P5.2)

Директор (любой ПК, HTTPS на P7) и digital (дев-стенд) входят логином и паролем.

| Правило | Деталь |
| --- | --- |
| Учётки | **две**, без ролей, один inbox |
| Хранение | `users.password_hash` в Postgres; bootstrap из `.env` |
| Сессия | таблица `sessions`; cookie `scout_session` = opaque token (в БД `sha256`); не JWT |
| Cookie | HttpOnly, SameSite=Lax, Path `/`, TTL 7 суток; `Secure` если `SCOUT_COOKIE_SECURE=1` |
| В git/docs/чате | **запрещены** логины, пароли, значения cookie сессии |
| `.env.example` | только **имена** переменных |

Имена (значения только в `.env`): `SCOUT_DIGITAL_USERNAME`, `SCOUT_DIGITAL_PASSWORD`, `SCOUT_DIRECTOR_USERNAME`, `SCOUT_DIRECTOR_PASSWORD`; опционально `*_DISPLAY`; `SCOUT_COOKIE_SECURE` (0 на дев HTTP, 1 на P7). P5.1 пишет хеши в `users` при пустой таблице. Login пишет `sessions` — P5.2.

Ротация: смена пароля в `.env` + перезапуск api сверяет хеш по **совпадающему username**, обновляет hash и гасит сессии этого пользователя. Смена username в env — не авто-rename (пустая `users` или ручной сброс). Значения сюда не писать.

## 2. Rostender — cookies worker (P1+)

В прогоне **нет** интерактивного логина и ввода капчи владельцем на площадке. Сессия площадки = Netscape HTTP Cookie File.

### Переменные (см. [`../../.env.example`](../../.env.example) — имена, не значения)

| Переменная | Назначение |
| --- | --- |
| `ROSTENDER_COOKIES_FILE` | Путь к cookies (рекомендуется `./cookies.rostender.txt`; на VPS — bind/secret) |
| `ROSTENDER_BASE_URL` | По умолчанию `https://rostender.info` |
| `ROSTENDER_USER` / `ROSTENDER_PASSWORD` | Не для Scout UI; не использовать в v0 runbook |

### Как положить файл

1. Экспорт cookies из браузера в формате Netscape.
2. Сохранить как `cookies.rostender.txt` в корне репо на **деве** или на **VPS** (путь из `.env`).
3. Файл **в gitignore** (`cookies*.txt`). Значения **не** копировать в markdown, journal, ADR, чат-логи репо.

### Ротация

- Редирект на логин площадки / выдача «как гость» — cookies протухли.
- Владелец обновляет файл на машине прогона (ПК или VPS); агент не просит капчу в UI.
- После утечки в чат — сменить пароль/сессию на площадке.

## 3. Другие ЭТП — cookies worker (NEXT+)

Тот же паттерн, что rostender: Netscape-файл в корне, **gitignore** `cookies*.txt`, в markdown только путь и имена cookie.

| Площадка | Файл | Переменная (имя) | Зонд |
| --- | --- | --- | --- |
| СИБУР SRM (`sibur-srm`) | `./cookies.sibur.txt` | `SIBUR_COOKIES_FILE` | [`../discovery/sibur-srm-probe.md`](../discovery/sibur-srm-probe.md) |
| OnlineContract (`onlinecontract`) | `./cookies.onlinecontract.txt` | `ONLINECONTRACT_COOKIES_FILE` | [`../discovery/onlinecontract-probe.md`](../discovery/onlinecontract-probe.md) |
| Tender.Pro (`tender-pro`) | `./cookies.tender-pro.txt` | `TENDER_PRO_COOKIES_FILE` | [`../discovery/tender-pro-probe.md`](../discovery/tender-pro-probe.md) |

Учётка OnlineContract: имена `ONLINECONTRACT_USER` / `ONLINECONTRACT_PASSWORD` только в `.env`. Worker as-is **не** читает cookie-файлы NEXT+ кроме rostender. После [024](./tasks/024-tender-pro-adapter.md) worker читает `TENDER_PRO_COOKIES_FILE` для ЛК/файлов; **список Tender.Pro идёт и без файла**. Не путать со Scout login и с `cookies.rostender.txt`. Значения cookie и пароли сюда не писать. Пароль Tender.Pro в env **не** заводим — только Netscape-файл.

После утечки дампа в чат / зонда, который трогал NWBC `page_collection`: перелогин в ЛК площадки и свежий экспорт файла.

## Запрещено

- Коммитить cookies площадки, пароли Scout, `.env` с секретами.
- Вставлять содержимое cookie-файла в `runs/**/*.md` или discovery/delivery.
- Отдавать cookie values / пароли в JSON API.
- Пускать пароль директора в интернет по HTTP (P7 = HTTPS + домен).
