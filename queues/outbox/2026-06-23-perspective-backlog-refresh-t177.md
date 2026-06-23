---
type: report
agent: codex
task: T-177
title: perspective backlog refresh after T-176
status: proposed
date: 2026-06-23
---

# T-177 — perspective backlog refresh

## What changed

Обновлён `темы/perspective-backlog-2026-06-23.md`, потому `tools/conveyor.py next` после закрытия T-176 продолжал предлагать stale-кандидаты из старого снимка.

Сделано:

- Q-017 semantic doc-merge перенесён в shipped/closed со ссылкой на T-176;
- Q-016 done-gate, F-020 gate-poison, T-166 check-report advisory, T-173 promotion coverage и currency finding перенесены в shipped/closed;
- секция `Готовы к запуску` заменена на актуальные next automation candidates верхнего слоя: result-intake classifier, conveyor regulate, synthesis gate, process-landed classification hardening;
- добавлено правило, что perspective-backlog является входом для `conveyor.py next`, а не архивом старых диагнозов.

## Result

Верхний слой теперь должен дозаливать реальные следующие работы, а не повторять уже закрытый Q-017/T-176. Это маленькая, но важная feedback-правка: после выполнения задачи backlog обязан обновляться, иначе параллелизм тратится на дубли.

## Checks

Checks:
python tools\conveyor.py next
python tools\top.py assurance all --json
python tools\generate.py
python tools\validate.py
python tools\generate.py --check

## Applied instructions

- `AGENTS.md` / `PROTOCOL.md`: задача оформлена через `tasks/T-177.md`, claim в pipeline, результат вынесен в `queues/outbox/`.
- `темы/perspective-backlog-2026-06-23.md`: обновлён источник кандидатов для `conveyor.py next`.
- `tasks/T-177.md`: зафиксирован результат и критерий, что stale Q-017 больше не должен предлагаться.
- `tasks/T-176.md`, `tasks/T-173.md`, `tasks/T-166.md`: использованы как evidence закрытых пунктов.
- `tools/conveyor.py`: код не менялся; изменён входной backlog, который этот инструмент читает.
- Checks: команды перечислены выше; результаты будут проверены перед закрытием T-177.
- Commit safety: commit и staging не выполнялись в dirty shared tree.