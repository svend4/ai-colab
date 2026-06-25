---
type: report
agent: codex
task: T-175
title: D-014 execute OFF ratification packet
date: 2026-06-23
status: historical
---

# D-014 ratification packet — T-175

## What changed

Подготовлена агентская часть ратификации D-014, но само решение не переведено в `accepted`.

Сделано:

- создан `topics/d014-execute-off-ratification-2026-06-23.md` с proposal, технической проверкой, гуманитарной проверкой, минусами и точным human gate;
- `tools/instructions.py` теперь surface'ит D-014 через `execute-preflight`;
- `docs/execute-sandbox-preflight.md` получил ratification note и ссылки на D-014/D-006/D-018;
- `tasks/T-175.md` переведён в `blocked`, потому D-006 требует человека.

## Result

D-014 рекомендуется принять как запретительный governance-контракт: execute OFF по умолчанию, 10 preflight-гейтов обязательны, текущий read-only контур продолжает работать.

Но D-014 остаётся `status: proposed`, пока Stefan явно не подтвердит acceptance.

## Checks

Checks:
python tools/instructions.py preflight codex T-175
Select-String -Path drivers/*.md -Pattern '^mode:\s*execute' -Encoding UTF8
python tools/top.py assurance all --json
python tools/validate.py

## Applied instructions

- `AGENTS.md` / `PROTOCOL.md`: зона записи соблюдена; accepted-решение не утверждалось агентом.
- `decisions/D-006.md`: человеко-гейт соблюдён; D-014 не переведён в accepted.
- `decisions/D-018.md`: подготовлен котёл-пакет с технической и гуманитарной проверкой.
- `docs/execute-sandbox-preflight.md`: использован профильный execute-preflight; execute не включался.
- `tasks/T-175.md`: критерий закрытия не выполнен из-за human gate, поэтому задача `blocked`.
- Friction/work-mode: dirty shared tree учтён; правки точечные, `git add -A` не применялся.
- Checks: команды перечислены выше; результаты зафиксированы в теме и задаче.
- Commit safety: commit не выполнялся; staging не выполнялся.