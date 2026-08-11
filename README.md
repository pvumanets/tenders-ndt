# ndt-tender-scout

UI-мониторинг тендеров rostender.info для **ООО СВАРКА** (пул 1000, уровни L1–L3).

**Фазы: P0–P4 done.** P5 Operator HTML · P6 Docker — дальше.

## Канон

[docs/CANON.md](./docs/CANON.md) → `ndt-buisness-proc/.../tender-monitoring/delivery/`

## Запуск

```powershell
.\.venv\Scripts\Activate.ps1
# полный цикл:
python -m app.worker run --limit 1000 --out runs/YYYY-MM-DD
# только карточки+артефакты по готовому scored-list:
python -m app.worker run --from-score --out runs/2026-08-11
```

Команды: `scrape` · `score` · `cards` · `artifacts` · `run`

## Прогон 2026-08-11

- 1000 лотов; L1/L2/L3 = 77/67/366
- Cards: **510/510** ok
- Артефакты: `tenders.csv`, `tenders.md`, `priority-fit.md`

## Транспорт

httpx + cookies (Playwright → WAF 403 в этой среде).

## Следующее

**P5** — FastAPI + HTML хода работы ([operator-ui](../ndt-buisness-proc/docs/projects/tender-monitoring/delivery/operator-ui.md) в каноне).
