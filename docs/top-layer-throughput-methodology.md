---
id: top-layer-throughput-methodology
type: doc
title: Методология верхнего слоя — обработка, проверка, синтез и commit результатов агентов
status: proposed
owner: codex
date: 2026-06-23
related: [agent-capacity-methodology, workflow-conveyor-policy, top-layer-command-groups, instruction-assurance, T-169]
---

# Методология верхнего слоя

Главный ограничитель системы с множеством агентов — не запуск новых исполнителей, а способность верхнего
слоя принять их результаты, проверить качество, синтезировать расхождения, принять допустимые решения и
безопасно внести изменения в канон. Поэтому верхний слой должен быть не большим ручным чатом, а
**control plane**: тонкой диспетчерской над задачами, конвейером, инструкциями, проверками, синтезом и commit.

## 1. Формула пропускной способности верхнего слоя

```text
реальная_ширина_флота <= min(
  intake_bandwidth,      # сколько output'ов можно принять и не потерять
  verification_bandwidth,# сколько результатов можно проверить
  synthesis_bandwidth,   # сколько вариантов можно свести без деградации смысла
  commit_bandwidth,      # сколько изменений можно безопасно закоммитить
  decision_bandwidth     # сколько спорных решений может утвердить человек/maintainer
)
```

Если увеличить число агентов выше этой границы, система не ускоряется: растёт очередь `landed`, появляются
непрочитанные outbox-файлы, дубли, устаревшие предпосылки, конфликтующие правки и формальные отчёты без
реального synthesis. Поэтому `conveyor.py target` должен регулироваться не желанием “запустить больше”, а
скоростью обработки верхним слоем.

## 2. Верхний слой как цикл управления

Верхний слой работает циклом:

```text
SENSE -> INTAKE -> TRIAGE -> VERIFY -> SYNTHESIZE -> DECIDE -> COMMIT -> FEEDBACK
```

| Стадия | Назначение | Основные инструменты | Выход |
|---|---|---|---|
| **SENSE** | понять состояние проекта | `top.py status`, `top.py conveyor --json`, `top.py health`, `top.py assurance` | snapshot состояния |
| **INTAKE** | принять результаты агентов | `conveyor.py land --output`, `queues/outbox/`, `queues/done/` | результат привязан к workflow/task |
| **TRIAGE** | классифицировать результат | `cohort.py self`, `top.py work-mode`, ручная классификация | read-only / docs / build / governance |
| **VERIFY** | проверить evidence и команды | `instructions.py check-report`, `validate.py`, `generate.py --check`, `merge_gate.py`, тесты | pass/fail/advisory |
| **SYNTHESIZE** | свести варианты и расхождения | `variants.py`, `synthesis_helper.py`, `doc_consensus.py`, conductor-agent | consensus / disagreements / recommendation |
| **DECIDE** | понять, что можно принять | `DECISIONS.md`, D-018 котёл, human approval | accepted/proposed/blocked |
| **COMMIT** | безопасно внести в git | `commit_lock.py`, `cohort.py ship`, selective-add, worktree+merge_gate | commit или отложенный пакет |
| **FEEDBACK** | создать новые задачи/вопросы | `next_id.py`, `pipeline.py`, `conveyor.py next/ship` | новые T/Q/D или shipped workflow |

## 3. Что автоматизировать в верхнем слое

### 3.1. Intake: не принимать “голый текст” без machine hook

Каждый результат агента должен иметь машинную привязку:

- `workflow_id` или `task_id`;
- путь к output: `queues/outbox/<date>-<topic>.md`, `reports/<name>.md`, `streams/<topic>/...`;
- applied/evidence-блок;
- список прочитанных файлов или scope;
- список проверок.

Минимальная команда:

```powershell
python tools\conveyor.py land <workflow-id> --output queues\outbox\<result>.md
```

Если output не указан, верхний слой должен считать результат незавершённым процессом, а не готовым знанием:
`PROCESS-MISSING-OUTPUT` блокирует новый fan-out до привязки или `dismiss --reason`.

### 3.2. Triage: классифицировать до проверки

Одинаковая проверка для всех результатов — ошибка. Сначала результат классифицируется:

| Класс | Что это | Верхний режим |
|---|---|---|
| `read-only-report` | анализ, обзор, карта, аудит | проверка evidence + synthesis |
| `variant` | альтернативное мнение/форк | не закрывать как дубль; сравнить через synthesis |
| `docs-change` | документация/методология | validate + links + applied instructions |
| `build-change` | код/тест/скрипт | work-mode, tests, merge_gate, commit_lock |
| `governance` | правила, accepted decisions, AGENTS/PROTOCOL | proposed-only, human approval |
| `external-code` | sandbox/intake/svend4 | read-only sandbox, no execute без preflight |

Эта классификация должна появиться в будущем `tools/top.py process-landed` или отдельном
`tools/result_intake.py`.

### 3.3. Verify: evidence перед мнением

Порядок проверки результата:

```powershell
python tools\instructions.py check-report queues\outbox\<result>.md
python tools\validate.py
python tools\generate.py --check
python tools\top.py assurance all
```

Для build:

```powershell
python tools\top.py work-mode codex <T-id> --parallel --hot-files
python tools\merge_gate.py check codex
# затем task-specific tests
```

Для docs/synthesis:

```powershell
python tools\repo-search.py "<topic>" --limit 5
python tools\synthesis_helper.py report <topic> --out topics\<topic>-synthesis.md
```

Проверка должна отвечать не “мне нравится”, а:

- есть ли applied instructions;
- существуют ли указанные файлы;
- не устарели ли generated indexes;
- не затронуты ли чужие half-done изменения;
- не требует ли изменение human approval;
- есть ли тест/валидатор для изменённой поверхности.

### 3.4. Synthesize: не путать дубли и варианты

Если два агента пишут на одну тему, это не обязательно дубль. Верхний слой должен различать:

- **duplicate noise:** повторяет уже принятое без новой информации;
- **independent confirmation:** та же рекомендация с новой доказательной базой;
- **variant:** альтернативное решение;
- **conflict:** несовместимое утверждение;
- **complement:** закрывает другую часть той же темы.

Метод synthesis:

```text
1. Собрать все outputs по topic/workflow/task.
2. Выписать совпадающие пункты как consensus.
3. Выписать расхождения как disagreements.
4. У каждого расхождения потребовать evidence: файл, команда, тест, риск.
5. Что доказано и low-risk -> принять.
6. Что спорно/governance -> Q/D proposed или human approval.
7. Что недоделано -> T-id с owner: pool.
```

Это именно работа верхнего слоя: нижние агенты производят варианты, верхний слой не даёт им потеряться или
слиться в случайный текст.

### 3.5. Commit: серийная точка должна быть короткой

Commit нельзя превращать в долгий ручной процесс. Верхний слой должен заранее подготовить всё до момента
захвата lock:

```text
до lock: прочитать, проверить, синтезировать, выбрать файлы, сформулировать message
lock: acquire -> explicit git add <files> -> commit -> release
после lock: conveyor ship, outbox/done marker, status
```

Правила:

- не использовать `git add -A` в dirty shared tree;
- не коммитить runtime-шум (`logs/`, `LIVE.md`, временные файлы);
- generated files (`TASKS.md`, `index.json`) добавлять только вместе с источником (`tasks/T-*.md`);
- если hot/shared files или чужая работа — Level 1 worktree + `merge_gate.py`;
- если governance — не переводить `accepted` без человека.

## 4. Инструкции и skills для верхнего слоя

### Уже существующие project skills

| Skill | Что даёт верхнему слою |
|---|---|
| `pipeline-operator` | дисциплина claim/done/generate/validate для задач |
| `repo-review` | периодическая ревизия, дрейф, плюсы/минусы, рекомендации |
| `repo-friction-playbook` | быстрые рецепты повторяющихся проблем Windows/git/runtime |
| `driver-acceptance` | строгая приёмка драйверов и MCP-tools |

### Новый project skill

Добавлен `skills/top-layer-orchestrator/SKILL.md`. Его роль — короткий процедурный цикл для агента,
который находится на вершине пирамиды и должен обрабатывать поток результатов, а не просто писать новые
ответы.

### Когда нужен будущий plugin/MCP

Project skill достаточно, пока верхний слой выполняется агентом в этом репозитории. Plugin/MCP нужен позже,
когда появляются требования:

- запускать одинаковый верхний слой в нескольких проектах;
- иметь UI-кнопки поверх `top.py buttons --json`;
- принимать webhook/event от завершившегося workflow;
- автоматически читать `landed` outputs и предлагать action plan;
- интегрироваться с GitHub PR/issues или внешним сервером-оркестратором.

До этого plugin преждевременен: дешевле развивать `tools/top.py`, `tools/conveyor.py`, project skills и
машинные отчёты.

## 5. Скрипты верхнего слоя: текущие и будущие

### Текущие рабочие команды

```powershell
python tools\top.py buttons
python tools\top.py status codex
python tools\top.py health
python tools\top.py assurance all --json
python tools\top.py instruction-preflight codex <T-id>
python tools\top.py conveyor --json
python tools\top.py work-mode codex <T-id> --parallel --hot-files
python tools\top.py subagent-handoff <agent> <T-id> "<label>" --worktree --json
python tools\conveyor.py plan 9
python tools\conveyor.py target 4
python tools\conveyor.py land <workflow-id> --output queues\outbox\<result>.md
python tools\conveyor.py ship <workflow-id>
```

### Следующие автоматизации

| Будущий инструмент | Назначение | Почему не делать слишком рано |
|---|---|---|
| `tools/result_intake.py` | классифицировать outbox/landed result | сначала стабилизировать форматы result |
| `tools/top.py process-landed` | взять первый landed output и напечатать verify/synthesis plan | реализовано в T-170 как read-only advisory; дальнейший шаг — больше классификации после ручных циклов |
| `tools/conveyor.py regulate` | advisory target +1/0/-1 / process-first | реализовано T-179 как read-only; следующий шаг — накопить метрики throughput |
| `tools/synthesis_gate.py` [planned] | проверять consensus/disagreement структуру | сначала закрепить шаблон synthesis |
| `tools/commit_batch.py` [planned] | подготовить selective-add batch под commit_lock | опасно без точного ownership classifier |
| `dashboard/app` или ChatGPT App | UI-кнопки для людей | имеет смысл после стабильного CLI contract |

## 6. Метрики верхнего слоя

Чтобы понять, можно ли увеличивать флот, верхний слой должен смотреть не на число агентов, а на метрики:

| Метрика | Хорошо | Плохо |
|---|---|---|
| `landed_waiting` | 0 или быстро разбирается | растёт после каждого цикла |
| `missing_output` | 0 | есть landed без output-ref |
| `verify_fail_rate` | редкие advisory | отчёты без evidence, stale indexes |
| `synthesis_ratio` | 3-9 results -> 1 clear synthesis | много outputs без итогового consensus |
| `commit_wait_time` | lock короткий | долгие lock/повторы/index.lock |
| `rework_rate` | мало переделок | частые исправления одних и тех же ошибок |
| `human_blockers` | только governance | человек нужен для каждого мелкого шага |

Правило масштабирования:

```text
если landed_waiting=0, missing_output=0, validate OK и synthesis_ratio нормальный:
    target можно поднять на 1-2
если PROCESS или missing_output:
    не запускать новых агентов, сначала process-landed
если verify_fail_rate растёт:
    улучшить preflight/check-report/skill, а не запускать больше workers
если commit_wait_time растёт:
    уменьшить build target, перейти в worktree или batch commits
```

## 7. Роли верхнего слоя

| Роль | Кто может выполнять | Что делает |
|---|---|---|
| **Chief/orchestrator** | Codex или человек | держит состояние, выбирает target, принимает safe commit |
| **Conductor** | Lagrange/Mavis/worker-agent | сводит 2-4 worker outputs в synthesis |
| **Reviewer** | reviewer-agent или Codex | проверяет риски, evidence, противоречия |
| **Committer** | один назначенный агент | берёт lock и делает selective commit |
| **Human approver** | Stefan/maintainer | governance, accepted decisions, execute/network/high-risk |

Одна ошибка, которую нужно избегать: не давать всем агентам одновременно быть committer'ами. Много агентов
могут думать, читать и писать outbox; commit в mainline должен быть короткой управляемой стадией.

## 8. Минимальный рабочий протокол на сейчас

Для каждого нового результата:

```text
1. top.py conveyor --json
2. если landed есть: найти output path
3. instructions.py check-report <output>
4. классифицировать: report / variant / docs / build / governance
5. если несколько outputs по теме: synthesis_helper или conductor-agent
6. validate/generate --check/assurance
7. если изменения safe: commit_lock + selective-add + commit
8. conveyor ship <workflow-id>
9. если есть новые долги: next_id.py task/question + generate + validate
```

Для текущей стадии проекта самый полезный следующий шаг — не повышать target, а несколько раз провести этот
протокол вручную и только потом автоматизировать `process-landed`.

## 9. Моё мнение

Верхний слой должен развиваться как **операционная система процесса**, а не как ещё один большой агент.
Агент может быть умным, но без внешнего состояния он теряет очередь, забывает, что уже landed, смешивает
варианты с дублями и коммитит слишком широко. Поэтому лучшие инвестиции сейчас:

1. machine-readable result contracts;
2. `land --output` и запрет missing-output;
3. instruction/evidence gate;
4. synthesis-шаблон consensus/disagreement;
5. короткий commit-lock batch;
6. project skill для повторения этого цикла;
7. `process-landed` как полуавтоматическая read-only кнопка верхнего слоя; позже — классификатор result_intake.

Так верхний слой сможет масштабировать агентов не “по надежде”, а по реальной способности превращать их
результаты в проверяемый канон.