# Agent delegation wave2 synthesis - 2026-07-06

Author: Codex  
Status: proposed synthesis  
Related: `T-286`, `T-274`, `D-015`, `D-026`, `reports/agent-delegation-pilot-synthesis-2026-07-06.md`, `reports/no-verify-bulk-guard-review-2026-07-06.md`

## Wave agents

| Agent | Role | Mode | Status | Result |
|---|---|---|---|---|
| Epicurus | data-driver-verifier | read-only | completed | Found that `data` was close but still had manifest/code drift: CSV/TSV only, BOM fixed in code but not in docs, `max_output_bytes` missing for non-`head()` paths, no `verified_by` yet. |
| Turing | pipeline-tripwire-designer | read-only | completed | Confirmed `T-274` must not be edited while claimed by `novax`; proposed reproducible concurrency block for `pipeline.py`, `PIPELINE.md`, and `logs/pipeline.json`. |
| Aquinas | bulk-range-guard-spec | read-only/spec | completed | Confirmed local pre-commit is not enough; proposed `bulk_guard.py --range <base>..<head> --strict --json`, unknown-arg rejection, aggregate + per-commit scan. |
| Locke | data-driver-cleanup worker | bounded writer | completed | Edited only `drivers/data.md`, `drivers/data/data_driver.py`, `drivers/data/test_data.py`; added BOM and bounded-output fixes; did not add `verified_by`. |

## Consensus

1. `T-286` was the right write target for this wave because it had a clear disjoint scope and an active `codex` claim.
2. `data` is now technically cleaner: current runtime is CSV/TSV L2, not JSON/SQLite/index runtime.
3. `verified_by` must remain absent until D-015/D-038 receives independent multi-agent reverification.
4. `timeout_seconds` is still a known issue, but it belongs to a runner/MCP-host timeout policy rather than a narrow CSV parser patch.
5. `T-274` should stay design-only until the `novax` claim is resolved or explicitly handed off.
6. `bulk_guard --range` is the next important safety task because `--no-verify` can bypass local hooks.
7. The best current orchestration pattern is still: read-only scouts in parallel, one lead integrator, bounded writer only on a disjoint scope.

## Applied in this wave

- `drivers/data.md`: corrected title, level, inputs, current-vs-planned contract, known issues, and D-015 status notes.
- `drivers/data/data_driver.py`: added `utf-8-sig` CSV/TSV reads and `max_bytes` bounds for `list_tables`, `columns`, `head`, and `summarize`.
- `drivers/data/test_data.py`: added regression tests for BOM handling and bounded output on table lists, wide columns, and summary payloads.
- `drivers/CATALOG.md`, `drivers/index.json`, `index.json`, `indexes/drivers.md`, `tools/README.md`: refreshed by generator/catalog tooling.

## Checks

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'; python drivers\data\test_data.py
# TESTS OK tables=2 cols=3 rows=2

$env:PYTHONDONTWRITEBYTECODE='1'; python -m py_compile drivers\data\data_driver.py drivers\data\mcp_server.py drivers\data\test_data.py
# exit 0

git diff --check -- drivers\data.md drivers\data\data_driver.py drivers\data\mcp_server.py drivers\data\test_data.py
# exit 0

python drivers\mcp_sync_probe.py data --timeout 60
# OK data tools=4 ['columns', 'head', 'list_tables', 'summarize']; RESULT OK

python drivers\mcp_sync_acceptance.py data --timeout 90
# SYNC ACCEPTANCE pass=4 fail=0; RESULT OK

python tools\drivers_catalog.py
# OK, 9 drivers

python tools\generate.py
# generated indexes refreshed

python tools\validate.py
# OK=17 WARN=6 ERROR=0
```

## Divergence / unresolved

1. `interfaces` semantics remain partly conceptual. This wave made the split explicit with `tools` as machine-checked MCP tools and `planned` as future conceptual API, but a later schema decision can make this cleaner.
2. `list_tables` and `columns` enforce byte limits by returning a shortened list; unlike `summarize`, they do not include a `truncated` flag because their return type is a simple list. If agents need explicit truncation metadata, the future contract should introduce object-shaped responses.
3. `timeout_seconds` remains advisory. A proper solution should be a shared call wrapper for MCP/driver invocations, not per-function ad hoc timers.
4. `synthesis_helper.py report agent-delegation-wave2` could not generate a report because no registered variants existed for that topic. That is a cauldron automation gap: agent outputs should be materialized as variants automatically.

## Next tasks for the cauldron

1. Reverify `data` through D-038 with two independent agents before adding `verified_by`.
2. Create/claim a separate task for `bulk_guard.py --range <base>..<head> --strict --json`, starting with unknown-argument rejection.
3. Keep `T-274` as design material until the `novax` claim is cleared; then implement concurrency tripwire from Turing's spec.
4. Add a cauldron materializer that turns subagent final messages into variant files, so `synthesis_helper.py` can operate on them directly.