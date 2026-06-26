---
id: outbox-2026-06-26-zed-headless-workbench-plan
type: outbox
status: proposed
owner: codex
date: 2026-06-26
related:
  - zed-like-headless-workbench-mvp
  - zed-multiplayer-agents-analysis-2026-06-26
---

# Outbox: Zed-like headless workbench plan

Codex read the Zed article, primary Zed docs, and the provided Claude JSON export.
Subagents Ptolemy, Goodall and Hegel returned read-only perspectives.

## Main proposal

Do not clone Zed GUI now. Build a headless/file-native Zed-like workbench:

```text
thread registry
terminal-thread descriptor
workspace-cell status card
local LLM adapter
MCP/read-only gateway
sandbox/drafts for code variants
stream/worktree/synthesis adoption path
```

## New repo artifacts

- `docs/zed-like-headless-workbench-mvp.md`
- `topics/zed-multiplayer-agents-analysis-2026-06-26.md`

## Consensus candidate

- Zed is useful as architecture: threads, worktree isolation, external agents,
  terminal threads, MCP and local model routing.
- Current repo already has many headless equivalents: `top.py`, `pipeline.py`,
  `conveyor.py`, `stream.py`, `worktree.py`, `flow.py`, `merge_gate.py`,
  `drivers/gateway`.
- Missing first-class object: one durable `thread/workspace-cell` that links
  conversation, task, stream, worktree, output and checks.
- Offline path should be optional and local-first: Ollama/LM Studio/OpenAI-compatible
  adapter, no required network.
- Code-writing agents should write first to `sandbox/drafts/code/` or worktree,
  never directly to shared mainline hot files.

## Open disagreements

- Thread registry source-of-truth: topic-local folders vs global `logs/threads.json`.
- How soon to build local LLM adapter versus thread schema first.
- Whether ACP adapter is worth building before terminal-thread descriptor.
- Whether thread messages should be Markdown-first, JSON-first or hybrid.
- When CRDT/Automerge/Yjs should enter the mainline architecture.

## Suggested next implementation batch

1. Create task: `thread schema MVP`.
2. Build `tools/thread.py init/status/add-message` stdlib-only.
3. Add `tools/test_thread.py`.
4. Add `top.py workspace-cell <id> --json`.
5. Add docs for terminal-thread descriptor.
6. Add `sandbox/drafts/code/README.md` convention.
7. Only then build local LLM adapter and optional `thread ask`.
## Downloads intake update

A selected read-only copy of today's `.inf`/CRDT/context samples was placed in:

```text
sandbox/intake/2026-06-26-inf-zed-samples/
```

Subagent Rawls and Lorentz both recommend the same policy:

- use these samples for `view/context` and terminal-thread context assembly tests;
- do not make `.inf` the canonical repo format now;
- keep local-LLM and `--llama` paths disabled until an adapter/preflight exists;
- reject silent LWW body merge for canon text;
- promote only reviewed, tested pieces through normal task/worktree flow.

Immediate follow-up after T-264: create a `view/context recall` task inspired by `inf_accuracy.py` and `inf_falsify.py`.
