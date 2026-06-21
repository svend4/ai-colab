---
id: t137-consensus-result-2026-06-21
type: report
title: T-137 technical consensus result
status: review
related: T-137, D-020, D-017, D-018, D-019
---

# T-137 — technical consensus result

## Итог

T-137 доведён до стадии `review`, не `done`: технический пакет проверен, но D-018 требует коллективного review для спорных governance-пунктов.

## Что принято как рабочее предложение

- Тонкая автоматизация вместо большого нового фреймворка: `top.py` + `cohort.py` + малые CLI-гейты.
- Fork-and-synthesize остаётся нормой для содержательных работ: варианты не снимаются как дубли, а индексируются и синтезируются.
- `streams/` остаётся semi-commit форматом; worktree-streams остаются на утверждении.
- T-020 переведён в честный blocked: нужен read-only источник, после чего запускается generic sandbox intake.
- `promote.py` — gate подъёма между уровнями пирамиды, не массовый мигратор.
- Text-extract развивается ступенчато: текущий safe path уже есть, DOCX без зависимости возможен следующим шагом, PDF требует отдельного решения о зависимости.

## Проверенные инструменты

| Инструмент | Роль | Проверка |
|---|---|---|
| `tools/variants.py` | найти все fork-варианты темы | `python tools/test_variants.py` |
| `tools/stream.py` | создать/list/adopt semi-commit stream | `python tools/test_stream.py` |
| `tools/promote.py` | check/move gate L4->L3->L2->L1 | `python tools/test_promote.py` |
| `tools/merge_gate.py` | read-only merge gate | `python tools/test_merge_gate.py` |
| `tools/sandbox_intake_demo.py` | read-only intake demo без svend4 | `python tools/test_sandbox_intake_demo.py` |
| `tools/cohort.py` | многоагентная верхняя панель | `python tools/test_cohort.py` |

## Runtime correction

`test_stream.py`, `test_promote.py` and `test_sandbox_intake_demo.py` были переведены с системного temp на `drivers/test_tmp.py` / `tmp-work/`. Это не косметика: в текущем Windows runtime `%TEMP%` может создавать каталоги, в которые тот же Python потом не может писать.

## Что осталось на review

1. Принять или отложить D-020.
2. Принять или отложить D-019 Level 1 worktree-streams.
3. Дать read-only источник для T-020 или закрыть старый svend4-долг как ожидание внешних данных.
4. Выбрать следующий text-extract шаг: DOCX stdlib или ожидание реального corpus.
5. Решить, кто является интегратором merge-gate при работе нескольких агентов.
