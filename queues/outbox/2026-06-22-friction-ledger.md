---
from: codex
type: result
task: T-147
related: [docs/friction-ledger.md, docs/friction-playbook.md, Q-015, D-022]
status: done
---

# T-147 result — friction ledger/playbook

Созданы два документа для повторяющихся проблем разработки:

- `docs/friction-ledger.md` — таблица симптомов, где встречалось, ручное решение, риск и что автоматизировать;
- `docs/friction-playbook.md` — короткая инструкция “если видишь X, делай Y”.

Включены типовые проблемы: `apply_patch` в Windows sandbox, PowerShell mojibake, зависания shell/runtime, TEMP PermissionError, git index.lock, чужая half-done работа, stale generated indexes, runtime-шум `LIVE.md/logs`, placeholder tasks, doing без claim, docs drift, external-code sandbox, streams без adoption.

Рекомендация Codex: следующий шаг — не большой оркестратор, а read-only `tools/friction.py` или `tools/top.py friction`, который печатает симптомы и рецепты. Skill `repo-friction-playbook` стоит создавать после ещё 1-2 реальных применений ledger/playbook. Параллельный D-022-пакет принят как связанный источник политики Level 1.