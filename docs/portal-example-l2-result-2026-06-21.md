---
id: portal-example-l2-result-2026-06-21
type: report
title: First L2 example portal result
status: done
related: T-139, D-016, D-020, docs/pyramid-candidate-map.md
---

# First L2 example portal — result

## What changed

`portals/example/` is now the first clean L2 portal scaffold:

- `portal.md` — portal identity, level, links and relation to core/data;
- `current-state.md` — present-tense state;
- `workflows.md` — operational commands;
- `sources.md` — curated source list and L2/L4 boundary.

The operational corpus remains in `data/portals/example/corpus/`. After D-021/T-145, `tools/portal.py` reads the clean L2 manifest from `portals/example/portal.md` and resolves `corpus_ref` back to `data/portals/example/corpus/`.

## Verification

Passed:

```powershell
python tools/tests/test_portal.py
python tools/promote.py list
```

`tools/tests/test_portal.py` confirms the existing operational portal still builds/reports over 2 documents
and 3 topics. `tools/promote.py list` sees `portals/example/*` as L2 artifacts.

## Follow-up closed by D-021/T-145

The location model is now Variant A: keep split `portals/` + `data/portals/`, and make `portal.py` read the L2 manifest directly when present. Legacy `data/portals/<name>/portal.md` remains supported.
