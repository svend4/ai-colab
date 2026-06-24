---
id: 2026-06-24-t235-python-analyzer
type: report
task: T-235
agent: codex
claim_id: 121ff30a174f
status: done-proposed
---
# T-235 — Python AST analyzer and sandbox intake integration

## Result

Implemented `tools/python_analyzer.py` as a read-only semantic analyzer for Python source files. It uses only the standard-library `ast` parser, reads target files as text, and does not import, exec, eval, or otherwise run analyzed code.

The analyzer extracts:
- imports/dependency signals;
- class definitions and methods;
- function and async-function definitions;
- risk signals for `os`, `sys`, `subprocess`, network modules, `eval`, `exec`, `os.system`, and subprocess calls.

Integrated it into `drivers/repo-runner/inventory.py` so Python files scanned by repository intake now populate `python_analysis` and mirror AST risk findings into the existing `risks` list with `source=python_analyzer`.

Updated `tools/sandbox.py` so external-source intake reports include a `Python semantic analysis (read-only AST)` section and correct file counts from `summary.total_files`.

## Files changed

- `tools/python_analyzer.py` — new read-only AST analyzer and CLI.
- `tools/test_python_analyzer.py` — direct analyzer tests.
- `drivers/repo-runner/inventory.py` — inventory integration and `python_analysis` summary field.
- `drivers/repo-runner/test_inventory.py` — integration tests for Python analysis inside repo inventory.
- `tools/sandbox.py` — intake report now prints Python AST summary and better risk labels.
- `tools/test_sandbox.py` — sandbox intake regression for Python AST report output.

## Safety boundary

No external code execution was added. The only module dynamically loaded by inventory is the repo-local `tools/python_analyzer.py`; scanned source files are parsed as text through `ast.parse`. Execute sandbox remains gated by `docs/execute-sandbox-preflight.md`.

## Applied instructions

- `AGENTS.md` / `PROTOCOL.md`: worked in allowed repo areas; did not delete or rewrite other agents messages; left this outbox report for polilog visibility.
- Pipeline guide: continued claimed task `T-235`; original claim `121ff30a174f`; refreshed stale work with `python tools/pipeline.py heartbeat codex T-235 --progress 95 --note ...` before closing.
- External sandbox policy: kept external-code handling read-only; no foreign source was imported or executed.
- Instruction assurance: report includes exact changed files, rationale, and check evidence.
- Friction playbook: `apply_patch` is still blocked by the Windows sandbox wrapper, so edits used the documented UTF-8 PowerShell fallback and were immediately followed by py_compile/tests.
- Checks:
  - `python -m py_compile tools\python_analyzer.py tools\test_python_analyzer.py drivers\repo-runner\inventory.py drivers\repo-runner\test_inventory.py tools\sandbox.py tools\test_sandbox.py` -> OK
  - `python tools\test_python_analyzer.py` -> OK
  - `python drivers\repo-runner\test_inventory.py` -> OK
  - `python tools\test_sandbox.py` -> OK
  - `python tools\python_analyzer.py tools\pipeline.py --base .` -> OK, parsed 31 functions and 2 risk imports
  - `python tools\generate.py` -> OK, generated files already current

## Next recommendations

- Add a compact JSON export command for sandbox intake if future agents need machine-readable AST summaries outside the in-memory inventory result.
- Extend risk rules later with confidence levels and alias tracking, for example `import subprocess as sp; sp.run(...)`.
- Keep execute sandbox separate; this task intentionally improves understanding of code before any run decision.