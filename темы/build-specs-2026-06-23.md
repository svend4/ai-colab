---
id: build-specs-2026-06-23
type: topic
title: Worktree-ready build specs (2026-06-23)
status: proposed
date: 2026-06-23
related: [Q-016, D-018]
---

# Worktree-ready build specs (2026-06-23)

Готовые edit-спеки для Codex-hot / post-ratification сборок: каждая секция ниже — это аддитивный, symbol-anchored план правок, который можно отдать в worktree без доразведки.

## Wiring `assurance.py` into the `top.py` apex (S1 top-wiring)

Five strictly **additive**, **symbol-anchored** edits to `C:/Users/stefan/Documents/New project ai colab/tools/top.py` that surface the apex verifiability dashboard (`tools/assurance.py`, Q-016 — applied/currency/coverage/flow) inside the `top.py` apex. The file is co-owned, so all edits are anchored to symbol names rather than line numbers; line refs below are orientation only. New elements only — no existing rows, checks, or subparsers are touched.

**Safety posture — advisory, never blocking.** `assurance` is in status **ATTENTION** today, so it is integrated as an advisory signal, not a hard gate. This rests on `assurance.py`'s exit contract: `return 1 if (strict and hard > 0) else 0` (`tools/assurance.py:382`) — exit 0 by default, nonzero only when `--strict` is passed AND there are hard findings. Every wiring point exploits this so a noisy verdict can never break `top.py` or turn health red.

**The five edits:**

1. **`_BUTTONS`** (append after the final `work-mode` dict, before the closing `]` on line 206) — add one additive button-row dict `id: "assurance"`, `audience: "both"`, `effect: "read-only"`, command `python tools/top.py assurance [section] [--json] [--strict] [--max-age N]`. Trailing comma preserved so the next co-owner append stays clean.

2. **`cmd_assurance`** (NEW handler, insert after `cmd_friction` which ends at line 284) — shells to `assurance.py` via the existing `_tool` + `_run` helpers, mirroring `cmd_friction`'s shape (optional positional `section`, `--json`, `--strict`, `--max-age` pass-through). Key line: `fail_ok=not args.strict` — advisory by default; only `--strict` flips `fail_ok=False` so a hard verdict surfaces a nonzero exit when the caller explicitly asks. No new parser/index, no mutation.

3. **`build_parser`** (NEW subparser block, insert after the `friction` block ending at line 497, before the `health` block) — additive `add_parser("assurance", ...)` mirroring `assurance.py`'s CLI: positional `section` with `choices=["applied","currency","coverage","flow","all"]`, plus `--json` / `--strict` / `--max-age` (type=int), `set_defaults(func=cmd_assurance)`.

4. **`cmd_health`** (insert between the existing `drift check (warning layer)` `_run` on line 298 and `return rc` on line 299) — one warning-layer `_run("assurance (warning layer)", _tool("assurance.py", "all"), timeout=90, fail_ok=True)`, placed AFTER the hard-checks loop and AFTER the drift warning. Runs WITHOUT `--strict` (so `assurance.py` exits 0) AND with `fail_ok=True` — double insurance. The existing checks list and `if step != 0` accumulation are untouched; health stays green.

5. **`cmd_agent_start`** (insert between the `top status` call on line 304 and the `if args.context:` block on line 305) — one advisory `_run("assurance (advisory)", _tool("assurance.py", "all"), timeout=90, fail_ok=True)` so a newly onboarded agent sees the apex verifiability snapshot at start. No `--strict`, `fail_ok=True`, and the function's returned `rc` (from onboard) is unchanged, so a noisy verdict cannot fail agent-start.

This is the "Codex-hot half of S1": the worktree-ready, top-wiring portion (button + `cmd_assurance` + subparser + `cmd_health` warning line + agent-start advisory).

## Weave governance decisions into the instruction surface (D-008/D-004/D-009/D-002)

**What to build.** A symbol-anchored, additive edit pass that weaves four ratified governance decisions into the project's instruction surface. Eight insertions across three files; every insert is appended/inline next to an existing exact-match anchor — no existing text is rewritten or deleted. Apply only **after** ratification (per D-006/D-018).

**Files and anchors.**

- **AGENTS.md** (3 edits):
  - **D-008** — appended after the `novax` registry row whose cell ends `…правки служебных файлов — с обоснованием по D-003` (`AGENTS.md:26-27`); adds the note that D-008 defines the boundary of a "significant" service-file edit requiring D-003 justification (structure, rules, decisions, tasks, statuses, protocol, agent rights, queues, templates, active topics = required; typos/formatting/typography = not).
  - **D-009** — appended after the line "Автоматический агент может добавлять решения со статусом `proposed`…"; documents new-agent onboarding: current stage = variant A (self-registration into the registry with justification in `dialog.md`), evolving to variant C (registration as proposal → maintainer approval) as agent count grows; `permissions.py` flags a new agent's governance edits as a signal, not a block.
  - **D-002** — inline `<!-- … -->` tag on the line "Для больших тем писать отдельные сообщения в `темы/<topic>/messages/`."; a large topic is a folder `темы/<topic>/` with `messages/`, one message = one file.

- **PROTOCOL.md** (3 edits):
  - **D-008** — appended at the end of §7 "Обоснование правок", after the "видимый след" paragraph (`PROTOCOL.md:133, 161`); restates the significance boundary.
  - **D-004** — appended in §8 next to "Правило D-006:" (`PROTOCOL.md:173`); each open question, before moving to `answered`, is framed as "варианты → плюсы/минусы → рекомендация → голоса → итог" (template `templates/decision-options.md`), with the итог carried into the decisions registry.
  - **D-002** — inline `<!-- … -->` tag on "Правило: **одно сообщение = один файл**." (`PROTOCOL.md:42`).

- **docs/agent-onboarding.md** (1 edit):
  - **D-009** — appended after the §2 "Граница (важно)" paragraph "агент **предлагает** решения…" (`docs/agent-onboarding.md:94`); spells out onboarding variant A now → variant C later, with `permissions.py` marking self-registration as a signal.

**Safety posture.** Advisory and additive by construction: all eight edits are pure insertions appended to or inlined beside verified, exact-string anchors drawn from `governance-proposals-2026-06-23.md`; no deletion or rewrite of existing instruction text. Enforcement stays advisory — `permissions.py` flags new-agent governance edits as a **signal, not a block**, and decision authority remains human (auto-agents leave decisions `proposed`; promotion to `accepted` is human/maintainer per D-006). Application is strictly gated on ratification (D-006/D-018). Anchors were re-verified against the live files at the cited lines before composing this spec.

Absolute paths: `C:/Users/stefan/Documents/New project ai colab/AGENTS.md`, `C:/Users/stefan/Documents/New project ai colab/PROTOCOL.md`, `C:/Users/stefan/Documents/New project ai colab/docs/agent-onboarding.md`.

## Hardening `check-report`: advisory reference verification

**Goal.** Upgrade `tools/instructions.py check-report` from token-presence checking to reference-verification — confirm that files and commands a report cites actually exist on disk — while keeping the new logic strictly **advisory** so it never tightens the existing evidence gate.

**Core constraint (verified on disk).** `check_report_text(text)` at `tools/instructions.py:369-382` returns a list of missing token strings only (`AGENTS.md`/`PROTOCOL.md`, `"Applied instructions evidence"`, `"Checks:"`). It is consumed as a **hard signal** by three call sites:
- `tools/assurance.py:137` — `ok = ... and not ins.check_report_text(text) ...`
- `tools/assurance.py:148` — `missing = ins.check_report_text(text)` (weak-evidence finding)
- `tools/pipeline.py:343` — `missing = check_report_text(marker_text)` (done-marker gate)

Folding path/command checks into its return list would make them blocking for done/commit and retroactively fail historic done-markers — contrary to the staged "warning before strict gate" plan (`docs/instruction-assurance.md:91,99`). Therefore `check_report_text` is left **untouched**, and the new behavior lands in a separate function. Tests at `tools/test_instructions.py:71-77` pin its exact return values (`[]` for ok cases; `"Checks:"` / `"Applied instructions evidence"` for bad cases) and must stay green.

**Design — all in `tools/instructions.py`:**
1. Add `import re` (currently only argparse/json/os/subprocess/sys at :14-18).
2. New advisory function `report_reference_findings(text, root=ROOT)` returning `list[str]` of human-readable findings (empty == clean):
   - **Path extraction:** scan whole report body for candidates via backticked tokens `` `([^`]+)` `` plus bare tokens matching repo extensions (`.md/.py/.json/.txt/.ps1/.ya?ml`) and `dir/...` shapes. A candidate qualifies if it contains `/` or a known repo extension, AND is not a URL (`://`), not absolute, not `..`, matching `^[\w./-]+$`. De-dupe preserving first-seen order; normalize `\` to `/`; join to `root` and `os.path.exists` each. Missing → `"referenced path not found: <ref>"`. Cap reported misses (~first 20). Canonical docs (`AGENTS.md`, `PROTOCOL.md`, `docs/instruction-assurance.md`) exist at root and SHOULD be verified (the point: catch a moved/renamed cited doc).
   - **Checks-command extraction:** find commands after a `Checks:` label, strip result annotations (`-> OK` / `=>` / `:`), and flag only high-confidence bogus cases — no plausible runner prefix (`python`/`python3`/`py`/`pytest`/`pwsh`/`powershell`/`git`/`node`/`npm`/`bash`/`sh`) → `"checks command not runnable-shape: <cmd>"`; `python tools/<x>.py` whose script is missing under root → `"checks command references missing script: <path>"`. **Read-only — nothing is executed**; plausible-but-unknown commands are not flagged.
3. Wire into `cmd_check_report` (:404-417) **only**: keep existing `missing = check_report_text(text)` plus MISSING/OK and rc 1/0 behavior unchanged; additionally compute `advisories = report_reference_findings(text)` and, if non-empty, print an `ADVISORY:` block. **rc stays driven solely by token `missing`** so shell-out callers are unaffected. Optional `--strict` flag (default off) may later promote advisories to rc=1 — safe because default preserves current behavior.

**Tests** to add in `tools/test_instructions.py` (extend existing `main`, keep prints): report citing an existing doc (`docs/instruction-assurance.md`) → `[]`; citing `docs/does-not-exist.md` → finding contains "referenced path not found"; `Checks:` commands → existing script gives no finding, `python tools/nope.py` → "missing script", `frobnicate the repo` → "not runnable-shape"; regression: asserts at :71-77 unchanged and passing.

**Docs to update** (advisory wording, no gate-promise): `docs/instruction-assurance.md:100` ('Дальше' item 2) mark implemented/advisory; `docs/top-layer-command-groups.md:139` note `check-report` now also prints advisory path/command findings (read-only, non-blocking).

**Safety posture.** Additive (separate function, no change to `check_report_text` contract), advisory/non-blocking (rc unchanged; gate semantics for assurance/pipeline preserved), symbol-anchored (wired through `cmd_check_report` only), and read-only (no command execution). This realizes instruction-assurance item-2 intent ("проверять ссылки на реально существующие файлы и команды") without coupling to the done/commit gate.
