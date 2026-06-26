---
id: sandbox-intake-2026-06-26-inf-zed-samples
type: sandbox-intake
status: proposed
owner: codex
date: 2026-06-26
source: C:/Users/stefan/Downloads
related:
  - zed-like-headless-workbench-mvp
  - zed-multiplayer-agents-analysis-2026-06-26
  - T-264
---

# Intake: 2026-06-26 .inf / Zed-like samples

This folder is a read-only sandbox copy of selected files from `C:/Users/stefan/Downloads` dated 2026-06-26. It is not mainline code and is not accepted architecture.

## Copied files

- `SPEC.md`, `README.md`, `RESULTS.md`
- `infon.py`, `test_infon.py`
- `inf_crdt.py`, `test_crdt.py`
- `inf_collab.py`
- `inf_accuracy.py`, `inf_falsify.py`
- `sample_nodelink.json`, `normenkg_slice.json`, `_groups.json`

## Why this intake exists

The files are useful as experimental material for the headless Zed-like workbench line:

- `.inf` block envelope, stable ids, typed links, graph walk and view slices;
- CRDT/convergence experiments for offline collaboration;
- context slicing, falsification and accuracy harnesses;
- possible inspiration for terminal-thread context assembly and view recall tests.

## Safety rules

- Do not execute these samples as part of normal validation.
- Do not promote raw scripts into `tools/` without a task, review and tests.
- Do not make `.inf` the canonical repository format by default.
- Do not use LWW body merge for canon text without conflict detection.
- Do not allow macros/tool calls from document text to execute commands.
- Treat local LLM calls in `inf_collab.py` as disabled until a separate local-LLM adapter and preflight exist.

## Preliminary static inventory

Static AST inventory from 2026-06-26:

- `infon.py`: stdlib imports; classes `Link`, `Block`, `Graph`, `C`; parser, Q6 vector, Hamming, cluster, walk, validate, view/tree/stats commands, nodelink import.
- `test_infon.py`: unittest coverage for parse, Q6, cluster, walk, validate, nodelink.
- `inf_crdt.py`: classes `LWW`, `ORSet`, `Doc`; merge/convergence utilities.
- `test_crdt.py`: unittest coverage for LWW, ORSet, merge laws, concurrent same block and round trip.
- `inf_collab.py`: converts graph blocks, renders `.inf`, calls llama-like endpoint, parses agent blocks, demo/laws commands.
- `inf_accuracy.py`: compares context regimes and grades whether reference closure recovers load-bearing facts.
- `inf_falsify.py`: measures context volume, repeated reads, Hamming distance and conflict behavior.

## Integration recommendations

1. Use the samples to design `thread.py` and `workspace-cell`, not to replace the repo format.
2. Use `inf_accuracy.py` idea as future acceptance: a view/context slice must recover linked exceptions outside the initial slice or explicitly flag missing evidence.
3. Use CRDT code only as research. For canon files prefer explicit conflicts over silent LWW body overwrite.
4. Keep any adapter code in `sandbox/drafts/code/` until promoted by a task/worktree.
5. Link findings to T-264 first; create later tasks for `view recall/accuracy` and block-level reconcile.

## Current status

- Raw copy completed: 13 files.
- No execution performed by Codex during intake.
- Subagent Rawls reviewed the samples read-only and recommended using them for view/context/accuracy hardening while rejecting `.inf` as immediate canon.