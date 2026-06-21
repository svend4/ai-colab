---
id: git-log-second-verification-result-2026-06-21
title: Git-log second verification result — T-103
status: done
owner: Codex
related: tasks/T-103.md, tasks/T-102.md, drivers/git-log.md, drivers/git-log/git_log.py, drivers/mcp_sync_acceptance.py
---

# Git-log second verification result — T-103

Дата: 2026-06-21.

## Что проверено

Codex выполнил вторую сверку `git-log` driver после реализации T-102.

Проверки:

```text
python drivers\git-log\test_git_log.py
TESTS OK git-log: commits=2 authors=1 file_hist=2
```

```text
python drivers\mcp_sync_probe.py git-log --timeout 60
OK git-log tools=4 ['author_stats', 'file_history', 'recent_commits', 'repo_summary']
RESULT OK
```

```text
python drivers\mcp_sync_acceptance.py --timeout 90
SYNC ACCEPTANCE pass=23 fail=0
RESULT OK
```

## Найденный runtime-нюанс

Первый `tools/call` прогон зависал на 4 вызовах `git-log`. Engine/CLI работал быстро, а MCP call не отвечал. Причина: при работе как stdio MCP server дочерний `git` subprocess наследовал stdin-пайп сервера. На Windows это приводило к зависанию `tools/call`.

Исправление: `drivers/git-log/git_log.py` запускает git с `stdin=subprocess.DEVNULL`.

## Вывод

`git-log` прошёл вторую сверку и может быть `ready` как read-only L2 driver. Sync MCP acceptance теперь покрывает 23 tools/call: прежние 19 + 4 `git-log`.
