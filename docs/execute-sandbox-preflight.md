---
id: execute-sandbox-preflight
title: Execute sandbox preflight — до запуска чужого кода
status: accepted
last_verified: 2026-06-23
owner: Codex
related: tasks/T-114.md, tasks/T-020.md, decisions/D-014.md, decisions/D-006.md, decisions/D-018.md, drivers/SCHEMA.md, docs/driver-safety-policy.md, docs/bridge-usage.md
---

# Execute sandbox preflight

Дата: 2026-06-21.

Назначение: описать, что должно быть проверено до любого запуска чужого или непроверенного кода, включая будущий кейс `svend4`.

Это preflight-документ, а не разрешение на `mode: execute`. Текущий проект остается read-only для внешних репозиториев.

## Ratification note 2026-06-23

D-014 (accepted, 2026-06-23) формализует эту policy как binding 10-гейтовый preflight: execute OFF по умолчанию + 10 обязательных preflight-гейтов. До явного подтверждения Stefan по D-006/D-018 документ остаётся рабочей policy-поверхностью, но не становится самостоятельным разрешением на execute.

Связанная рабочая зона: `sandbox/`. Её описание — `docs/external-code-sandbox.md`.
`sandbox/` не даёт разрешение на запуск. Это quarantine/intake/workspace структура для любого внешнего
кода до решения о sandbox runner.

## Жесткие запреты до отдельного решения

- Не запускать `run`, `test`, `install`, `pip install`, `npm install`, `make`, shell-скрипты или бинарники из непроверенного репозитория на хостовой Windows-системе.
- Не включать `mode: execute` в driver manifest без реальной песочницы и отдельного accepted-решения.
- Не монтировать в песочницу весь `C:\Users`, домашнюю папку, `.ssh`, браузерные профили, токены, API keys, Docker socket или `.gitconfig`.
- Не давать контейнеру `--privileged`, host network, host PID namespace, доступ к Docker socket, системным дискам или production-секретам.
- Не считать Docker/WSL само по себе полной безопасностью: нужен набор лимитов, сеть, секреты, audit и rollback.

## Минимальный gate перед execute

Перед первой задачей, где агент или скрипт сможет запускать чужой код, должны быть закрыты все пункты:

| Gate | Требование | Проверка |
|---|---|---|
| Решение | Есть accepted decision на конкретный execute-сценарий | запись в `DECISIONS.md` |
| Источник | Репозиторий доступен read-only и уже прошел inventory | `repo-runner`/`git-log`/report |
| Песочница | Реальная изоляция: Docker/container, VM, nsjail/firejail/gVisor или отдельный сервер | команды preflight ниже |
| Права | Нет секретов и широких host mount | ручной review команды запуска |
| Сеть | По умолчанию `--network none`; если сеть нужна, отдельное разрешение | manifest + команда запуска |
| Лимиты | CPU, память, PIDs, диск, timeout | manifest + runner config |
| Логи | Есть audit лог команды, exit code, runtime, diff/output | `logs/*` + `reports/*` |
| Rollback | Результаты пишутся в отдельную output-папку, контейнер удаляется | `--rm`, отдельный workspace |
| Валидация | `tools/validate.py` не пропускает fake sandbox | validate green |
| Человек | Человек явно подтвердил first-run | отдельная запись/команда |

Если хотя бы один gate не закрыт, режим остается `read-only`.

## Рекомендуемая архитектура

### Вариант A: локально через WSL2 + Docker

Подходит для маленьких экспериментов и локального MVP.

Минимальные свойства:

- исходный репозиторий монтируется read-only;
- output пишется в отдельную папку;
- сеть выключена по умолчанию;
- контейнер не privileged;
- есть лимиты CPU/RAM/PIDs;
- есть timeout на процесс;
- нет host secrets;
- базовый образ заранее выбран и зафиксирован.

Форма команды для будущего runner-а:

```powershell
docker run --rm `
  --network none `
  --memory 2g `
  --cpus 2 `
  --pids-limit 256 `
  --read-only `
  --tmpfs /tmp:rw,noexec,nosuid,size=256m `
  -v C:\path\to\repo:/work:ro `
  -v C:\path\to\out:/out:rw `
  --workdir /work `
  image-name:tag `
  command
```

Эту команду нельзя использовать как готовое разрешение на запуск. Это форма для review: каждый mount, image и command должны быть проверены отдельно.

### Вариант B: выделенный сервер или VM

Подходит, если код нельзя запускать локально или нужен Linux/runtime, которого нет на Windows.

Минимальные свойства:

- отдельный пользователь без административных прав;
- отдельная VM или disposable server без личных данных;
- firewall/egress policy;
- лимиты CPU/RAM/disk/processes;
- снапшот или возможность быстро удалить VM;
- логи копируются в `reports/`, сырые runtime-логи остаются вне git;
- доступ по ключам без передачи секретов в репозиторий.

### Вариант C: без execute

Остается предпочтительным режимом по умолчанию:

- `git-log`;
- `repo-runner` inventory;
- `files` read/search/summarize;
- `knowledge.py` ingest/query/report;
- ручной review зависимостей и скриптов.

Для текущей стадии проекта вариант C уже дает пользу без риска выполнения непроверенного кода.

## Ручные PowerShell-проверки без установки

Эти команды ничего не устанавливают. Они только показывают, что уже есть в системе.

Сначала включить читаемый UTF-8:

```powershell
chcp 65001
[Console]::InputEncoding = [System.Text.UTF8Encoding]::new($false)
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
$OutputEncoding = [Console]::OutputEncoding
```

Если команды иногда зависают, используйте timeout-wrapper без `Stop-Job -Force`:

```powershell
function Invoke-Timed {
  param(
    [string]$Name,
    [scriptblock]$Script,
    [int]$TimeoutSec = 20,
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

  Remove-Job $job -Force -ErrorAction SilentlyContinue
}
```

Проверить Git:

```powershell
Invoke-Timed "git command" { Get-Command git -ErrorAction SilentlyContinue | Select-Object Source, Version } 10
Invoke-Timed "git version" { git --version 2>&1 } 10
```

Проверить WSL:

```powershell
Invoke-Timed "wsl command" { Get-Command wsl -ErrorAction SilentlyContinue | Select-Object Source, Version } 10
Invoke-Timed "wsl status" { wsl --status 2>&1 } 20
Invoke-Timed "wsl list" { wsl --list --verbose 2>&1 } 20
```

Проверить Docker:

```powershell
Invoke-Timed "docker command" { Get-Command docker -ErrorAction SilentlyContinue | Select-Object Source, Version } 10
Invoke-Timed "docker version" { docker version 2>&1 } 30
Invoke-Timed "docker context" { docker context ls 2>&1 } 20
Invoke-Timed "docker security options" { docker info --format '{{json .SecurityOptions}}' 2>&1 } 30
```

Проверить, что в проекте нет execute-драйверов:

```powershell
Invoke-Timed "validate" {
  param($repo)
  Set-Location -LiteralPath $repo
  python tools\validate.py
} 60 @((Get-Location).Path)

Invoke-Timed "driver execute scan" {
  param($repo)
  Set-Location -LiteralPath $repo
  Select-String -Path drivers\*.md -Pattern '^mode:\s*execute' -Encoding UTF8
} 20 @((Get-Location).Path)
```

Ожидаемое состояние сейчас: `validate.py` зеленый, а `driver execute scan` не находит активных execute-драйверов.

## Что логировать при будущем запуске

Если execute когда-нибудь будет разрешен отдельным решением, каждый запуск должен оставлять:

- task id;
- agent id;
- claim id;
- commit hash или snapshot источника;
- точную команду;
- image/tag или VM id;
- network mode;
- mounts;
- timeout;
- CPU/RAM/PID limits;
- exit code;
- длительность;
- список созданных файлов;
- ссылку на summary report.

Сырые runtime-логи лучше хранить в `logs/` и не версионировать. Человеко-читаемый итог хранить в `reports/sandbox-run-YYYY-MM-DD-<task>.md`.

## Следующий безопасный шаг

До появления реальной песочницы развивать нужно read-only контур:

1. расширять `repo-runner` inventory;
2. сохранять отчеты в `reports/`;
3. делать knowledge corpus и query/report;
4. проверять зависимости и риск-файлы без запуска;
5. регистрировать внешние источники через `sandbox/` и `docs/external-code-sandbox.md`;
6. только после этого проектировать sandbox-runner как отдельный L3/L4 модуль.

Моё мнение: запуск чужого кода должен быть не "следующей кнопкой" в текущем драйвере, а отдельной подсистемой с собственным review, лимитами и audit. Иначе весь полезный read-only слой становится слишком рискованным для обычной многоагентной работы.
