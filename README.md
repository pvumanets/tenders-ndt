# ndt-tender-scout

UI-мониторинг тендеров rostender.info для **ООО СВАРКА** (пул 1000, уровни L1–L3).

**Фазы: P0 + P1 + P2 done.** Карточки / Excel / HTML / Docker one-command — P3–P6.

## Канон продукта

[docs/CANON.md](./docs/CANON.md) → `ndt-buisness-proc/docs/projects/tender-monitoring/delivery/`

## Стек

- **P1 транспорт:** `httpx` + BeautifulSoup (сессия cookies). Playwright против rostender из этой среды получает **WAF 403**; HTML те же страницы UI.
- **P2:** `app/scoring` по fit-tiers / relevance-rules.
- Далее: Playwright может пригодиться для карточек (P3), если WAF пустит; иначе HTTP.

## Секреты

```powershell
copy .env.example .env
# cookies.rostender.txt — Netscape, gitignore
```

## Запуск P1 + P2

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

python -m app.worker run --limit 1000 --out runs/YYYY-MM-DD
# или по шагам:
python -m app.worker scrape --limit 1000 --out runs/YYYY-MM-DD
python -m app.worker score --out runs/YYYY-MM-DD
```

Артефакты: `raw-list.json`, `scored-list.json`, `tier-summary.json`, `card-ids.json` (L1∪L2∪L3 для P3).

## Последний прогон

`runs/2026-08-11/` — 1000 строк; см. `tier-summary.json` / README прогона.

## Структура

```text
app/worker/    # P1 scrape + CLI
app/scoring/   # P2 rules/tiers
app/api/       # P5
app/static/    # P5
runs/
```

## Следующая фаза

**P3 — Cards:** открыть карточки только для id из `card-ids.json`.
