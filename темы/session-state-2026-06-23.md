---
id: session-state-2026-06-23
type: topic
title: Authoritative session state (2026-06-23) — shipped tools, open backlog, orchestration architecture
status: proposed
date: 2026-06-23
related: [engine-state-2026-06-22, workflow-conveyor-policy, perspective-backlog-2026-06-23, build-specs-2026-06-23, governance-proposals-2026-06-23, pyramid-grounding-plan-2026-06-23, Q-016, Q-017, D-018]
---

# Authoritative session state (2026-06-23)

Single canonical snapshot of where the project stands at the close of the 2026-06-23 session, folding three producer-workflow outputs into one record: **what was built** this session, **what open work remains** (the ranked, buildable backlog with dispositions), and **the orchestration architecture** that now governs how production and integration scale. It supersedes the scattered per-section drafts; the upstream spec docs it cites (`темы/perspective-backlog-2026-06-23.md`, `темы/build-specs-2026-06-23.md`, `темы/governance-proposals-2026-06-23.md`, `темы/pyramid-grounding-plan-2026-06-23.md`, `docs/workflow-conveyor-policy.md`) remain the live working surfaces; this doc is the consolidated state-of-record.

As of 2026-06-23 the conveyor's forward queue is empty in `TASKS.md` (everything "lives in the cauldron"), and `assurance.py` reports **ATTENTION** with three machine findings: currency-20, orphan-L1-12, flow-7 (`темы/perspective-backlog-2026-06-23.md:18`).

---

## Построено: tools and capabilities shipped this session

The `git log --oneline -28` window (top commit `91cd162`, down to `e57b78e`) introduced six distinct tool capabilities. Each is listed below with the commit that *introduced* it and a one-line purpose drawn from the tool's own module docstring.

| Capability | Introducing commit | Purpose |
|---|---|---|
| **`assurance.py`** — instruction-verifiability apex dashboard | `9465956` | Single READ-ONLY apex dashboard (Q-016) that folds four formerly-scattered signals — `applied` / `currency` / `coverage` / `flow` — into one verdict; mutates nothing, advisory by default, `--strict` exits 1 on findings (`tools/assurance.py:1-24`). |
| **`conveyor.py`** — workflow conveyor supervisor | `6623e28` | Supervisor that watches the workflow conveyor so it never drains: keeps an in-flight registry (`logs/conveyor.json`), emits a `REFILL` / `PROCESS` / `IDLE` verdict with exit code, and tracks orchestrator heartbeat staleness (`tools/conveyor.py:1-29`). |
| **`repo_search.py`** — FTS5 ranked documentation search | `052406c` | Ranked full-text search over repo documentation (docs/decisions/questions/темы/tasks), indexing content into FTS5 memory on top of the L6 `knowledge.py` engine (bm25); READ-ONLY, DB lives in gitignored `logs/` (`tools/repo_search.py:1-15`). |
| **`pipeline.py done` `--strict`** — applied-evidence done-gate | `78da3a3` | Opt-in `--strict` flag on `pipeline.py done` that turns the applied-evidence check from warn into a hard block (S3 of the Q-016 ladder); default stays soft. Gate logic at `tools/pipeline.py:356-373`, flag parsing at `:662-663`. |
| **`validate.py`** — driver `source_last_verified` age-WARN | `291f9a4` | Adds an advisory WARN in `validate.py` when a driver manifest's `source_last_verified` is older than the freshness threshold (>30 days), prompting re-verification against source; WARN does not fail the run. Logic at `tools/validate.py:24-39`, invoked in `check_drivers` at `:363`. |
| **`drift_check.py`** — content/currency-drift of references | `c135b4e` | Extends the drift detector to surface content-drift of references by pulling HIGH findings from `assurance.py currency --json` (broken structural links + links to superseded decisions) into the drift summary (`tools/drift_check.py:67-82`, wired at `:115-117`). |

### Notes on attribution

- **Follow-on commits** in the same window refined these tools but are not the introducing commit: `fb0dfc7` (repo_search clickable paths/snippets), `d16903c` + `8efc85a` (conveyor `target N` command and landed-output refs), and `cf25296`/`c7688fd`/`84c4731` (surfacing repo_search/conveyor/context-search in the top layer). The introducing commits are the ones cited in the table above.
- All six tools follow the repo's read/observe convention: `assurance.py`, `repo_search.py`, and `drift_check.py` are READ-ONLY and store any indexes/state under gitignored `logs/`; the `validate.py` and `pipeline.py` additions are advisory-by-default with strictness opt-in.
- The `drift_check.py` currency capability explicitly depends on `assurance.py` (it shells out to `assurance.py currency --json`), so it could only land after `9465956`.

---

## Осталось: the buildable backlog and its dispositions

The remaining open work is captured across four spec docs as a ranked backlog plus worktree-ready edit specs. Below are the buildables, each with its **mode** and the **spec doc** that holds it.

### Ranked backlog (queue-of-record)

`темы/perspective-backlog-2026-06-23.md:40-54` is the ranked, deduplicated queue (25 raw → 13 items). Each row carries an explicit "Вид" (mode) column:

| # | Item | Effort | Mode (Вид) |
|---|---|---|---|
| 1 | **Q-016 done-gate** — wire `check_report` into `pipeline.py` `cmd_done` (today `cmd_done` at `pipeline.py:342-343` only prints WARN, never calls `check_report`) | S | `worktree-build` |
| 2 | **F-020 gate-poison detector** — wire the gate-poison / validate-ERROR probe into `friction.py` (incident class T-150) | S | `worktree-build` |
| 3 | **Q-017 `--semantic` doc-merge** — add `report --semantic` to `doc_consensus.py` (mechanical high-thr pre-cluster + subprocess agent-pass over residue, `_merge` by unit-id, `status:proposed` output) + "one idea, different words" fixture | M | `worktree-build` |
| 4 | **Populate L2 portals** for the 12 orphan-L1 core modules (only `portals/example/portal.md` exists) | M | `worktree-build` |
| 5 | **check-report hardening** — extend `instructions.py check-report` to verify referenced files and check-commands actually exist (not just token presence) | S | `worktree-build` |
| 6 | **Currency migration** — adopt `last_verified` front-matter across the 20 accepted decisions/policies that lack it; moves currency-gate from observe → enforce | S | `cauldron-task` |
| 7 | Assurance Wave-2: build `tools/instruction_freshness_check.py` | M | `workflow` (depends on #6) |
| 8 | Update stale "not yet implemented" claims in `docs/parallel-work-policy.md` | S | `worktree-build` |
| 9 | Assurance Wave-3: build `tools/promotion_coverage.py` (reverse upward-flow check) | L | `workflow` (depends on #4) |
| 10 | ~~`reconcile_state.py` `fix` subcommand~~ — **SHIPPED 2026-06-23 (`94c3c35`)**: `cmd_fix` at `tools/reconcile_state.py:259`, dry-run + `--apply`, derived-only; no longer a stub | M | done |
| 11 | Flow orphans: wire the 7 dangling accepted decisions into the instruction surface or mark background-only | S | `cauldron-task` |
| 12 | Decision batch (vote-gated): Q-010 rename, Q-013 onboarding, gate-poison shared-gate contract, two-commit divergence (D-018) | M | `decision` (ratify) |
| 13 | Q-009/T-020 svend4 source access: choose A / B / C | S | `decision` (ratify) |

The backlog's own framing (`:20-26`): items 1–3 are independent, touch different subsystems (gate / friction / doc-merge) and parallelize cleanly; item 4 is the fourth wave-slot and unblocks Wave-3; decision-track items (12, 13) go through the cauldron/vote and do **not** block builds.

### The six named buildables, fully specced

**1. `derive_reuse` (effort M) — mode: worktree-build; spec: `темы/pyramid-grounding-plan-2026-06-23.md`.**
This is backlog item #4 fully specced. `pyramid-grounding-plan-2026-06-23.md:66-72` ("Buildable") defines `derive_reuse(root)` in `promote.py`: build the L1 inventory from engine-manifest `files:` + `core/*.md`, scan which portals reference each L1 artifact (basename-substring, same mechanic as orphan-L1 / `assurance._portal_text`), and return `token->portals`. The critical fact (`:46-48`, `:20`): `reused_in` has **zero writers** anywhere in the repo (only read at `promote.py:140`, `assurance.py:267`, doc'd at `promotion-rules.md:52`), so `reuse_across_portals` can never pass today and a hand-edited field could fake it. The fix is derived coverage stamped via `_stamp_fm` as provenance, not an author claim. Touches `tools/promote.py`, `tools/assurance.py`, `core/engine-manifest.md`, `portals/example/portal.md`, `docs/promotion-rules.md`, `tools/test_assurance.py` (`:72`). All stdlib, root-hermetic. Application stays `status: proposed` under D-018 collective ratification (`:22`, `:64`).

**2. F-020 gate-poison (effort S) — mode: worktree-build; spec: `темы/perspective-backlog-2026-06-23.md` (rank 2, `:43`/`:35`).**
Wire the gate-poison / validate-ERROR probe into `friction.py` as the F-020 detector; the detector is today blind to the most dangerous shared-tree state (incident class T-150). Independent of the others. Note this item appears only in the perspective backlog — `build-specs-2026-06-23.md` does **not** carry a symbol-anchored edit spec for it (unlike top.py-wiring and check-report below).

**3. Q-017 `--semantic` (effort M) — mode: worktree-build; spec: `темы/perspective-backlog-2026-06-23.md` (rank 3, `:44`).**
Add `report --semantic` to `doc_consensus.py`: mechanical high-threshold pre-cluster + subprocess agent-pass over the residue, `_merge` by unit-id, `status:proposed` output, plus a "one idea, different words" fixture. Direction is already ratified and the spec is described as ready; only implementation + fixture remain. Held in the backlog doc, not in `build-specs`.

**4. `top.py` wiring (S1 top-wiring) — mode: worktree-build ("Codex-hot half of S1"); spec: `темы/build-specs-2026-06-23.md:14-32`.**
Five strictly **additive**, symbol-anchored edits to `tools/top.py` surfacing the `assurance.py` verifiability dashboard (Q-016) inside the `top.py` apex: (1) append an `id: "assurance"` row to `_BUTTONS` (before the closing `]` ~line 206); (2) new `cmd_assurance` handler after `cmd_friction` (~line 284), `fail_ok=not args.strict`; (3) new `assurance` subparser in `build_parser` after the `friction` block (~line 497) with `choices=["applied","currency","coverage","flow","all"]`; (4) a warning-layer `_run(...assurance..., fail_ok=True)` in `cmd_health` (~line 298); (5) an advisory `_run` in `cmd_agent_start` (~line 304). **Safety posture is advisory, never blocking** — `assurance.py` is in ATTENTION today, and its exit contract `return 1 if (strict and hard > 0) else 0` (`tools/assurance.py:382`) means exit 0 unless `--strict` is passed with hard findings, so a noisy verdict can never turn `top.py` health red (`build-specs-2026-06-23.md:16-18`).

**5. Currency migration (effort S) — mode: cauldron-task / ratify (S0 governance-commit); spec: `темы/governance-proposals-2026-06-23.md:34-52`.**
Backlog item #6 (`perspective-backlog-2026-06-23.md:47`, mode `cauldron-task`). Promote the driver-level `source_last_verified` (origin D-013:40, semantics D-015:42-43) to a `last_verified: YYYY-MM-DD` key on accepted decisions/policies. Rules (`governance-proposals-2026-06-23.md:39-47`): stamp **today (2026-06-23), not back-dated** (back-dating either lies or instantly lights freshness ~23×); accepted/policy only (`assurance.py:203` already gates on `status==accepted`); one SLA per corpus (90d governance / 30d drivers — fix the `assurance.py:361` default `--max-age=180` vs `driver-safety-policy.md:14`=30 mismatch); warn→block ladder, `currency --strict` only at S4. **Migration S0 (`:49-52`): one governance commit, no code** — stamp `last_verified: 2026-06-23` on **20 accepted decisions** (D-001..D-013, D-015..D-018, D-021..D-023) + **4 policies** (`parallel-work-policy`, `promotion-rules`, `workflow-orchestration-policy`, `instruction-assurance`, hardwired at `assurance.py:181-184`). Implementation **after ratification** (D-018, "не solo").

**6. check-report hardening (effort S) — mode: worktree-build; spec: `темы/build-specs-2026-06-23.md:57-79`.**
Backlog item #5 (`perspective-backlog-2026-06-23.md:46`). Upgrade `tools/instructions.py check-report` from token-presence to reference-verification, kept strictly **advisory** so it never tightens the existing evidence gate. The constraint (`build-specs-2026-06-23.md:61-66`): `check_report_text` at `instructions.py:369-382` is a **hard signal** at three call sites (`assurance.py:137`, `assurance.py:148`, `pipeline.py:343`), so it is left untouched and new logic lands in a separate function `report_reference_findings(text, root=ROOT)` (`:70-72`) that extracts cited paths and `Checks:` commands, `os.path.exists`-checks them read-only (nothing executed), and emits human-readable findings. Wired into `cmd_check_report` (`:404-417`) **only**, printing an `ADVISORY:` block; **rc stays driven solely by token `missing`** so shell-out callers are unaffected (`:73`). Tests extend `test_instructions.py` keeping the `:71-77` asserts green; docs update `docs/instruction-assurance.md:100` and `docs/top-layer-command-groups.md:139`.

### Also remaining (governance / ratify track)

Two additional dispositions sit in `темы/governance-proposals-2026-06-23.md` and `темы/build-specs-2026-06-23.md` that gate other work but are themselves **ratify-mode** (cauldron D-018, apply only after ratification per D-006/D-018):

- **7 flow-orphan dispositions** (`governance-proposals-2026-06-23.md:16-30`): weave D-008, D-004, D-009, D-002 into the instruction surface; keep D-001/D-010/D-013 background-only. The corresponding **edit spec** for the four "вплести" decisions is `build-specs-2026-06-23.md:34-55` — eight additive, symbol-anchored insertions across `AGENTS.md`, `PROTOCOL.md`, `docs/agent-onboarding.md`, advisory and gated on ratification.

These two (flow-orphans, currency) are the cauldron/decision items #6, #11, #12 in the ranked backlog and explicitly do **not** block the worktree builds above.

---

## Архитектура: the conveyor pipeline, supervisor signals, and the producer/integrator brigade

The orchestration layer is specified in `docs/workflow-conveyor-policy.md` and implemented in `tools/conveyor.py`. It sits **above** the single-workflow orchestration policy (`docs/workflow-orchestration-policy.md`): that base policy defines one workflow (one cluster of parallel sub-agents launched in background); the conveyor policy is the layer that runs **≥2 workflows as a pipeline** — staggered launch, return-to-first draining, and a self-feeding backlog (`docs/workflow-conveyor-policy.md:10-12`).

### The conveyor as a STREAM, not a BATCH (§3-bis)

The core principle is that a pipeline is a **flow**, not a batch. The named anti-pattern is treating it as "one batch of N": launch 3 → process 3 → empty → stall. That stall wastes wall-clock; the conveyor must instead keep the next nodes already running while the current result is being processed (`docs/workflow-conveyor-policy.md:55-72`). The discipline rules:

- **Refill EARLY, not after** — launch the next node the moment you *begin* processing a completed one (at its RELEASE/REPLENISH step), not after fully finishing it, so no idle gap opens between "done" and "launched next" (`:59`).
- **Never drain in-flight to zero** — hold a target of N≈2-4 workflows in flight; if the counter falls toward 0-1 and commit-bandwidth allows, top it up (`:60`).
- **A standing backlog feeds the pipeline** — a recurrent **backlog-scanner workflow** (surfaces: open `Q-*`, todo tasks, `assurance.py`/`drift_check` findings, doc "Next" sections, `TODO`/`FIXME`) emits ranked launchable briefs for the next wave, so the conveyor **feeds itself**. Its out-degree is maximal (it gates all future launches), so it sorts first topologically (`:62`).
- **The flow boundary is COMMIT bandwidth, not desire** — an unread `.output` on disk wastes wall-clock exactly like an idle orchestrator, so N is tuned to the processing band, not the worker maximum (`:63`).

### The supervisor `tools/conveyor.py` and its REFILL/PROCESS/IDLE signals (§3-ter)

Because the orchestrator is a single context that can "forget" to refill, drift into a foreground build, and silently drain the pipeline to 0-1, discipline alone is insufficient — an **external watchdog process** is required (`docs/workflow-conveyor-policy.md:74-78`). `tools/conveyor.py` is that watchdog: a read-mostly registry plus signal emitter.

- **Registry** at `logs/conveyor.json` (runtime, gitignored), mutated by `conveyor.py launch/land/ship/dismiss <id>`; every action also writes an orchestrator **heartbeat** (`tools/conveyor.py:36-40`, `:93-116`). The state machine is `inflight → landed → shipped | dismissed`; `land --output <path>` records a machine-readable reference to the durable result so the orchestrator can extract work without searching chat/terminal (`docs/workflow-conveyor-policy.md:80-93`, `tools/conveyor.py:226-228`).
- **`conveyor.py status`** counts in-flight against the target and prints a VERDICT plus an **exit code** (1 = action needed, so it can be polled from a hook/CI/wakeup). The pure assessment lives in `assess()` (`tools/conveyor.py:129-167`) and emits exactly these signals (`tools/conveyor.py:144-155`, doc `:84-88`):
  - **REFILL** — in-flight < target (top up; `conveyor.py next` pulls candidates from the perspective backlog).
  - **PROCESS** — landed workflows are waiting to be processed (with a `PROCESS-MISSING-OUTPUT` variant when a workflow landed without an attached `--output` ref).
  - **IDLE** — heartbeat is older than the threshold: the orchestrator has gone silent (hung or forgot to tick).
- **Discipline:** on EVERY wake (a workflow-completion notification OR a message) run `conveyor.py tick` + `status`; on REFILL, launch. This makes "never drain to zero" **verifiable** rather than memory-dependent (`docs/workflow-conveyor-policy.md:89-93`).
- **Keeping the orchestrator alive** (it is event-driven): (1) workflow-completion notifications self-re-invoke it; (2) a Claude Code `Stop` hook in `.claude/settings.json` prints the verdict after each response; (3) `ScheduleWakeup`/cron gives a timer heartbeat — the only way to survive a *full* drain when no notifications remain (`docs/workflow-conveyor-policy.md:95-104`).

Critically, the supervisor **does not launch workflows itself** — it is read-mostly and only **signals**; the decision and launch stay with the orchestrator, mirroring the system's separation-of-concerns pattern where "`friction.py` signals, `cohort.py` executes" (`docs/workflow-conveyor-policy.md:105-106`; both tools confirmed present at `tools/friction.py` and `tools/cohort.py`).

### Fleet scale (§3-ter, end)

The target is **not hard-wired to 2**: `conveyor.py target <N>` raises it on demand (default `DEFAULT_TARGET = 2`, `tools/conveyor.py:39`, `:240-246`). With many open questions you launch a **fleet** — one workflow per question (5, 8, more) — because launch is cheap and parallel, so *production* scales freely. The ceiling is the **processing band of the single orchestrator**: results land in a `landed` queue but can only be extracted/re-verified/committed serially. If the `landed` queue grows faster than processing, the watchdog prints `PROCESS: N waiting` — a signal **not** to launch more but to clear the backlog. The fan-out technical ceilings (≈16 agents/workflow, 1000/run) sit far above real need; the commit band binds first (`docs/workflow-conveyor-policy.md:108-115`).

### Parallelizing the CONSUMER — the integrator/brigade model (§3-quater)

When the bottleneck is the consumer (the orchestrator) rather than the producers, it too is parallelized by splitting processing into two parts of different nature (`docs/workflow-conveyor-policy.md:117-134`):

- **COMPOSITION of a result** (read the `.output`, re-verify, assemble a clean canonical artifact) is the expensive "thought" — and it **parallelizes freely**. It is handed to an **integrator-workflow**: fan-out of one composer-agent per landed output, each returning a finished `{path, content, commit-msg}` artifact. Literally "workflows that clear up what other workflows brought in" (`:121-125`).
- **INTEGRATION into a single git history** (write file + commit/merge) is **irreducibly serial** — one canon, one `index.lock` — but **cheap** (write + commit take milliseconds, not minutes of thinking). Parallelizing commits via worktree only relocates the serial point into `merge` (the same integration into one history). The system's unique serial point is **one canonical history**, and its cost is ≈ a write, not thought (`:126-129`).

So "multiple orchestrators" = multiple composer-agents/integrator-workflows in parallel, while the single integrator (one git tree) collapses to a cheap final step: gather the finished artifacts and **batch-commit them as a cohort**. The pipeline becomes **two-sided** — a wide producer front + a wide consumer front (composer-agents) + a thin, cheap integrator (`docs/workflow-conveyor-policy.md:131-144`):

```
producers (wide front)  →  landed queue (with output-ref, §3-ter)  →
   integrator-workflow: one composer-agent PER output  (wide, parallel)  →
      orchestrator: write + BATCH commit  (narrow, but cheap — the single serial point)
```

### The single cheap serial git-integration point

The whole architecture is engineered so the one unavoidable serial step is also the cheapest. Concretely the cohort ships via `tools/cohort.py guard` → Level-0 `ship` (own files, selective-add, never `git add -A`) or Level-1 worktree + `merge_gate` if guard flags hot/shared files or a build (`docs/workflow-conveyor-policy.md:202`; tooling confirmed at `tools/cohort.py`, `tools/merge_gate.py`, `tools/worktree.py`). Commit serialization itself is protected by a TTL self-healing lock, `tools/commit_lock.py acquire <agent> --ttl <T> --wait <W>` (atomic O_EXCL with `lease_epoch` and stale-takeover, proven by `tools/test_commit_lock.py`) (`docs/workflow-conveyor-policy.md:213`). The system's stated limit is therefore not "how much to think" but "how much can be integrated into one history" (`docs/workflow-conveyor-policy.md:144`).

### Relation to collective decision-making

The conveyor is also the substrate for the project's decision process: under `decisions/D-018.md` (accepted 2026-06-21), all substantial questions go into the **котёл** — a `pipeline.py` pool-task to drive X to consensus — and must pass a dual re-check (technical: code works + ≥2-agent cross-check per D-015; humanitarian: human/values/consequences). The conveyor policy routes contentious/cross-agent side-branches there as a котёл task rather than a solo build (`docs/workflow-conveyor-policy.md:180`, `decisions/D-018.md:18-30`).

> **Status note:** the policy doc carries `status: proposed`, dated 2026-06-23 (`docs/workflow-conveyor-policy.md:5`). The supervisor implementation `tools/conveyor.py` already exists and faithfully implements the REFILL/PROCESS/IDLE verdicts, registry, heartbeat, and `next`/`target` commands described above. This state doc is likewise `status: proposed` and applies under D-018 collective ratification ("не solo").
