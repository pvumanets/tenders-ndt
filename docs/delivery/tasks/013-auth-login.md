---
id: "013"
type: task
status: done
phase: P5.2
title: "Auth: session login API + экран входа"
was: ""
---

# 013 — Auth: session login API + экран входа

**route:** scout-architect → scout-backend → scout-designer → scout-ux-writer → scout-frontend → scout-qa → scout-documentation-writer

## Проблема

Директор заходит с любого ПК — нужен логин, не открытый inbox.

## Решение

[`../platform-phases.md`](../platform-phases.md) § P5.2. Две учётки, без ролей. HttpOnly cookie `scout_session` → таблица `sessions`. Экран: логин, пароль, «Войти», personal kit. «Выйти» в шапке.

## Acceptance

- [x] login / logout / me
- [x] без cookie inbox и status — 401
- [x] ошибка «неверные данные» без утечки существования логина
- [x] экран входа на personal kit, RU copy

## Файлы

- `app/api/auth.py`, `app/api/main.py`; `app/db/models.py` (`sessions`); Alembic `0002_sessions`
- `app/web/src/components/scout/LoginScreen.tsx`, `copy.ts`, `lib/auth.ts`

## Out of scope

- Роли, Bitrix SSO, JWT в localStorage, TLS (018), inbox из БД (015)

## Links

- API: [`../sales-inbox-api.md`](../sales-inbox-api.md)
- Auth rules: [`../auth-cookies.md`](../auth-cookies.md)
- Index: [README](./README.md)
