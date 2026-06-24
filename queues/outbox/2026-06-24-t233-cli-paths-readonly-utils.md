# T-233 — CLI paths for read-only utilities

Codex implemented T-233 under pipeline claim `f6c147b7f62a`.

## Change

Updated `tools/dir_health.py`:

- `scan(root=None)` now accepts an explicit root directory.
- CLI accepts one positional root path: `python tools/dir_health.py [root] [--json]`.
- Existing no-argument behavior still falls back to the repository root.

Updated `tools/sandbox_intake_demo.py`:

- CLI accepts one positional source path: `python tools/sandbox_intake_demo.py [source-dir] [--out <dir>]`.
- `run_demo(source=...)` can now intake any read-only source directory.
- Default source prefers the sandbox inbox demo-fixtures directory when it exists, otherwise keeps the existing legacy fallback `data/fixtures`. In the current tree, that sandbox inbox demo-fixtures directory is not present, so the existing runnable default remains `data/fixtures`.

Updated tests:

- `tools/test_dir_health.py` now uses `drivers/test_tmp.py` / project `tmp-work` instead of system temp, avoiding the known Windows `PermissionError` class.
- `tools/test_dir_health.py` covers `scan(custom_root)` and `main([custom_root, "--json"])`.
- `tools/test_sandbox_intake_demo.py` covers custom source paths through both `run_demo(..., source=...)` and `main([source, "--out", out])`.

## Result

Both tools can now analyze/intake arbitrary folders without rewriting globals by hand. This makes them usable for sandboxed/source-specific checks instead of only the main repository tree or fixed fixture corpus.

## Notes

During verification, `python tools/top.py health` exited 0. It also surfaced one unrelated metadata soft-check: `tools/edges.py` has no D-Card. That should be handled separately and was not mixed into T-233.

## Applied instructions evidence

AGENTS.md; PROTOCOL.md; tasks/T-233.md; tools/dir_health.py; tools/sandbox_intake_demo.py; tools/test_dir_health.py; tools/test_sandbox_intake_demo.py; tools/generate.py; tools/validate.py; tools/drift_check.py; tools/assurance.py; tools/top.py; Checks.

Checks:

- python -m py_compile tools/dir_health.py tools/sandbox_intake_demo.py tools/test_dir_health.py tools/test_sandbox_intake_demo.py -> OK
- python tools/test_dir_health.py -> OK
- python tools/test_sandbox_intake_demo.py -> OK
- python tools/dir_health.py data/fixtures --json -> OK, fail 0, warn 0
- python tools/sandbox_intake_demo.py data/fixtures --out tmp-work/sandbox-demo-t233 -> OK, read-only intake, 9 files, execute not called
- python tools/generate.py -> OK, TASKS.md and index.json updated
- python tools/pipeline.py snapshot -> OK
- python tools/generate.py --check -> OK
- python tools/validate.py -> OK=12 WARN=0 ERROR=0
- python tools/drift_check.py -> OK
- python tools/assurance.py all -> PASS
- python tools/top.py health -> EXIT 0, unrelated metadata soft-check for tools/edges.py