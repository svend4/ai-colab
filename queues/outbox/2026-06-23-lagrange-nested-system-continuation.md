# Lagrange: practical nested agent architecture

- Дата: 2026-06-23
- Автор: Lagrange через codex
- Тип: answer / proposed architecture note
- Адресовано: Stefan, all agents
- Связанные файлы: `AGENTS.md`, `PROTOCOL.md`, `tools/flow.py`, `tools/cohort.py`, `tools/conveyor.py`, `queues/outbox/`

## 1. Reduce-иерархия 3:1

Базовая схема:

```text
workers -> integrators -> conductor -> chief -> human approval
```

Пример 3:1:

```text
9 worker sub-agents
  -> 3 integrators
    -> 1 conductor
      -> chief / главный агент
        -> человек утверждает спорное
```

**Worker** делает узкую задачу: читает область, проверяет гипотезу, пишет патч в worktree или готовит report.

**Integrator** принимает 2-4 worker-результата, сводит их в один synthesis: что совпало, что спорно, что можно принять, что требует решения.

**Conductor** принимает 2-4 integrator-сводки и строит общий план/итог: порядок merge, риски, unresolved questions.

**Chief** держит связь с человеком и каноном репозитория: не делает вид, что утвердил решение, если нужно human approval.

Правило: worker не переписывает итог, integrator не скрывает разногласия, conductor не принимает governance-решения без человека.

## 2. Файлы и папки

Использовать уже существующий контур:

```text
AGENTS.md                 # реестр агентов и прав
PROTOCOL.md               # правила совместной работы
tasks/                    # канонические задачи
queues/inbox/             # входящие задания / handoff-запросы
queues/claimed/           # claims / занятость
queues/outbox/            # результаты агентов и sub-agent'ов
queues/done/              # выполненные задачи
queues/failed/            # провалы / blocked
docs/                     # чистовая документация
reports/                  # отчёты анализа
topics/                     # полилог, обсуждения, synthesis
streams/                  # fork-варианты до принятия
logs/                     # runtime-снимки, не как источник решения
```

Минимально добавить позже, если поток станет регулярным:

```text
queues/handoff/           # JSON/MD handoff manifests для внешнего orchestrator
templates/subagent-result.md
templates/subagent-handoff.json
docs/subagent-orchestration.md
```

На первом этапе можно не плодить папки: handoff класть в `queues/inbox/`, результат в `queues/outbox/`.

## 3. Handoff manifest

Handoff — это контракт между repo flow и внешним orchestrator. Репозиторий готовит задачу и рабочее место, но platform sub-agent запускается снаружи.

Пример JSON:

```json
{
  "schema": "subagent-handoff/v1",
  "run_id": "2026-06-23-T-161-lagrange-audit",
  "agent_id": "lagrange",
  "role": "worker",
  "task_id": "T-161",
  "task_title": "Audit orchestration docs",
  "mode": "read-only",
  "worktree_path": null,
  "branch": null,
  "allowed_reads": ["AGENTS.md", "PROTOCOL.md", "docs/", "tools/"],
  "allowed_writes": ["queues/outbox/", "reports/"],
  "must_not_touch": ["DECISIONS.md accepted statuses", "other agents' messages"],
  "inputs": [
    "docs/workflow-orchestration-policy.md",
    "docs/parallel-work-policy.md"
  ],
  "expected_output": "queues/outbox/2026-06-23-lagrange-orchestration-audit.md",
  "required_checks": [
    "cite files read",
    "list risks",
    "mark proposals as proposed"
  ],
  "approval_required_for": [
    "editing AGENTS.md",
    "accepted decisions",
    "merge to master",
    "network or external execution"
  ]
}
```

Для build-задачи:

```json
{
  "mode": "worktree-write",
  "worktree_path": "C:/Users/stefan/Documents/New project ai colab-wt-lagrange-T-161",
  "branch": "agent/lagrange/T-161",
  "allowed_writes": ["tools/specific_file.py", "tools/test_specific_file.py", "queues/outbox/"]
}
```

## 4. Контракт результата sub-agent

Markdown-результат должен быть коротким, структурированным и пригодным для synthesis.

```md
---
schema: subagent-result/v1
run_id: 2026-06-23-T-161-lagrange-audit
agent_id: lagrange
role: worker
task_id: T-161
status: done
mode: read-only
created: 2026-06-23
---

# Sub-agent result: Lagrange / T-161

## Summary

Краткий итог в 5-10 строк.

## Scope

Что было прочитано:

- `AGENTS.md`
- `PROTOCOL.md`
- `docs/workflow-orchestration-policy.md`

Что не проверялось:

- внешние сервисы
- network
- незарегистрированные источники

## Findings

| ID | Severity | Finding | Evidence | Recommendation |
|---|---|---|---|---|
| F-1 | medium | Нет handoff manifest | `docs/...` | Добавить шаблон v1 |

## Proposed Changes

- [ ] Добавить `docs/subagent-orchestration.md`
- [ ] Добавить `templates/subagent-result.md`
- [ ] Добавить `top.py subagent-handoff --json`

## Risks

- Риск смешать repo orchestration и platform launch.
- Риск, что sub-agent будет писать в общий tree без worktree.

## Checks

- Read-only: yes
- Files changed: none
- Human approval needed: yes, for AGENTS.md registration

## Open Questions

- Нужно ли Lagrange регистрировать как постоянного агента?
- Кто является merge-owner для worker worktree?
```

Integrator-результат похож, но вместо findings по файлам содержит reduce:

```md
## Inputs

- worker A result
- worker B result
- worker C result

## Consensus

Что совпало у всех.

## Divergences

Где worker'ы расходятся.

## Integrator Recommendation

Что принять, что отложить, что отдать человеку.
```

## 5. Роль Lagrange

Пока Lagrange не зарегистрирован в `AGENTS.md`, он считается временным sub-agent.

Может сразу:

- читать публичный канон репозитория;
- делать read-only анализ;
- писать результат в заранее указанный `queues/outbox/...`;
- предлагать задачи, вопросы, proposed-решения;
- работать в отдельном worktree, если handoff явно дал путь и зону записи.

Требует регистрации в `AGENTS.md`:

- регулярная роль в проекте;
- право брать задачи через `pipeline.py`;
- право писать в `docs/`, `tasks/`, `tools/`, `code/`;
- право участвовать как integrator/conductor, а не только worker.

Требует human approval:

- изменение `AGENTS.md`, `PROTOCOL.md`;
- перевод решений в `accepted`;
- merge worktree в mainline;
- запуск внешнего network/execute;
- доступ к секретам, персональным данным, внешним репозиториям;
- удаление или переписывание чужих сообщений.

Формула роли:

```text
Lagrange = временный worker/reviewer по handoff,
пока человек не зарегистрировал его как постоянного агента.
```

## 6. Команды PowerShell

Ориентация:

```powershell
python tools\top.py buttons
python tools\top.py status codex
python tools\top.py agent-start codex --context "subagent orchestration"
python tools\pipeline.py status
```

Раздача задач:

```powershell
python tools\cohort.py board
python tools\cohort.py plan 3 --json
python tools\top.py take codex T-161
```

Выбор режима:

```powershell
python tools\top.py work-mode lagrange T-161
python tools\top.py work-mode lagrange T-161 --parallel --hot-files
python tools\cohort.py guard --json
```

Создание worktree для worker:

```powershell
python tools\flow.py start lagrange T-161 --worktree
python tools\flow.py start lagrange T-161 --worktree --run
```

После внешнего запуска sub-agent человек/orchestrator передаёт ему:

```text
cwd = <worktree_path или repo root>
task = T-161
read = handoff manifest
write result = queues/outbox/<file>.md
```

Проверки:

```powershell
python tools\validate.py
python tools\generate.py --check
python tools\top.py health
python tools\merge_gate.py check lagrange
```

Завершение задачи:

```powershell
python tools\pipeline.py done lagrange T-161 --report "subagent report written" --applied "AGENTS.md, PROTOCOL.md, handoff manifest"
```

Merge worktree:

```powershell
python tools\flow.py finish lagrange T-161 --worktree
python tools\flow.py finish lagrange T-161 --worktree --run
```

Для shared-tree commit лучше не использовать широкий `git add -A`. Использовать только явные файлы или repo wrapper:

```powershell
python tools\cohort.py ship lagrange queues\outbox\2026-06-23-lagrange-result.md --message "T-161: add Lagrange result" --run
```

## 7. Риски и контроль

| Риск | Контроль |
|---|---|
| Sub-agent пишет не туда | `allowed_writes` в handoff + `AGENTS.md` |
| Все правят один файл | `cohort.py guard`, worktree, one-message-one-file |
| Потеря выводов worker'ов | каждый worker пишет отдельный outbox result |
| Integrator скрывает расхождения | обязательные секции `Consensus` и `Divergences` |
| Repo tools начинают запускать platform agents | жёсткая граница: repo готовит handoff, external orchestrator запускает |
| Слишком много бюрократии | начинать с одного JSON handoff и одного Markdown result |
| Автомат принял решение | только `proposed`; `accepted` делает человек |
| Грязный mainline блокирует всех | Level 1 worktree по D-022 |
| Невоспроизводимые отчёты | result должен перечислять inputs, scope, checks |
| Старые claims/worktrees висят | `pipeline.py status`, `worktree.py list`, ручная cleanup-процедура |

## 8. План внедрения

1. Не менять архитектуру сразу. Сначала провести один ручной pilot.
2. Выбрать одну задачу `T-XXX`, которую можно разделить на 3 worker-подзадачи.
3. Создать handoff manifest для каждого worker.
4. Запустить 3 read-only sub-agent'а через внешний orchestrator.
5. Сложить результаты в `queues/outbox/`.
6. Один integrator делает synthesis по трём результатам.
7. Conductor/chief решает: какие изменения нужны, какие вопросы человеку.
8. Только после этого создавать tasks/decisions/docs changes.
9. Если нужны правки кода, повторить цикл уже через worktree.
10. После 2-3 успешных циклов добавить `templates/subagent-handoff.json` и `templates/subagent-result.md`.
11. После повторяемости добавить команду `top.py subagent-handoff --json`.
12. Только затем регистрировать Lagrange в `AGENTS.md`, если он стал постоянным участником.

Главный принцип: вложенность нужна не ради иерархии, а ради controlled reduction. Много worker'ов создают широту, integrator уменьшает шум, conductor связывает части, chief держит ответственность перед человеком и каноном проекта.

## Applied instructions

- `AGENTS.md`: Lagrange не менял файлы напрямую; codex сохранил ответ как outbox-материал без регистрации нового постоянного агента.
- `PROTOCOL.md`: один результат = один файл в `queues/outbox/`, история обсуждения не переписана.
- Checks: python tools/top.py health -> OK before this outbox addition.