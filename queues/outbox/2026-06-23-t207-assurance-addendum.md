---
type: report
agent: codex
task: T-207-addendum
title: T-207 assurance addendum for text_extract candidate
date: 2026-06-23
status: historical
---

# T-207 assurance addendum — text_extract candidate

## What changed

After T-207 promoted `tools/knowledge.py` from `candidates` to `files` in `core/engine-manifest.md`, `tools/text_extract.py` disappeared from the L1 inventory although two portals still declare it in `l1_basis`.

I kept the T-207 promotion intact and restored only:

```md
candidates: [tools/text_extract.py]
```

## Why

This is the smallest consistency fix:

- `tools/knowledge.py` remains promoted to `files`.
- `tools/text_extract.py` remains a visible L1 candidate for portals that already depend on it.
- No portal basis needs to be weakened.

## Evidence

- `python tools/assurance.py all` previously reported two promotion-coverage findings for `tools/text_extract.py` missing from L1 inventory.
- `tools/text_extract.py` and `tools/test_text_extract.py` both exist.
- `portals/bridge-knowledge/portal.md` and `portals/repo-inventory/portal.md` both declare `tools/text_extract.py` in `l1_basis`.

## Applied instructions

- `AGENTS.md` / `PROTOCOL.md`: no чужие сообщения удалены; правка ограничена metadata-consistency после completed T-207.
- Friction/work-mode: dirty shared tree respected; no git staging/commit.
- Checks: `python tools/assurance.py all`; `python tools/validate.py`; `python tools/generate.py --check`; `python tools/drift_check.py`.