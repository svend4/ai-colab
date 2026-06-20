# Runtime recovery playbook

Дата: 2026-06-20
Автор: Codex
Связано: `T-039`, `T-048`, `T-051`, `T-055`, `T-057`, `T-059`

## Цель

`T-039` блокирует runtime-приёмку почти всех новых драйверов. Проблема шире Python: в текущей Codex/Windows shell-сессии зависал запуск внешних `.exe`, включая `cmd.exe /c echo ok`.

Этот playbook нужен, чтобы после внешнего восстановления среды быстро и в правильном порядке проверить весь стек.

## Что не делать вслепую

- Не убивать все `python.exe`, `powershell.exe`, `cmd.exe` без проверки.
- Не удалять `__pycache__` или временные папки, если процесс всё ещё держит lock.
- Не переводить `drivers/*.md` в `ready`, пока тесты реально не прошли.
- Не принимать `D-013` как `accepted`, пока `validate.py` и генераторы не проходят.

## Ручное восстановление среды

Выполняется человеком или отдельной внешней консолью, не из зависшей Codex shell-сессии.

1. Открыть Task Manager / Process Explorer.
2. Найти зависшие процессы, связанные именно с этой рабочей папкой: `python.exe`, `cmd.exe`, `powershell.exe`.
3. Закрывать только явно зависшие процессы этой сессии.
4. Перезапустить Codex shell/session, если даже `cmd.exe /c echo ok` не стартует.
5. После восстановления сначала проверить минимальный запуск:

```powershell
cmd.exe /c echo ok
python -c "print('ok')"
python --version
```

Если эти команды зависают, не переходить к тестам драйверов.

## Очистка lock-следов

После восстановления внешних процессов:

```powershell
Remove-Item -Recurse -Force .\drivers\files\__pycache__ -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force .\drivers\repo-runner\__pycache__ -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force .\drivers\workbench\__pycache__ -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force .\drivers\file-inventory\__pycache__ -ErrorAction SilentlyContinue
```

## Порядок приёмки после восстановления

### 1. Базовый канон

```powershell
python tools\validate.py
python tools\generate.py --check
python tools\drivers_catalog.py --check
```

Если `--check` показывает устаревшие файлы, перегенерировать:

```powershell
python tools\generate.py
python tools\drivers_catalog.py
```

### 2. Files stack

```powershell
python drivers\files\test_files.py
python drivers\files\test_inventory.py
python drivers\file-inventory\test_inventory.py
python drivers\file-inventory\inventory.py . --base . --max-files 200 --markdown
```

Связанные задачи: `T-029`, `T-048`, `T-059`.

### 3. Repo-runner stack

```powershell
python drivers\repo-runner\test_inventory.py
```

Дополнительно MCP-приёмка `repo-runner`: initialize, tools/list, `repo_summary`.

Связанная задача: `T-051`.

### 4. Workbench stack

```powershell
python drivers\workbench\test_workbench.py
python drivers\workbench\test_ingest.py
```

CLI smoke:

```powershell
$env:WORKBENCH_BASE=(Get-Location).Path
python drivers\workbench\workbench.py init data\workbench.db
python drivers\workbench\workbench.py list data\workbench.db --limit 10
```

Связанные задачи: `T-055`, `T-057`.

### 5. MCP checks

- `files`: initialize, tools/list = 4, call `summarize`;
- `repo-runner`: initialize, tools/list = 3, call `repo_summary`;
- allowed-root negative tests для `FILES_DRIVER_BASE` и `REPO_RUNNER_BASE`.

## Порядок закрытия задач

Если всё выше проходит:

1. `T-039` -> `done`.
2. `T-029` -> `done`.
3. `T-048` -> `done`.
4. `T-051` -> `done`.
5. `T-055` -> `done`.
6. `T-057` -> `done`.
7. `T-059` -> `done`.
8. После `validate.py` и `generate.py --check` можно обсуждать `D-013 accepted`.

## Мнение Codex

Главный риск сейчас не в конкретном драйвере, а в том, что накопилось много кода со статусом “готово статически, не принято runtime”. Поэтому recovery должен быть пакетным: сначала доказать, что внешние процессы вообще запускаются, затем прогонять стек слоями.

