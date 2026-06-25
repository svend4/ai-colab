---
id: 2026-06-24-lagrange-centralization-information-plan
type: workflow-design
status: historical
owner: lagrange
scope: low-conflict/outbox-only
date: 2026-06-24
related: 
---

# Lagrange workflow/conveyor plan for information centralization

## 0. Purpose

Этот документ оформляет постоянный workflow для Lagrange как параллельного read-only/low-conflict агента. Его задача - помогать верхнему слою не терять информацию: находить уже существующие рекомендации, превращать их в применимые задания, отделять consensus от divergence и подготавливать следующий круг работы для Codex или других агентов.

Ключевой принцип: Lagrange не должен соревноваться с Codex за одни и те же файлы. Его нормальный выход - один outbox-отчет, где есть evidence, рекомендации, безопасные write scopes и следующий handoff.

## 1. Current workflow loop

Постоянный цикл агентской работы:

```text
SENSE -> ASSIGN -> EXECUTE -> REPORT -> VERIFY -> SYNTHESIZE -> IMPLEMENT/ROUTE -> NEXT LOOP
```

| Stage | Кто действует | Где фиксируется | Что получается |
|---|---|---|---|
| SENSE | Codex / человек | `python tools/top.py status`, `python tools/top.py conveyor --json`, `python tools/top.py health` | понятно, есть ли готовые задачи, landed outputs, warnings |
| ASSIGN | человек / Codex-интегратор | `tasks/`, `queues/inbox/`, direct prompt | сформулирован task id, owner, scope, verification |
| EXECUTE | Lagrange / другой агент | свой outbox-файл, read-only поиск, иногда isolated stream | результат без перезаписи чужого кода |
| REPORT | исполнитель | `queues/outbox/` | отчет с evidence, выводами, next suggestions |
| VERIFY | Codex-интегратор | `instructions.py check-report`, `validate.py`, точечные команды | проверено, что отчет применим и не ломает правила |
| SYNTHESIZE | Codex / synthesis-agent | `doc_synthesis.py`, `synthesis_helper.py`, divergence stream | consensus, near-consensus, divergence |
| IMPLEMENT/ROUTE | Codex / назначенный worker | claimed task files | либо код/документация, либо новая задача/вопрос |
| NEXT LOOP | Codex / человек | новый task, новый outbox request, conveyor refill | следующий круг не ждет полной ручной переписки |

Кто запускает следующий круг:

- человек задает стратегическое направление;
- Codex-интегратор выбирает ближайший безопасный шаг, проверяет отчет и создает или берет следующую задачу;
- Lagrange предлагает карту следующего слоя, но не утверждает `accepted` решения без человека;
- если landed/outbox накапливаются, приоритет не fan-out, а обработка и synthesis.

## 2. Format of one agent task

Рекомендуемый формат задания агенту:

```md
# Agent task

- task_id: concrete task id or ad-hoc-outbox
- owner: lagrange | mavis | reviewer | pool
- mode: read-only | outbox-only | stream-only | worktree
- topic: краткое имя темы
- objective: что получить к концу
- allowed_writes: точный один файл или изолированная папка
- forbidden_writes: generated files, shared code, mainline docs без отдельного claim
- read_targets: docs, decisions, questions, tasks, portals, core, sandbox docs
- verification_commands: runnable commands only
- expected_report: summary, evidence, consensus, divergence, next suggestions
- handoff_next: Codex verify, synthesize, create or claim next task
```

Важно: `allowed_writes` должен быть точным. Чем уже write scope, тем больше агентов можно запускать параллельно.

## 3. Format of one agent report

Каждый отчет Lagrange должен иметь одинаковую структуру:

```md
# <topic> report

## Summary
3-7 строк: главный вывод, не история работы.

## Read evidence
Какие документы/папки читались, какие команды поиска использовались, какие ключевые ссылки найдены.

## Findings
Consensus, near-consensus, divergence, unused advice.

## Proposed workflow actions
Какие действия сделать дальше, какой write scope, кто может выполнять, какие проверки.

## Apply / do not apply
Apply now: безопасные read-only/docs/build шаги.
Do not apply yet: governance, execute, конфликтующие варианты, непроверенный внешний код.

## Next task suggestions
Таблица: candidate, goal, owner, write scope, verification, risk.

## Applied instructions
AGENTS.md, PROTOCOL.md, low-conflict note.
```

Такой формат делает отчет пригодным для автоматического `read -> verify -> synthesize`.

## 4. How Codex should apply the report

Порядок применения отчета верхним слоем:

1. Read: открыть outbox-файл и выделить `Apply now`, `Do not apply yet`, `Next task suggestions`.
2. Verify: запустить `python tools\instructions.py check-report queues\outbox\2026-06-24-lagrange-centralization-information-plan.md` или тот outbox-файл, который реально проверяется.
3. Classify: определить тип результата: `docs-change`, `build-change`, `governance`, `external-code`, `synthesis`.
4. Synthesize: если есть несколько похожих отчетов, использовать `tools/doc_synthesis.py` или `tools/top.py synthesize-docs`.
5. Decide: consensus превращать в implementation task; divergence - в отдельный stream или отдельный вопрос.
6. Create/claim next task: только после проверки write scope и hot files.
7. Optionally ask another agent: если нужен independent review, дать outbox-only/review-only задание с непересекающимся путем.
8. Implement: Codex или worker меняет код/доки в своем claim/worktree.
9. Report back: результат фиксируется в outbox и закрывается через pipeline только если была pipeline-задача.

Главное правило: Codex не должен механически применять все предложения. Отчет Lagrange - вход в верхний слой, а не автоматическое решение.

## 5. Conflict avoidance

Низкоконфликтная модель:

- read-only exploration по `docs/`, `tasks/`, `decisions/`, `questions/`, `core/`, `portals/`, `sandbox/`;
- outbox-only reports для Lagrange, reviewer, researcher;
- stream-only variants для альтернативных решений;
- один Codex-интегратор для generated files и mainline-кода;
- generated files обновляет только main integrator;
- build-задачи с hot/shared files идут через claim/worktree/merge gate;
- не использовать `git add -A` в dirty shared tree;
- execute и внешний код только через sandbox policy и `docs/execute-sandbox-preflight.md`, без прямого запуска из отчета.

Типовые write scopes для параллельных агентов:

| Agent type | Allowed writes | Почему безопасно |
|---|---|---|
| Lagrange analyst | один новый файл в `queues/outbox/` | не конфликтует с кодом и индексами |
| Reviewer | один новый review-файл в `queues/outbox/` | независимая проверка без правок |
| Stream author | изолированный future stream folder | вариант сохраняется как ручей, mainline не трогается |
| Sandbox researcher | sandbox report или outbox summary | внешний код не смешивается с core |
| Codex integrator | claimed files по конкретной задаче | один интегратор отвечает за применение |

## 6. Example: three sequential loops

### Loop 1 - Lagrange analysis

Input:

- задача: найти, как централизовать информацию и активировать уже существующие советы;
- write scope: только этот outbox-файл;
- mode: read-only/outbox-only.

Lagrange делает:

1. Ищет документы про top layer, conveyor, portals, instruction assurance, synthesis, sandbox.
2. Выделяет unused advice: советы есть, но не являются стандартной кнопкой или check.
3. Делит предложения на `ratify/build` и `divergence/detail`.
4. Возвращает отчет с candidate tasks.

Codex после этого проверяет отчет и решает, что можно применить.

### Loop 2 - Codex implementation

Codex выбирает один consensus пункт, например:

- сделать read-only кнопку верхнего слоя для next actions;
- добавить тест;
- написать outbox-отчет;
- обновить generated files только после изменения source task/docs.

Safe implementation task:

```md
owner: codex
scope: selected source files only
verification_commands:
  - python -m py_compile selected files
  - python task-specific test
  - python tools/validate.py
  - python tools/instructions.py check-report report file
```

Если задача затрагивает shared generated files, Codex делает это один, после claim, и не смешивает с outbox-only работой Lagrange.

### Loop 3 - Lagrange review / next map

После реализации Codex дает Lagrange review-only задание:

```md
owner: lagrange
mode: outbox-only review
objective: проверить, стало ли проще агенту вершины пирамиды находить команды и применять советы
allowed_writes: one new review file in queues/outbox
verification_commands:
  - python tools/top.py buttons
  - python tools/top.py health
  - python tools/top.py advice codex --parallel --hot-files
expected_report: improvements, remaining unused advice, next build candidate, divergence list
```

Так цикл становится повторяемым: analysis -> implementation -> review -> next map.

## 7. Practical centralization backlog for Lagrange

### Quick read-only improvements

| Task | Goal | Files/folders | Verification | Risk | Expected result |
|---|---|---|---|---|---|
| Centralization map | Карта уже существующих команд верхнего слоя | read: `docs/`, `tools/`, `core/`, `portals/`; write: outbox only | report check | низкий | один файл с action map |
| Unused advice audit | Найти рекомендации без команды активации | read: `docs/friction-ledger.md`, `docs/friction-playbook.md`, `docs/top-layer-command-groups.md`, `docs/top-layer-throughput-methodology.md`, `queues/outbox/` | search + report check | низкий | список совет -> как активировать |
| D-Card/header gap scan | Найти файлы без понятной визитной карточки | read-only по documentation and tool files | `top.py health`, `assurance` | низкий | кандидаты для metadata cleanup |

### Top-layer automation

| Task | Goal | Files/folders | Verification | Risk | Expected result |
|---|---|---|---|---|---|
| Next-action button design | Спроектировать верхнюю read-only кнопку для следующих действий | outbox design only | report check | средний, если сразу писать код | спецификация перед build |
| Report intake recipe | Уточнить `read -> verify -> synthesize` для outbox | outbox/docs proposal | report check | низкий | единый шаблон intake |
| Conveyor refill rules | Улучшить правила target/refill/process | outbox proposal | `top.py conveyor --json` | низкий | рекомендации для будущего regulate |

### Indexes / metadata / navigation

| Task | Goal | Files/folders | Verification | Risk | Expected result |
|---|---|---|---|---|---|
| Navigation headers proposal | Формат file card для больших docs | outbox/stream proposal | report check | низкий | шаблон для doc headers |
| Portal command index | Свести команды по `portals/` и `core/` | outbox only | `top.py buttons`, `portal.py list` | низкий | короткий command catalog |
| Human quickstart map | Какие 5 команд запускать человеку | outbox/docs proposal | manual review | низкий | меньше ручной навигации |

### Synthesis and consensus/divergence

| Task | Goal | Files/folders | Verification | Risk | Expected result |
|---|---|---|---|---|---|
| Consensus candidates | Найти темы с 2+ похожими отчетами | outbox only | `doc_synthesis.py candidates` | низкий | список ratify/build |
| Divergence queue | Найти темы, где нужен отдельный stream | outbox/stream proposal | `top.py synthesize-docs` | средний | список спорных пунктов |
| Two-lane board review | Проверить, работает ли деление ratify vs divergence | outbox only | `top.py cauldron-lanes` | низкий | next actions по двум полосам |

### External code through sandbox

| Task | Goal | Files/folders | Verification | Risk | Expected result |
|---|---|---|---|---|---|
| Sandbox readiness map | Что уже есть для внешнего кода | read: `sandbox/`, `docs/external-code-sandbox.md`, `tools/sandbox.py`, `tools/sandbox_intake_demo.py`, `tools/sandbox_schema_validator.py` | report check | низкий | карта read-only intake |
| External source manifest guide | Уточнить минимальный manifest для новых источников | outbox/docs proposal | schema validator after implementation | средний | меньше хаоса во входных источниках |
| No-execute gate review | Проверить, где случайно может появиться execute | outbox review only | search for risky calls | низкий | список мест для будущего hardening |

## 8. How apex agents find commands faster

Чтобы агент на вершине пирамиды не читал всю историю, старт должен быть таким:

```powershell
python tools\top.py agent-start codex --context "centralization information workflow"
python tools\top.py buttons
python tools\top.py health
python tools\top.py advice codex --parallel --hot-files
python tools\top.py repo-search "centralization top layer conveyor synthesis" --limit 8
python tools\top.py conveyor --json
```

Если команда неизвестна:

1. Сначала `top.py buttons`.
2. Потом `top.py repo-search` по теме.
3. Потом `instructions.py preflight` для конкретного агента/задачи.
4. Потом только низкоуровневый инструмент.

Правило для документации: хороший совет считается активированным только если у него есть хотя бы один из трех путей:

- команда верхнего слоя (`top.py ...`);
- skill/playbook с коротким trigger;
- проверка/gate, которая поднимает этот совет перед ошибкой.

## 9. Parallel tasks with non-overlapping write scopes

Можно запускать одновременно:

| Parallel task | Agent | Write scope | Why non-conflicting |
|---|---|---|---|
| Centralization workflow review | Lagrange | one new review file in `queues/outbox/` | только отчет |
| Sandbox no-execute audit | reviewer | one new sandbox review file in `queues/outbox/` | только отчет |
| Portal navigation map | researcher | one new portal navigation file in `queues/outbox/` | только отчет |
| Divergence stream draft | synthesis-agent | future isolated stream folder | отдельный stream |
| Implementation of one accepted button | Codex | claimed source files, tests, report | один интегратор, не параллельно с другим build по тем же файлам |

Нельзя запускать одновременно без worktree:

- два build-агента по одному source file;
- агент, который меняет source tasks, и агент, который регенерирует derived indexes;
- sandbox execute и code integration;
- governance acceptance без человека.

## 10. Applied instructions

- AGENTS.md: результат оформлен в `queues/outbox/`, без удаления чужих сообщений и без утверждения final decisions.
- PROTOCOL.md: соблюден режим "один результат = один файл"; общие служебные и generated файлы не менялись.
- Low-conflict mode: не изменялись `TASKS.md`, `index.json`, `PIPELINE.md`, код, generated files и git history.
- Workflow/conveyor policy: отчет оформлен как повторяемый цикл, а не как одноразовый список идей.
- Top-layer methodology: главный bottleneck трактуется как `intake -> verify -> synthesize -> commit`, а не как число запускаемых агентов.

Checks:

- `python tools\instructions.py check-report queues\outbox\2026-06-24-lagrange-centralization-information-plan.md` -> rerun after cleanup.

Low-conflict note: `generate.py`, `pipeline.py snapshot`, code edits, generated-file edits and git commit were intentionally not run for this workflow-design artifact.

## 11. Recommended next handoff

Следующее безопасное задание для Lagrange:

```text
Прочитай этот workflow plan и сделай review-only outbox.

Проверь:
1. каких команд верхнего слоя не хватает;
2. какие рекомендации уже есть, но не активируются;
3. какие 3 задачи можно отдать разным агентам без конфликтов;
4. какой один build-шаг Codex должен сделать первым.

Не меняй код, TASKS.md, index.json, generated files и git.
```