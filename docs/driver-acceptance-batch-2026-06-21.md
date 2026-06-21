# Driver acceptance batch

Дата: 2026-06-21

Статус: runnable checklist для Windows PowerShell.

Связано:

- `T-039`
- `T-048`
- `T-051`
- `T-055`
- `T-057`
- `T-059`
- `T-067`
- `T-068`
- `docs/runtime-validation-batch-2026-06-20.md`

## Цель

После успешного core runtime validation нужно прогнать driver acceptance batch. Этот пакет проверяет не только, что Python и общие индексы работают, но и что конкретные драйверы выполняют свои тесты.

Этот документ не утверждает, что задачи закрыты. Он задаёт воспроизводимый порядок команд и ожидаемые критерии для ручного запуска в Windows PowerShell.

## Подготовка PowerShell

```powershell
$repo = "C:\Users\stefan\Documents\New project ai colab"
Set-Location -LiteralPath $repo

chcp 65001
[Console]::InputEncoding = [System.Text.UTF8Encoding]::new($false)
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
$OutputEncoding = [Console]::OutputEncoding
```

Исправленная функция таймаута для Windows PowerShell:

```powershell
function Invoke-Timed {
  param(
    [string]$Name,
    [scriptblock]$Script,
    [int]$TimeoutSec = 30,
    [object[]]$ArgumentList = @()
  )

  "===== $Name ====="
  $job = Start-Job -ScriptBlock $Script -ArgumentList $ArgumentList
  $done = Wait-Job $job -Timeout $TimeoutSec

  if ($null -eq $done) {
    Stop-Job $job
    "TIMEOUT after $TimeoutSec sec: $Name"
  } else {
    Receive-Job $job
  }

  Remove-Job $job -Force
}
```

Важно: использовать `python`, не `py`, потому что `py --version` ранее уходил в timeout.

## Batch A — core sanity repeat

```powershell
Invoke-Timed "validate" {
  param($repo)
  Set-Location -LiteralPath $repo
  python tools\validate.py
} 60 @($repo)

Invoke-Timed "drivers catalog" {
  param($repo)
  Set-Location -LiteralPath $repo
  python tools\drivers_catalog.py
} 60 @($repo)
```

Критерий:

- `validate.py` завершает `OK=... WARN=0 ERROR=0`;
- `drivers_catalog.py` пишет, что `drivers/index.json` и `drivers/CATALOG.md` актуальны.

## Batch B — driver tests

```powershell
Invoke-Timed "files tests" {
  param($repo)
  Set-Location -LiteralPath $repo
  python drivers\files\test_files.py
  python drivers\files\test_inventory.py
} 60 @($repo)

Invoke-Timed "repo-runner tests" {
  param($repo)
  Set-Location -LiteralPath $repo
  python drivers\repo-runner\test_inventory.py
} 60 @($repo)

Invoke-Timed "workbench tests" {
  param($repo)
  Set-Location -LiteralPath $repo
  python drivers\workbench\test_workbench.py
  python drivers\workbench\test_ingest.py
  python drivers\workbench\test_search.py
} 90 @($repo)

Invoke-Timed "workbench-db tests" {
  param($repo)
  Set-Location -LiteralPath $repo
  python drivers\workbench-db\test_db.py
} 60 @($repo)

Invoke-Timed "file-inventory tests" {
  param($repo)
  Set-Location -LiteralPath $repo
  python drivers\file-inventory\test_inventory.py
} 60 @($repo)
```

Критерий:

- нет `TIMEOUT`;
- нет traceback;
- каждый тестовый файл завершает процесс с кодом `0`.

Если вывод теста не содержит явного `OK`, но команда вернулась без ошибки, это считается pass для текущего batch, потому что часть тестов самописные.

### Result 2026-06-21

Пользователь прислал файл `queues/inbox/2026-06-21-driver-acceptance-output.txt`.

После декодирования смешанной кодировки подтверждено:

- `files tests` passed;
- `repo-runner tests` passed;
- `workbench tests` passed;
- `workbench-db tests` passed;
- `file-inventory tests` passed.

Вывод: Batch B / driver tests пройден. Подробности: `docs/driver-tests-result-2026-06-21.md`.

Остаток: Batch C / pipeline guards.

## Batch C — pipeline guards

Проверка `T-067`: placeholder-задачи не попадают в ready queue.

```powershell
Invoke-Timed "pipeline ready_sorted no-write" {
  param($repo)
  Set-Location -LiteralPath $repo
  python -c "import tools.pipeline as p; print([t['id'] for t in p.ready_sorted(p.collect_tasks())])"
} 30 @($repo)
```

Ожидаемый результат:

```text
[]
```

Проверка `T-068`: `T-020` отображается как `doing without active claim`.

```powershell
Invoke-Timed "pipeline status" {
  param($repo)
  Set-Location -LiteralPath $repo
  python tools\pipeline.py status
} 30 @($repo)
```

Ожидаемый смысл результата:

- в работе: `0`;
- готово к взятию: `0`;
- `T-020` есть в not-ready/blocked с причиной `doing without active claim`;
- `T-062`, `T-063`, `T-064` есть с причиной `placeholder task`.

### Result 2026-06-21

Пользователь прислал `queues/inbox/documentoutput.md`.

Подтверждено:

```text
===== pipeline ready_sorted no-write =====
[]
```

Также `pipeline status` показал ожидаемый смысл результата:

- в работе: `0`;
- готово к взятию: `0`;
- `T-020` отображается как `doing without active claim`;
- `T-062`, `T-063`, `T-064` отображаются как `placeholder task`.

Вывод: Batch C / pipeline guards пройден. Подробности: `docs/pipeline-guards-result-2026-06-21.md`.

## Batch D — MCP smoke

Текущий `drivers/mcp_handshake_test.py` проверяет только:

- `data`;
- `codex-local`;
- `gateway`.

```powershell
Invoke-Timed "mcp handshake" {
  param($repo)
  Set-Location -LiteralPath $repo
  python drivers\mcp_handshake_test.py
} 60 @($repo)
```

Критерий:

```text
RESULT OK
```

Если PowerShell показывает `NativeCommandError`, но в конце есть `RESULT OK`, smoke-handshake считается пройденным: это stderr-логи MCP/FastMCP, а не обязательно провал.

### Result 2026-06-21

Пользователь прогнал Batch D.

Результат:

```text
OK data tools=4 ['columns', 'head', 'list_tables', 'summarize']
OK codex-local tools=2 ['codex_available', 'codex_info']
OK gateway tools=6 ['files_list', 'files_read', 'files_search', 'files_summarize', 'memory_query', 'repo_inspect']
RESULT OK
```

Вывод: Batch D / MCP smoke пройден. Подробности: `docs/mcp-handshake-result-2026-06-21.md`.

## Как интерпретировать результаты

Если Batch A-D проходят:

- `T-067` можно переводить в `done`;
- `T-068` можно переводить в `done`;
- `T-048`, `T-051`, `T-055`, `T-057`, `T-059` нужно закрывать по соответствующим результатам driver tests;
- `T-039` можно пересмотреть: либо закрыть, либо переопределить как остаточный blocker только для `py` launcher и долгоживущих процессов.

Если какой-то batch падает:

1. Скопировать полный вывод в чат или в `queues/outbox/`.
2. Не переводить зависимые задачи в `done`.
3. Создать отдельную задачу на конкретный failing driver.
