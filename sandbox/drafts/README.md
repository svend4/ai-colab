# Draft-code sandbox lane

`sandbox/drafts/` is a no-execute lane for experimental code written by agents or humans.

This folder is for code proposals, prototypes, adapters, snippets, or test fixtures that should be reviewed before they become part of `tools/`, `drivers/`, `core/`, or another main project area.

## Default Rule

```text
write draft -> static review -> outbox report -> Codex decision -> separate promotion task
```

Draft code in this lane must not be executed automatically. A file appearing in `sandbox/drafts/` is not permission to run it.

## Git Policy

Raw draft folders are ignored by Git by default through `sandbox/.gitignore`.

The repository tracks this README and templates, not every experiment. If a draft becomes useful, promote it through a separate task and report rather than committing the raw draft directly.

## Suggested Draft Structure

```text
sandbox/drafts/<draft-id>/
  manifest.json
  README.md
  src/
  tests/
  notes.md
```

`manifest.json` should follow `sandbox/templates/draft-code-manifest.template.json`.

## Allowed Uses

- Agent writes a proposed implementation without touching shared code.
- Agent writes a small prototype for review.
- Agent writes test fixtures or pseudo-code for later promotion.
- Observer compares several alternative draft implementations.
- Codex reviews the draft and creates a normal build task if it is worth promoting.

## Forbidden Uses

- Do not run draft code automatically.
- Do not install dependencies from draft code.
- Do not treat draft code as trusted external source.
- Do not store secrets, tokens, private keys, browser data, or credentials.
- Do not use this lane to bypass `docs/execute-sandbox-preflight.md`.
- Do not promote code into `tools/`, `drivers/`, or `core/` without a separate task, checks, and outbox report.

## Review Flow

1. Agent creates a draft in its own `<draft-id>` folder.
2. Agent writes an outbox report describing the draft, risks, and proposed promotion path.
3. Observer or reviewer inspects the draft read-only.
4. Codex decides whether to reject, ask for another variant, or create a promotion task.
5. Promotion happens outside this lane as a normal claimed build task.

## Static Checks Before Promotion

Useful checks before promotion may include:

```powershell
python tools\python_analyzer.py sandbox\drafts\<draft-id> --base sandbox\drafts\<draft-id>
python tools\sandbox_link_checker.py sandbox\drafts\<draft-id> --json
python tools\instructions.py check-report queues\outbox\<draft-report>.md
```

These checks are read-only. They do not authorize executing draft code.