---
id: outbox-2026-06-23-subagent-handoff-json
status: proposed
agent: codex
related: T-162, T-161, docs/agent-launch-workflow.md, tools/flow.py, tools/top.py
---

# Sub-agent handoff JSON — отчёт Codex

Продолжение T-161: handoff-пакет теперь можно читать машинно.

Добавлен контракт `subagent_launch_plan.v1`:

```powershell
python tools\flow.py launch-plan mavis T-162 "agent launch workflow json" --worktree --json
python tools\top.py subagent-handoff mavis T-162 "agent launch workflow json" --worktree --json
```

JSON содержит agent/task/context, repo lane, prepare/finish commands, worker prompt, policies и checks. Это следующий слой для GUI-кнопки, MCP wrapper, ChatGPT App или серверного scheduler. Markdown остаётся default для человека.