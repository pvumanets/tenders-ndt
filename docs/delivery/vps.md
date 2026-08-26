# VPS — доступ и деплой

**status:** active  
**last-review-date:** 2026-08-19  
**фаза:** P7 ([018](./tasks/018-vps-tls.md)) — **done**; HTTPS live  
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

Агент читает `.env.vps` с диска. Не выводить значения. Не копировать пароль в md/skills/правила.  
`--sync` — **только** чтобы заново залить секреты с ПК, не каждый деплой.

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

Код на сервере = **GitHub `main`**. Каталог `/opt/tenders-ndt`. На VPS **не правят** продукт и **не `scp`** фичи — только merge в `main`, потом pull.

Агент деплоит так (секреты не трогает):

```powershell
python scripts/vps-bootstrap.py --deploy
```

`--deploy` сначала смотрит `git status --porcelain`. Если дерево грязное — **exit ≠ 0, без reset**. Иначе: `fetch` + `reset --hard origin/main` + `git clean -fd` (без `-x`) + `compose up --build`.

Перед ручным reset (если скрипт недоступен):

1. `git status --porcelain` в `/opt/tenders-ndt`.
2. Tracked правки (` M`, `M `, `A`, `D`, `R`) — **стоп**. Rescue-ветка `rescue/YYYYMMDD-hhmm` + commit, либо тот же diff уже на `feat/<id>`.
3. Untracked `.env` / `cookies*.txt` — ок. Прочие untracked исходники (`?? app/...`) — тоже стоп: `git clean -fd` их удалит.
4. Только если чисто:

```bash
cd /opt/tenders-ndt
git fetch origin
git checkout main
git reset --hard origin/main
git clean -fd
docker compose -f docker-compose.prod.yml up -d --build
```

Секреты в gitignore — `git reset --hard` их не удаляет. `--sync` — разово залить `.env` / `cookies*.txt` с ПК, не каждый деплой.

Проверка: [https://tenders.ndtexam.ru/api/health](https://tenders.ndtexam.ru/api/health) → `"db":"ok"`. `:8765` только на `127.0.0.1`. Тома Postgres и сертификатов Caddy сохраняются.

Compose prod: Caddy **80/443**; api/Postgres loopback. Публичный HTTP-логин Scout = fail. TLS: Let's Encrypt на `tenders.ndtexam.ru`.

---

## Агент: запрещено

- Править продукт на VPS / `scp` файлы фичи в `/opt/tenders-ndt`
- `git reset --hard` или `git clean -fd`, если porcelain грязный (tracked или untracked исходники)
- Коммитить `.env`, `.env.vps`, ключи, cookie-файлы
- Печатать пароль root / Scout / Postgres
- Отключать `PasswordAuthentication`
- Публиковать `:8765` или `:5433` на `0.0.0.0`
- Считать эти доступы скомпрометированными и крутить их без просьбы владельца
