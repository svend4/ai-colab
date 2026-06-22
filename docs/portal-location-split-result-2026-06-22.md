# Portal-location split result — 2026-06-22

Task: `T-145`
Related: `D-021`, `T-139`, `tools/portal.py`, `portals/example/portal.md`

## What changed

`tools/portal.py` now supports the D-021 Variant A split:

- clean L2 identity/config: `portals/<name>/portal.md`;
- operational corpus/runtime: `data/portals/<name>/...`;
- link between them: `corpus_ref` in the L2 portal manifest.

The change is additive. If `portals/<name>/portal.md` does not exist, `portal.py` falls back to the legacy manifest at `data/portals/<name>/portal.md`.

## Technical behavior

Resolution order:

1. `portals/<name>/portal.md` if present;
2. else `data/portals/<name>/portal.md`.

Corpus path:

- L2 manifest: `corpus_ref`, for example `data/portals/example/corpus`;
- legacy manifest: `data/portals/<name>/<corpus>`.

The generated database remains in `data/portals/<name>/<name>.db`.

## Verification

Passed:

- `python tools\test_portal.py`
- `python tools\portal.py list`
- `python tools\portal.py report example --query alpha`

The test covers both paths: legacy `data/portals/<name>/portal.md` and L2 split `portals/<name>/portal.md` with `corpus_ref`.

## My opinion

This closes an important conceptual gap in the pyramid model. People can now open `portals/example/` as the clean present-tense L2 surface, while the machine keeps corpus and runtime artifacts in `data/`. That is a better mental model than hiding the portal identity under `data/`, and it avoids polluting L2 with generated `.db` files.