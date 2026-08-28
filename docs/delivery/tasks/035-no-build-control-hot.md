---
id: "035"
type: task
status: done
phase: NEXT+
title: "Строительный контроль не в Горячих"
was: ""
---

# 035 — Строительный контроль не в Горячих

> **Deprecated (2026-08-28):** hard L3 и вырезание query заменены каноном плюс/минус ([`search-system-v2.md`](../../discovery/search-system-v2.md), [036](./036-search-plus-minus.md)). При коде 036 — откатить `is_construction_watch` и вернуть «строительный контроль» в plus пакета D.

**route:** scout-backend → scout-qa → scout-documentation-writer → ops

**Owner lock 2026-08-28 (исторический):** после P16 на доске ~155/196 L1 — «строительный контроль»; ничего не подходит → убрать из Горячих.

## Решение (AS-IS на проде до 036 code)

1. Hard rule: `строительн… контрол` → всегда **L3** (`is_construction_watch`), как поставка.
2. Убрать query `строительный контроль` из сидов RT/TP пакет D (миграция `0010`).
3. На проде: `UPDATE lots SET tier='L3'` для уже залитых L1/L2 с этой фразой (без полного wipe).

## Acceptance

- [x] Unit: заголовок со стройконтролем → L3
- [x] Deploy + 0010
- [x] Prod: L1 без стройконтроля (0; L1 41 / L3 172 после demote)

## Out of scope

- Wipe / полный прогон (не обязателен)
- ИИ
