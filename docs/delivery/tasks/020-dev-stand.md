---
id: "020"
type: task
status: done
phase: P5.1
title: "Дев-стенд: скрипт подъёма + агенты не скикают БД"
was: ""
---

# 020 — Дев-стенд: скрипт подъёма + агенты не скикают БД

**route:** scout-architect → scout-backend → scout-qa → scout-documentation-writer

## Проблема

Postgres уже в compose (012), но агенты скикали smoke («нет БД»), потому что скилл QA запрещал поднимать стек из Cursor.

## Решение

Канон [`../dev-stand.md`](../dev-stand.md). Скрипт `scripts/dev-up.ps1`. Оркестратор и QA перед smoke поднимают стенд; пароль из `.env` не выдумывают.

## Acceptance

- [x] `.\scripts\dev-up.ps1` поднимает db+api и ждёт health
- [x] пустой `POSTGRES_PASSWORD` → exit 1, без секретов в выводе
- [x] скиллы: не скикать smoke, если Docker есть и `.env` заполнен
- [x] канон + README + CANON ссылаются на стенд

## Файлы

- `scripts/dev-up.ps1`, `docs/delivery/dev-stand.md`, `AGENTS.md`, `.cursor/skills/scout-*`

## Out of scope

- P5.5 docs download; P6 wire; Postgres вне Docker; авто-прогон rostender

## Links

- Phases: [`../platform-phases.md`](../platform-phases.md)
- Index: [README](./README.md)
