---
id: "006"
type: task
status: done
phase: P5.0
title: "PlatformIcon + реестр площадок"
was: "F"
---

# 006 — PlatformIcon + реестр площадок

**route:** scout-product-manager → scout-designer → scout-frontend → scout-documentation-writer

## Проблема

На карточке не было сигнала «откуда тендер» — директор не видит площадку.

## Решение

- Реестр [`docs/discovery/platforms.md`](../../discovery/platforms.md); ассеты `app/web/public/platforms/{id}.png` (32×32).
- Поле лота `source_platform_id` (мок = `rostender`).
- `PlatformIcon` на карточке (**правый рейл**, [011](./011-platform-icon-rail.md)), в таблице (колонка «Площадка»), в drawer у «На площадке».
- Ship A scrape остаётся только rostender; остальные id — backlog реестра.

## Acceptance

- [x] Реестр platforms.md + ссылки CANON / platform-api-research
- [x] Иконки в `public/platforms/` + `scripts/fetch-platform-icons.py`
- [x] UI: card / table / drawer
- [ ] **Owner gate:** визуально ок ли иконки / плотность — layout follow-up [011](./011-platform-icon-rail.md)

## Файлы

- `docs/discovery/platforms.md`
- `app/web/public/platforms/`
- `app/web/src/platforms.ts`
- `app/web/src/components/scout/PlatformIcon.tsx`
- `app/web/src/components/scout/LotMiniCard.tsx`
- `app/web/src/components/scout/LotTable.tsx`
- `app/web/src/components/scout/TenderDrawer.tsx`
- `scripts/fetch-platform-icons.py`

## Out of scope

- Scrape других ЭТП; multi-site cron

## Links

- Platforms: [`platforms.md`](../../discovery/platforms.md)
- Design: PlatformIcon в specs/components/copy
- Index: [README](./README.md)
