# Runtime PowerShell check

Дата: 2026-06-20

Источник: ручной запуск пользователем в Windows PowerShell.

Связано:

- `T-039`
- `docs/runtime-diagnostics.md`
- `docs/runtime-recovery-playbook.md`

## Полученный результат

Команда `python --version` через PowerShell job ответила успешно:

```text
Python 3.11.15
```

Команда `python -c "import sys, json, sqlite3; ..."` также ответила успешно:

```text
C:\Users\stefan\AppData\Local\hermes\hermes-agent\venv\Scripts\python.exe
3.11.15 (main, Jun 11 2026, 04:59:07) [MSC v.1944 64 bit (AMD64)]
sqlite3 3.53.1
```

Команда `py --version` ушла в timeout.

Дополнительная проблема: в Windows PowerShell `Stop-Job -Force` не поддержался:

```text
Stop-Job : A parameter cannot be found that matches parameter name 'Force'.
```

## Наблюдение по процессам

В списке процессов есть несколько долгоживущих Python-процессов с очень большим CPU time, включая процессы `python` из:

- `C:\Users\stefan\AppData\Roaming\uv\python\cpython-3.11-windows-...`
- `C:\Users\stefan\AppData\Local\hermes\hermes-agent\venv\Scripts\...`
- `C:\Users\stefan\AppData\Local\Programs\Python\Python313\python.exe`
- `C:\Users\stefan\AppData\Roaming\Claude\Claude Extensions\...`

Это не доказывает, что процессы вредные или зависшие, но объясняет, почему `py` launcher и часть runtime-проверок могли вести себя нестабильно.

## Уточнение статуса T-039

`T-039` больше не выглядит как полная неработоспособность команды `python`.

Более точная формулировка:

- `python` доступен и может импортировать `sqlite3`;
- `py` launcher зависает;
- в системе есть долгоживущие Python-процессы, которые нужно диагностировать по command line;
- проектные проверки ещё не прогнаны полным пакетом, поэтому `T-039` остаётся `blocked`.

## Исправленная функция Invoke-Timed

Для Windows PowerShell лучше использовать такую версию:

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

## Следующий безопасный шаг

Использовать именно `python`, не `py`, и прогнать сначала короткий пакет:

```powershell
$repo = "C:\Users\stefan\Documents\New project ai colab"
Set-Location -LiteralPath $repo

Invoke-Timed "pipeline status" {
  param($repo)
  Set-Location -LiteralPath $repo
  python tools\pipeline.py status
} 30 @($repo)

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

Invoke-Timed "mcp handshake" {
  param($repo)
  Set-Location -LiteralPath $repo
  python drivers\mcp_handshake_test.py
} 60 @($repo)
```

Если этот пакет проходит, можно переходить к runtime-приёмке драйверов.

