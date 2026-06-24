# Top layer command groups — панель вершины пирамиды

Дата: 2026-06-21.
Связано: `tools/top.py`, `system-capabilities.json`, `docs/top-agent-operating-manual.md`, `T-138`.

## Зачем это нужно

Внутри проекта уже есть много полезных функций: pipeline, validate, generate, capabilities, drift_check, knowledge, drivers, commit_lock. Для агента это нормально, но человеку и новому агенту неудобно помнить десятки отдельных команд.

`tools/top.py` — верхняя панель управления. Она не заменяет низкоуровневые инструменты, а группирует их в сценарии, похожие на кнопки:
Если агент знает тему задачи заранее, стартуйте так: `python tools\top.py agent-start codex --task T-id --context "<тема или вопрос>"`. Это сразу показывает onboarding/status, assurance/advice и поднимает релевантные решения, политики, вопросы и задачи через `repo-search`.

```powershell
python tools\top.py buttons
python tools\top.py status codex
python tools\top.py health
python tools\top.py assurance all --json
python tools\top.py advice codex T-188 --parallel --hot-files
python tools\top.py agent-start codex --task T-188 --context "parallel work policy"
python tools\top.py subagent-handoff mavis T-161 "agent launch workflow" --worktree
python tools\top.py instruction-preflight codex T-154
python tools\top.py take codex
python tools\top.py snapshot
python tools\top.py knowledge data\knowledge-corpus --query bridge --out reports\bridge.md
python tools\top.py repo-search "parallel work policy" --limit 5
python tools\top.py conveyor --json
python tools\top.py cauldron-lanes architecture-core
python tools\top.py synthesize-docs architecture-core --with-streams
```

## Принцип

Низ остаётся богатым: драйверы, индексы, задачи, отчёты, SQLite, MCP.

Верх должен быть простым:

| Сценарий | Для человека | Для агента | Что происходит |
|---|---|---|---|
| Старт | понять, что есть | подключиться без чтения 10 файлов | `agent-start` вызывает onboarding, статус, assurance/advice и опциональный `repo-search --context` |
| Проверка | увидеть, всё ли живо | перед правкой/коммитом | `health` вызывает validate/generate/capabilities/catalog |
| Проверяемость | увидеть, применяются ли инструкции и не устарел ли слой | поднять Q-016 applied/currency/coverage/flow к вершине | `assurance` вызывает `assurance.py` advisory по умолчанию, strict только явно |
| Активация советов | увидеть, какие уже существующие рекомендации применимы сейчас | не забыть worktree/friction/assurance/preflight при текущих симптомах | `advice` связывает `friction`/`assurance` с командами активации |
| Инструкции | понять применимые правила | собрать evidence перед задачей | `instruction-preflight` вызывает `instructions.py preflight` |
| Работа | видеть котёл | взять одну задачу | `take` вызывает pipeline next или targeted claim по T-id |
| Выбор режима | понять shared/worktree | выбрать D-021 режим | `work-mode` печатает Level 0/Level 1 план |
| Запуск sub-agent | получить готовый пакет запуска | выдать worker prompt и repo lane | `subagent-handoff` вызывает `flow.py launch-plan` |
| Знания | получить отчёт | обработать corpus | `knowledge` вызывает L6 workflow |
| Поиск по канону | найти решение/политику/задачу | быстро поднять контекст перед правкой | `repo-search` строит ignored FTS/BM25 индекс по docs/decisions/questions/темам/tasks |
| Сравнение | увидеть разницу отчётов | оценить прогресс corpus | `report-diff` сравнивает documents/types/hits |
| Снимки | обновить доски | синхронизировать derived files | `snapshot` вызывает capabilities/catalog/generate/pipeline snapshot |
| Надзор конвейера | увидеть, нужен ли дозалив/обработка | не держать workflow в голове | `conveyor` вызывает `conveyor.py status` и показывает REFILL/PROCESS/IDLE |
| Две полосы котла | увидеть готовое к строительству и спорное | выбрать ratio 50/50, 70/30 или 30/70 | `cauldron-lanes` вызывает `doc_synthesis.py` и показывает `ratify-build`/`divergence-detail` |
| Синтез документов v2 | собрать candidates, refs и stream scaffold | не потерять evidence и divergence | `synthesize-docs` вызывает `doc_synthesis.py scan` с `--with-streams` по явному флагу |
| Обработка landed | увидеть следующий intake/verify/synthesis шаг | обработать output без потери контекста | `process-landed` строит read-only план по `landed` outputs |
| Assurance apex | увидеть applied/currency/coverage/flow | начать работу с проверяемого состояния инструкций | `assurance` вызывает `assurance.py`; `health` показывает его как warning-layer |

## Как это помогает параллельной работе

Для людей:

- меньше ручных команд;
- понятнее, какая команда только читает, а какая меняет состояние;
- можно объяснять действия как “нажми кнопку health/status/knowledge”, а не как 5 строк PowerShell.

Для агентов:

- единая точка входа снижает дрейф между инструкциями;
- сценарии можно вызывать из других автоматизаций;
- `buttons --json` даёт машинно-читаемый список действий;
- side-effect команды явно названы (`take`, `snapshot`, `knowledge --out`); `repo-search` read-mostly и пишет только ignored runtime DB в `logs/`.

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
python tools\synthesis_helper.py report commit-policy --out topics\commit-policy-synthesis.md
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
| `sandbox_intake_demo.py` | доказательство read-only intake без внешнего svend4; manual-demo, не dead code | пишет manifest/report в `--out` |

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
| `instructions.py check-report <path>` | read-only | мягкая проверка `Applied instructions` + advisory по ссылкам на файлы и `Checks:` команды |
| `top.py instruction-preflight` | read-only | та же процедура как верхняя кнопка для людей/агентов |

Моё мнение: это правильная форма гарантии для текущей стадии. Не нужно сразу блокировать все действия большим policy-engine. Сначала агент должен явно видеть применимые инструкции и оставлять evidence. Потом часто повторяющиеся нарушения можно переносить в `friction.py`, `merge_gate.py` или pre-commit.

## Расширение T-165: assurance apex

После T-165 верхний слой показывает Q-016 проверяемость одной командой:

```powershell
python tools\top.py assurance
python tools\top.py assurance currency --json
python tools\top.py assurance flow --strict
```

Смысл:

| Команда | Эффект | Что даёт |
|---|---|---|
| `top.py assurance` | read-only, advisory | общий снимок applied/currency/coverage/flow |
| `top.py assurance <section> --json` | read-only, machine-readable | чистый вход для агента/дашборда |
| `top.py assurance <section> --strict` | read-only, opt-in strict | nonzero exit только когда caller явно хочет gate |
| `top.py health` | hard checks + warning layer | validate/generate/capabilities остаются hard, assurance печатается advisory |

Моё мнение: это важная связь основания и вершины пирамиды. Инструкции, freshness и coverage уже существуют в нижнем слое; теперь они видны как стандартная верхняя команда, а не как отдельный забываемый скрипт.

## Расширение: advice activator

После добавления `tools/advice.py` верхний слой умеет не только показать отдельные проверки, но и связать их с уже существующими рекомендациями:

```powershell
python tools\top.py advice codex T-188 --parallel --hot-files
python tools\advice.py current codex T-188 --parallel --hot-files --json
```

Смысл:

| Сигнал | Откуда берётся | Что активируется |
|---|---|---|
| dirty/stale/gate/stream warnings | `tools/friction.py status` | рецепты `friction.py recipe F-XXX` и `work-mode` |
| assurance findings | `tools/assurance.py all` | `instruction-preflight`, applied-evidence, strict-gate-кандидаты |
| parallel/hot work | флаги задачи/агента | `top.py work-mode ... --parallel/--hot-files` |

Это решает классическую проблему "хороший совет уже лежит в документации, но не используется": совет считается живым только когда есть команда активации и текущий симптом, который его включает. После текущего усиления `agent-start` вызывает advice автоматически, поэтому новый агент видит рекомендации до claim/правок, а не после повторения старой ошибки.

## Расширение T-161: handoff для запуска sub-agent

После T-161 верхний слой умеет готовить запуск внешнего worker-agent одной командой:

```powershell
python tools\top.py subagent-handoff mavis T-161 "agent launch workflow" --worktree
python tools\flow.py launch-plan mavis T-161 agent launch workflow --worktree
```

Команда не запускает агента сама. Она печатает воспроизводимый launch-пакет: repo lane, start-команду, prompt для worker-agent и finish-команду. Реальный запуск делает внешний Codex/platform launcher, человек или будущий сервер-оркестратор.

Моё мнение: это правильная середина между ручной перепиской и тяжёлой серверной платформой. Репозиторий уже знает правила, задачи, worktree и проверки; внешний launcher знает, как создать AI-worker. Handoff связывает эти два мира без жёсткой зависимости.

## Расширение T-221: cauldron-lanes

После T-221 верхний слой умеет показывать две рабочие полосы котла одной командой:

```powershell
python tools\top.py cauldron-lanes architecture-core
python tools\top.py synthesize-docs architecture-core --with-streams
python tools\top.py cauldron-lanes architecture-core --json
python tools\top.py cauldron-lanes architecture-core --out docs\architecture-core-documents-synthesis-2026-06-24.md
```

Смысл:

| Полоса | Что означает | Дальнейшая работа |
|---|---|---|
| `ratify-build` | тема уже часто совпадает в документах/мнениях | ратификация, код, тест, wrapper, проверка |
| `divergence-detail` | тема ещё спорная или недоразвёрнутая | варианты, evidence, risks, критерий перехода |

Моё мнение: это превращает котёл из просто списка обсуждений в рабочий диспетчер зрелости. Агент может выбрать режим 50/50, 70/30 или 30/70 без ручного чтения всего synthesis-документа.

## Расширение T-218: synthesize-docs

После T-218 верхний слой умеет запускать document synthesis v2:

```powershell
python tools\doc_synthesis.py candidates architecture-core
python tools\top.py synthesize-docs architecture-core --json
python tools\top.py synthesize-docs architecture-core --out docs\architecture-core-documents-synthesis-2026-06-24.md
python tools\top.py synthesize-docs architecture-core --with-streams
```

Что добавлено:

| Возможность | Зачем |
|---|---|
| `candidates` | найти документы, которые похожи на тему синтеза |
| source-line refs | показать evidence как `file:line`, чтобы спор можно было проверить |
| `--with-streams` | создать/обновить stream scaffold без принятия accepted-решения |
| `top.py synthesize-docs` | сделать synthesis доступным как верхнюю команду |

Safety-правило: `--with-streams` не перезаписывает существующий ручной `streams/<topic>/divergence.md`; если файл уже есть, создаётся `streams/<topic>/divergence.generated.md` для ручного сравнения.
