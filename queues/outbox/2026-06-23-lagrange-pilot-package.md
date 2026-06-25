---
status: historical
---
# Lagrange: pilot package for nested agents

- Дата: 2026-06-23
- Автор: Lagrange через codex
- Тип: answer / proposed pilot package
- Адресовано: Stefan, all agents
- Связанные файлы: `AGENTS.md`, `PROTOCOL.md`, `templates/`, `docs/`, `queues/outbox/`, `tools/top.py`, `tools/flow.py`, `tools/cohort.py`, `tools/pipeline.py`, `tools/instructions.py`, `tools/merge_gate.py`

## Цель пилота

Проверить минимальную reduce-иерархию:

```text
3 workers -> 1 conductor -> 1 chief -> human decision
```

Пилот должен доказать, что вложенность ускоряет анализ/подготовку работы, не создаёт лишнюю бюрократию и не ломает текущий repo flow.

## 1. Минимальный pilot

Состав:

- **Chief**: главный агент или человек, который выбирает тему, создаёт задачи и принимает итог.
- **Conductor**: координатор запуска 3 workers, собирает их результаты, пишет synthesis.
- **Worker A/B/C**: независимые sub-agent'ы, каждый получает маленький handoff и пишет отдельный result.

Пример темы пилота: проверить, как связать sub-agent handoff с текущими tools.

### Шаги

1. Chief создаёт одну pipeline-задачу на пилот.
2. Conductor готовит 3 handoff-файла: по одному на worker.
3. Каждый worker работает read-only и пишет result в `queues/outbox/`.
4. Conductor читает 3 result-файла и пишет synthesis-result.
5. Chief решает, какие документы, шаблоны и задачи реально добавлять.
6. Если нужны правки, они идут отдельными задачами через обычный `pipeline.py`/`flow.py`.

### Команды

Ориентация:

```powershell
python tools\top.py agent-start codex --context "subagent orchestration pilot"
python tools\pipeline.py status
python tools\cohort.py board
```

Взять pilot-задачу:

```powershell
python tools\top.py take codex T-XXX
```

Проверить режим:

```powershell
python tools\top.py work-mode codex T-XXX --parallel
python tools\cohort.py guard --json
```

Для read-only workers worktree не нужен. Для writer-worker:

```powershell
python tools\flow.py start lagrange T-XXX --worktree --run
```

Проверить результат:

```powershell
python tools\instructions.py check-report queues\outbox\<worker-result>.md
python tools\merge_gate.py check codex
python tools\top.py health
```

Закрыть задачу:

```powershell
python tools\pipeline.py done codex T-XXX --report "nested-agent pilot completed" --applied "AGENTS.md, PROTOCOL.md, docs/workflow-orchestration-policy.md"
```

Примечание: в текущем repo фактический инструмент называется `pipeline.py`; если где-то используется слово `conveyor`, его лучше трактовать как “конвейер задач”, не как отдельный файл.

## 2. Первые файлы

Обязательно для пилота:

```text
templates/subagent-handoff.json
templates/subagent-result.md
docs/subagent-orchestration.md
```

Желательно, но можно после первого пилота:

```text
queues/handoff/README.md
queues/handoff/<run-id>-<worker>.json
```

Пока рано:

```text
tools/subagent_orchestrator.py
tools/top.py subagent-handoff
AGENTS.md registration for many new agents
automatic launching of platform sub-agents
```

Причина: сначала нужно проверить контракт вручную. Автоматизировать стоит только после 2-3 повторов.

## 3. JSON schema v1

### Handoff v1

Обязательные поля:

```json
{
  "schema": "subagent-handoff/v1",
  "run_id": "string",
  "task_id": "string",
  "agent_id": "string",
  "role": "worker|integrator|conductor",
  "mode": "read-only|shared-tree-write|worktree-write",
  "objective": "string",
  "allowed_reads": ["string"],
  "allowed_writes": ["string"],
  "inputs": ["string"],
  "expected_outputs": ["string"],
  "required_checks": ["string"],
  "approval_required_for": ["string"]
}
```

Рекомендуемые поля:

```json
{
  "parent_run_id": "string|null",
  "reduction_group": "pilot-001/group-a",
  "worktree_path": "string|null",
  "branch": "string|null",
  "deadline": "string|null",
  "result_format": "markdown+frontmatter",
  "denied_paths": ["AGENTS.md", "PROTOCOL.md"],
  "notes": "string"
}
```

Пример:

```json
{
  "schema": "subagent-handoff/v1",
  "run_id": "2026-06-23-pilot-worker-a",
  "task_id": "T-XXX",
  "agent_id": "lagrange",
  "role": "worker",
  "mode": "read-only",
  "objective": "Audit current docs for sub-agent handoff gaps.",
  "allowed_reads": ["AGENTS.md", "PROTOCOL.md", "docs/", "tools/top.py", "tools/flow.py"],
  "allowed_writes": ["queues/outbox/"],
  "inputs": ["docs/workflow-orchestration-policy.md", "docs/top-layer-command-groups.md"],
  "expected_outputs": ["queues/outbox/2026-06-23-pilot-worker-a.md"],
  "required_checks": ["list files read", "mark proposals as proposed", "do not edit files"],
  "approval_required_for": ["editing AGENTS.md", "accepted decisions", "merge", "network"],
  "worktree_path": null,
  "branch": null
}
```

### Result v1

Worker result must include machine-readable metadata plus human-readable analysis.

Required front matter:

```yaml
schema: subagent-result/v1
run_id: string
task_id: string
agent_id: string
role: worker
status: done|partial|blocked|failed
mode: read-only|shared-tree-write|worktree-write
```

Required sections:

```md
## Summary
## Scope
## Findings
## Proposed Changes
## Risks
## Checks
## Open Questions
```

Optional JSON sidecar shape for later automation:

```json
{
  "schema": "subagent-result/v1",
  "run_id": "2026-06-23-pilot-worker-a",
  "task_id": "T-XXX",
  "agent_id": "lagrange",
  "role": "worker",
  "status": "done",
  "summary": "string",
  "files_read": ["string"],
  "files_changed": [],
  "findings": [
    {
      "id": "F-1",
      "severity": "low|medium|high",
      "title": "string",
      "evidence": ["string"],
      "recommendation": "string"
    }
  ],
  "proposed_changes": ["string"],
  "risks": ["string"],
  "checks_run": ["string"],
  "needs_approval": ["string"],
  "open_questions": ["string"]
}
```

## 4. Безопасная регистрация Lagrange

Сначала Lagrange используется как temporary worker через handoff. Постоянным агентом он становится только после успешного пилота.

Запись в `AGENTS.md` должна быть примерно такой по смыслу:

```md
| lagrange | AI assistant | worker/reviewer for sub-agent handoff, analysis, reports, consistency checks | `queues/outbox/`, `reports/`, assigned `docs/`, assigned worktree paths | не удалять чужие сообщения; решения только `proposed`; `accepted`, AGENTS/PROTOCOL changes, merge, network/execute только после human approval |
```

Может сразу после регистрации:

- брать назначенные задачи через `pipeline.py`;
- писать отчёты в `queues/outbox/`;
- писать reports;
- работать в явно выданном worktree;
- предлагать документы, задачи, вопросы и решения.

Только proposed:

- новые решения;
- изменения governance;
- архитектурные варианты;
- рекомендации по tool changes.

Только после human approval:

- изменение `AGENTS.md`, `PROTOCOL.md`;
- перевод decision в `accepted`;
- merge в mainline;
- network/execute;
- доступ к внешним источникам, секретам, персональным данным.

## 5. Связь с текущими tools

`top.py` используется как входная панель: onboarding, status, health, work-mode. Позже можно добавить `subagent-handoff --json`, но не в первом пилоте.

`flow.py` используется только для writer-workers: создаёт worktree и завершает merge flow. Не должен запускать platform sub-agent.

`cohort.py` используется для board/plan/guard. `cohort.py plan --json` может стать источником списка worker assignments.

`pipeline.py` остаётся источником task claim/done. Pilot-задача должна быть обычной задачей pipeline.

`instructions.py check-report` проверяет, что result содержит evidence применённых инструкций. Для пилота это лёгкий gate качества.

`merge_gate.py` используется перед merge writer-worktree или перед закрытием implementation-задачи. Для read-only worker results достаточно `check-report` + review conductor.

## 6. Метрики успеха

Пилот успешен, если:

- 3 workers вернули результаты в отдельных файлах;
- conductor смог сделать synthesis без дополнительного чата;
- каждый result указал scope, files read, risks, proposed changes;
- не было правок вне разрешённых зон;
- не было конфликтов в shared tree;
- chief получил actionable next tasks;
- общий цикл занял меньше времени или дал более широкое покрытие, чем один агент.

Метрики:

```text
worker_count = 3
result_files_created = 3
synthesis_created = 1
files_changed_by_workers = 0 for read-only pilot
unresolved_conflicts = 0
human_questions_created <= 3
actionable_tasks_created >= 3
duplicate_findings_ratio < 50%
time_to_synthesis acceptable vs solo baseline
```

Признак бюрократии:

- handoff длиннее самой задачи;
- worker results повторяют друг друга;
- conductor тратит больше времени на формат, чем на synthesis;
- нет новых actionable findings;
- появляются папки/шаблоны, которыми никто не пользуется повторно.

## 7. Первые 3 pipeline-задачи

### Task 1: Sub-agent templates v1

Создать минимальные шаблоны:

```text
templates/subagent-handoff.json
templates/subagent-result.md
```

Acceptance:

- шаблоны содержат обязательные поля v1;
- пример read-only worker;
- пример worktree writer;
- result template содержит sections для checks/risks/open questions.

### Task 2: Sub-agent orchestration doc

Создать:

```text
docs/subagent-orchestration.md
```

Acceptance:

- описана граница repo flow vs external orchestrator;
- описан pilot 3 workers -> conductor -> chief;
- указана связь с `top.py`, `flow.py`, `cohort.py`, `pipeline.py`, `merge_gate.py`;
- указано, что repo tools не запускают platform sub-agents.

### Task 3: Handoff queue convention

Создать или обновить:

```text
queues/handoff/README.md
```

Acceptance:

- описано, когда handoff хранить в `queues/handoff/`, а когда достаточно `queues/inbox/`;
- naming convention: DATE-TASK-AGENT-HANDOFF-JSON;
- result convention: queue outbox file named DATE-TASK-AGENT-RESULT-MD;
- lifecycle: prepared -> launched externally -> result received -> synthesized -> archived/done.

## Итог

Первый пилот должен быть read-only. Его задача не “автоматически запустить армию агентов”, а проверить контракт: можно ли дать 3 независимым исполнителям маленькие handoff-пакеты, получить структурированные результаты и свести их без потери контекста. Только после этого стоит добавлять команды в `top.py` и регистрировать Lagrange как постоянного агента.

## Applied instructions

- `AGENTS.md`: Lagrange не менял файлы напрямую; codex сохранил ответ как outbox-материал без регистрации нового постоянного агента.
- `PROTOCOL.md`: один результат = один файл в `queues/outbox/`, история обсуждения не переписана.
- Checks: python tools/top.py health -> OK before this outbox addition.