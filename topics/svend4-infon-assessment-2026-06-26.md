---
id: svend4-infon-assessment-2026-06-26
type: topic
title: svend4/infon assessment for multi-agent repo work
status: proposed
owner: codex
date: 2026-06-26
related:
  - zed-like-headless-workbench-mvp
  - zed-multiplayer-agents-analysis-2026-06-26
  - T-264
---

# svend4/infon Assessment For Multi-Agent Repo Work

## 1. Independent Codex view

`svend4/infon` is valuable for this project less as a video-call product and more as a set of architectural metaphors and concrete protocol patterns:

- terminal-first interaction;
- headless/offline operation;
- protocol-first design;
- event packets with sequence/timestamp/payload;
- degraded rendering depending on terminal capability;
- swappable AI brain endpoint;
- local deterministic fallback before real model calls;
- P2P/offline transport as a later layer, not the core state model.

For this repository, the correct adaptation is not terminal video. The correct adaptation is **terminal workbench telemetry**: compact status cards, append-only event logs, thread transcripts, brain request/response envelopes and import/export bundles.

## 2. What to take now

### 2.1. Protocol first, transport second

`infon` separates the idea of data packets from the concrete transport. Our repository should follow the same rule:

```text
thread.v1             -> durable file thread
terminal_thread.v1    -> descriptor for terminal-backed sessions
workspace_cell.v1     -> task/thread/stream/worktree/checks card
brain_request.v1      -> optional local/cloud model request
brain_response.v1     -> model answer as proposal, not authority
```

Transport can be file/git now, localhost HTTP later, P2P/Yggdrasil much later.

### 2.2. Swappable brain endpoint

The `tvcp-ai/1` idea of changing the brain by URL maps well to our future local model layer. In this repo it should become metadata, not governance:

```json
{
  "schema": "brain_request.v1",
  "thread_id": "thread-...",
  "kind": "answer|plan|check|propose_patch",
  "mode": "read-only|draft|build",
  "brain_url": "http://127.0.0.1:11434/v1",
  "context_hash": "...",
  "allowed_tools": ["files_search", "repo_inspect"],
  "allowed_writes": ["sandbox/drafts/"],
  "max_output_chars": 12000
}
```

The response is still a proposal. It cannot approve decisions or mutate canon by itself.

### 2.3. Terminal status cards

The terminal video renderer is not directly needed. But the idea of compact terminal frames is useful for:

```text
python tools\top.py workspace-cell <id>
python tools\thread.py status <id>
python tools\conveyor.py status
```

Render modes should degrade:

- JSON canonical output for tools;
- plain text table for basic terminal;
- ANSI/card output only as optional view.

### 2.4. Event envelope

For terminal-thread transcripts, use event envelopes inspired by packet design:

```json
{
  "seq": 12,
  "timestamp": "2026-06-26T...Z",
  "kind": "message|tool_result|status|heartbeat|output_ref|error",
  "thread_id": "thread-...",
  "byte_count": 2048,
  "truncated": false,
  "sha256": "...",
  "payload_ref": "messages/20260626-....md"
}
```

This is more useful than recording raw terminal flood as one giant text file.

### 2.5. Safe fallback chain

For AI/model work, adopt fallback chain:

```text
real model endpoint -> localhost mock -> deterministic reference brain -> dry-run preview
```

Normal repo operations must not require a local model. If no endpoint exists, the tool prints `NOT CONFIGURED` and exits cleanly.

## 3. What to adapt later

1. `thread-brain.v1` mock protocol with no real model.
2. Local OpenAI-compatible/Ollama adapter after T-264 and workspace-cell.
3. Terminal-thread descriptor with `cwd`, `command`, `env_policy`, `allowed_writes`, `transcript`, `pty_mode:false`.
4. Export/import bundles for thread events.
5. Optional P2P/Yggdrasil transport only after bundles are stable.
6. Optional richer terminal cards after JSON contracts are stable.

## 4. What not to take

- Do not copy TVCP video/UDP/P2P stack into this repo now.
- Do not make live terminal video the collaboration substrate.
- Do not let a brain endpoint execute commands or write files directly.
- Do not replace append-only Markdown/JSON canon with a live HTTP service.
- Do not make Ollama/local LLM required for normal operation.
- Do not treat alpha documentation as proven production design.

## 5. Advice to svend4/infon

If advising `svend4/infon`, I would suggest:

1. Separate `tvcp-core`, `tvcp-ai`, `tvcp-network`, `tvcp-renderer` documentation more sharply.
2. Mark which docs are implemented, experimental or aspirational at the top of each file.
3. Add a machine-readable capability manifest for AI brain protocol: supported kinds, max sizes, timeout, streaming, safety mode.
4. Add `context_hash` / `input_hash` to AI requests so stale model responses can be detected.
5. Keep AI brain responses as proposals/events, not implicit commands.
6. Provide a tiny reference brain and golden test corpus for `tvcp-ai/1`.
7. Add terminal capability matrix and renderer fallback tests.
8. Add event-log/export format for non-video collaboration, because text/agent workflows are a natural adjacent use case.
9. Split P2P transport from application protocol so file/git/HTTP/Yggdrasil can share the same event envelope.
10. Add a security page specifically for local model endpoints, prompt injection, tool execution and secret redaction.

## 6. Swarm consensus

Arendt and Boole independently converged on the same direction:

- adopt protocol-first thinking;
- adopt swappable brain endpoint as metadata;
- adapt terminal rendering into status cards;
- treat P2P as late transport;
- keep append-only files as source of truth;
- reject direct code/protocol copying without safety/license review.

## 7. Proposed local tasks after T-264

1. `workspace-cell read-only aggregator`.
2. `thread-brain.v1 mock protocol`.
3. `terminal-thread transcript events`.
4. `local-llm adapter dry-run`.
5. `thread context/view-slice recall test`.
6. `terminal status card renderer`.
7. `brain safety gate`.

## 8. Source notes

Primary external sources reviewed:

- `https://github.com/svend4/infon`
- `https://github.com/svend4/infon/blob/main/ai/BRAIN_PROTOCOL.md`
- `https://github.com/svend4/infon/blob/main/NETWORK.md`
- `https://github.com/svend4/infon/blob/main/LOSS_RECOVERY.md`
- `https://github.com/svend4/infon/blob/main/YGGDRASIL.md`
- `https://github.com/svend4/infon/blob/main/pkg/terminal/renderer.go`
- `https://github.com/svend4/infon/blob/main/pkg/terminal/diff.go`
- `https://github.com/svend4/infon/blob/main/pkg/terminal/capability.go`