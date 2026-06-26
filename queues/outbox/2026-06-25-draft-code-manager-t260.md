---
id: 2026-06-25-draft-code-manager-t260
type: report
status: done
owner: codex
date: 2026-06-25
related: [T-260, T-257, T-259, streams/code-variant-draft-manager/20260625-1942-codex/STREAM.md]
---

# T-260 — draft-code no-execute packet manager

## Summary

Implemented a no-execute manager for agent draft-code packets. The core rule is unchanged from T-257:

```text
draft code is evidence, not implementation
```

The implementation creates and reviews quarantine packets, but does not execute code, install dependencies, import draft modules, or promote files into mainline.

## What changed

- Added `tools/draft_code.py` with `create`, `check`, `review`, `list`.
- Added `tools/test_draft_code.py`.
- Added thin `python tools/top.py draft-code ...` proxy.
- Updated `tools/test_top.py` for the new button/parser/proxy.
- Updated `tools/README.md`, `docs/top-layer-command-groups.md`, `tools/capabilities.py`, `system-capabilities.json`.
- Added independent stream `streams/code-variant-draft-manager/20260625-1942-codex/STREAM.md`.

## Sub-agent input used

Averroes confirmed the methodology: draft-code lane should be a quarantine evidence layer, not a mini-mainline. It recommended two pseudocode levels and explicit static review statuses.

Kierkegaard recommended the implementation order: first `tools/draft_code.py` as owner of lifecycle logic, then a thin `top.py` proxy. This was applied.

## Consensus

1. `sandbox/drafts/<draft-id>/` is a quarantine lane.
2. `manifest.json` uses `draft-code-proposal.v1`.
3. `execution_allowed` remains false.
4. `review` delegates to read-only `sandbox_intake_chain.py`.
5. Promotion requires a separate claimed task.
6. Raw drafts remain ignored by Git by default through `sandbox/.gitignore`.

## Remaining divergence / next questions

1. Whether stream lifecycle needs a distinct `ready-for-static-review` status.
2. Whether reviewed draft bundles should have an explicit export format for Git.
3. Whether observer agents may edit draft code or only write notes/forks.
4. Whether `draft_code.py` should later create an outbox review report automatically with an explicit flag.

## Checks

```powershell
python -m py_compile tools\top.py tools\test_top.py tools\draft_code.py tools\test_draft_code.py tools\capabilities.py
python tools\test_draft_code.py
python tools\test_top.py
python tools\stream.py check --max-age-days 7 --json
python tools\validate.py
python tools\generate.py --check
python tools\capabilities.py --check
python tools\top.py draft-code list --root sandbox\drafts --json
```

Results: all passed. `top.py draft-code list` returned schema `draft_code_list.v1` and no current tracked draft packets.

## Applied instructions

- `AGENTS.md` / `PROTOCOL.md`: task, stream, outbox, pipeline claim used; no чужие сообщения deleted.
- D-017 / D-028: independent stream first, then comparison with sub-agent variants.
- D-018 / cauldron-synthesis: consensus and divergence preserved.
- Sandbox policy: no execute; read-only static review only.

Checks:
- python tools\validate.py -> OK
- python tools\generate.py --check -> OK
- python tools\instructions.py check-report <this-file> -> OK after footer normalization
