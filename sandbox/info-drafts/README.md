# Info/document draft sandbox lane

`sandbox/info-drafts/` is a structured no-canon lane for experimental documentation, information maps, source notes, question trees, decision material, portal notes, and synthesis candidates.

This folder is not the final documentation layer. Draft packets are evidence for later synthesis and promotion.

## Default Rule

```text
write info draft -> structural review -> doc synthesis -> separate promotion task
```

A file appearing in this lane is not an accepted decision, not canonical documentation, and not permission to overwrite `docs/`, `topics/`, `core/`, or `portals/`.

## Git Policy

Raw info draft folders are ignored by Git by default through `sandbox/.gitignore`.

The repository tracks this README and templates. If a draft becomes useful, promote it through a separate task, report, and synthesis rather than committing the raw packet directly.

## Suggested Draft Structure

```text
sandbox/info-drafts/<draft-id>/
  manifest.json
  README.md
  brief.md
  outline.md
  claims.md
  sources.md
  open_questions.md
  divergence.md
  notes.md
```

## Allowed Uses

- Agent writes a proposed documentation structure without touching `docs/`.
- Agent gathers claims and sources for later synthesis.
- Agent prepares a decision material packet.
- Observer compares several alternative document packets.
- Codex creates a normal promotion task if synthesis shows the draft is useful.

## Forbidden Uses

- Do not mark packet contents as accepted decisions.
- Do not overwrite clean docs from this lane directly.
- Do not delete divergence or alternative positions.
- Do not store secrets, credentials, private notes, or private data.
- Do not use this lane to bypass `QUESTIONS.md`, `DECISIONS.md`, or review.

## Review Flow

1. Agent creates a draft in its own `<draft-id>` folder.
2. Agent fills brief, outline, claims, sources, questions, divergence.
3. Reviewer checks structure and evidence read-only.
4. Synthesizer uses `doc_synthesis.py` or manual comparison.
5. Promotion happens outside this lane as a normal claimed task.