# Friction ledger

Дата: 2026-06-22
Связано: `T-147`, `docs/friction-playbook.md`, `docs/runtime-recovery-playbook.md`, `docs/powershell-utf8-output.md`, `docs/parallel-streams-problems-review-2026-06-22.md`, `docs/commit-stream-policy.md`, `Q-015`, `D-022`.

## Назначение

Этот документ — бухгалтерия повторяющегося трения в проекте. Он нужен не для истории ради истории, а для принятия инженерного решения: что пока лечится инструкцией, а что уже повторилось достаточно раз и должно быть автоматизировано.

Правило отбора:

- один раз встретилось — записать как наблюдение;
- два-три раза встретилось с одинаковым решением — добавить в playbook;
- продолжает мешать после playbook — переносить в `tools/friction.py` или `tools/top.py friction`.

## Сводная таблица

| ID | Симптом | Где встречалось | Частота | Ручное решение сейчас | Риск | Что автоматизировать |
|---|---|---|---|---|---|---|
| F-001 | `apply_patch` падает в Windows sandbox | текущие Codex-сессии, правки T-146/T-147 | повторяется | Перед правкой объяснить причину; писать UTF-8 через PowerShell `[IO.File]::WriteAllText` только внутри workspace | случайная запись не туда, потеря patch-audit | `tools/friction.py apply-patch-fallback` с проверкой пути и UTF-8 |
| F-002 | PowerShell mojibake (`Ð...`, `Ñ...`) при чтении Markdown | `docs/powershell-utf8-output.md`, T-071/T-073 | повторялось | `chcp 65001`; выставить Input/OutputEncoding; читать `Get-Content -Encoding UTF8` | ложное исправление нормального UTF-8 файла | `tools/friction.py encoding` печатает команды и проверяет roundtrip |
| F-003 | PowerShell/CMD/Python зависают или долго стартуют | `docs/runtime-recovery-playbook.md`, `docs/runtime-diagnostics.md`, T-039/T-065 | повторялось | короткие команды; timeout wrapper; не запускать длинные цепочки; проверять процессы отдельно | потеря часов, неверное ощущение блокировки проекта | `tools/friction.py runtime` с smoke-check и советом внешней консоли |
| F-004 | `%TEMP%`/`tempfile` даёт `PermissionError` | driver tests, `docs/t137-consensus-result-2026-06-21.md`, пользовательский `test_files.py` вывод | повторялось | использовать `tmp-work/`, `C:\tmp`, `drivers/test_tmp.py`; не полагаться на пользовательский `%TEMP%` | тесты ложнопадают, создают мусор | общий temp helper + checker в `tools/friction.py temp` |
| F-005 | Git `.git/index.lock` / права на `.git` | commit attempts, sandbox restore/stage, `tools/commit_lock.py` | повторяется | `tools/commit_lock.py acquire/release`; escalation для git stage/commit; selective-add | коммиты блокируются, можно сломать чужой lock | `tools/friction.py git-lock` проверяет lock owner/status и печатает безопасный порядок |
| F-006 | Чужая half-done работа в общем дереве | T-133/T-136, T-146, текущие чужие `tools/cohort.py` правки | повторяется | не использовать `git add -A`; selective-add только своих файлов; при hot/dirty — Level 1 worktree | чужой незавершённый код попадёт в commit | `tools/top.py preflight` группирует own/foreign/unknown files |
| F-007 | Stale generated indexes (`TASKS.md`, `index.json`, `QUESTIONS.md`) из-за чужой работы | D-019, T-136, T-146 | повторяется | если stale мой — `generate.py`; если чужой — не коммитить смешанный индекс, использовать worktree/ожидание/интеграцию | mainline фиксирует transient-состояние | preflight: определить источник stale и предложить Level 0/1 |
| F-008 | Runtime-шум `LIVE.md`, `logs/heartbeat.json`, `logs/pipeline.json` попадает в status | T-146, heartbeat/snapshot runs | повторяется | не включать volatile snapshots в обычный commit; restore своих runtime-файлов при необходимости | шумные commits, конфликт видимости | `tools/friction.py volatile` показывает, что исключить из add |
| F-009 | Placeholder tasks засоряют pipeline | T-067, pipeline placeholder gating | решено, но важно | placeholder-задачи не выдаются `pipeline.py next`; заполнить перед claim | агенты берут пустые задачи | validate/pipeline уже покрывают; держать в ledger |
| F-010 | `doing` без active claim | T-068, stale-work cleanup, pipeline reports | решено частично | `pipeline.py status`, `reconcile_state.py`, не закрывать чужое молча | задача кажется занятой навсегда | `tools/friction.py claims` показывает orphan/stale claims |
| F-011 | Docs drift: отчёты/roadmap отстают от факта | T-128..T-131, drift_check, top health | повторяется | `generate.py --check`, `validate.py`, `drift_check.py`, result docs | агент принимает решение по старой информации | `top.py health` уже частично; friction summary объединит |
| F-012 | External code / svend4 / неизвестный repo нельзя запускать напрямую | `docs/external-code-sandbox.md`, `tools/sandbox.py`, T-020 | постоянный блокер | read-only intake; execute off до preflight/decision | запуск недоверенного кода на Windows host | sandbox preflight checklist + intake status command |
| F-013 | Streams создаются, но могут зависать без adoption | `streams/`, D-017/D-019/D-021, T-146 stream | растущий риск | каждый stream должен иметь status, related, adoption conditions; синтез через Q/D/task | кладбище вариантов, потеря решений | `tools/stream.py check` и stale stream report |
| F-014 | Слишком много команд для человека/агента | top facade, user feedback, T-144 | повторяется | `tools/top.py buttons/status/health/work-mode`; короткие группы команд | медленная работа, ошибки порядка | `tools/top.py friction` как одна кнопка диагностики |
| F-015 | Сторонние правки появляются между проверкой и commit | T-146/T-147 текущая ситуация | повторяется | перед commit снова `git status`; stage только явный список; не трогать чужие файлы | смешанный commit, потеря ответственности | preflight snapshot + selective staging audit |

## Детали по ключевым проблемам

### F-001. `apply_patch` в Windows sandbox

Симптом: `apply_patch` не может подготовить sandbox wrapper и отказывается работать с split writable roots.

Текущий безопасный fallback:

1. Сообщить в чат, что `apply_patch` недоступен именно из-за sandbox.
2. Писать только внутри workspace.
3. Использовать UTF-8 без BOM:

```powershell
$enc = [System.Text.UTF8Encoding]::new($false)
[IO.File]::WriteAllText((Join-Path (Get-Location) 'docs\file.md'), $text, $enc)
```

Автоматизировать стоит только проверку пути и шаблон записи; сам факт fallback должен оставаться видимым.

### F-004. TEMP permissions

Симптом: Python создаёт каталог во временной директории, но затем не может писать внутрь (`PermissionError`).

Рабочий принцип: тесты проекта должны брать temp из контролируемого места: `tmp-work/`, `C:\tmp`, helper `drivers/test_tmp.py`.

Команды для человека:

```powershell
New-Item -ItemType Directory -Force tmp-work | Out-Null
$env:TEMP = (Resolve-Path 'tmp-work').Path
$env:TMP = $env:TEMP
$env:TMPDIR = $env:TEMP
```

### F-006/F-007. Half-done и stale generated indexes

Это главный многоагентный дефект: даже если агент не коммитит чужие source-файлы, `generate.py` может втянуть чужую незавершённую задачу в общий индекс.

Текущий порядок:

- если дерево чистое и stale вызван моими source-файлами — `generate.py`, затем selective-add источников и индексов;
- если stale вызван чужими файлами — не коммитить смешанный индекс;
- если работа параллельная или hot — переходить в Level 1 worktree;
- если спорная идея, но ещё не code/mainline — оформить stream.

### F-008. Volatile runtime snapshots

`LIVE.md`, `logs/heartbeat.json`, `logs/pipeline.json`, per-agent heartbeat — это операционная видимость. Они полезны во время работы, но часто не являются смысловой частью commit.

Правило: включать volatile snapshots только если задача прямо про live-room/heartbeat/pipeline snapshot. В обычной docs/code задаче исключать.

### F-013. Stream lifecycle

`streams/` полезен только если есть жизненный цикл. Минимальная карточка stream должна отвечать:

- что это за вариант;
- с чем он связан;
- какой статус;
- как проверить;
- что нужно для adoption;
- чем он завершился.

Без этого stream становится ещё одним местом, которое надо вручную перечитывать.

## Приоритет автоматизации

### P1. `tools/top.py friction` или `tools/friction.py status`

Должен выполнять read-only диагностику:

```powershell
python tools\top.py friction
```

Минимальный вывод:

```text
FRICTION STATUS
- dirty foreign source: yes/no
- hot files touched: yes/no
- generated index stale: yes/no
- volatile runtime noise: yes/no
- active/stale claims: yes/no
- temp writable: yes/no
- encoding note: powershell/cp65001 unknown
recommendation: Level 0 / Level 1 / stop and ask
recipes: exact commands
```

### P2. `tools/stream.py check`

Проверять stream lifecycle:

- stale proposed streams;
- missing related;
- missing adoption section;
- adopted stream without commit/task link.

### P3. Project skill after stabilization

Когда ledger/playbook будут применены несколько раз, можно создать `skills/repo-friction-playbook/SKILL.md`. Сейчас лучше не делать skill первым источником правды: источник правды должен быть в `docs/friction-ledger.md` и `docs/friction-playbook.md`.

## Решение по этой итерации

В T-147 создаётся документация и outbox. Большой автоматический инструмент не пишется: список симптомов ещё надо один-два раза применить в реальных задачах, затем переносить стабильные проверки в `tools/friction.py` или `tools/top.py friction`.
## Архетипы повторяющегося трения

| Архетип | Включает F-ID | Оценка ручных повторов | Типовое ручное лечение | Порог автоматизации | Следующий автоматический слой |
|---|---|---:|---|---|---|
| Windows shell/runtime friction | F-002, F-003, F-004 | 6+ | UTF-8 setup, короткие команды, workspace temp, runtime smoke-check | если снова блокирует задачу больше 10 минут | `tools/friction.py runtime`, `tools/friction.py temp`, `tools/friction.py encoding` |
| Git/shared-worktree friction | F-005, F-006, F-007, F-008, F-015 | 8+ | commit_lock, selective-add, restore volatile, Level 1 worktree по триггерам | если agent дважды ждёт чужой commit или ловит stale-loop | `tools/top.py friction`, `cohort guard`, auto work-mode preflight |
| Pipeline/coordination friction | F-009, F-010, F-014, F-016 | 4+ | заполнить task до claim, проверить mine/status, не вызывать `next` если нужна конкретная задача | если агент взял не ту задачу или оставил orphan claim | `pipeline.py claim <T-id>` или `top.py take <T-id>` |
| Knowledge/governance drift | F-011, F-013 | 4+ | generate/validate/drift_check, stream adoption/rejection, outbox summary | если stream/decision/task висит без итога больше N дней | `stream.py check`, stale governance report |
| External-code safety friction | F-012 | постоянный блокер | read-only sandbox intake, execute off, external-source preflight | когда появится реальный внешний источник | sandbox intake status + preflight checklist |

## Новые находки 2026-06-22

| ID | Симптом | Где встречалось | Оценка повторов | Ручное решение сейчас | Риск | Что автоматизировать |
|---|---|---|---:|---|---|---|
| F-016 | `pipeline.py next` берёт следующую задачу по приоритету/ID, а не “ту, которую агент имел в виду” | T-149: `next` взял T-148, пришлось вручную снять свой claim и повысить priority T-149 | 1, но высокий UX-риск | если нужна конкретная задача, не вызывать `next` вслепую; либо временно выставить priority/depends, либо нужен targeted claim | агент может случайно занять чужой/нежелательный work item и оставить claim | добавить `pipeline.py claim <agent> <T-id>` или `top.py take <agent> <T-id>` с проверкой ready/placeholder/claim |
| F-017 | Ручная бухгалтерия “сколько раз решали” пока приблизительная | T-147/T-149 ledger | 1 | вести оценку `1 / 2-3 / 4+ / 8+`, пока нет event log | невозможно точно приоритизировать автоматизацию | future: `logs/friction.jsonl` или `tools/friction.py note <F-id>` |
| F-018 | Skill/документы могут разойтись | создание `repo-friction-playbook` после ledger/playbook | 1 | skill должен быть тонкой навигацией, а детали остаются в `docs/friction-*` | агент читает устаревший skill и не смотрит канон | в `validate.py` позже проверить наличие ссылок skill -> docs |

## Бухгалтерское правило для автоматизации

Автоматизировать не “по желанию”, а по повторяемости и цене:

1. **1 раз:** записать в ledger как наблюдение.
2. **2-3 раза:** добавить рецепт в playbook.
3. **4+ раза:** создать skill или top-command, если рецепт уже стабилен.
4. **6+ раз или потеря >10 минут:** добавить read-only detector.
5. **8+ раз или риск чужого commit/data loss:** добавить guard/gate, который блокирует опасное действие или явно переводит в Level 1.

## Формат новой записи friction

```md
| F-XXX | Симптом | Где встречалось | Оценка повторов | Ручное решение сейчас | Риск | Что автоматизировать |
```

Минимум для каждой записи:

- симптом должен быть видимым в команде, ошибке, статусе или поведении;
- решение должно быть уже реально применено хотя бы один раз;
- риск должен объяснять, почему это не просто неудобство;
- automation candidate должен быть read-only/dry-by-default, пока нет отдельного решения на auto-fix.

## T-150 — deep retrospective + first detector

Дата: 2026-06-22
Связано: `docs/friction-retrospective-2026-06-22.md`, `tools/friction.py`, `tools/test_friction.py`, `tools/top.py friction`.

Что изменилось:

- проведён глубокий retrospective audit по прошлым инцидентам и текущей сессии;
- F-001..F-019 сохранены как стабильный реестр симптомов и рецептов;
- добавлен `tools/friction.py status` как read-mostly detector: dirty/stale/volatile/lock/pipeline/drift/streams/temp/sandbox/skill-links;
- добавлена команда верхнего уровня `python tools/top.py friction`;
- тест `tools/test_friction.py` специально закрепляет правила F-004: не использовать системный `%TEMP%` в герметичных тестах этой среды.

Новая практическая норма: перед повторным ручным workaround сначала запускать:

```powershell
python tools\top.py friction
python tools\friction.py recipe <F-id>
```

Если detector показывает dirty/stale/stream warnings, это не обязательно блокер работы. Это сигнал: не использовать `git add -A`, не смешивать чужие изменения и перед commit делать selective-add.
