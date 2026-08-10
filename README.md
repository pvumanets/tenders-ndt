# ndt-tender-scout

UI-мониторинг тендеров rostender.info для **ООО СВАРКА** (пул 1000, уровни L1–L3, HTML оператора).

**Фаза сейчас: P0 — bootstrap.** Скрейп / scoring / API / UI — ещё не реализованы.

## Канон продукта

См. [docs/CANON.md](./docs/CANON.md) → репозиторий `ndt-buisness-proc`, каталог  
`docs/projects/tender-monitoring/delivery/`  
Главный план реализации: **code-phases.md** (P0–P6).

## Стек (целевой)

Python 3.12 · Playwright · FastAPI · static HTML · Docker Compose

## Секреты

1. `copy .env.example .env`
2. Положить Netscape cookies в `cookies.rostender.txt` (файл в `.gitignore`, не коммитить)
3. Подробности: канон `delivery/auth-cookies.md`

## Структура

```text
app/api/       # FastAPI — с P5
app/worker/    # Playwright — с P1
app/scoring/   # L1–L3 — с P2
app/static/    # Operator HTML — с P5
runs/          # артефакты прогонов
docs/CANON.md  # ссылка на business-proc
```

## Локально

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Docker (скелет P0, без рабочего API):

```powershell
docker compose build
docker compose run --rm api
```

## Следующая фаза

**P1 — List scrape:** cookies → поиск `неразрушающий` → до 1000 строк → `runs/YYYY-MM-DD/raw-list.json`
