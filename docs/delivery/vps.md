# VPS — доступ и деплой

**status:** active  
**last-review-date:** 2026-08-13  
**фаза:** P7 ([018](./tasks/018-vps-tls.md)) — HTTPS live; owner login с другого ПК  
**git:** [`git-workflow.md`](./git-workflow.md)

Owner lock 2026-08-13: доступы **не считаем скомпрометированными**. Не ротировать, пока владелец не попросит. **Значения пароля не коммитить, не печатать в чат, не класть в skills.**

---

## Куда класть секреты

| Что | Где |
| --- | --- |
| Host, user, root password | локальный **`.env.vps`** (gitignore `.env.*`) |
| SSH ключ этой машины | `~/.ssh/id_ed25519_tenders_ndt_vps` |
| SSH alias | `tenders-ndt-vps` в `~/.ssh/config` (не в git) |
| Scout/Postgres на сервере | `/opt/tenders-ndt/.env` (не в git) |
| Cookies площадок | `/opt/tenders-ndt/cookies*.txt` (не в git) |

Агент читает `.env.vps` с диска. Не выводить значения. Не копировать пароль в md/skills/правила. Sync: `python scripts/vps-bootstrap.py --sync`.

---

## Факты (не секреты)

| Параметр | Значение |
| --- | --- |
| Host / IP | `77.91.94.111` (`ru-vmnano`) |
| User | `root` |
| Публичный UI | **https://tenders.ndtexam.ru** |
| DNS | A `tenders.ndtexam.ru` → `77.91.94.111` |
| Ключ | `~/.ssh/id_ed25519_tenders_ndt_vps` |
| Каталог приложения | `/opt/tenders-ndt` |
| Origin | `https://github.com/pvumanets/tenders-ndt.git` |
| Password SSH | **остаётся включён** (`PasswordAuthentication yes`) |

Вход с этой машины: ключ. Пароль не отключать.

```powershell
ssh tenders-ndt-vps
```

Публичный ключ этой машины:

```
ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIPsQtPyJ0XA+aZhId3ptGORZXd69iyeTX4VV5ER45HM7 tenders-ndt-vps
```

UI: [https://tenders.ndtexam.ru](https://tenders.ndtexam.ru)  
Health: [https://tenders.ndtexam.ru/api/health](https://tenders.ndtexam.ru/api/health)

---

## Деплой

1. Код — `git clone` / overlay `docker-compose.prod.yml` + `Caddyfile` с ПК (`--sync`), пока нет merge в `main`.
2. Compose prod: Caddy **80/443**; api/Postgres только `127.0.0.1`. Публичный HTTP-логин Scout = fail.
3. `python scripts/vps-bootstrap.py --sync` — `.env`, `cookies*.txt`, Caddy, `SCOUT_COOKIE_SECURE=1`.
4. TLS: Let's Encrypt на `tenders.ndtexam.ru`.

---

## Агент: запрещено

- Коммитить `.env`, `.env.vps`, ключи, cookie-файлы
- Печатать пароль root / Scout / Postgres
- Отключать `PasswordAuthentication`
- Публиковать `:8765` или `:5433` на `0.0.0.0`
- Считать эти доступы скомпрометированными и крутить их без просьбы владельца
