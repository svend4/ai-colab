---
id: text-diffusion-canvas-from-infon-2026-06-26
type: topic
title: Text diffusion canvas from svend4/infon for multi-agent work
status: proposed
owner: codex
date: 2026-06-26
related:
  - svend4-infon-assessment-2026-06-26
  - zed-like-headless-workbench-mvp
  - T-264
---

# Text Diffusion Canvas From svend4/infon

## 1. Core thesis

`svend4/infon` is a terminal video communication project, but the strongest idea for this repository is not video itself. The stronger transferable idea is:

```text
turn a terminal into a multi-layer communication surface
```

For video, the surface is a grid of pixels or glyph cells. For this repository, the surface should be a grid of **semantic text blocks**: cards, cells, menus, status strips, question clusters, agent lanes and progressive summaries.

A normal chat is one-dimensional:

```text
message -> message -> message -> message
```

A multi-agent workbench should be two-dimensional:

```text
rows    = topics / tasks / agents / stages / evidence / risks
columns = time / priority / status / depth / owner / consensus
cells   = typed text blocks with ids and links
```

This is the proposed meaning of **text diffusion**: not image diffusion, but progressive multi-agent refinement of a 2D semantic field.

## 2. What infon contributes

From the public repository and docs, useful patterns are:

1. **Terminal as medium.** TVCP renders video in terminal using Unicode/ANSI. We can render multi-agent state in terminal using cards/tables/glyphs.
2. **Headless-first.** It is designed for SSH/servers/no GUI. Our repo also needs terminal-first work.
3. **Offline/P2P mindset.** Yggdrasil docs frame serverless, accountless, local mesh operation. For us: file/git/local bundles before cloud service.
4. **AI brain endpoint.** `tvcp-ai/1` is JSON-over-HTTP where the brain can be swapped by URL. For us: optional brain adapter behind a safe proposal boundary.
5. **Capability-based rendering.** Terminal renderer should degrade depending on terminal support. For us: JSON canonical, plain text default, ANSI card view optional.
6. **Frame/diff idea.** Video sends changed visual state over time. For us: event log sends changed semantic blocks over time.
7. **Generative pipeline.** Infon uses generated video/graphics. For us: generated text-canvas views from structured repo state.

## 3. What not to copy

Do not copy the video stack into this repository now:

- UDP/video transport does not solve our current bottleneck.
- Live media is harder to audit than append-only text.
- P2P/Yggdrasil should be late-stage transport, not source of truth.
- A brain endpoint must not execute commands or approve decisions.
- Terminal colors/cards are views, not canon.

Our canon remains:

```text
Markdown + JSON + tasks/questions/decisions/topics/streams/git
```

## 4. Text diffusion model

### 4.1. Unit: semantic cell

A cell is not a character and not a whole document. It is a small durable block:

```json
{
  "schema": "text_cell.v1",
  "id": "cell-...",
  "canvas_id": "canvas-...",
  "kind": "question|answer|claim|risk|evidence|task|decision|status|patch|summary",
  "owner": "codex|agent-id|human",
  "topic": "svend4-infon",
  "position": {"row": "risks", "col": "agent-codex"},
  "depth": 1,
  "status": "draft|proposed|confirmed|conflict|accepted",
  "links": [
    {"rel": "supports", "target": "cell-..."},
    {"rel": "contradicts", "target": "cell-..."},
    {"rel": "derived_from", "target": "file-or-url"}
  ],
  "body": "short text block"
}
```

This is the text equivalent of a pixel/tile in terminal video.

### 4.2. Frame: canvas snapshot

A frame is a rendered view of many cells:

```json
{
  "schema": "text_frame.v1",
  "canvas_id": "svend4-infon-workbench",
  "frame_no": 42,
  "created_at": "...",
  "view": "overview|risks|consensus|agent-lanes|timeline|deep-dive",
  "cells": ["cell-a", "cell-b", "cell-c"],
  "changed_cells": ["cell-c"],
  "summary": "what changed since previous frame"
}
```

This is the text equivalent of a video frame.

### 4.3. Diffusion step

A diffusion step is a controlled update:

```text
sense -> propose cells -> compare -> merge/keep-conflict -> render frame -> route next work
```

Multiple agents can write candidate cells in their own lanes. The integrator does not flatten them immediately. It marks:

- repeated same idea -> consensus candidate;
- same title but different body -> variant;
- contradiction -> conflict cell;
- useful but not adopted -> side lane;
- accepted -> canon route.

### 4.4. Agent lanes

A 2D canvas can show agents as columns:

```text
                 codex        hegel        goodall       human
question         Q1           Q1           Q1            comment
proposal         P1           P2           P1'           --
evidence         file A       file B       test C        source D
risk             R1           R2           R1            --
consensus        C1-----------C1-----------C1------------pending
```

This is better than chat because disagreement is visible spatially, not buried in chronology.

### 4.5. Topic lanes

Or topics as rows:

```text
thread.py        open -> implemented -> tested -> needs workspace-cell
svend4/infon     source review -> text diffusion -> brain protocol -> tasks
Downloads .inf   sandbox -> parser ideas -> recall tests -> defer canon
```

### 4.6. MMORPG analogy

In a multiplayer game, each player occupies a position and performs actions in a shared world. Here:

- map = text canvas;
- player = human/agent/script;
- zone = topic/task/portal;
- item = text cell/document/code draft;
- quest = task;
- raid = workflow/swarm;
- minimap = dashboard/workspace-cell;
- fog of war = unknown/unread/unverified area;
- combat log = append-only events;
- guild bank = shared knowledge/index;
- referee = governance/validate/merge-gate.

This analogy is useful because it avoids the false idea that collaboration is only chat. Collaboration is spatial, role-based, stateful and event-driven.

## 5. How to implement in our repo

### Stage 1. Use thread.py as event spine

`tools/thread.py` now gives durable thread folders. Next add event/cell layers near it, not inside a large monolith.

Potential structure:

```text
topics/<topic>/threads/<thread-id>/
  THREAD.json
  messages/
  events/
  canvas/
    cells/*.json
    frames/*.json
```

### Stage 2. workspace-cell first

Before a full canvas, build one cell-like dashboard object:

```text
workspace-cell = task + thread + stream + worktree + outbox + checks + next action
```

This gives immediate value and tests the model.

### Stage 3. text-canvas renderer

Add a renderer that reads cells/events and prints:

1. JSON for machines.
2. Plain table for normal terminal.
3. Optional ANSI blocks for rich terminal.
4. Later HTML static view.

### Stage 4. diffusion/convergence rules

Rules:

- cell IDs stable;
- updates append events;
- conflicting body changes are not silently overwritten;
- consensus is derived, not guessed;
- accepted canon requires human or named integrator.

### Stage 5. brain adapter

Only after the canvas exists:

```text
brain_request.v1 -> model proposes cells -> human/agent verifies -> cells become proposed/accepted
```

The brain should write proposals, not files.

## 6. How this helps multi-agent terminal work

### Current pain

Sequential chat loses parallel structure:

- agents answer same topic but results are far apart;
- duplicates and variants are hard to distinguish;
- unresolved conflicts disappear into history;
- evidence links are scattered;
- terminal output is long and linear.

### Text diffusion improvement

A text canvas can show:

- who is working;
- which cells changed;
- which claims are converging;
- which disagreements need attention;
- which code drafts are sandboxed;
- which tasks are ready to commit;
- what the next best action is.

### Practical terminal example

```text
[CANVAS svend4-infon] frame 018

AGENTS        STATUS          NEW CELLS       RISK
codex         integrating     4               subprocess test slow
arendt        source review   6               P2P late-stage
boole         brain protocol  5               endpoint must be proposal-only

CONSENSUS
C-01 protocol first, transport later
C-02 brain URL is metadata, not authority
C-03 terminal video idea -> text status cards

CONFLICTS
X-01 should P2P/Yggdrasil be early? codex:no, future:maybe
X-02 should .inf become canon? no current consensus, defer

NEXT
1. workspace-cell aggregator
2. thread-brain mock
3. terminal-thread events
```

This is a 2D text frame, not a one-line chat.

## 7. Recommendations for this repo

1. Keep building from T-264: thread first, then workspace-cell.
2. Add `text_cell.v1` only after workspace-cell proves useful.
3. Add `terminal_thread_event.v1` for large terminal output: chunk, hash, truncate, link.
4. Add `text-canvas report` command before any UI.
5. Do not make ANSI rendering canonical.
6. Add recall tests: a compact canvas must not hide load-bearing exceptions.
7. Treat agents as actors on a map, not just chat authors.
8. Use sandbox/worktree for code cells; never let model cells mutate mainline directly.
9. Add imports from external repos as sandbox intakes, then synthesize to topics/docs.
10. Use P2P only after import/export bundles are stable.

## 8. Recommendations for svend4/infon

1. Add a text-canvas mode next to terminal video: semantic cards instead of pixels.
2. Define `tvcp-text/1` or `tvcp-canvas/1` as JSON event/cell protocol.
3. Make AI brain responses proposal-based: cards/actions/events, not direct execution.
4. Add `input_hash` and `context_hash` to brain protocol.
5. Add a non-video collaboration demo: several agents editing a shared text board.
6. Add renderer modes: plain, ANSI, braille/sextant-like dense text, HTML export.
7. Add safety docs for local brain endpoints and prompt injection.
8. Separate implemented features from aspirational docs more visibly.
9. Add golden fixtures for renderer diff and event replay.
10. Treat P2P as transport for event bundles, not only live video frames.

## 9. Open questions

1. What is the minimal useful cell size: sentence, paragraph, card, task, or section?
2. Should row/column positions be fixed or derived from metadata?
3. How to display uncertainty without visual noise?
4. How to avoid agents optimizing for pretty cards instead of true work?
5. How to merge two canvases from offline agents?
6. Should text diffusion frames be committed, or generated from events?
7. What should be the first renderer: plain table, Markdown, ANSI, or HTML?
8. How much of this belongs in `tools/thread.py` vs a separate `tools/text_canvas.py`?

## 10. Proposed next tasks

1. `workspace-cell read-only aggregator`.
2. `terminal-thread event schema`.
3. `text-cell/canvas prototype` in sandbox or topic-local folder.
4. `text-canvas renderer` plain text + JSON.
5. `brain_request.v1 dry-run` that produces proposed cells.
6. `view recall test` for compact canvas context.

## 11. Sources

- `https://github.com/svend4/infon`
- `https://github.com/svend4/infon/blob/main/README.md`
- `https://github.com/svend4/infon/blob/main/YGGDRASIL.md`
- `https://github.com/svend4/infon/blob/main/ai/BRAIN_PROTOCOL.md`
- `https://github.com/svend4/infon/blob/main/NETWORK.md`
- `https://github.com/svend4/infon/blob/main/LOSS_RECOVERY.md`
- `https://github.com/svend4/infon/blob/main/pkg/terminal/renderer.go`
- `https://github.com/svend4/infon/blob/main/pkg/terminal/diff.go`
- `https://github.com/svend4/infon/blob/main/pkg/terminal/capability.go`