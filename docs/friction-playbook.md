# Friction playbook

Дата: 2026-06-22  
Связано: `docs/friction-ledger.md`, `T-147`.

## Быстрый принцип

Если видишь повторяющуюся проблему, не лечи её каждый раз заново из памяти:

1. Определи симптом.
2. Примени короткий рецепт ниже.
3. Если рецепт сработал — добавь ссылку/подтверждение в задачу или outbox.
4. Если рецепт не сработал — создай вопрос или stream, не переписывай канон вслепую.

## Перед любой новой задачей

```powershell
git status --short --untracked-files=all
python tools\top.py status codex
python tools\generate.py --check
python tools\validate.py
```

Если в `git status` есть чужие изменения, не делай `git add -A`. Для commit используй только явный список файлов.

## Если `apply_patch` падает

Симптом: ошибка Windows sandbox / restricted-token / writable roots.

Действие:

1. Сообщить, что `apply_patch` недоступен в этой среде.
2. Писать только внутри workspace.
3. Использовать UTF-8 без BOM:

```powershell
$enc = [System.Text.UTF8Encoding]::new($false)
[IO.File]::WriteAllText((Join-Path (Get-Location) 'docs\target.md'), $text, $enc)
```

Не использовать этот fallback для удаления/перемещения чужих файлов.

## Если русский текст в PowerShell битый

```powershell
chcp 65001
[Console]::InputEncoding = [System.Text.UTF8Encoding]::new($false)
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
$OutputEncoding = [Console]::OutputEncoding
Get-Content -Encoding UTF8 -LiteralPath ".\PIPELINE.md"
```

Если JSON нужен машинно:

```powershell
Get-Content -Raw -Encoding UTF8 -LiteralPath ".\logs\pipeline.json" | ConvertFrom-Json
```

## Если shell, CMD или Python зависают

Не запускать большой пакет команд. Проверить минимально:

```powershell
cmd.exe /c echo ok
python --version
python -c "print('ok')"
```

Если это зависает, перейти к `docs/runtime-recovery-playbook.md`. Не закрывать runtime-задачи по догадке.

## Если TEMP даёт PermissionError

```powershell
New-Item -ItemType Directory -Force tmp-work | Out-Null
$env:TEMP = (Resolve-Path 'tmp-work').Path
$env:TMP = $env:TEMP
$env:TMPDIR = $env:TEMP
```

Для тестов лучше использовать существующие helpers (`drivers/test_tmp.py`) или `C:\tmp`, если он доступен.

## Если git ругается на index.lock или права `.git`

Сначала:

```powershell
python tools\commit_lock.py status
```

Перед commit:

```powershell
python tools\commit_lock.py acquire codex --ttl 120 --wait 10
```

После commit или отказа:

```powershell
python tools\commit_lock.py release codex
```

Если git stage/commit требует `.git/index.lock` и sandbox запрещает, использовать escalated git-команду только для stage/commit/restore конкретных файлов. Не удалять `.git/index.lock` вслепую.

## Если есть чужая half-done работа

Симптомы:

- в `git status` есть файлы, которые вы не меняли;
- другой агент держит claim;
- есть untracked docs/tools/tasks от параллельной работы.

Действие:

```powershell
git status --short --untracked-files=all
python tools\pipeline.py status
python tools\top.py work-mode codex <T-id> --dirty-mainline --hot-files
```

Правило:

- не делать `git add -A`;
- не коммитить чужие файлы;
- если нужно продолжать параллельно — Level 1 worktree;
- если это только документационный fork — stream/variant рядом.

## Если `generate.py --check` показывает stale

1. Понять источник stale.
2. Если stale вызван вашими source-файлами:

```powershell
python tools\generate.py
python tools\generate.py --check
```

3. Если stale вызван чужими незавершёнными файлами: не коммитить смешанный индекс. Использовать worktree или дождаться integration window.

## Если появились `LIVE.md` или `logs/*` изменения

Это чаще runtime-шум.

В обычной задаче не включать:

```powershell
git status --short --untracked-files=all
```

В commit добавлять только свои смысловые файлы. Runtime snapshots включать только если задача прямо про heartbeat/live/pipeline snapshot.

## Если задача placeholder

Симптом: title `(зарезервировано — заполните)`.

Действие: заполнить task перед claim. `pipeline.py next` не должен выдавать placeholder-задачи.

## Если task `doing`, но claim нет

```powershell
python tools\pipeline.py status
python tools\pipeline.py mine codex
python tools\reconcile_state.py
```

Не переводить чужую задачу в `done` без владельца/основания. Создать outbox или вопрос, если это блокирует работу.

## Если docs drift

```powershell
python tools\generate.py --check
python tools\validate.py
python tools\drift_check.py
python tools\top.py health
```

Если drift реальный, создать маленькую docs-refresh задачу. Если drift только из-за чужой half-done работы, не коммитить смешанный индекс.

## Если надо работать с внешним кодом или svend4

Не запускать внешний код напрямую.

Порядок:

1. Получить read-only источник/путь/archive.
2. Использовать `docs/external-code-sandbox.md` и `tools/sandbox.py` для intake/list.
3. Execute оставлять off до preflight/decision.
4. Отчёт писать в `docs/` или `queues/outbox/`.

## Если stream создан, но непонятно что с ним делать

Проверить:

- есть ли `status`;
- есть ли related task/question/decision;
- есть ли adoption conditions;
- есть ли итог: `adopted`, `superseded`, `rejected`, `archived`.

Если этого нет, не плодить новый stream без причины. Лучше сделать короткий synthesis/outbox.

## Рекомендуемый следующий инструмент

Стабильный минимум для `tools/friction.py` или `tools/top.py friction`:

```powershell
python tools\top.py friction
python tools\friction.py status --json
python tools\friction.py recipe stale-index
python tools\friction.py recipe temp-permission
```

Сначала инструмент должен быть read-only и dry-by-default: обнаружить симптомы, показать рецепт и предложить режим Level 0/Level 1. Автоматически исправлять можно только после отдельного решения.
## Частые вопросы и ответы

### Q: Я уже видел эту ошибку раньше. Что делать сначала?

A: Не решать из памяти. Найти ID в `docs/friction-ledger.md`, применить рецепт из этого playbook, затем записать подтверждение в task/outbox, если проблема снова повторилась.

### Q: Когда проблема становится кандидатом на автоматизацию?

A: Если один и тот же ручной рецепт применён 2-3 раза, он идёт в playbook. Если 4+ раза или стоит больше 10 минут, нужен read-only detector. Если риск связан с чужим commit/data loss, нужен guard/gate.

### Q: Нужно взять конкретную задачу, можно ли просто вызвать `pipeline.py next`?

A: Нет, если нужна именно конкретная задача. `next` берёт следующую ready-задачу по приоритету/ID. Если нужна конкретная T-id, сначала убедиться, что нет более приоритетной ready-задачи, либо нужен будущий `pipeline.py claim <agent> <T-id>`/`top.py take <T-id>`. Если ошибочно взяли не ту задачу, снять только свой claim и вернуть status, не трогая чужую работу.

### Q: Что делать, если `generate.py --check` красный, но я не понимаю почему?

A: Проверить `git status --short --untracked-files=all`. Если есть чужие source-файлы или hot files, это D-022/Q-015-триггер Level 1. Не коммитить смешанный индекс.

### Q: Когда создавать stream, а когда задачу?

A: Stream — для варианта/мнения/доказательств, которые ещё не должны попасть в mainline. Task — для конкретной исполнимой работы с done-критерием. Если stream принят, нужен task/adoption для переноса в mainline.

### Q: Когда делать skill?

A: Когда playbook уже содержит стабильный повторяемый workflow, который должен запускаться по смыслу запроса. Skill должен быть коротким: он не копирует весь ledger, а говорит агенту какие docs читать и какой порядок действий применять.

### Q: Когда делать tool?

A: Когда симптом можно обнаружить машинно: dirty foreign files, stale generated indexes, volatile runtime noise, stale claims, temp write failure. Tool сначала должен быть read-only/dry-by-default.

## Мини-чеклист жалобы

Если агент или человек пишет “опять зависло/сломалось/мешает”, оформить так:

```md
- Симптом:
- Команда/файл/ситуация:
- Было раньше? F-ID:
- Сколько раз примерно:
- Что помогло вручную:
- Потеря времени/риск:
- Нужно ли автоматизировать сейчас:
```
## Если skill frontmatter или metadata validation падает

- Для длинного `description` с двоеточиями использовать YAML block scalar:

```yaml
description: >
  Use when ... friction: Windows sandbox, Git index.lock, stale indexes ...
```

- Если Python-скрипт skill-creator читает UTF-8 как cp1252, повторить с:

```powershell
$env:PYTHONUTF8='1'
python <script>.py ...
```

## Одна команда friction-preflight

Перед задачей, где есть риск повторить старую проблему, запускайте:

```powershell
python tools\top.py friction
```

Или напрямую:

```powershell
python tools\friction.py status
python tools\friction.py recipe F-007
python tools\friction.py list
```

Как читать результат:

- `OK` — проверка не видит симптом сейчас.
- `INFO` — проверка пропущена или носит справочный характер.
- `WARN` — работа может продолжаться, но нужен рецепт и осторожный commit scope.
- `FAIL` — сначала устранить runtime/temp/critical состояние, потом продолжать.

Типичный смысл предупреждения `F-006/F-007/F-015`: рабочее дерево грязное или есть generated/shared файлы. Это нормально во время активной задачи, но запрещает `git add -A`. Перед commit нужно снова выполнить `git status --short --untracked-files=all` и stage только явные файлы текущей задачи.

Если `friction.py` нашёл stream/skill/docs drift, не чините это внутри чужой задачи без основания. Создайте отдельную cleanup-задачу или outbox-заметку.
