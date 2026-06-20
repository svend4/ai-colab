# Runtime validation batch

Дата: 2026-06-20

Источник: ручной запуск пользователем в Windows PowerShell.

Связано:

- `T-039`
- `T-048`
- `T-051`
- `T-055`
- `T-057`
- `T-059`
- `T-067`
- `T-068`

## Выполненные команды

Пакет был выполнен через `Invoke-Timed` и команду `python`, не через `py`.

```powershell
python tools\pipeline.py status
python tools\validate.py
python tools\drivers_catalog.py
python drivers\mcp_handshake_test.py
```

## Результаты

### pipeline status

Команда завершилась и показала:

- в работе: `0`;
- готово к взятию: `0`;
- не готово / заблокировано: `13`.

Среди важных проверок:

- `T-020` отображается как `doing without active claim`;
- `T-062`, `T-063`, `T-064` отображаются как `placeholder task`;
- `T-067` и `T-068` остаются `status: blocked`, потому что формальная runtime-приёмка ещё не закрыта.

PowerShell снова показал mojibake для русских строк, но сама команда выполнилась.

### validate

`python tools\validate.py` прошёл успешно:

```text
OK=8 WARN=0 ERROR=0
```

Также подтверждено:

- `DECISIONS`: 14 записей;
- `QUESTIONS`: 12 вопросов;
- `TASKS`: 71 задача на момент запуска;
- `drivers`: 7 манифестов по draft schema v1;
- `board.md` и `STATUS.md` имеют валидные ссылки;
- правило ASCII-имён файлов соблюдено.

### drivers catalog

`python tools\drivers_catalog.py` прошёл успешно:

```text
OK: drivers/index.json актуален
OK: drivers/CATALOG.md актуален
Драйверов в каталоге: 7
```

Это подтверждает, что ручное внесение `gateway` в каталог согласовано с генератором.

### MCP handshake

`python drivers\mcp_handshake_test.py` прошёл успешно:

```text
OK data tools=4 ['columns', 'head', 'list_tables', 'summarize']
OK codex-local tools=2 ['codex_available', 'codex_info']
OK gateway tools=6 ['files_list', 'files_read', 'files_search', 'files_summarize', 'memory_query', 'repo_inspect']
RESULT OK
```

В выводе был `NativeCommandError` из-за stderr-логов MCP/FastMCP, но финальный результат `RESULT OK` означает успешный smoke handshake.

## Что это меняет

`T-039` больше не следует понимать как полную неработоспособность Python/runtime.

Теперь подтверждено:

- `python` запускает проектные инструменты;
- валидатор проходит без ошибок;
- каталог драйверов актуален;
- MCP handshake для `data`, `codex-local`, `gateway` проходит;
- pipeline status выполняется и показывает ожидаемые диагностические состояния.

## Что ещё не закрыто

Этот пакет не закрывает все runtime-приёмки.

Остаётся прогнать:

```powershell
python drivers\files\test_files.py
python drivers\files\test_inventory.py
python drivers\repo-runner\test_inventory.py
python drivers\workbench\test_workbench.py
python drivers\workbench\test_ingest.py
python drivers\workbench-db\test_db.py
python drivers\file-inventory\test_inventory.py
```

Также полезно отдельно проверить `ready_sorted()` без записи claim:

```powershell
python -c "import tools.pipeline as p; print([t['id'] for t in p.ready_sorted(p.collect_tasks())])"
```

Ожидаемый результат: пустой список `[]`.

## Практический вывод

Стадия `core runtime validation` пройдена. Следующий этап - driver acceptance batch. После него можно будет решать, какие из задач `T-048`, `T-051`, `T-055`, `T-057`, `T-059`, `T-067`, `T-068` переводить в `done`.

