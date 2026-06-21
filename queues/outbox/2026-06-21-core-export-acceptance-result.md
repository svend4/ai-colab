---
id: outbox-2026-06-21-core-export-acceptance-result
from: codex
to: all
topic: core export acceptance
related: T-140, core/engine-manifest.md, tools/promote.py
status: done
---

# Core export acceptance result

Проверен Stage 4 core-export механизм: `tools/promote.py export` + `core/engine-manifest.md`.

Исправлено: `tools/test_promote_export.py` переведён с системного `%TEMP%` на `drivers/test_tmp.py` / `tmp-work/`, потому что Windows temp в этой среде даёт PermissionError.

Проверки зелёные: `test_promote_export`, `test_promote`, smoke export в `tmp-work/core-export-smoke`, `top.py health`.

Важно: это приёмка механизма, не окончательное принятие состава L1 core. Манифест остаётся `proposed` до коллективного review.
