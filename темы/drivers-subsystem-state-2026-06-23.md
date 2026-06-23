---
id: drivers-subsystem-state-2026-06-23
type: topic
status: proposed
date: 2026-06-23
related: [D-010, D-013, driver-safety-policy, pyramid-candidate-map]
---

# Drivers / AI-OS Bridge subsystem — authoritative state (2026-06-23)

This topic is the single canonical description of the drivers / AI-OS Bridge subsystem: the
checkable driver schema and its enforcement, the safety posture (read-only intake, an execute-gate
that stays closed, audit logging and secret redaction), the registered catalog, and the realized
L2 bridge from the ready drivers up into the thematic portals.

It integrates three producer-workflow slices into one state-of-the-world doc. Status is **proposed**
(not yet through the котёл per D-018); the underlying mechanisms it describes are mostly accepted and
code-backed. The decision frame is **D-010** (AI-OS Bridge strategy) and **D-013** (driver schema v1);
the safety contract lives in `docs/driver-safety-policy.md`; the portability frame is the candidate
pyramid map (`docs/pyramid-candidate-map.md`, itself proposed under D-018).

**Bottom line up front.** The catalog is in the D-010 "early L2" state: **9 drivers registered, 8
ready, only `file-inventory` still draft**. Read-only is the dominant mode, secrets are uniformly
forbidden in-repo, and a real sandbox is demanded before any write/run. The L2 bridge to portals is
realized in two layers — `gateway` composes the ready leaf drivers into one `ai-os-bridge` MCP
(ready-as-contract, with an open Windows stdio `call_tool` acceptance blocker), and
`knowledge.py`/`portal.py` reuse the same drivers as a domain-agnostic engine so portals are pure
data+manifest over an unchanged universal core.

---

## 1. Driver schema, validation, and freshness

### 1.1 Schema contract (the manifest)

A driver is an L1 Markdown file in `drivers/` whose front-matter is a checkable capability manifest,
not just prose (`drivers/SCHEMA.md:10-14`). The schema is `driver-schema-v1`, still marked **draft**
in the doc itself (`drivers/SCHEMA.md:12`), even though the governing decision **D-013** is `accepted`
(`decisions/D-013.md:5`, `decisions/D-013.md:69-72`).

**Required fields (19)** are defined identically in two places — the schema table
(`drivers/SCHEMA.md:18-38`) and D-013 (`decisions/D-013.md:24-44`): `id`, `type`, `title`, `status`,
`level`, `mode`, `owner`, `risk`, `activation`, `interfaces`, `inputs`, `outputs`, `sandbox`,
`secrets`, `source_last_verified`, `timeout_seconds`, `max_output_bytes`, `audit`, `related`. D-013
chose **variant B** (extended manifest = minimal +
`source_last_verified`/`timeout_seconds`/`max_output_bytes`/`audit`), deliberately deferring full MCP
metadata (`protocol_version`, `transport`, `capabilities`) to a later L2/MCP PoC
(`decisions/D-013.md:20-22`, `decisions/D-013.md:56-57`).

**Enumerated value sets** (`drivers/SCHEMA.md:46-71`): `status` ∈ {draft, ready, deprecated};
`level` ∈ {L1, L2, L3}; `mode` ∈ {read-only, manual, safe-write, execute}; `risk` ∈ {low, medium,
high}; `activation` ∈ {manual, pipeline, mcp, scheduled}.

**Safety rules** (`drivers/SCHEMA.md:73-80`): medium/high risk ⇒ `audit: true`; `mode: execute`
forbidden without a separate decision; `secrets` must not be `in-repo`; `timeout_seconds`/
`max_output_bytes` required even at L1 so the future L2/L3 runtime is designed safe up front;
`source_last_verified` exists specifically to fight manifest drift against the real source.

**Optional field `tools`** (`drivers/SCHEMA.md:40-44`): the actual `@mcp.tool()` names registered by
the driver's MCP server — a machine-checkable contract distinct from the conceptual `interfaces`
field. A live example is `drivers/sqlite.md:11-12`, which declares both `interfaces:` and a matching
`tools:` list.

### 1.2 How `tools/validate.py` enforces it

`check_drivers()` (`tools/validate.py:296-384`) iterates `drivers/*.md`, skipping `README.md`,
`SCHEMA.md`, and `_`-prefixed files (`tools/validate.py:331`), and only processes files whose
front-matter `type == "driver"` (`tools/validate.py:338-339`). Front-matter is parsed by the shared
`parse_front_matter` from `_canon.py` (`tools/validate.py:109`; `tools/_canon.py:15-26`), a naive
`key: value` splitter — so list fields like `tools: [a, b]` arrive as raw strings and are split later
by `_parse_inline_list` (`tools/validate.py:387-392`).

Enforcement, mirroring the schema's safety rules:
- **Required fields** — the 19-field `required` list (`tools/validate.py:300-320`) exactly matches the
  schema; any missing/empty field is an **ERROR** (`tools/validate.py:345-347`).
- **Duplicate ids** → ERROR (`tools/validate.py:342-344`).
- **Enum checks** for status/level/mode/risk/activation are **WARN** (non-standard, not fatal)
  (`tools/validate.py:348-357`).
- **`source_last_verified` format**: must match `^\d{4}-\d{2}-\d{2}$`; wrong format is an **ERROR**
  (`tools/validate.py:358-361`).
- **`timeout_seconds`/`max_output_bytes`**: must be positive integers — non-positive or non-numeric →
  ERROR (`tools/validate.py:366-372`).
- **Audit rule**: `risk` ∈ {medium, high} with `audit != "true"` → ERROR (`tools/validate.py:373-374`).
- **Execute/sandbox rule (T-078 finding G)**: `mode: execute` requires real isolation — `sandbox` ∈
  {container, docker, nsjail, firejail, gvisor, sandboxed-vm} (`tools/validate.py:327`). Anything else
  (including declarative values like `required-before-run`) → ERROR; a real-isolation value still emits
  a **WARN** to confirm an accepted decision exists (`tools/validate.py:375-382`). This matches
  `drivers/SCHEMA.md:93`.

A separate pass `check_driver_tools()` (`tools/validate.py:409-444`) handles the optional `tools`
field: only for drivers that declare it, it extracts real `@mcp.tool()` names from
`drivers/<id>/mcp_server.py` via `_mcp_tool_names` (`tools/validate.py:395-406`) and ERRORs if the
declared set ≠ the registered set, or if `tools` is declared but no `mcp_server.py` exists
(`tools/validate.py:428-442`). `interfaces` is conceptual and explicitly not checked
(`tools/validate.py:414`).

Both passes run in `main()` between `check_sources()` and `check_nav()` (`tools/validate.py:451-453`).
Overall exit is 1 only if any ERROR exists; WARN never fails the build (`tools/validate.py:12`,
`tools/validate.py:464-465`).

### 1.3 Freshness (the age-WARN)

Freshness is advisory and lives in
`driver_freshness_warning(date_str, today=None, max_days=DRIVER_FRESHNESS_DAYS)`
(`tools/validate.py:24-40`), with the SLA constant `DRIVER_FRESHNESS_DAYS = 30`
(`tools/validate.py:21`). A comment notes 30 days is the driver SLA (code-backed); decisions/policies
use their own SLA via `assurance.py` (`tools/validate.py:19-20`).

Behavior:
- Returns `None` for anything not matching `^\d{4}-\d{2}-\d{2}$` or unparseable, so it never raises on
  garbage (`tools/validate.py:30-36`).
- Computes age in days; only **age > max_days** yields a WARN string `"source_last_verified … — N дн.
  назад (> 30): пере-сверь манифест с источником"` (`tools/validate.py:37-39`). The threshold is strict
  `>`, so exactly 30 days does not warn.
- `today` is parameterized purely for deterministic tests (`tools/validate.py:28-32`).

Wiring: inside `check_drivers`, when the format check passes, the result feeds a WARN
(`tools/validate.py:362-365`) — i.e. malformed date = ERROR, stale-but-well-formed date = WARN.

`tools/test_validate_freshness.py` locks the contract deterministically with `today = 2026-06-23`
(`tools/test_validate_freshness.py:25`): 40 days → WARN containing "пере-сверь" (`:28-30`); exactly 30
days → None, 31 → WARN (strict boundary) (`:33-36`); 3 days → None (`:39-40`); garbage inputs (`""`,
`None`, `2026-13-99`, `вчера`, `2026/06/01`, `20260601`) → None (`:43-44`); custom `max_days=7` with 10
days → WARN (`:47-48`).

### 1.4 Catalog generator (`tools/drivers_catalog.py`)

A separate generator (T-030) builds the machine slice `drivers/index.json` and the human table
`drivers/CATALOG.md` from front-matter, skipping `README.md`/`_template.md`/`SCHEMA.md`/`CATALOG.md`
(`tools/drivers_catalog.py:29`) and any file without an `id` (`tools/drivers_catalog.py:43-44`). It
uses the same `_canon.parse_fm` parser (`tools/drivers_catalog.py:33`) and projects a fixed field
subset `[id, title, level, mode, risk, status, sandbox, secrets, activation]`
(`tools/drivers_catalog.py:30`). `--check` writes nothing and exits 1 if either generated file is stale
(`tools/drivers_catalog.py:66-92`).

Note: this generator does **not** validate the schema — it only mirrors front-matter into the catalog;
schema enforcement is solely `validate.py`'s job. D-013's acceptance conditions confirm both run clean:
`validate.py = OK=8 WARN=0 ERROR=0` including the driver schema-check, and `generate.py --check` clean
(`decisions/D-013.md:72`).

---

## 2. Driver safety: read-only intake, execute-gate, audit logging, redaction

The driver safety layer enforces an "intake is read-only, execute stays closed until a gate clears"
posture, backed by a canonical append-only audit log and a shared secret-redaction helper with hard
byte limits. The policy lives in `docs/driver-safety-policy.md`; the mechanisms live in
`drivers/audit.py` and `drivers/redaction.py`; the staged intake/execute contract is split across
`docs/external-code-sandbox.md` and `docs/execute-sandbox-preflight.md`.

### 2.1 Read-only-intake / execute-closed-until-gate posture

The baseline is read-only by default. A new driver starts in `mode: read-only`; write/modify/delete
require an explicit decision and manifest update (`docs/driver-safety-policy.md:7`). Writes also require
dry-run-then-confirm, mandatory for batch edits (`docs/driver-safety-policy.md:8`). Running unvetted
external code (`run`/`test`/`install`/shell/network for external repos) is forbidden until there is a
dedicated sandbox (isolated user/container), CPU/memory/network limits, and a separate decision — until
then only `inspect`/`summary` are allowed (`docs/driver-safety-policy.md:9`).

External code is never integrated directly into the core. It first lands in a controlled sandbox
intake, passes read-only inventory, is discussed via reports, and only then becomes an execute
candidate after a separate safety gate (`docs/external-code-sandbox.md:19`). The intake is staged
S0–S7: decision/goal, intake manifest in `sandbox/inbox/`, quarantine in `sandbox/sources/` (untrusted
until inventory — no scripts/install/tests/hooks/binaries: `docs/external-code-sandbox.md:82`),
read-only inventory whose first technical step is always read-only
(`docs/external-code-sandbox.md:86`), disposable workspaces, execute candidate, run plan, and
reports/promotion (`docs/external-code-sandbox.md:46-145`). Any promotion from sandbox into the main
project must be a separate task, not an automatic merge (`docs/external-code-sandbox.md:145`).

Execute stays closed until a hard gate is fully satisfied. `docs/execute-sandbox-preflight.md` is
explicitly a preflight document, not a grant of `mode: execute`; the project stays read-only for
external repos (`docs/execute-sandbox-preflight.md:15`). It lists hard prohibitions before any separate
decision: no `run`/`test`/`install`/`pip install`/`npm install`/`make`/shell/binaries from an unvetted
repo on the host Windows system; no enabling `mode: execute` without a real sandbox and accepted
decision; no mounting all of `C:\Users`, home dir, `.ssh`, browser profiles, tokens, API keys, Docker
socket or `.gitconfig`; no `--privileged`/host network/host PID/Docker socket; and Docker/WSL alone is
not treated as full safety (`docs/execute-sandbox-preflight.md:22-27`). The minimal gate is a 10-row
table — Decision, Source (inventoried), Sandbox (real isolation), Permissions (no secrets/wide mounts),
Network (`--network none` by default), Limits (CPU/RAM/PIDs/disk/timeout), Logs (audit log), Rollback
(`--rm` + separate workspace), Validation (`tools/validate.py` rejects fake sandbox), Human (explicit
first-run confirmation) — and if even one gate is unclosed, the mode stays `read-only`
(`docs/execute-sandbox-preflight.md:33-46`). Variant C (no execute) is the default preferred mode
(`docs/execute-sandbox-preflight.md:98-108`), and a scan is expected to find no active execute drivers
(`docs/execute-sandbox-preflight.md:182-189`). The risk ladder ties this together: `low` → AUTO,
`medium` → REVIEW + audit, `high` (running code, deletion, secret/system access) → HUMAN + audit +
sandbox (`docs/driver-safety-policy.md:18-22`).

### 2.2 Audit logging

`drivers/audit.py` is the canonical audit helper: drivers with `risk: medium|high` are required to log
calls (`docs/driver-safety-policy.md:11`; `drivers/audit.py:6-9`). It is a lightweight append-only
JSONL journal — one shared mechanism rather than per-driver coupling to `workbench.db`
(`drivers/audit.py:7-9`). The log path comes from env `DRIVER_AUDIT_LOG`, else
`<repo-root>/logs/driver-audit.jsonl` (`drivers/audit.py:11`, `drivers/audit.py:26-31`). A single-line
write is OS-atomic (one append-mode `write`), and audit never raises outward — a journal failure must
not break a read-only call (`drivers/audit.py:12-13`). The `audit(driver, action, target=None,
**extra)` function builds a record with a unix `ts`, `driver`, `action`, `target` plus any extra
fields, creates the parent dir, appends one `json.dumps(...)+"\n"` line, and on any exception only
prints a `WARN: audit write failed` to stderr (`drivers/audit.py:34-48`). A `tail [N]` CLI prints the
last N records (`drivers/audit.py:51-66`). The policy notes audit records go to `logs/` (per-agent/
per-task, not a shared hot file) and/or `workbench.db audit_log` (`docs/driver-safety-policy.md:11`).
For a future execute runner, the preflight enumerates the full audit payload — task/agent/claim id,
commit/snapshot, exact command, image/tag or VM id, network mode, mounts, timeout, CPU/RAM/PID limits,
exit code, duration, created-file list, and a link to the summary report — with raw runtime logs kept
in `logs/` (unversioned) and the human-readable summary in
`reports/sandbox-run-YYYY-MM-DD-<task>.md` (`docs/execute-sandbox-preflight.md:191-210`).

### 2.3 Data redaction and byte limits

`drivers/redaction.py` is the canonical secret-masking helper for driver text output — pure stdlib,
stateless, the single source of truth so `SECRET_RE` is not copied across drivers
(`drivers/redaction.py:4-15`). Two patterns: `SECRET_RE` matches
`api_key`/`secret_key`/`access_key`/`aws_key`/`token`/`secret`/`password`/`passwd` in `key=value` or
`key: value` form and masks the value, and `AWS_KEY_RE` matches a bare AWS access key id (`AKIA` + 16
chars) (`drivers/redaction.py:20-25`). `redact(value)` returns non-strings unchanged, substitutes the
secret value with `***` while preserving the key and separator, then masks bare AKIA keys
(`drivers/redaction.py:28-37`). The module is wired into the `files` and `data` drivers
(`files_driver.py` historically kept its own copy of these patterns); new drivers must import from here
(`drivers/redaction.py:9-12`). In practice `drivers/data/data_driver.py:27` imports `redact` and
applies it per-cell (`drivers/data/data_driver.py:93`), and `drivers/files/files_driver.py:28` imports
it as `redact_text`, applying it to file reads (`drivers/files/files_driver.py:124-125`) and to each
search hit, also truncated to 300 chars (`drivers/files/files_driver.py:145`).

Byte limits guard against runaway output and memory blow-up. The policy mandates per-process
`timeout_seconds` (default 30) and `max_output_bytes` (default 1MB) (`docs/driver-safety-policy.md:13`).
The drivers implement this concretely: `drivers/data/data_driver.py:30` sets `MAX_OUTPUT_BYTES =
1_048_576` (matching `drivers/data.md`) and `head(...)` stops accumulating rows once `used + size`
would exceed `max_bytes` (`drivers/data/data_driver.py:81`, `drivers/data/data_driver.py:95`);
`drivers/files/files_driver.py:40` sets `MAX_OUTPUT_BYTES = 1_000_000`, reads `max_bytes + 1` to detect
truncation, decodes only the first `max_bytes`, and returns a `truncated` flag plus the byte count
(`drivers/files/files_driver.py:116`, `drivers/files/files_driver.py:121-126`). Both the audit helper
and the redaction module trace to the T-078 review (audit finding E, redaction finding L:
`drivers/audit.py:9`, `drivers/redaction.py:9-10`); per-process limits and the `audit: true` field
derive from Q-008/B (`docs/driver-safety-policy.md:11`, `docs/driver-safety-policy.md:13`).

---

## 3. Driver catalog and the AI-OS Bridge to L2 portals

### 3.1 The decision frame (D-010)

`decisions/D-010.md` sets the AI-OS Bridge strategy: start neither with a full platform nor a pile of
ad-hoc scripts, but with a staged path **B → E / L1 → early L2** (`decisions/D-010.md:13`). **L1** is
the `drivers/` catalog of markdown manifests plus a template, risk/sandbox/secret policy and first
driver drafts; **L2** is a single safe **read-only PoC driver** after agreement
(`decisions/D-010.md:13`). The canonical folder name is `drivers/` (the metaphor "Treiber"/"трайбер"
is allowed in prose but does not spawn a competing `trailers/` folder) (`decisions/D-010.md:14`).
Consequences: `drivers/` becomes a separate capability registry; running unverified Sven4 code is
explicitly **out of the first stage** — inventory/read-only first, execution only later and only behind
a sandbox; the full L3/L4 server platform is not built ahead of need (`decisions/D-010.md:15`).

### 3.2 Catalog state (`drivers/CATALOG.md` + `drivers/index.json`)

`drivers/CATALOG.md` is generated from `drivers/*.md` by `tools/drivers_catalog.py` and must not be
hand-edited (`drivers/CATALOG.md:3`). It lists nine drivers; `drivers/index.json` is the
machine-readable mirror (the per-driver `sandbox`/`secrets`/`activation` policy fields live there).

| ID | Level | Mode | Risk | Status | Activation | Source |
|---|---|---|---|---|---|---|
| `codex-local` | L1 | manual | medium | **ready** | manual | `drivers/CATALOG.md:7`, `index.json:4` |
| `data` | L1 | read-only | medium | **ready** | manual | `drivers/CATALOG.md:8`, `index.json:14` |
| `file-inventory` | L2 | read-only | low | **draft** | manual | `drivers/CATALOG.md:9`, `index.json:26` |
| `files` | L1 | read-only | low | **ready** | manual | `drivers/CATALOG.md:10`, `index.json:36` |
| `gateway` | L2 | read-only | medium | **ready** | mcp | `drivers/CATALOG.md:11`, `index.json:47` |
| `git-log` | L2 | read-only | medium | **ready** | mcp | `drivers/CATALOG.md:12`, `index.json:58` |
| `repo-runner` | L1 | read-only | medium | **ready** | manual | `drivers/CATALOG.md:13`, `index.json:69` |
| `sqlite` | L2 | read-only | medium | **ready** | mcp | `drivers/CATALOG.md:14`, `index.json:80` |
| `workbench` | L2 | safe-write | medium | **ready** | manual | `drivers/CATALOG.md:15`, `index.json:91` |

**Ready (8): `codex-local`, `data`, `files`, `gateway`, `git-log`, `repo-runner`, `sqlite`,
`workbench`. Proposed/draft (1): `file-inventory`** (the only non-ready entry, status `draft`,
`index.json:31`). This matches the pyramid map's "8/9 ready" tally for the read-only driver contract
(`docs/pyramid-candidate-map.md:22`).

Policy invariants captured per driver in `index.json`: `secrets: forbidden-in-repo` for all nine;
sandbox posture varies by mode — read-only drivers are `not-required-for-read-only`, while `data` is
`required-before-write-or-code-exec` (`index.json:21`), `repo-runner` is `required-before-run-or-test`
(`index.json:76`), `codex-local` uses `current-workspace-policy` (`index.json:11`), and `workbench` is
`workspace-write-only` (`index.json:98`). `README.md` records the default rules: drivers are passive
(do not self-start), default mode is read-only, no secrets in `drivers/`, and running unverified code
needs a separate sandbox + decision (`drivers/README.md:21-26`). At L1 a driver is "a markdown
manifest, not a running process" (`drivers/README.md:16`).

### 3.3 The L2 PoC and the gateway composition

`files` is the named candidate for the **first L2 PoC** because read-only is safer than code execution
(`drivers/files.md:28`), and it already has working L2 code: `drivers/files/files_driver.py`,
`inventory.py`, a FastMCP stdio wrapper `mcp_server.py`, and tests (`drivers/files.md:49-54`).

`gateway` is the realized L2 bridge — explicitly **not a leaf driver but a composition**: one MCP
server (`drivers/gateway/mcp_server.py`, server name `ai-os-bridge`) that fronts three existing drivers
— `files`, `repo-runner`, and `workbench` (query-only) — behind a single connector so an agent gets one
entry point into the "middle layer" (`drivers/gateway.md:28-34`). It exposes 6 tools
(`files_list/read/search/summarize`, `repo_inspect`, `memory_query`), confirmed by handshake
(2026-06-20) and sync-probe (2026-06-21) (`drivers/gateway.md:38`). Its status is nuanced: `ready` as a
manifest/tools-list contract but `ready-except-mcp-stdio-call-acceptance` at runtime, because full
`call_tool` MCP acceptance over async stdio on Windows is still blocked (`drivers/gateway.md:59-61`); an
in-process regression `drivers/gateway/test_gateway.py` covers composition, redaction, allowed-root
confinement and audit (`drivers/gateway.md:63`). Policy is required to flow top-down — gateway must pass
`base_dir`/limits into each nested driver rather than bypass them (`drivers/gateway.md:50`). The `level`
field is constrained to L1/L2/L3 by the driver schema v1 (D-013), so the composition is filed as **L2**
(local MCP) even though conceptually it is orchestration (`drivers/gateway.md:73`).

### 3.4 How portals reuse the drivers (the bridge to L2 portals)

The chain is **drivers → `knowledge.py` (generic L6 engine) → `portal.py` (L2 portals)**.

`tools/knowledge.py` is the universal ingest→query→report engine. It loads driver code directly from
`drivers/` via `_load(...)` — `drivers/workbench/workbench.py` and `drivers/files/files_driver.py`
(`tools/knowledge.py:87-88`) — and calls them as engines: `build()` scans a corpus with
`fd.list_files(...)` and stores documents (with redacted summaries) into the SQLite workbench memory
via `wb.add_document(...)` (`tools/knowledge.py:121-127`). Its docstring states it explicitly reuses the
ready `files` and `workbench` drivers as a "scenario layer" over them, with no vector/RAG until real
demand per D-010 (`tools/knowledge.py:6-9`). Search is FTS5+bm25 with a LIKE fallback
(`tools/knowledge.py:149-164`).

`tools/portal.py` implements the thematic portals of D-016 as a thin file-based plugin model **on top
of that core**: it imports `knowledge as kn` as the "universal L6 engine" (`tools/portal.py:31`) and
delegates wholesale — `portal.build()` calls `kn.build(db, corpus)` (`tools/portal.py:119`) and
`portal.report()` calls `kn.report(...)` then layers per-topic coverage using `kn.fts_search(...)`
(`tools/portal.py:126-138`). The design principle is that the domain lives inside the portal (its files
+ taxonomy as data in `portal.md`), **not in core code**, so the universal engines work on any portal
unchanged (`tools/portal.py:7-9`). A portal is a clean L2 manifest `portals/<name>/portal.md` plus a
runtime corpus under `data/portals/<name>/`, with a legacy fallback to
`data/portals/<name>/portal.md` (`tools/portal.py:11-16`, `:54-61`).

So the bridge is concrete: the read-only/ready drivers (`files`, `workbench`, and via the gateway also
`repo-runner`) are the reusable substrate; `knowledge.py` turns them into a generic knowledge engine;
and `portal.py` reuses that engine to stand up L2 portals without touching driver code.

### 3.5 Pyramid map context (`docs/pyramid-candidate-map.md`)

The candidate map (status **proposed**, for collective Q2/Q3 decision under D-018,
`docs/pyramid-candidate-map.md:2`) lists the driver layer among L1 core-export candidates: "read-only
drivers `files/git-log/sqlite` + `drivers/SCHEMA.md` + `redaction.py`" as a portable "information
drivers" contract, marked **8/9 ready**, acceptance-tested (`docs/pyramid-candidate-map.md:22`); and
`knowledge.py` + `text_extract.py` as the generic L6 engine, T-133 done
(`docs/pyramid-candidate-map.md:23`). For L2, the recommended first portal is the **generic demo**
`portals/example/` built from the green `data/portals/example`, deferring the legal/social domain portal
until data exists (`docs/pyramid-candidate-map.md:45-54`). A later update records that this L2 `example`
scaffold was implemented and that Q4 (portal location) was closed via D-021/T-145: `portal.py` reads the
clean L2 manifest from `portals/example/portal.md` while corpus/runtime stay in `data/portals/example`
via `corpus_ref` (`docs/pyramid-candidate-map.md:83-88`).

---

## 4. Open items

- **Schema doc status drift.** `drivers/SCHEMA.md` is still self-labeled `draft` (`:12`) even though
  D-013 is `accepted` — worth reconciling so the schema doc reflects the accepted decision.
- **Gateway runtime blocker.** `gateway` is contract-ready but `ready-except-mcp-stdio-call-acceptance`:
  full `call_tool` over async stdio on Windows is unresolved (`drivers/gateway.md:59-61`). The
  in-process regression test is the current guarantee.
- **`file-inventory` still draft** — the single non-ready entry; either promote to ready or fold into
  the `files`/gateway path.
- **Execute stays closed.** No active execute drivers exist; `docs/execute-sandbox-preflight.md` is
  preflight only, and Variant C (no execute) is the default until the 10-row gate is fully closed behind
  a separate accepted decision.

## Related

- `decisions/D-010.md` — AI-OS Bridge strategy (B → E / L1 → early L2)
- `decisions/D-013.md` — driver schema v1 (variant B, accepted)
- `docs/driver-safety-policy.md` — risk ladder, audit, byte limits
- `docs/external-code-sandbox.md`, `docs/execute-sandbox-preflight.md` — staged intake + execute gate
- `docs/pyramid-candidate-map.md` — portability map (proposed under D-018)
- `decisions/D-018.md` — collective decision via котёл (governs this doc's `proposed` status)
</doc_content>
</invoke>
