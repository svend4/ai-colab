# Top layer command groups — панель вершины пирамиды

Дата: 2026-06-21.
Связано: `tools/top.py`, `system-capabilities.json`, `docs/top-agent-operating-manual.md`, `T-138`.

## Зачем это нужно

Внутри проекта уже есть много полезных функций: pipeline, validate, generate, capabilities, drift_check, knowledge, drivers, commit_lock. Для агента это нормально, но человеку и новому агенту неудобно помнить десятки отдельных команд.

`tools/top.py` — верхняя панель управления. Она не заменяет низкоуровневые инструменты, а группирует их в сценарии, похожие на кнопки:

```powershell
python tools\top.py buttons
python tools\top.py status codex
python tools\top.py health
python tools\top.py agent-start codex
python tools\top.py instruction-preflight codex T-154
python tools\top.py take codex
python tools\top.py snapshot
python tools\top.py knowledge data\knowledge-corpus --query bridge --out reports\bridge.md
```

## Принцип

Низ остаётся богатым: драйверы, индексы, задачи, отчёты, SQLite, MCP.

Верх должен быть простым:

| Сценарий | Для человека | Для агента | Что происходит |
|---|---|---|---|
| Старт | понять, что есть | подключиться без чтения 10 файлов | `agent-start` вызывает onboarding и статус |
| Проверка | увидеть, всё ли живо | перед правкой/коммитом | `health` вызывает validate/generate/capabilities/catalog |
| Инструкции | понять применимые правила | собрать evidence перед задачей | `instruction-preflight` вызывает `instructions.py preflight` |
| Работа | видеть котёл | взять одну задачу | `take` вызывает pipeline next или targeted claim по T-id |
| Выбор режима | понять shared/worktree | выбрать D-021 режим | `work-mode` печатает Level 0/Level 1 план |
| Знания | получить отчёт | обработать corpus | `knowledge` вызывает L6 workflow |
| Сравнение | увидеть разницу отчётов | оценить прогресс corpus | `report-diff` сравнивает documents/types/hits |
| Снимки | обновить доски | синхронизировать derived files | `snapshot` вызывает capabilities/catalog/generate/pipeline snapshot |

## Как это помогает параллельной работе

Для людей:

- меньше ручных команд;
- понятнее, какая команда только читает, а какая меняет состояние;
- можно объяснять действия как “нажми кнопку health/status/knowledge”, а не как 5 строк PowerShell.

Для агентов:

- единая точка входа снижает дрейф между инструкциями;
- сценарии можно вызывать из других автоматизаций;
- `buttons --json` даёт машинно-читаемый список действий;
- side-effect команды явно названы (`take`, `snapshot`, `knowledge --out`).

## Граница безопасности

`top.py` не открывает execute. Он запускает только уже существующие проверенные инструменты внутри workspace. Опасные будущие действия должны идти через отдельные gates:

- network/source intake — через sandbox policy;
- execute — только после preflight и accepted decision;
- commit — через `commit_lock.py` и selective-add.
- worktree — только как явный Level 1 режим; `work-mode` по умолчанию ничего не создаёт.

## Моё мнение

Это правильный следующий шаг для “середины пирамиды”: не строить ещё один большой слой, а сделать тонкую панель над уже работающими возможностями. Для настоящей UI-кнопки позже можно обернуть `tools/top.py buttons --json` в GUI, web-dashboard, MCP tool или ChatGPT app. Контракт уже будет готов.

## Расширение T-144: выбор режима работы

После `D-021` верхний слой умеет не только показывать команды, но и помогать выбрать режим выполнения задачи:

```powershell
python tools\top.py work-mode codex T-144
python tools\top.py work-mode codex T-144 --parallel --hot-files
python tools\top.py work-mode codex T-144 --mode worktree
```

Смысл:

| Режим | Когда использовать | Что печатает |
|---|---|---|
| Level 0 shared tree | маленькая низкоконфликтная задача | status/mine/health/merge_gate/cohort ship |
| Level 1 worktree | параллельная работа, грязная mainline, горячие generated files | `flow.py start/finish --worktree` dry-run |

Команда не создаёт worktree и не делает commit. Она превращает принятую D-021 политику в короткую подсказку для старта задачи.

## Расширение T-137: параллельная работа и синтез

После T-137 верхний слой использует не только одиночный `top.py`, но и набор коротких команд для многих агентов:

```powershell
python tools\cohort.py board
python tools\cohort.py self --json
python tools\variants.py list --topic commit-policy
python tools\synthesis_helper.py report commit-policy --out темы\commit-policy-synthesis.md
python tools\merge_gate.py check codex
python tools\stream.py list commit-policy
python tools\promote.py check --artifact sandbox\reports\demo-fixtures-inventory.md
python tools\sandbox_intake_demo.py --out tmp-work\sandbox-demo
```

Смысл разделения:

| Инструмент | Роль | Эффект |
|---|---|---|
| `cohort.py` | верхняя панель для нескольких агентов: board/plan/turn/gate/ship/self | dry/read-only по умолчанию, кроме явного `--run` |
| `variants.py` | найти fork-варианты перед синтезом | read-only |
| `synthesis_helper.py` | подготовить scaffold синтеза без принятия решения | пишет report при `--out` |
| `stream.py` | semi-commit пакет варианта в `streams/` | пишет отдельный пакет, mainline не трогает |
| `merge_gate.py` | read-only проверка перед вливанием | read-only |
| `promote.py` | gate подъёма L4→L3→L2→L1 | `check` read-only, `move` только после review |
| `sandbox_intake_demo.py` | доказательство read-only intake без внешнего svend4 | пишет manifest/report в `--out` |

Моё мнение: это именно та “середина пирамиды”, которую стоит развивать сейчас. Она автоматизирует повторяемые действия агентов и людей, но не вводит тяжёлый router/RAG/execute слой до доказанной необходимости.

## Расширение T-154: instruction preflight

После T-154 верхний слой умеет показывать не только состояние и команды, но и применимые правила для конкретной задачи:

```powershell
python tools\top.py instruction-preflight codex T-154
python tools\instructions.py manifest
python tools\instructions.py check-report queues\outbox\2026-06-22-instruction-assurance-and-synthesis.md
```

Смысл:

| Команда | Эффект | Что даёт |
|---|---|---|
| `instructions.py manifest` | read-only | курируемая карта инструкций и областей применения |
| `instructions.py preflight <agent> [T-id]` | read-only | task-scoped список правил, gates и evidence-template |
| `instructions.py check-report <path>` | read-only | мягкая проверка, что отчёт содержит `Applied instructions` |
| `top.py instruction-preflight` | read-only | та же процедура как верхняя кнопка для людей/агентов |

Моё мнение: это правильная форма гарантии для текущей стадии. Не нужно сразу блокировать все действия большим policy-engine. Сначала агент должен явно видеть применимые инструкции и оставлять evidence. Потом часто повторяющиеся нарушения можно переносить в `friction.py`, `merge_gate.py` или pre-commit.
