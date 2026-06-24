# T-234 — result_intake external-code structural heuristics

Codex implemented T-234 under pipeline claim `0f0863f376c4`.

## Change

Updated `tools/result_intake.py` so classification no longer depends only on vocabulary:

- a `.py` analyzed path now receives a strong `external-code` signal;
- a path under `sandbox/` receives a strong `external-code` signal;
- front-matter `type: external-source` receives an `external-code` signal.

This fixes the dogfooding failure where a Python source file such as `tools/pipeline.py` could be pulled toward `build-change` because the text talks about implementation, tools, tasks, and governance.

Updated `tools/test_result_intake.py` with regression cases:

- a `.py` file with build-like text is classified as `external-code`;
- a file under `sandbox/` is classified as `external-code`.

## Result

`python tools/result_intake.py classify tools/pipeline.py --json` now returns:

- class: `external-code`
- confidence: `high`
- structural signal: `python source file path`

## Notes

`python tools/top.py health` exits 0. It also reports an unrelated metadata soft-check for `tools/edges.py` and `tools/test_edges.py` missing D-Cards. That is not part of T-234 and should be handled as a separate small metadata task.

## Applied instructions evidence

AGENTS.md; PROTOCOL.md; tasks/T-234.md; tools/result_intake.py; tools/test_result_intake.py; tools/generate.py; tools/validate.py; tools/drift_check.py; tools/assurance.py; tools/top.py; Checks.

Checks:

- python -m py_compile tools/result_intake.py tools/test_result_intake.py -> OK
- python tools/test_result_intake.py -> OK
- python tools/result_intake.py classify tools/pipeline.py --json -> class external-code, confidence high
- python tools/generate.py -> OK
- python tools/pipeline.py snapshot -> OK
- python tools/generate.py --check -> OK
- python tools/validate.py -> OK=12 WARN=0 ERROR=0
- python tools/drift_check.py -> OK
- python tools/assurance.py all -> PASS
- python tools/top.py health -> EXIT 0, unrelated metadata soft-check for tools/edges.py and tools/test_edges.py