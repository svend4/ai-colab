---
id: sandbox-ideas-readme
type: sandbox-doc
status: proposed
owner: codex
date: 2026-06-25
---

# Sandbox Ideas Lab

`sandbox/ideas/` — безопасная зона для странных, философских, художественных, научных, религиозных, исторических и фантастических идей, которые могут дать полезный технический принцип.

## Правила

- [ ] По умолчанию это `thought-experiment`, не executable-код.
- [ ] Любой кодовый образец должен идти в `sandbox/drafts/` с manifest и проходить intake.
- [ ] Нельзя исполнять код из этой папки без отдельного preflight/decision.
- [ ] Каждая идея должна иметь expected learning: что мы хотим узнать.
- [ ] Каждая идея должна получить disposition: adopt / adapt / archive / reject.
- [ ] Спорные идеи не стирать; переносить в divergence/streams.

## Шаблон

```md
---
id: idea-YYYY-MM-DD-short-name
type: thought-experiment
status: proposed
risk: low|medium|high
execute_allowed: false
owner: agent-id
---

# Название идеи

## Источник метафоры

## Технический принцип

## Что можно проверить

## Риск

## Expected learning

## Disposition

- [ ] adopt
- [ ] adapt
- [ ] archive
- [ ] reject
```

## Applied instructions

- AGENTS.md
- docs/external-code-sandbox.md
- docs/protocol-machine-layer.md

Checks:
- OK: python tools\heading_check.py sandbox\ideas\README.md sandbox\ideas\idea-2026-06-25-question-alchemy.md sandbox\ideas\idea-2026-06-25-agent-cell-mapreduce.md
- OK: python tools\validate.py
- OK: python tools\generate.py --check
