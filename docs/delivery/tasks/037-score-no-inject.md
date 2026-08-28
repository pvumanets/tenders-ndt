---
id: "037"
type: task
status: done
phase: NEXT+
title: "Скоринг: supply-минусы + без впрыска methods + wipe #5"
was: ""
---

# 037 — Скоринг: supply-минусы + без впрыска methods

**route:** scout-backend → scout-qa → scout-documentation-writer → ops

## Owner lock (2026-08-28)

- Минус на **всех** пакетах A–E (+ TP): `поставка`, `закупка`, `прибор` (list filter).
- Скоринг: device/supply → L3 даже с «неразрушающий»; убрать жадный `услуги…контроль`; `methods` **не** в rescore; detect methods только из title.
- Wipe #5 + RT-only; poll статуса короткими SSH-запросами.

## Acceptance (code)

- [x] Migration `0012` + seeds supply exclude
- [x] rules.py supply/device/энерг/SERVICE_NDT
- [x] pipeline rescore без methods; card_scrape title-only methods
- [x] pytest эталоны Hot-мусора

## Acceptance (ops)

- [x] Deploy `5304269` + wipe #5 + RT run + sanity (2026-08-28)
- session `ok`; L1 **3** (was ~191 до 037); L2 **5**, L3 **27**
- `customer_name` на всех L1; 1 L1 с подстрокой «поверк» в длинном заголовке услуг НК (не supply-мусор)

## ИИ (ops, 2026-08-28)

- [x] `PROVOD_API_KEY` в `COPY_ENV_KEYS` → `--sync` на VPS (`1ef36ab`)
- [x] Первый «Разобрать с ИИ» — 35 лотов, 0 сбоев (2026-08-28)

## Out of scope

ИИ; глобальный один минус вместо per-package.
