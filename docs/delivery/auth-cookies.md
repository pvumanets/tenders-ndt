# Auth: два контура

**status:** accepted  
**last-review-date:** 2026-08-28  
**архитектура:** [`tech-architecture.md`](./tech-architecture.md)  
**API Scout:** [`sales-inbox-api.md`](./sales-inbox-api.md)  
**реестр площадок:** [`../discovery/platforms.md`](../discovery/platforms.md)  
**фазы:** P5.2 (Scout login), worker cookies — как P1

Это **не** один механизм. Путать логин директора (Scout) и сессию ЭТП (rostender / Tender.Pro / B2B / Росэлторг / …) нельзя.

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

Тот же паттерн, что rostender: Netscape-файл в корне, **gitignore** `cookies*.txt`, в markdown только путь и имена переменных. Значения cookie и пароли сюда не писать.

### As-is / с учёткой (owner 2026-08-28)

| Площадка | Файл cookies | Переменные (имена в `.env`) | Зонд / статус |
| --- | --- | --- | --- |
| Tender.Pro (`tender-pro`) | `./cookies.tender-pro.txt` | `TENDER_PRO_COOKIES_FILE` (логин/пароль **не** в env) | [`../discovery/tender-pro-probe.md`](../discovery/tender-pro-probe.md) · адаптер [024](./tasks/024-tender-pro-adapter.md) |
| B2B-Center (`b2b-center`) | `./cookies.b2b-center.txt` | `B2B_CENTER_USER` / `B2B_CENTER_PASSWORD` / `B2B_CENTER_COOKIES_FILE` | account · зонд/адаптер позже |
| Росэлторг (`roseltorg`) | `./cookies.roseltorg.txt` (опц.) | `ROSELTORG_USER` / `ROSELTORG_PASSWORD` / `ROSELTORG_COOKIES_FILE` | **канон списка = логин ELK** (password grant → CORP Bearer); cookies alone ≠ сессия · зонд [`../discovery/roseltorg-probe.md`](../discovery/roseltorg-probe.md) · адаптер [040](./tasks/040-roseltorg-adapter.md) |
| OilB2B (`oilb2bcs`) | `./cookies.oilb2bcs.txt` | `OILB2BCS_USER` / `OILB2BCS_PASSWORD` / `OILB2BCS_COOKIES_FILE` | account · зонд/адаптер позже |
| Северсталь (`severstal`) | `./cookies.severstal.txt` | `SEVERSTAL_USER` / `SEVERSTAL_PASSWORD` / `SEVERSTAL_COOKIES_FILE` | account · портал `procurement.severstal.com` |

Worker as-is читает `cookies.rostender.txt`, `TENDER_PRO_COOKIES_FILE` и **Росэлторг** через `ROSELTORG_USER`/`PASSWORD` (ELK Bearer). Список Tender.Pro идёт и без cookies; **файлы** лотов rostender/TP — с живой сессией. Остальные `*_COOKIES_FILE` — после зонда и адаптера. Не путать со Scout login.

### Parked (нет учётки в актуальном перечне)

| Площадка | Файл | Переменная (имя) | Зонд |
| --- | --- | --- | --- |
| СИБУР SRM (`sibur-srm`) | `./cookies.sibur.txt` | `SIBUR_COOKIES_FILE` | [`../discovery/sibur-srm-probe.md`](../discovery/sibur-srm-probe.md) |
| OnlineContract (`onlinecontract`) | `./cookies.onlinecontract.txt` | `ONLINECONTRACT_COOKIES_FILE` (+ `ONLINECONTRACT_USER` / `ONLINECONTRACT_PASSWORD`) | [`../discovery/onlinecontract-probe.md`](../discovery/onlinecontract-probe.md) |

После утечки дампа в чат / зонда, который трогал NWBC `page_collection`: перелогин в ЛК площадки и свежий экспорт файла. Учётки из перечня 2026-08-28 **не** считаем скомпрометированными без явной команды владельца.

## Запрещено

- Коммитить cookies площадки, пароли Scout, `.env` с секретами.
- Вставлять содержимое cookie-файла в `runs/**/*.md` или discovery/delivery.
- Отдавать cookie values / пароли в JSON API.
- Пускать пароль директора в интернет по HTTP (P7 = HTTPS + домен).
