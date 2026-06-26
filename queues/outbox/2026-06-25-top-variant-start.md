---
id: outbox-2026-06-25-top-variant-start
type: report
status: proposed
from: codex
to: all
related: [T-254, D-028, variant-start-top, top.py]
created: 2026-06-25
---

# Outbox - T-254 top variant-start

## Что сделано

- По новой политике создан independent stream-вариант: `streams/variant-start-top/20260625-1743-codex/STREAM.md`.
- Добавлена команда `python tools\top.py variant-start <agent> <topic...> [--task T-id] [--reason TEXT] [--json]`.
- Команда создаёт stream-пакет, запускает repo-search по теме, опционально запускает instruction-preflight по task и печатает next commands.
- Добавлен JSON-режим `schema: top_variant_start.v1`.
- Обновлены `tools/test_top.py`, `docs/independent-variant-stream-policy.md`, `docs/top-layer-command-groups.md`, `tools/README.md`, `tools/capabilities.py`.

## Команда

```powershell
python tools\top.py variant-start codex "parallel work policy" --task T-254
python tools\top.py variant-start codex "parallel work policy" --json
```

## Граница безопасности

`variant-start` пишет только stream-пакет. Она не делает synthesis, не меняет mainline documents, не принимает `accepted` decisions и не коммитит.

## Applied instructions

- AGENTS.md: proposed report; no accepted decision.
- PROTOCOL.md: работа через T-254.
- D-017/D-024/cauldron-synthesis: варианты сохраняются и сводятся позже.
- D-028: independent-first старт стал top-layer командой.

## Checks

- OK: `python -m py_compile tools\top.py tools\test_top.py tools\capabilities.py`
- OK: `python tools\test_top.py` -> includes `variant-start` parser and JSON smoke with temp stream root.
- OK: `python tools\top.py variant-start codex variant-start-manual-smoke --reason smoke --json --no-search --no-preflight --stream-root tmp-work\variant-start-manual-smoke` -> created temp stream; temp directory removed after path check.
- OK: `python tools\top.py buttons --json` -> includes `variant-start`.
- OK: `python tools\capabilities.py snapshot`
- OK: `python tools\capabilities.py --check`
- OK: `python tools\heading_check.py docs\independent-variant-stream-policy.md` -> 0 findings.
- OK: `python tools\heading_check.py docs\top-layer-command-groups.md` -> 0 findings.
- OK: `python tools\stream.py check --max-age-days 7 --json` -> `stale: []`, `broken: []`, `incomplete_ready: []`.
- OK: `python tools\generate.py`
- OK: `python tools\validate.py` -> `OK=12 WARN=0 ERROR=0`.
- OK: `python tools\generate.py --check`

Checks:
- python tools\validate.py -> OK
- python tools\generate.py --check -> OK
- python tools\instructions.py check-report <this-file> -> OK after footer normalization
