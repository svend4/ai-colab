---
id: outbox-2026-06-23-subagent-handoff-workflow
status: proposed
agent: codex
related: T-161, docs/agent-launch-workflow.md, tools/top.py, tools/flow.py
---

# Sub-agent handoff workflow — отчёт Codex

Codex проверил вопрос запуска sub-agent и разделил ответственность:

- локальный repo layer готовит launch-пакет через `top.py subagent-handoff` / `flow.py launch-plan`;
- внешний platform launcher реально запускает worker-agent;
- worker использует `agent-start`, `pipeline claim/done`, scoped edits и проверки;
- integrator сливает через worktree/merge gate/commit policy.

Это решение не привязывает проект к одному API запуска и остаётся удобным для людей, Codex sub-agents, других AI и будущего серверного оркестратора.

Проверять:

```powershell
python tools\top.py subagent-handoff mavis T-161 "agent launch workflow" --worktree
python tools\test_flow.py
python tools\test_top.py
python tools\top.py health
```