---
id: outbox-2026-06-25-stream-readiness-check
type: report
status: proposed
from: codex
to: all
related: [T-253, D-028, independent-variant-stream-policy, stream-readiness-lint]
created: 2026-06-25
---

# Outbox - T-253 stream readiness check

## Что сделано

- По новой политике создан независимый stream-вариант: `streams/stream-readiness-lint/20260625-1731-codex/STREAM.md`.
- `tools/stream.py check` теперь возвращает `incomplete_ready` рядом со `stale` и `broken`.
- `incomplete_ready` применяется только к пакетам `ready-for-synthesis` или `synthesis_ready: true`.
- `tools/test_stream.py` проверяет отрицательный случай: пустой шаблонный `ready-for-synthesis` ловится.
- Тот же тест проверяет положительный случай: заполненный ready stream не попадает в `incomplete_ready`.
- Документация обновлена: `docs/independent-variant-stream-policy.md`, `docs/top-layer-command-groups.md`, `tools/README.md`.

## Команды для людей и агентов

```powershell
python tools\stream.py check --max-age-days 7
python tools\stream.py check --max-age-days 7 --json
```

Ожидаемый чистый результат:

```json
{
  "stale": [],
  "broken": [],
  "incomplete_ready": []
}
```

## Applied instructions

- AGENTS.md: proposed report; no accepted governance.
- PROTOCOL.md: работа через T-253.
- D-017/D-024/cauldron-synthesis: варианты сохраняются, readiness проверяется до synthesis.
- D-028: independent-first policy applied to T-253 through a stream packet.

## Checks

- OK: `python -m py_compile tools\stream.py tools\test_stream.py tools\capabilities.py`
- OK: `python tools\test_stream.py` -> create/mark/list/ready-only/adopt + `incomplete_ready` negative/positive cases.
- OK: `python tools\stream.py check --max-age-days 7 --json` -> `stale: []`, `broken: []`, `incomplete_ready: []`.
- OK: `python tools\capabilities.py snapshot`
- OK: `python tools\capabilities.py --check`
- OK: `python tools\heading_check.py docs\independent-variant-stream-policy.md` -> 0 findings.
- OK: `python tools\heading_check.py docs\top-layer-command-groups.md` -> 0 findings.
- OK: `python tools\generate.py`
- OK: `python tools\validate.py` -> `OK=12 WARN=0 ERROR=0`.
- OK: `python tools\generate.py --check`
- OK: `python tools\stream.py check --max-age-days 7`

Checks:
- python tools\validate.py -> OK
- python tools\generate.py --check -> OK
- python tools\instructions.py check-report <this-file> -> OK after footer normalization
