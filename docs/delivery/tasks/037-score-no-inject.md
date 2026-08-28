---
id: "037"
type: task
status: doing
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

- [ ] Deploy + wipe #5 + RT run + sanity

## Out of scope

ИИ; глобальный один минус вместо per-package.
