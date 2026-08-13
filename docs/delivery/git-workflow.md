# Git workflow — ndt-tender-scout

**status:** accepted  
**last-review-date:** 2026-08-13  
**origin:** [https://github.com/pvumanets/tenders-ndt](https://github.com/pvumanets/tenders-ndt)

Канон веток и пуша. Детали деплоя VPS — P7 / [018](./tasks/018-vps-tls.md). Cursor Plans ≠ backlog.

---

## Origin

| Параметр | Значение |
| --- | --- |
| GitHub | `https://github.com/pvumanets/tenders-ndt.git` |
| Default branch | **`main`** |
| Локальный путь | `C:\Users\NDT\Documents\ndt-tender-scout` |
| P7 | VPS **клонирует / `git pull` с GitHub**, не копирует папку с ПК |

Первый пуш на пустой origin — исключение (один коммит на `main`). После него агент в `main` не коммитит.

---

## Ветки

Имя = тип + id таска из [tasks/README.md](./tasks/README.md) + slug карточки.

| Тип работы | Ветка |
| --- | --- |
| Фича | `feat/<id>-<slug>` |
| Фикс | `fix/<id>-<slug>` |
| Только docs/skills | `docs/<id>-<slug>` |

Примеры: `feat/018-vps-tls`, `fix/019-open-upcoming-only`, `docs/021-github-origin`.

Перед правками:

1. `git fetch origin` и обновить `main`
2. Создать / переключить ветку от **свежего `main`**
3. Не копить несвязанные таски в одной ветке

Вливать в `main` **через PR**. Не squash-ить чужую историю без просьбы владельца.

---

## Агент: запрещено

- Коммитить в `main` (кроме явно запрошенного bootstrap origin)
- `git push --force` / `--force-with-lease` в `main`
- `--no-verify` / `--no-gpg-sign` / пропуск hooks
- Пуш без явной просьбы владельца
- Коммит `.env`, `cookies*.txt`, паролей, cookie-значений, `_probe_*`
- Менять `git config`

Коммит — только если владелец попросил (этот репо: user rule). Сообщение: 1–2 предложения, **зачем**, в стиле существующих коммитов.

---

## Секреты

Tracked: `.env.example` (имена), правила в [auth-cookies.md](./auth-cookies.md).  
Never: `.env`, `cookies*.txt`, пароли в md/чате. Перед `git add` — `git status` / `git diff --cached`.
