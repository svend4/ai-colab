---
id: new-problems-2026-06-23
type: topic
status: resolved
date: 2026-06-23
related: [friction-subsystems-synthesis-2026-06-22, q016-assurance-state-2026-06-23, drivers-subsystem-state-2026-06-23, D-018]
---

# Three newly-surfaced producer-workflow problems + designs (2026-06-23)

Этот документ собирает три проблемы, которые выделились **из решения по уже готовой документации** — то есть всплыли не как новые исследовательские вопросы, а как конкретные расхождения между тем, что наши синтез-доки уже описывают, и тем, что живёт в коде репозитория `C:/Users/stefan/Documents/New project ai colab` на 2026-06-23. Каждая из трёх — это узкая, проверенная по исходнику дыра между двумя уже существующими подсистемами, у каждой есть аддитивный, символьно-привязанный дизайн-фикс и ясный режим выполнения (inline / worktree / ratify). Все три остаются `proposed` до распределения и приёмки.

Логика отбора одна и та же для всех трёх: синтез-док уже **заявляет** связь (cohort→friction cross-link; base↛apex трассируемость; gateway call-acceptance), а живой репозиторий эту связь **не держит** — указатель висячий, ключа нет, или приёмка завязана на сломанный транспорт. Ниже — проблема, дизайн и рекомендованный режим по каждой, плюс итоговая таблица назначений.

> **SHIPPED 2026-06-23 — все три зашиплены, документ переведён в `status: resolved`:**
> - **F-020 gate-poison** (`67fa8b5`): F-020 REGISTRY-запись + `check_gate_poison()` + `collect_status`/`recommendation` в `friction.py`; cohort→friction cross-link `gate-poison` теперь резолвится.
> - **Base↛apex** (`53e6d61` + `83ac920`): shared `surfaces`-ключ + read-only `trace(D-NNN)` в `instructions.py`; `section_flow` grounding в `assurance.py`.
> - **Gateway call-acceptance** (`T-174`): `drivers/gateway.md` ## Статус переписан — `call_tool` acceptance закрыта переносимым sync-путём; async stdio остаётся environment-dependent, трекается в T-174.

---

## F-020 gate-poison: wire the missing friction.py detector + cohort↔friction cross-link

### Problem, confirmed against source

The two collaboration-safety subsystems detect the **same** T-150-class incident (a foreign half-done task turns the shared `validate.py` gate red, blocking commits for everyone via the pre-commit hook) but they do not share one canonical id, and the cross-link they already advertise is **broken**.

- `tools/cohort.py` **already** has the primary probe. `guard()` shells `validate.py`, regexes `ERROR=(\d+)`, collects up to 3 `ERROR:` lines as evidence, and emits a `gate-poison` trigger:
  - `tools/cohort.py:355-359` — runs `validate.py`, `m = re.search(r"ERROR=(\d+)", val)`, `poison_errs = [...startswith("ERROR:")][:3]`, `poison = bool(m and int(m.group(1)) > 0)`.
  - `tools/cohort.py:369-370` — `if poison: triggers.append({"trigger": "gate-poison", "files": poison_errs or ["validate ERROR>0"], "recipe": "gate-poison"})`.
  - `tools/cohort.py:384-385` — prints the cross-link `"Рецепты (детектор Codex): friction.py recipe %s"` using `t.get("recipe")`, i.e. it literally tells the user to run **`friction.py recipe gate-poison`**.
- `tools/friction.py` REGISTRY ends at **F-019** (`tools/friction.py:262-271`); there is no F-020 and no `gate-poison` alias. `ALIASES` is built only from REGISTRY ids + their `aliases` (`tools/friction.py:275-279`), and `resolve_fid()` (`:630-634`) looks up exactly that map. So `friction.py recipe gate-poison` resolves to `None` → `cmd_recipe` prints `"Unknown friction id/alias: gate-poison"` and returns 1 (`:660-666`). **The advertised cohort→friction cross-link is a dangling pointer today.**
- `friction.py`'s `collect_status()` runs eight probes — runtime, git status, volatile, generate, commit_lock, pipeline, drift, stream, temp, sandbox, top, skill-links (`tools/friction.py:542-587`) — but **never runs `validate.py`**, so friction.py is blind to the single most dangerous shared-tree state, exactly as the synthesis docs note (`темы/friction-subsystems-synthesis-2026-06-22.md:86,94`; `темы/collab-safety-subsystem-2026-06-23.md:124-126`; `docs/engine-subsystems-overview-2026-06-23.md:37`).

The validate-side contract the detector must read: `tools/validate.py:461-465` prints each error as `ERROR: <msg>` then a summary `OK=N WARN=N ERROR=N` and `sys.exit(1 if ERRORS else 0)`. The half-done quarantine that distinguishes WARN vs ERROR lives at `tools/validate.py:164-171` (questions) and `:194-202` (tasks): an open/doing task whose topic file is missing = WARN (carantine), a **done** task with missing deliverable = ERROR (poison). This is the exact S1 mine-vs-foreign nuance F-020 should reference.

### Design — additive, symbol-anchored, worktree-ready (friction.py is co-owned by Codex)

All changes are additive (new dict entry + new function + one call) and touch no existing F-001..F-019 behavior, so a Codex-owned worktree can take them without index coupling.

**1. Add the F-020 registry entry** — append one dict after the F-019 block at `tools/friction.py:271` (closing `}` of F-019), before the `]` at `:272`. This is the only edit inside the shared `REGISTRY` literal and is purely additive:

```python
{
    "id": "F-020",
    "name": "Gate-poison: shared validate gate is RED",
    "symptom": "validate.py reports ERROR=N>0 (often a foreign half-done task: done card with a missing deliverable, broken topic link, bad front-matter, or duplicate id) so the pre-commit hook blocks commits for everyone.",
    "recipe": [
        "Run python tools/validate.py and read the ERROR: lines.",
        "If the offending source maps to YOUR claim, fix it; if it is foreign/unknown, do not wait — escalate to a Level 1 worktree from a CLEAN base (python tools/cohort.py guard for the verdict).",
        "Merge back only once the shared gate is green again.",
    ],
    "docs": ["темы/gate-poison-situation-2026-06-22.md", "docs/parallel-work-policy.md", "tools/cohort.py"],
    "aliases": ["gate-poison", "poison", "validate-error"],
},
```

The `"gate-poison"` alias is the load-bearing fix: it makes the cross-link emitted at `tools/cohort.py:385` (`friction.py recipe gate-poison`) resolve instead of erroring. `BY_ID`/`ALIASES` are rebuilt from REGISTRY (`:274-279`) with no code change.

**2. Add a `check_gate_poison()` probe** — a new module-level function mirroring the other `check_*` helpers (`tools/friction.py:424-539`), reusing the existing `run_cmd` (`:296`), `first_lines` (`:318`) and `make_check` (`:323`) helpers and the same `re.search(r"ERROR=(\d+)", out)` contract `cohort.py` already uses:

```python
def check_gate_poison(rc, out):
    text = out or ""
    m = re.search(r"ERROR=(\d+)", text)
    errs = [ln.strip()[:90] for ln in text.splitlines() if ln.strip().startswith("ERROR:")][:3]
    if (m and int(m.group(1)) > 0) or rc not in (0, None):
        return make_check(
            "F-020", "warn", "shared validate gate is RED (commits blocked for everyone)",
            evidence=errs or first_lines(text, 4),
            recipe_hint="Foreign half-done? escalate to L1 worktree from a clean base (cohort.py guard); merge when the gate clears.",
        )
    return make_check("F-020", "ok", "shared validate gate is green")
```

`import re` must be added to the import block at `tools/friction.py:16-21` (currently argparse/json/os/subprocess/sys/time — `re` is not imported). This is the only new import.

**3. Wire it into `collect_status()`** — additive call inside `collect_status` (`tools/friction.py:542-587`), placed alongside the other shelled probes (e.g. right after the `drift`/`stream` block at `:573-577`, before the temp probe at `:579`):

```python
val = run_cmd(PY, os.path.join(ROOT, "tools", "validate.py"), timeout=45)
checks.append(check_gate_poison(val["rc"], val["out"]))
```

**4. Cross-link the verdict (one canonical id, both directions):**
- cohort→friction is fixed automatically by step 1 (the `gate-poison` alias now resolves; `tools/cohort.py:384-385` already prints `friction.py recipe gate-poison`). No cohort.py edit is strictly required for the link to resolve.
- friction→cohort: extend `recommendation()` (`tools/friction.py:590-605`) so F-020 routes to the escalation verdict. F-020 is whole-tree commit-blocking (highest severity per the automation ladder `docs/friction-ledger.md:166-167`), so it belongs in the strongest non-runtime bucket — add `"F-020"` to the warn set at `:601` and have the message point to `python tools/cohort.py guard`:

```python
if warn_ids & {"F-006", "F-007", "F-011", "F-013", "F-015", "F-020"}:
    return "LEVEL 1 OR SELECTIVE-ADD: dirty/drift/stream/gate-poison signals; run `python tools/cohort.py guard` for the escalation verdict; do not use git add -A."
```

### Governance note (do not over-reach in this change)

The synthesis is explicit (`темы/friction-subsystems-synthesis-2026-06-22.md:109-111`, `:114`): only the **read-only detector** is in scope and pre-approved (it is already live in `cohort guard`). The **structural** fix — scoping `validate.py` per-agent/per-zone so one foreign ERROR does not block all — changes the shared gate contract, is owned by integrator/Stefan (D-021), and must go through D-017/D-018 collective acceptance. F-020 stays a proposed shared archetype until ratified; this PR adds only the detector + the canonical id + the cross-link, nothing that alters `validate.py`'s blocking behavior.

### Mode

**Inline + worktree.** Steps 1–4 are all additive to `tools/friction.py` (REGISTRY append, one new function, one import, one probe call, one route), touching no existing F-001..F-019 behavior and no `validate.py` logic — so a Codex-owned worktree can take it without index coupling. The detector half is **pre-approved** (already live in `cohort guard`); only the structural validate-scoping spinoff is **ratify** (D-021, gated by D-017/D-018). Ship the detector + canonical id + cross-link now; leave the gate-scoping as a separate ratified decision.

### Files / anchors

- `C:/Users/stefan/Documents/New project ai colab/tools/friction.py` — REGISTRY end `:262-272` (append F-020), imports `:16-21` (add `import re`), `make_check` `:323`, `collect_status` `:542-587` (add probe call), `recommendation` `:590-605` (route F-020), `resolve_fid`/`ALIASES` `:275-279,630-634` (auto-picks up new alias).
- `C:/Users/stefan/Documents/New project ai colab/tools/cohort.py` — gate-poison trigger `:355-359,369-370`, cross-link print `:384-385` (already emits `friction.py recipe gate-poison`).
- `C:/Users/stefan/Documents/New project ai colab/tools/validate.py` — error/summary contract `:461-465`, half-done quarantine `:164-171,194-202`.
- `C:/Users/stefan/Documents/New project ai colab/темы/friction-subsystems-synthesis-2026-06-22.md:86,94,105-114` — F-020 proposal + governance.
- `C:/Users/stefan/Documents/New project ai colab/темы/gate-poison-situation-2026-06-22.md:287-315` — incident + recommended F-020 ledger entry.
- `C:/Users/stefan/Documents/New project ai colab/docs/engine-subsystems-overview-2026-06-23.md:37` and `темы/collab-safety-subsystem-2026-06-23.md:124-126` — the documented drift this closes.

---

## Base↛apex: the missing shared key between the instruction registry and the promotion pyramid

### The break, confirmed in the live repo

There are three independent namespaces that never share a key, so no single lookup walks a base decision up to the apex:

1. **Instruction registry** — `tools/instructions.py:40-132` `INSTRUCTIONS` is a flat list of dicts keyed only on `id` / `path` / `scope` / `why` / `evidence` (e.g. `agent-rules`→`AGENTS.md`, `collab-protocol`→`PROTOCOL.md`, `instruction-assurance`→`docs/instruction-assurance.md`). `BY_ID` (`instructions.py:134`) indexes by the string id `agent-rules` etc. **No entry carries a decision id (`D-NNN`) or a pyramid level.** The only `D-NNN` anywhere in the list is inside a free-text `why` string — `"...D-003 обоснование правок..."` at `instructions.py:52` — which is prose, not a structured key (confirmed by grep: the sole hits are the `why` literal, the `evidence` literal at `:123`, and `"decisions"` as a directory name at `:389`).

2. **Pyramid levels** — `tools/promote.py:47-52` `LEVELS = ["L1","L2","L3","L4"]` with `level_of(artifact)` (`promote.py:59-72`) deriving a level **purely from the artifact's top-level directory** (`core`→L1, `portals`→L2, `tasks/decisions/questions/streams/темы/collab`→L3, `sandbox`→L4). A decision file lives in `decisions/`, so `level_of` always returns `"L3"` for it — there is no key that says "this decision is realized in instruction X" or "promoted to L1 core". The one place a decision id touches promotion is the L4→L3 gate's `_has_decision_ref(fm)` (`promote.py:92-101`) and the `decision_ref` stamp written by `move(...)` (`promote.py:261`), but that is a runtime gate argument, not a persistent registry link, and it is keyed on the *artifact being promoted*, not on the base decision.

3. **Base decisions** — `decisions/D-*.md` front-matter carries only `id, type, title, status, date, participants` (verified across D-001/D-002/D-004/D-008/D-009/D-023). They link to other decisions/docs **only in prose** (`Связано:` lines, e.g. `D-023.md:44`, and inline `D-022`/`D-018` mentions) — never via a parseable key, and never to an instruction id or a level. `_canon.parse_front_matter` (`tools/_canon.py:15-26`) is a plain `key: value` parser, so any new linking key must be a real front-matter field to be machine-readable.

### Why the assurance map already flags this

`tools/assurance.py:279-307` `section_flow` is the existing read-only detector of exactly this gap. It builds `surface_text` by concatenating the *bodies* of all `INSTRUCTIONS` files (`assurance.py:282-288`), then for every `accepted` decision checks `if did not in surface_text` and reports "accepted-решения, не упомянутые в поверхности инструкций" (`assurance.py:290-302`). This is a **substring scan over prose**, not a key join — it can only say "this `D-NNN` string does not appear anywhere in the instruction files." It cannot answer the structured question "which instruction surfaces decision D-008, and at which pyramid level does that surface sit." The `q016-assurance-state` topic (`темы/q016-assurance-state-2026-06-23.md:24`, and item #4 at `:73`) records these as "flow-сироты" (D-008/D-004/D-009/D-002) and the fix today is manual: hand-weave each decision's text into `AGENTS.md`/`PROTOCOL.md`/`docs/agent-onboarding.md` by symbol anchor. Nothing makes base↛apex one traceable path.

### Design: a shared key + a small read-only tracer

Two additive pieces, no behavior change to existing contracts:

**(1) Shared key `surfaces` on instruction entries.** Extend each relevant dict in `INSTRUCTIONS` (`instructions.py:40-132`) with an optional list field naming the base decisions that instruction operationalizes, e.g.:
```python
{ "id": "collab-protocol", "path": "PROTOCOL.md", ...,
  "surfaces": ["D-002", "D-003", "D-004", "D-008"] },
{ "id": "agent-onboarding", "path": "docs/agent-onboarding.md", ...,
  "surfaces": ["D-009"] },
```
This is the single shared join key the two namespaces lack: it points an instruction `id` at base `D-NNN`s. It is read by `manifest_payload`/`instruction_entry` (`instructions.py:207-216`, `333-334`) — just thread `surfaces` through `instruction_entry` so `manifest --json` exposes it. Pyramid level is derivable from the entry's existing `path` via `promote.level_of(os.path.join(root, item["path"]))` (`promote.py:59`): `AGENTS.md`/`PROTOCOL.md` resolve to `None` (root-level base files), `docs/...` likewise base — i.e. the surface sits at the foundation, and the apex is the `assurance.py` dashboard that consumes it. (Optionally add the inverse key `surfaced_by: [collab-protocol]` to decision front-matter for a two-way check, but one direction is enough to make the path traceable and avoids editing the ratify-gated decision registry.)

**(2) A read-only tracer `trace(decision_id)`** — a new function in `tools/instructions.py` (sibling to `manifest_payload`, read-only like the rest of the module, `instructions.py:333`) plus a `trace` subcommand in `build_parser` (`instructions.py:531-550`). For a given `D-NNN` it returns the one path:
```
base decision (decisions/D-NNN.md, status)
  → instruction surface(s)  : every INSTRUCTIONS entry whose "surfaces" contains D-NNN
  → pyramid level           : promote.level_of(entry path)  (per surface)
  → apex                    : assurance.section_flow grounding (now key-checked, not substring)
```
It reuses `BY_ID` (`instructions.py:134`), `promote.level_of` (`promote.py:59`), and `_canon.parse_front_matter` (`_canon.py:15`) for the decision's `status` — no new parser/index, matching the stated reuse discipline of `assurance.py:18-21`.

**(3) Tighten `section_flow` to use the key** (optional, same ship). Replace the prose substring test at `assurance.py:295-296` (`if did not in surface_text`) with a structured check: a decision is grounded iff some `INSTRUCTIONS` entry's `surfaces` list contains it. This turns the existing "висячие accepted-решения" finding (`assurance.py:298-302`) from a fuzzy text match into an exact join, and lets the apex dashboard report, per decision, *which* instruction and *which* level grounds it — i.e. base↛apex becomes one verifiable path that the `--strict` gate can enforce.

### Why this is the minimal correct shape
- The join key lives on the **instruction** side (`instructions.py`), not the decision side, so it does **not** edit the ratify-gated `decisions/` registry (the `темы/q016-assurance-state` doc marks decision-registry edits as "ratify"/котёл D-018; instruction-surface edits are the lighter path).
- Pyramid level is **derived** from the already-present `path` via `promote.level_of`, so no level field is duplicated or can drift.
- The tracer is read-only and reuses existing primitives, so it inherits the read/observe boundary that `assurance.py:18` and `friction.py` already hold, and can be wired into `top.py` exactly like the existing `cmd_assurance` (`top.py:295`) without becoming a mutator.

### Mode

**Inline.** Pieces (1)–(3) are all additive edits to two read-only tools (`instructions.py`, `assurance.py`): a new optional front-matter-free list field on instruction dicts, a new read-only `trace()` function + subcommand, and one substring→join swap. No mutator boundary is crossed and the ratify-gated `decisions/` registry is **not** touched (the join key lives on the instruction side by design). The only **ratify** sub-option is the inverse `surfaced_by` key on decision front-matter — leave it out of the first ship; one direction is enough for traceability.

### Key file:line references
- `tools/instructions.py:40-132` (`INSTRUCTIONS`, no decision/level key), `:52` (only `D-003` mention, in prose `why`), `:134` (`BY_ID`), `:207-216` (`instruction_entry`), `:333-334` (`manifest_payload`), `:531-550` (parser to extend with `trace`).
- `tools/promote.py:47-52` (`LEVELS`, `L3_DIRS`), `:59-72` (`level_of` — dir-derived, returns L3 for any `decisions/` file), `:92-101` (`_has_decision_ref` — runtime gate arg, not a registry link), `:261` (`decision_ref` stamp).
- `tools/assurance.py:279-307` (`section_flow` — substring scan that already flags ungrounded accepted decisions), `:295-296` (the `did not in surface_text` test to replace with the key join).
- `tools/_canon.py:15-26` (`parse_front_matter` — plain key:value; any link key must be a real front-matter field).
- `decisions/D-008.md:1-8` etc. (decision front-matter: `id/type/title/status/date/participants` only — no surface/level key; cross-links only in prose, e.g. `D-023.md:44`).
- `темы/q016-assurance-state-2026-06-23.md:24` and item #4 `:73` (records D-008/D-004/D-009/D-002 as flow-orphans, current fix is manual hand-weaving).

---

## Diagnosing and fixing the gateway's Windows async-stdio `call_tool` blocker

### What "ready-except-mcp-stdio-call-acceptance" actually means

The `gateway` driver composes three ready leaf drivers (`files`, `repo-runner`, `workbench`) into one MCP server named `ai-os-bridge` (`drivers/gateway/mcp_server.py:49`), exposing 6 tools via FastMCP `@mcp.tool()` decorators (`drivers/gateway/mcp_server.py:54-100`) and launched over stdio with a bare `mcp.run()` (`drivers/gateway/mcp_server.py:103-104`). Its manifest is `status: ready` (`drivers/gateway.md:5`), but the doc qualifies this at runtime: it is *not* considered to have passed full `call_tool` MCP acceptance in the official async stdio client on Windows until a separate runtime blocker is closed or a synchronous `tools/call` acceptance is added (`drivers/gateway.md:59`). The short formula given to other agents is "`ready` as manifest/tools-list contract; `ready-except-mcp-stdio-call-acceptance` as runtime status" (`drivers/gateway.md:61`). Crucially the gap is *not* in gateway logic — `initialize` and `tools/list` (handshake) pass; what was blocked is the vertical `tools/call` acceptance over the official async stdio transport.

### Root-cause diagnosis (what specifically fails)

The blocker is in the **MCP Python stdio client's async transport, not the gateway code**. It was diagnosed under T-081 and written up in `docs/mcp-stdio-windows-pipe-diagnostics-2026-06-21.md`. The precise failure chain (`docs/mcp-stdio-windows-pipe-diagnostics-2026-06-21.md:26-43`, `tasks/T-081.md:51-54`):

- Plain `subprocess.Popen(..., stdout=PIPE, stderr=PIPE)` **works** (`docs/mcp-stdio-windows-pipe-diagnostics-2026-06-21.md:17-24`).
- `asyncio.create_subprocess_exec(..., stdout=PIPE, stderr=PIPE)` **fails** at `asyncio.windows_utils.pipe -> _winapi.CreateFile -> PermissionError: [WinError 5]` (access denied) — the overlapped (named) pipe that the Proactor loop needs cannot be created in the affected runtime (`tasks/T-081.md:52`, `tasks/T-048.md:56`).
- The usual escape hatch — switching to `asyncio.WindowsSelectorEventLoopPolicy()` — does not help: the selector loop raises `NotImplementedError` for subprocesses (the selector event loop does not support subprocess transports on Windows) (`tasks/T-081.md:53`).
- The official MCP Python `stdio_client` uses exactly this failing `asyncio.create_subprocess_exec` path, so the handshake/acceptance dies *before* any server tool is reached (`docs/mcp-stdio-windows-pipe-diagnostics-2026-06-21.md:41-43`, `tasks/T-081.md:54`).

So: the server is healthy; the client-side async-stdio subprocess spawn is what is blocked. The interpretation in the diagnostics doc is explicit — the runtime "can run ordinary subprocesses, but cannot create the overlapped pipes used by `asyncio.create_subprocess_exec`" (`docs/mcp-stdio-windows-pipe-diagnostics-2026-06-21.md:41`). This is a runtime/permissions property of a specific Windows/Python environment (the Codex sandbox), not a gateway defect (`tasks/T-081.md:56`). The gateway's own in-process regression `drivers/gateway/test_gateway.py` exercises composition, redaction, allowed-root confinement and audit without stdio, "обходит Windows WinError 5" (`drivers/gateway/test_gateway.py:7-11`) — strengthening trust in the logic but explicitly not substituting for `call_tool` acceptance (`drivers/gateway.md:63`).

Environment note (verified read-only on this machine, 2026-06-23): the runtime here is Python 3.11.15 with the default `WindowsProactorEventLoopPolicy`, and on this box `asyncio.create_subprocess_exec(...)` *succeeds* (returns `b'123\r\n'`). This confirms the blocker is **environment-specific** (it bites the Codex sandbox / certain locked-down Windows runtimes), which is why the durable answer cannot rely on async stdio working everywhere — it must be a transport-independent acceptance path.

### The fix / workaround (already designed, verified here)

The chosen design is a **synchronous, transport-independent `tools/call` acceptance** that bypasses the async overlapped-pipe path entirely, staying fully read-only:

1. **Sync stdio probe (T-087)** — `drivers/mcp_sync_probe.py` implements `SyncMcpClient`, which spawns the server with plain `subprocess.Popen(stdin/stdout/stderr=PIPE)` (`drivers/mcp_sync_probe.py:65-72`), uses background reader threads for stdout/stderr (`drivers/mcp_sync_probe.py:75-95`), and speaks raw newline-delimited JSON-RPC: `initialize` → `notifications/initialized` → `tools/list` (`drivers/mcp_sync_probe.py:104-159`). Because it uses `subprocess.Popen` rather than `asyncio.create_subprocess_exec`, it works in environments where the async path fails (`drivers/mcp_sync_probe.py:3-8`). The gateway is a registered target (`drivers/mcp_sync_probe.py:32`).
2. **Sync `tools/call` acceptance (T-101)** — `drivers/mcp_sync_acceptance.py` reuses `SyncMcpClient` and extends it from handshake to a real `tools/call` on **every** tool with fixture arguments (`drivers/mcp_sync_acceptance.py:120-145`). For the gateway it calls all 6 tools — `files_list`, `files_read`, `files_search`, `files_summarize`, `repo_inspect`, `memory_query` — against `data/fixtures` inside the allowed-root (`drivers/mcp_sync_acceptance.py:62-69`). It checks FastMCP success via `not result.get("isError")` (`drivers/mcp_sync_acceptance.py:95-97`). A documented placement subtlety: the file lives in `drivers/` (not `tools/`) because `tools/queue.py` would shadow the stdlib `queue` that the sync probe depends on (`drivers/mcp_sync_acceptance.py:14-16`, `tasks/T-101.md:26-28`).

Verification (read-only, executed here 2026-06-23): `python drivers/mcp_sync_acceptance.py gateway` returns `SYNC ACCEPTANCE pass=6 fail=0 / RESULT OK` — all 6 gateway tools accept a real `tools/call`. This is the concrete, portable closure of the call-acceptance gap; the project-wide run reports 19→23 tools/call green across servers (`tasks/T-101.md:23`, `tasks/T-110.md:22`). A related transport hardening that made gateway's nested calls robust under pipe-stdio is the `stdin=subprocess.DEVNULL` fix for the `git` subprocess inside the MCP server, which otherwise inherited the asyncio server's stdin pipe and deadlocked on Windows overlapped I/O (`tasks/T-105.md:17-20`, `tasks/T-103.md:41`).

### Recommended resolution and safety posture

- **Primary recommendation:** treat the sync `tools/call` acceptance (`drivers/mcp_sync_acceptance.py`) as the canonical, environment-portable acceptance gate for the gateway, and update the gateway doc's operational caveat to "call-acceptance covered via portable sync path; official async stdio remains environment-dependent." This is the reconciliation T-110 already started for the older blocked tasks T-048/T-051 (`tasks/T-110.md:26`).
- **Secondary (true async-stdio fix):** because the failure is the Proactor overlapped-pipe `CreateFile -> WinError 5` and the selector loop raises `NotImplementedError` for subprocesses (`tasks/T-081.md:53`), there is no in-loop policy swap that fixes it; the only ways to get the *official async* client green are (a) run acceptance in an environment where `asyncio.create_subprocess_exec` with pipes succeeds — confirmed working on this host today and listed as a workaround in the diagnostics (`docs/mcp-stdio-windows-pipe-diagnostics-2026-06-21.md:52`), or (b) keep the sync subprocess client as the in-repo check (`docs/mcp-stdio-windows-pipe-diagnostics-2026-06-21.md:53`).

All of the above stays inside the safety envelope: the gateway is `mode: read-only` / `sandbox: not-required-for-read-only` (`drivers/gateway.md:7,15`), the execute-gate stays closed (the safety policy forbids running unvetted code/writes without a separate decision and real sandbox — `docs/driver-safety-policy.md:7-9`, risk ladder `:18-22`), and the acceptance path only reads fixtures within the allowed-root and routes every call through `drivers/audit.py` per the `audit: true` / risk-medium rule (`drivers/gateway/mcp_server.py:46,57`; `docs/driver-safety-policy.md:11`). No fix proposed here writes, executes external code, or widens the gateway beyond read-only.

### Mode

**Inline (doc reconciliation) — the code fix already landed.** The portable closure (`drivers/mcp_sync_probe.py`, `drivers/mcp_sync_acceptance.py`) is already shipped and verified green here, so the remaining work is the one read-only documentation edit: update the gateway doc's runtime caveat (`drivers/gateway.md:59-63`) to "call-acceptance covered via portable sync path; official async stdio remains environment-dependent," matching the T-110 reconciliation. No mutator, no execute-gate, no widening beyond read-only — pure inline.

---

## Рекомендованные назначения

| Problem | Кому / как | Mode | Effort |
| --- | --- | --- | --- |
| **F-020 gate-poison** — wire the missing `friction.py` detector + canonical id + cohort↔friction cross-link | Codex (co-owner of `friction.py`): worktree from a clean base; additive REGISTRY append + one probe + `import re` + one route. Detector half **pre-approved**. Validate-scoping spinoff → Stefan/integrator under D-021 (ratify, gated by D-017/D-018). | inline + worktree | S — small additive PR; one new function + dict + import + route. (Plus a separate ratify decision for gate-scoping.) |
| **Base↛apex shared key + tracer** — `surfaces` join key on instruction entries + read-only `trace(D-NNN)` + tighten `section_flow` | Any agent touching the assurance/instructions surface: edits live **only** on the instruction side (`instructions.py`, `assurance.py`), not the ratify-gated `decisions/` registry. Inverse `surfaced_by` key left out of first ship. | inline | M — one new key threaded through `instruction_entry`, one new tracer + subcommand, one substring→join swap; plus data entry of `surfaces` lists per instruction. |
| **Gateway Windows async-stdio `call_tool` blocker** — adopt portable sync `tools/call` acceptance as canonical gate | Code fix already landed and verified green (`mcp_sync_acceptance.py`, pass=6/fail=0); remaining task is the one doc reconciliation on `drivers/gateway.md:59-63`, aligned with T-110. | inline (doc) | XS — single doc-caveat edit; the code is already shipped and verified. |
