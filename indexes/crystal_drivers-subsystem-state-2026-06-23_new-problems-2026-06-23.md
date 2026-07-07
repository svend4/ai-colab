# Кристаллизация: drivers-subsystem-state-2026-06-23 и new-problems-2026-06-23
> [!NOTE]
> Этот файл был сгенерирован алгоритмом Entropic Decay Monitor.
> Оригинальные файлы сохранены в неприкосновенности.

## Общие смысловые тезисы (пересечение)
- The policy notes audit records go to `logs/` (per-agent/
per-task, not a shared hot file) and/or `workbench.
- Py:331`), and only processes files whose
front-matter `type == "driver"` (`tools/validate.
- Py` implements the thematic portals of d-016 as a thin file-based plugin model **on top
of that core**: it imports `knowledge as kn` as the "universal l6 engine" (`tools/portal.
- It integrates three producer-workflow slices into one state-of-the-world doc.
- Md:24-44`): `id`, `type`, `title`, `status`,
`level`, `mode`, `owner`, `risk`, `activation`, `interfaces`, `inputs`, `outputs`, `sandbox`,
`secrets`, `source_last_verified`, `timeout_seconds`, `max_output_bytes`, `audit`, `related`.
- Writes also require
dry-run-then-confirm, mandatory for batch edits (`docs/driver-safety-policy.
- Py`, server name `ai-os-bridge`) that fronts three existing drivers
— `files`, `repo-runner`, and `workbench` (query-only) — behind a single connector so an agent gets one
entry point into the "middle layer" (`drivers/gateway.
- Json:91` |

**ready (8): `codex-local`, `data`, `files`, `gateway`, `git-log`, `repo-runner`, `sqlite`,
`workbench`.
- **l1** is
the `drivers/` catalog of markdown manifests plus a template, risk/sandbox/secret policy and first
driver drafts; **l2** is a single safe **read-only poc driver** after agreement
(`decisions/d-010.
- The log path comes from env `driver_audit_log`, else
`<repo-root>/logs/driver-audit.
- A single-line
write is os-atomic (one append-mode `write`), and audit never raises outward — a journal failure must
not break a read-only call (`drivers/audit.
- - **audit rule**: `risk` ∈ {medium, high} with `audit.
- The decision frame is **d-010** (ai-os bridge strategy) and **d-013** (driver schema v1);
the safety contract lives in `docs/driver-safety-policy.
- 3 the l2 poc and the gateway composition

`files` is the named candidate for the **first l2 poc** because read-only is safer than code execution
(`drivers/files.
- Py` rejects fake sandbox), human (explicit
first-run confirmation) — and if even one gate is unclosed, the mode stays `read-only`
(`docs/execute-sandbox-preflight.
- Its docstring states it explicitly reuses the
ready `files` and `workbench` drivers as a "scenario layer" over them, with no vector/rag until real
demand per d-010 (`tools/knowledge.
- Running unvetted
external code (`run`/`test`/`install`/shell/network for external repos) is forbidden until there is a
dedicated sandbox (isolated user/container), cpu/memory/network limits, and a separate decision — until
then only `inspect`/`summary` are allowed (`docs/driver-safety-policy.
- Note: this generator does **not** validate the schema — it only mirrors front-matter into the catalog;
schema enforcement is solely `validate.
- ** `gateway` is contract-ready but `ready-except-mcp-stdio-call-acceptance`:
  full `call_tool` over async stdio on windows is unresolved (`drivers/gateway.
- - **enum checks** for status/level/mode/risk/activation are **warn** (non-standard, not fatal)
  (`tools/validate.
- Py:395-406`) and errors if the
declared set ≠ the registered set, or if `tools` is declared but no `mcp_server.
- Json:58` |
| `repo-runner` | l1 | read-only | medium | **ready** | manual | `drivers/catalog.
- `gateway` is the realized l2 bridge — explicitly **not a leaf driver but a composition**: one mcp
server (`drivers/gateway/mcp_server.
- Read-only is the dominant mode, secrets are uniformly
forbidden in-repo, and a real sandbox is demanded before any write/run.
- Driver catalog and the ai-os bridge to l2 portals

### 3.
- Md` is
  preflight only, and variant c (no execute) is the default until the 10-row gate is fully closed behind
  a separate accepted decision.
- )+"\n"` line, and on any exception only
prints a `warn: audit write failed` to stderr (`drivers/audit.
- It first lands in a controlled sandbox
intake, passes read-only inventory, is discussed via reports, and only then becomes an execute
candidate after a separate safety gate (`docs/external-code-sandbox.
- For a future execute runner, the preflight enumerates the full audit payload — task/agent/claim id,
commit/snapshot, exact command, image/tag or vm id, network mode, mounts, timeout, cpu/ram/pid limits,
exit code, duration, created-file list, and a link to the summary report — with raw runtime logs kept
in `logs/` (unversioned) and the human-readable summary in
`reports/sandbox-run-yyyy-mm-dd-<task>.
- The risk ladder ties this together: `low` → auto,
`medium` → review + audit, `high` (running code, deletion, secret/system access) → human + audit +
sandbox (`docs/driver-safety-policy.
- The module is wired into the `files` and `data` drivers
(`files_driver.
- So the bridge is concrete: the read-only/ready drivers (`files`, `workbench`, and via the gateway also
`repo-runner`) are the reusable substrate; `knowledge.
- Status is **proposed**
(not yet through the котёл per d-018); the underlying mechanisms it describes are mostly accepted and
code-backed.
- )` and stores documents (with redacted summaries) into the sqlite workbench memory
via `wb.
- The l2 bridge to portals is
realized in two layers — `gateway` composes the ready leaf drivers into one `ai-os-bridge` mcp
(ready-as-contract, with an open windows stdio `call_tool` acceptance blocker), and
`knowledge.
- Py:300-320`) exactly matches the
  schema; any missing/empty field is an **error** (`tools/validate.
- Md`)

the candidate map (status **proposed**, for collective q2/q3 decision under d-018,
`docs/pyramid-candidate-map.
- 1 schema contract (the manifest)

a driver is an l1 markdown file in `drivers/` whose front-matter is a checkable capability manifest,
not just prose (`drivers/schema.
- - **`file-inventory` still draft** — the single non-ready entry; either promote to ready or fold into
  the `files`/gateway path.
- 1 read-only-intake / execute-closed-until-gate posture

the baseline is read-only by default.
- Py:9-10`); per-process limits and the `audit: true` field
derive from q-008/b (`docs/driver-safety-policy.
- ---
id: drivers-subsystem-state-2026-06-23
type: topic
title: drivers / ai-os bridge subsystem — authoritative state (2026-06-23)
status: proposed
date: 2026-06-23
related: [d-010, d-013, driver-safety-policy, pyramid-candidate-map]
---

# drivers / ai-os bridge subsystem — authoritative state (2026-06-23)

this topic is the single canonical description of the drivers / ai-os bridge subsystem: the
checkable driver schema and its enforcement, the safety posture (read-only intake, an execute-gate
that stays closed, audit logging and secret redaction), the registered catalog, and the realized
l2 bridge from the ready drivers up into the thematic portals.
- Py` is the canonical audit helper: drivers with `risk: medium|high` are required to log
calls (`docs/driver-safety-policy.
- Wiring: inside `check_drivers`, when the format check passes, the result feeds a warn
(`tools/validate.
- It lists hard prohibitions before any separate
decision: no `run`/`test`/`install`/`pip install`/`npm install`/`make`/shell/binaries from an unvetted
repo on the host windows system; no enabling `mode: execute` without a real sandbox and accepted
decision; no mounting all of `c:\users`, home dir, `.
- Consequences: `drivers/` becomes a separate capability registry; running unverified sven4 code is
explicitly **out of the first stage** — inventory/read-only first, execution only later and only behind
a sandbox; the full l3/l4 server platform is not built ahead of need (`decisions/d-010.
- Two patterns: `secret_re` matches
`api_key`/`secret_key`/`access_key`/`aws_key`/`token`/`secret`/`password`/`passwd` in `key=value` or
`key: value` form and masks the value, and `aws_key_re` matches a bare aws access key id (`akia` + 16
chars) (`drivers/redaction.
- Py:409-444`) handles the optional `tools`
field: only for drivers that declare it, it extracts real `@mcp.
- It exposes 6 tools
(`files_list/read/search/summarize`, `repo_inspect`, `memory_query`), confirmed by handshake
(2026-06-20) and sync-probe (2026-06-21) (`drivers/gateway.
- The policy lives in `docs/driver-safety-policy.
- Py`; the staged intake/execute contract is split across
`docs/external-code-sandbox.
- Md:11`, `docs/driver-safety-policy.
- Execute stays closed until a hard gate is fully satisfied.
- Driver safety: read-only intake, execute-gate, audit logging, redaction

the driver safety layer enforces an "intake is read-only, execute stays closed until a gate clears"
posture, backed by a canonical append-only audit log and a shared secret-redaction helper with hard
byte limits.
- The `level`
field is constrained to l1/l2/l3 by the driver schema v1 (d-013), so the composition is filed as **l2**
(local mcp) even though conceptually it is orchestration (`drivers/gateway.
- Md:82`),
read-only inventory whose first technical step is always read-only
(`docs/external-code-sandbox.
- Json` is the
machine-readable mirror (the per-driver `sandbox`/`secrets`/`activation` policy fields live there).
- Py` is the canonical secret-masking helper for driver text output — pure stdlib,
stateless, the single source of truth so `secret_re` is not copied across drivers
(`drivers/redaction.
- Policy is required to flow top-down — gateway must pass
`base_dir`/limits into each nested driver rather than bypass them (`drivers/gateway.
- Json`: `secrets: forbidden-in-repo` for all nine;
sandbox posture varies by mode — read-only drivers are `not-required-for-read-only`, while `data` is
`required-before-write-or-code-exec` (`index.
- Anything else
  (including declarative values like `required-before-run`) → error; a real-isolation value still emits
  a **warn** to confirm an accepted decision exists (`tools/validate.
- A new driver starts in `mode: read-only`; write/modify/delete
require an explicit decision and manifest update (`docs/driver-safety-policy.
- Md` — driver schema v1 (variant b, accepted)
- `docs/driver-safety-policy.
- Variant c (no execute) is the default preferred mode
(`docs/execute-sandbox-preflight.
- Gitconfig`; no `--privileged`/host network/host pid/docker socket; and docker/wsl alone is
not treated as full safety (`docs/execute-sandbox-preflight.
- Behavior:
- returns `none` for anything not matching `^\d{4}-\d{2}-\d{2}$` or unparseable, so it never raises on
  garbage (`tools/validate.
- Md:86`), disposable workspaces, execute candidate, run plan, and
reports/promotion (`docs/external-code-sandbox.
- Tool()` names registered by
the driver's mcp server — a machine-checkable contract distinct from the conceptual `interfaces`
field.
- Md:98-108`), and a scan is expected to find no active execute drivers
(`docs/execute-sandbox-preflight.
- Overall exit is 1 only if any error exists; warn never fails the build (`tools/validate.
- Its status is nuanced: `ready` as a
manifest/tools-list contract but `ready-except-mcp-stdio-call-acceptance` at runtime, because full
`call_tool` mcp acceptance over async stdio on windows is still blocked (`drivers/gateway.
- Md` is
explicitly a preflight document, not a grant of `mode: execute`; the project stays read-only for
external repos (`docs/execute-sandbox-preflight.
- This matches the pyramid map's "8/9 ready" tally for the read-only driver contract
(`docs/pyramid-candidate-map.
- Py` covers composition, redaction, allowed-root
confinement and audit (`drivers/gateway.
- Any promotion from sandbox into the main
project must be a separate task, not an automatic merge (`docs/external-code-sandbox.
- The policy mandates per-process
`timeout_seconds` (default 30) and `max_output_bytes` (default 1mb) (`docs/driver-safety-policy.
- Py:40` sets `max_output_bytes = 1_000_000`, reads `max_bytes + 1` to detect
truncation, decodes only the first `max_bytes`, and returns a `truncated` flag plus the byte count
(`drivers/files/files_driver.
- Py`" as a portable "information
drivers" contract, marked **8/9 ready**, acceptance-tested (`docs/pyramid-candidate-map.
- Py` locks the contract deterministically with `today = 2026-06-23`
(`tools/test_validate_freshness.
- Db audit_log` (`docs/driver-safety-policy.
- Md:2`) lists the driver layer among l1 core-export candidates: "read-only
drivers `files/git-log/sqlite` + `drivers/schema.
- Md:59-61`); an
in-process regression `drivers/gateway/test_gateway.
- 3 freshness (the age-warn)

freshness is advisory and lives in
`driver_freshness_warning(date_str, today=none, max_days=driver_freshness_days)`
(`tools/validate.
- Json:36` |
| `gateway` | l2 | read-only | medium | **ready** | mcp | `drivers/catalog.
- Py:15-26`), a naive
`key: value` splitter — so list fields like `tools: [a, b]` arrive as raw strings and are split later
by `_parse_inline_list` (`tools/validate.
- Md:73-80`): medium/high risk ⇒ `audit: true`; `mode: execute`
forbidden without a separate decision; `secrets` must not be `in-repo`; `timeout_seconds`/
`max_output_bytes` required even at l1 so the future l2/l3 runtime is designed safe up front;
`source_last_verified` exists specifically to fight manifest drift against the real source.
- The minimal gate is a 10-row
table — decision, source (inventoried), sandbox (real isolation), permissions (no secrets/wide mounts),
network (`--network none` by default), limits (cpu/ram/pids/disk/timeout), logs (audit log), rollback
(`--rm` + separate workspace), validation (`tools/validate.
- Both the audit helper
and the redaction module trace to the t-078 review (audit finding e, redaction finding l:
`drivers/audit.
- The canonical folder name is `drivers/` (the metaphor "treiber"/"трайбер"
is allowed in prose but does not spawn a competing `trailers/` folder) (`decisions/d-010.
- Md` records the default rules: drivers are passive
(do not self-start), default mode is read-only, no secrets in `drivers/`, and running unverified code
needs a separate sandbox + decision (`drivers/readme.
- Md` and `docs/execute-sandbox-preflight.
- The intake is staged
s0–s7: decision/goal, intake manifest in `sandbox/inbox/`, quarantine in `sandbox/sources/` (untrusted
until inventory — no scripts/install/tests/hooks/binaries: `docs/external-code-sandbox.