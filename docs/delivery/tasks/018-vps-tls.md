---
id: "018"
type: task
status: doing
phase: P7
title: "VPS: Caddy+TLS, домен, secrets на сервере"
was: ""
---

# 018 — VPS: Caddy+TLS, домен, secrets на сервере

**route:** scout-architect → scout-backend → scout-qa → scout-documentation-writer

## Проблема

Директор с любого ПК: пароль по HTTP в интернет — fail.

## Решение

[`../platform-phases.md`](../platform-phases.md) § P7. Caddy + Let's Encrypt на **https://tenders.ndtexam.ru**. `.env` и `cookies*.txt` на VPS по SSH (`python scripts/vps-bootstrap.py --sync`). Дев на ПК — HTTP analog.

**Сейчас (2026-08-13):** HTTPS live, health `db:ok`, `SCOUT_COOKIE_SECURE=1`, cookies с ПК залиты. Осталось: логин директора с другого ПК (Owner OK).

## Acceptance

- [x] SSH с этой машины (ключ `tenders-ndt-vps`); password login не выключен
- [x] приложение на VPS, `:8765` не на `0.0.0.0`
- [x] HTTPS с валидным сертификатом (`tenders.ndtexam.ru`)
- [ ] логин директора с другой машины
- [x] сессия переживает перезапуск контейнера api (БД жива)
- [x] cookies rostender и пароли не в git и не в UI

## Файлы

- [`../../docker-compose.prod.yml`](../../docker-compose.prod.yml)
- [`../../Caddyfile`](../../Caddyfile)
- [`../vps.md`](../vps.md)
- `scripts/vps-bootstrap.py`

## Out of scope

- Роли, Bitrix, cron; открытый HTTP с паролем

## Links

- UI: https://tenders.ndtexam.ru
- Index: [README](./README.md)
