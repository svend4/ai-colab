---
id: 2026-06-25-info-draft-manager-t261
type: report
status: done
owner: codex
date: 2026-06-25
related: [T-261, T-260, streams/info-draft-manager/20260625-2013-codex/STREAM.md]
---

# T-261 — info/document no-canon draft packet manager

## Summary

Implemented an information/document analogue of T-260.

Core rule:

```text
info draft is evidence, not canon
```

The tool creates and reviews structured information draft packets, but does not accept decisions, overwrite clean docs, delete divergence, or promote files into `docs/`, `topics/`, `core/`, or `portals/`.

## What changed

- Added `tools/info_draft.py` with `create`, `check`, `review`, `list`.
- Added `tools/test_info_draft.py`.
- Added `sandbox/info-drafts/README.md`.
- Added `sandbox/templates/info-draft-manifest.template.json`.
- Updated `sandbox/.gitignore` so raw `sandbox/info-drafts/*` packets are ignored by default, except README.
- Added thin `python tools/top.py info-draft ...` proxy.
- Updated `tools/test_top.py` for the new button/parser/proxy.
- Updated `tools/README.md`, `docs/top-layer-command-groups.md`, `tools/capabilities.py`, `system-capabilities.json`.
- Added independent stream `streams/info-draft-manager/20260625-2013-codex/STREAM.md`.

## Why this is not just another docs folder

`docs/` is for cleaner documentation. `topics/` and `streams/` are for discussion/variants. `sandbox/inbox` is raw intake. `sandbox/info-drafts/` fills the missing middle:

```text
raw idea -> structured info draft -> review -> doc_synthesis -> promotion task
```

## Packet structure

```text
sandbox/info-drafts/<draft-id>/
  manifest.json
  README.md
  brief.md
  outline.md
  claims.md
  sources.md
  open_questions.md
  divergence.md
  notes.md
```

## Review logic

`info_draft.py review` checks:

- manifest and required files;
- `canon_status` is not accepted;
- secrets/private-data flags;
- claim/source/question/divergence structure;
- readiness route: `keep-quarantine`, `ready-for-synthesis`, or `ask-agent-revision`.

`ready-for-synthesis` is not acceptance. It only means the packet is structured enough for comparison.

## Checks

```powershell
python -m py_compile tools\top.py tools\test_top.py tools\info_draft.py tools\test_info_draft.py tools\capabilities.py
python tools\test_info_draft.py
python tools\test_top.py
python tools\stream.py check --max-age-days 7 --json
python tools\validate.py
python tools\generate.py --check
python tools\capabilities.py --check
python tools\top.py info-draft list --root sandbox\info-drafts --json
```

Results: all passed. `top.py info-draft list` returned schema `info_draft_list.v1` and no current tracked info draft packets.

## Remaining questions

1. Whether selected info draft bundles should have an explicit Git export format.
2. Whether `info_draft.py review` should create an outbox report with an explicit flag.
3. Whether to add specialized draft kinds beyond `doc`, `question-tree`, `source-map`, `decision-material`, `portal-note`, `research-notes`.
4. Whether observer agents may edit draft packets or only create review notes/forks.

## Applied instructions

- `AGENTS.md` / `PROTOCOL.md`: task, stream, outbox, pipeline claim used; no чужие сообщения deleted.
- D-017 / D-028: independent stream first, then implementation.
- D-018 / cauldron-synthesis: consensus/divergence preserved; no accepted decision made.
- Sandbox policy: raw draft packets stay quarantined; promotion is separate.

Checks:
- python tools\validate.py -> OK
- python tools\generate.py --check -> OK
- python tools\instructions.py check-report <this-file> -> OK after footer normalization
