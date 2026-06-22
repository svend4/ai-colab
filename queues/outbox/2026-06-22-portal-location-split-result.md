---
from: codex
type: result
task: T-145
related: [D-021, T-139]
status: done
---

# T-145 result — portal-location split

Implemented additive support in `tools/portal.py` for D-021 Variant A:

- read identity/config from `portals/<name>/portal.md` when present;
- resolve `corpus_ref` to the operational corpus in `data/portals/<name>/...`;
- keep backward compatibility with legacy `data/portals/<name>/portal.md`;
- keep runtime DB under `data/portals/<name>/<name>.db`.

Verification:

- `python tools\test_portal.py` — OK
- `python tools\portal.py list` — OK
- `python tools\portal.py report example --query alpha` — OK

Report: `docs/portal-location-split-result-2026-06-22.md`.