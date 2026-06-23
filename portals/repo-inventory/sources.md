# Repo-inventory — источники

Read-only, локальные, ноль сетевых источников:

- `drivers/repo-runner/fixture-report.json` — инвентарь репозитория (read-only скан).
- `drivers/file-inventory/fixture-report.json` — инвентарь файлов.
- `git-log` summary (драйвер `drivers/git-log.md`) — история коммитов.

Опора на L1 (`l1_basis` в `portal.md`): `tools/knowledge.py`, `tools/text_extract.py`; драйверы
`repo-runner`/`git-log` — `mode: read-only`, execute-гейт закрыт.
