# Repo-runner MCP hardening report

Дата: 2026-06-20
Автор: Codex
Связано: `T-024`, `T-049`, `T-050`, `T-051`, `drivers/repo-runner.md`

## Контекст

Claude закрыл `T-049`: добавлен `drivers/repo-runner/mcp_server.py`, done-marker сообщает `handshake OK`, `tools/list=3`, `repo_summary OK`.

После статической перепроверки Codex усилил границы безопасности, потому что MCP-wrapper напрямую передавал произвольный `repo_path` в `inventory.scan_repo()`, а сам scanner не имел `max_files`.

## Что изменено

В `drivers/repo-runner/inventory.py`:

- добавлен `DEFAULT_MAX_FILES`;
- добавлен `PathAccessError`;
- добавлен `base_dir` / allowed-root;
- относительные пути при заданном `base_dir` резолвятся относительно allowed-root;
- добавлен `max_files` и флаг `truncated`;
- список skip-директорий вынесен в `SKIP_DIRS`;
- лимит чтения Python-файлов для risk scan вынесен в `RISK_READ_MAX_BYTES`;
- CLI получил `--base` и `--max-files`.

В `drivers/repo-runner/mcp_server.py`:

- добавлен `REPO_RUNNER_BASE` как allowed-root;
- если env не задан, allowed-root равен текущей рабочей папке процесса;
- все MCP-tools (`inspect_repo`, `repo_summary`, `repo_risks`) передают `base_dir` и `max_files`.

В `drivers/repo-runner/test_inventory.py`:

- исправлен import path теста на папку `drivers/repo-runner`;
- добавлена проверка `max_files`;
- добавлена проверка запрета выхода за `base_dir`.

## Что осталось не проверено

Codex не запускал Python-тесты и MCP handshake из-за текущего блокера `T-039`.

Нужна отдельная runtime-приёмка:

```powershell
python drivers\repo-runner\test_inventory.py
python tools\validate.py
python tools\generate.py --check
```

Дополнительно:

- MCP initialize;
- MCP tools/list должен показать 3 инструмента;
- MCP call `repo_summary` на безопасной fixture-папке;
- проверка запрета выхода за `REPO_RUNNER_BASE`;
- проверка `max_files`/`truncated`.

## Мнение Codex

`repo-runner` теперь ближе к правильному L2-драйверу. Его смысл — не “запустить репозиторий”, а сначала построить read-only карту и risk profile. Это важное отличие: репозиторий почти всегда содержит потенциальные точки запуска (`scripts`, `package.json`, `Makefile`, CI, shell-файлы), поэтому inspect-only слой должен быть намеренно строгим.

Следующий качественный шаг — не добавлять `run/test`, а сделать runtime acceptance и затем отдельный sandbox design для L3.

