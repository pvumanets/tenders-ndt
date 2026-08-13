---
id: "018"
type: task
status: backlog
phase: P7
title: "VPS: Caddy+TLS, домен, secrets на сервере"
was: ""
---

# 018 — VPS: Caddy+TLS, домен, secrets на сервере

**route:** scout-architect → scout-backend → scout-documentation-writer

## Проблема

Директор с любого ПК: пароль по HTTP в интернет — fail.

## Решение

[`../platform-phases.md`](../platform-phases.md) § P7. Тот же compose, профиль prod: Caddy + Let's Encrypt. Owner даёт домен и `.env` на сервере. Дев на ПК остаётся HTTP analog. Код на VPS — clone/pull с [GitHub](https://github.com/pvumanets/tenders-ndt), не папка с ПК.

## Acceptance

- [ ] HTTPS с валидным сертификатом
- [ ] логин директора с другой машины
- [ ] сессия переживает перезапуск контейнера api (БД жива)
- [ ] cookies rostender и пароли не в git и не в UI

## Файлы

- compose prod profile / Caddyfile; deploy runbook

## Out of scope

- Роли, Bitrix, cron; открытый HTTP с паролем

## Links

- Owner must: домен, две учётки в `.env` на VPS, cookies для живого прогона
- Index: [README](./README.md)
