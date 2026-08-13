---
id: "021"
type: task
status: done
phase: P6
title: "GitHub origin + git workflow"
was: ""
---

# 021 — GitHub origin + git workflow

**route:** scout-product-manager → scout-architect → scout-documentation-writer

## Проблема

Перед P7 код жил только локально. Деплой с папки на ПК не масштабируется; агенты не имели обязательных правил веток.

## Решение

Публичный origin [pvumanets/tenders-ndt](https://github.com/pvumanets/tenders-ndt). Канон: [`../git-workflow.md`](../git-workflow.md). Default branch `main`. Секреты и `_probe_*` не в git. P7 клонирует этот репо.

## Acceptance

- [x] remote `origin` = GitHub; default branch `main`
- [x] в git нет `.env` и `cookies*.txt`
- [x] `docs/delivery/git-workflow.md` + hard rules в `AGENTS.md` и scout-скиллах
- [x] агент после bootstrap не коммитит в `main`

## Файлы

- `docs/delivery/git-workflow.md`
- `AGENTS.md`, `.cursor/skills/scout-*/SKILL.md`
- `.gitignore` (`_probe_*`)

## Out of scope

- Caddy / TLS / домен (018)
- GitHub Actions CI
- установка `gh`

## Links

- Origin: https://github.com/pvumanets/tenders-ndt
- Index: [README](./README.md)
