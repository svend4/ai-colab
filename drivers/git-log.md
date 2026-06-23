---
id: git-log
type: driver
title: Git-log driver — read-only история git (коммиты, авторы, история файла)
status: ready
level: L2
mode: read-only
owner: Claude
risk: medium
activation: mcp
interfaces: [recent_commits, author_stats, file_history, repo_summary]
tools: [recent_commits, author_stats, file_history, repo_summary]
inputs: [repo-path, file-path, n]
outputs: [commit-list, author-stats, file-history, summary]
sandbox: not-required-for-read-only
secrets: forbidden-in-repo
source_last_verified: 2026-06-21
timeout_seconds: 30
max_output_bytes: 1048576
audit: true
related: topics/ai-os-bridge.md, drivers/repo-runner.md
---

# Driver: git-log

## Назначение

Read-only доступ к **истории git** репозитория — чтобы AI-агент понимал эволюцию проекта:
последние коммиты, статистику по авторам, историю изменений файла, краткую сводку. Дополняет
`repo-runner` (тот инвентаризует *срез* репозитория; `git-log` — его *историю*).

## Контракт

- Инструменты (4): `recent_commits(repo, n)`, `author_stats(repo)`, `file_history(repo, path, n)`,
  `repo_summary(repo)` — имена сверяются валидатором с `drivers/git-log/mcp_server.py` (`tools:`).
- Входы: `repo-path` (внутри allowed-root `GIT_LOG_BASE`), `file-path` (pathspec), `n` (лимит).
- Выходы: списки коммитов (`hash/author/date/subject`), статистика авторов, сводка.

## Безопасность

- **read-only**: вызывается строго фиксированный whitelist `git log/rev-list/rev-parse` —
  никаких пользовательских git-подкоманд; `file-path` идёт после `--` как pathspec (не команда).
- **Код репозитория НЕ запускается**: `git log` не исполняет hooks.
- **allowed-root**: `GIT_LOG_BASE` ограничивает репозиторий (`PathAccessError` при выходе).
- **Лимиты**: `n` ≤ 1000, `timeout` 15с на git-вызов.
- **Audit**: `true` (risk: medium) — вызовы журналируются через `drivers/audit.py`.

## Статус

`ready` по D-015 (код работает + сверка ≥2 агентами):
- **Claude:** unit-тест `drivers/git-log/test_git_log.py` (commits/authors/file-history/confinement/
  not-a-repo) + sync MCP `tools/call`-приёмка `drivers/mcp_sync_acceptance.py git-log` → `pass=4 fail=0`;
- **Codex:** интеграция git-log в `mcp_sync_probe.py` SERVERS и sync-приёмку, рефактор теста на `temp_dir`.

Рантайм-нюанс устранён: при работе как MCP-сервер `git`-вызовы шли с `stdin=DEVNULL`, иначе на
Windows возникал дедлок overlapped I/O (git наследовал stdin-пайп asyncio-сервера) — `tools/call` виснул.

## Реализация

- `drivers/git-log/git_log.py` — engine (read-only git, confinement, лимиты);
- `drivers/git-log/mcp_server.py` — FastMCP stdio wrapper + audit;
- `drivers/git-log/test_git_log.py` — тесты против временного git-репозитория.

CLI: `python drivers/git-log/git_log.py summary <repo>` (recent / authors / file / summary).
