---
id: closed-loop-agent-cauldron-conveyor
type: doc
title: "Замкнутый контур: стратегический агент, субагенты, workflow, synthesis, котёл и новые задачи"
status: proposed
date: 2026-07-06
author: codex
related:
  - D-017
  - D-018
  - D-035
  - T-273
  - T-274
  - T-275
  - T-276
  - workflow-orchestration-policy
  - workflow-conveyor-policy
  - agent-launch-workflow
---

# Замкнутый контур: стратегический агент, субагенты, workflow, synthesis, котёл и новые задачи

## 1. Короткая формула

1.1. Нужен не просто котёл задач и не просто запуск субагентов, а замкнутый управляемый цикл:

```text
стратегический вопрос
  -> формулировка задания
  -> согласование с человеком/агентами
  -> fan-out субагентов/workflow
  -> возврат результатов
  -> проверка и synthesis
  -> котёл: consensus / divergence / ratify-build / detail
  -> новые задачи / решения / worktree-build
  -> следующий цикл
```

1.2. Смысл: ведущие агенты не должны тонуть в мелкой ручной работе. Они должны держать стратегию, задавать вопросы человеку, формулировать задания, запускать исполнителей, проверять результаты и превращать их в следующий рабочий поток.

1.3. Субагенты не должны принимать стратегические решения сами. Они дают варианты, проверки, разведку, кодовые черновики, отчёты и доказательную базу.

1.4. Человек не должен читать сырой шум от всех исполнителей. Человек должен видеть сжатую карту: что согласовано, что спорно, что готово к ратификации, что нужно детализировать, что можно строить.

## 2. Что уже есть в проекте

2.1. Уже есть workflow-policy:

- `docs/workflow-orchestration-policy.md`;
- `docs/workflow-conveyor-policy.md`;
- `docs/agent-launch-workflow.md`;
- `docs/parallel-work-policy.md`.

2.2. Уже есть верхние команды:

```powershell
python tools\top.py cycle <agent>
python tools\top.py status [agent]
python tools\top.py advice <agent> [T-id]
python tools\top.py work-mode <agent> <task>
python tools\top.py take <agent> [T-id]
python tools\top.py subagent-handoff <agent> <task> [context...] [--worktree] [--json]
python tools\top.py conveyor [--target N] [--idle M] [--json]
python tools\top.py conveyor-recover [--json] [--limit N]
python tools\top.py process-landed [--json] [--all] [--topic TOPIC]
python tools\top.py synthesize-docs [topic] [--json] [--out docs/<name>.md]
python tools\top.py cauldron-lanes [topic] [--json] [--out docs/<name>.md]
```

2.3. Уже есть инструменты вариантов и синтеза:

```powershell
python tools\top.py variant-start <agent> <topic...> [--task T-id]
python tools\top.py variant-batch <topic...> --agents a,b,c [--task T-id]
python tools\stream.py create <topic> <agent> <reason>
python tools\stream.py mark <stream-id> ready-for-synthesis <note>
python tools\doc_synthesis.py candidates <topic>
python tools\doc_synthesis.py scan <topic> [files...] [--out OUT] [--json]
python tools\synthesis_helper.py report <topic> [--out PATH]
python tools\two_track.py board [--json]
python tools\two_track.py --track ratify [--json]
python tools\two_track.py --track detail [--json]
```

2.4. Уже есть pipeline/kotel:

```powershell
python tools\pipeline.py status
python tools\pipeline.py next <agent>
python tools\pipeline.py claim <agent> <T-id>
python tools\pipeline.py done <agent> <T-id> --claim <claim-id> --applied "..."
python tools\pipeline.py fail <agent> <T-id> --claim <claim-id> --reason "..."
python tools\pipeline.py snapshot
```

2.5. Уже есть правила:

- D-017: варианты не стирать;
- D-018: спорное через котёл;
- D-022: параллельная работа через worktree/streams;
- D-031: commit queue;
- D-035: котёл-день и пакетная ратификация.

2.6. Главный gap: все элементы есть, но нет одного обязательного runbook, который связывает их в непрерывную петлю и говорит, когда результат workflow становится задачей, решением, новым workflow или archived note.

## 3. Архитектура ролей

3.1. Human / Stefan.

3.1.1. Утверждает спорные решения.

3.1.2. Выбирает стратегические приоритеты, если агенты расходятся.

3.1.3. Пакетно отвечает на котёл-день по D-035.

3.2. Strategic agent / lead-agent.

3.2.1. Формулирует цель.

3.2.2. Делит работу на независимые кластеры.

3.2.3. Запускает субагентов или готовит handoff.

3.2.4. Не делает всю работу сам, если задача декомпозируется.

3.2.5. Проверяет результаты и несёт ответственность за интеграцию.

3.3. Coordinator.

3.3.1. Следит за conveyor: in-flight, landed, parked, shipped.

3.3.2. Не даёт конвейеру осушаться до нуля.

3.3.3. Не запускает больше, чем верхний слой может обработать.

3.4. Worker subagent.

3.4.1. Делает узкую задачу.

3.4.2. Пишет результат в выделенную зону или возвращает structured report.

3.4.3. Не принимает accepted decisions.

3.4.4. Не коммитит напрямую в общий канон, если это не было явно разрешено.

3.5. Verifier.

3.5.1. Ищет ошибки, ложные предположения, пропущенные файлы, несуществующие команды.

3.5.2. Работает read-only, если возможно.

3.6. Synthesizer.

3.6.1. Делит входы на consensus, near-consensus, divergence, uncertainty.

3.6.2. Не стирает разногласия.

3.6.3. Готовит материал для котла и человека.

3.7. Scribe.

3.7.1. Записывает итоговые решения, задачи и отчёты.

3.7.2. Обновляет индексы через генераторы, а не вручную.

3.8. Gatekeeper / integrator.

3.8.1. Проверяет validate, generate, hygiene, merge-gate.

3.8.2. Делает selective add/commit.

3.8.3. Не включает чужую half-done работу.

## 4. Состояния одного цикла

4.1. `INTAKE` — человек или агент формулирует исходный вопрос.

4.2. `BRIEF` — lead-agent превращает вопрос в задание: цель, scope, outputs, risks, done criteria.

4.3. `AGREED` — человек/агенты согласовали, что вопрос стоит запускать, или lead-agent имеет право стартовать read-only разведку.

4.4. `DAG` — работа разбита на независимые кластеры, зависимости и barriers.

4.5. `LAUNCHED` — подготовлены handoff/workflow/stream packets.

4.6. `IN_FLIGHT` — субагенты работают, conveyor отслеживает.

4.7. `LANDED` — результат пришёл, но ещё не проверен.

4.8. `EXTRACTED` — сырой вывод извлечён в структурированный документ.

4.9. `VERIFIED` — проверены evidence, команды, файлы, ограничения.

4.10. `SYNTHESIZED` — сделан consensus/divergence/new_tasks split.

4.11. `CAULDRON` — материал вынесен в котёл: ratify-build или divergence-detail.

4.12. `TASKED` — из результата созданы кандидатные задачи.

4.13. `DECIDED` — решение принято человеком или назначенным сборщиком.

4.14. `BUILT` — по принятому материалу сделана техническая реализация.

4.15. `SHIPPED` — результат проверен, закоммичен и отражён в индексах.

4.16. `REFILL` — новый цикл берёт входы из котла, synthesis, Q/T/D, drift/assurance/friction.

## 5. Обязательный формат стратегического brief

5.1. Перед запуском субагентов lead-agent должен записать brief хотя бы в сообщении, а для больших задач — в `topics/<topic>/brief.md` или `tmp-work/<topic>-brief.md`.

5.2. Минимальный brief:

```yaml
topic: короткое имя темы
lead: codex|claude|mavis|novax
mode: read-only|build|mixed
reason: зачем это нужно
scope:
  include: []
  exclude: []
outputs:
  - report
  - synthesis
  - task-candidates
constraints:
  - no auto-accepted decisions
  - no direct external-code execution
  - do not overwrite other agents
success:
  - consensus/divergence separated
  - evidence links present
  - next actions classified
```

5.3. Если brief нельзя написать коротко, значит задача ещё не готова к fan-out. Сначала нужна разведка.

## 6. Декомпозиция в DAG

6.1. Lead-agent строит DAG, а не плоский список поручений.

6.2. Типы узлов:

6.2.1. `RO-MAP` — read-only карта файлов/документов/тем.

6.2.2. `RO-VERIFY` — независимая проверка факта или команды.

6.2.3. `RO-SYNTH` — синтез нескольких документов.

6.2.4. `DRAFT-DOC` — независимый документ-вариант.

6.2.5. `DRAFT-CODE` — черновик кода в sandbox/worktree, no-execute по умолчанию.

6.2.6. `BUILD` — настоящая правка кода или документа в каноне.

6.2.7. `GATE` — проверка validate/generate/merge/permission.

6.2.8. `HUMAN` — решение, которое нельзя принимать агенту.

6.3. Правила DAG:

6.3.1. независимые read-only узлы можно запускать параллельно;

6.3.2. build-узлы с hot/shared files уходят в worktree;

6.3.3. зависимый узел не запускается, пока родитель не VERIFIED;

6.3.4. спорный узел идёт в котёл, а не в mainline;

6.3.5. follow-up не вписывается в уже in-flight workflow, а становится новой нодой.

## 7. Запуск субагентов

7.1. Локальный репозиторий не должен зависеть от конкретного API запуска агентов.

7.2. Поэтому локальная команда готовит launch-пакет:

```powershell
python tools\top.py subagent-handoff <agent> <T-id> "<context>" --worktree --json
```

7.3. Реальный запуск делает внешний launcher: Codex subagent, другой AI, человек или будущий сервер.

7.4. Для текущей среды Codex можно запускать platform sub-agents, но результаты всё равно должны возвращаться в репозиторный контур через отчёт, synthesis и selective integration.

7.5. Шаблон поручения worker-agent:

```text
Ты worker-agent в репозитории C:\Users\stefan\Documents\New project ai colab.

Задача: <узкая задача>.
Режим: read-only|worktree|sandbox-draft.
Разрешённые пути: <пути>.
Запрещено: удалять чужие сообщения, принимать accepted decisions, коммитить напрямую, запускать внешний код без approval.

Сделай:
1. Прочитай AGENTS.md, PROTOCOL.md и task/brief.
2. Проверь существующие команды/файлы, не выдумывай API.
3. Выполни только свой scope.
4. Верни structured report:
   - summary
   - files inspected/changed
   - findings
   - evidence
   - risks
   - open questions
   - proposed next actions
   - tests/checks
```

## 8. Conveyor runtime

8.1. Conveyor нужен, чтобы lead-agent не забывал о landed output и не осушал поток.

8.2. Минимальный цикл:

```powershell
python tools\top.py conveyor --target 3 --json
python tools\conveyor.py status
python tools\conveyor.py launch <label> --kind read-only --task T-xxx
python tools\conveyor.py land <label> --output <path>
python tools\top.py process-landed --topic <topic>
python tools\conveyor.py ship <label> --note "processed into <artifact>"
```

8.3. Если результат плохой:

```powershell
python tools\conveyor.py dismiss <label> --reason "bad output / superseded / duplicate"
python tools\top.py conveyor-recover --json
```

8.4. Важное правило: `landed` не равно `accepted`. Landed значит только "результат пришёл".

8.5. Cycle close запрещён, пока есть:

8.5.1. orphan landed output;

8.5.2. missing output;

8.5.3. parked result без решения;

8.5.4. divergence без follow-up;

8.5.5. task candidate без маршрута.

## 9. Synthesis contract

9.1. Каждый synthesis-документ должен иметь одинаковую структуру.

9.2. Минимальная схема:

```yaml
summary: краткий вывод
inputs:
  - file/path or agent report
consensus:
  - point: ...
    evidence: ...
near_consensus:
  - point: ...
    missing_confirmation: ...
divergence:
  - issue: ...
    position_a: ...
    position_b: ...
    evidence: ...
    needed_question: ...
uncertain:
  - claim: ...
    why_uncertain: ...
decisions_needed:
  - question: ...
    variants: [a, b, c]
    recommendation: ...
new_task_candidates:
  - title: ...
    reason: ...
    owner: pool
    priority: normal
    evidence: ...
route:
  ratify_build: []
  divergence_detail: []
  archive: []
```

9.3. Consensus без evidence не считается готовым.

9.4. Divergence нельзя стирать; его нужно переносить в detail lane.

9.5. New task candidates не должны автоматически становиться задачами без review/gate.

## 10. Котёл как двухполосная система

10.1. Полоса 1: `ratify-build`.

10.1.1. 2+ независимых источника согласны.

10.1.2. Evidence достаточно.

10.1.3. Нужна ратификация или уже можно строить.

10.2. Полоса 2: `divergence-detail`.

10.2.1. Есть расхождения.

10.2.2. Нужны уточняющие вопросы.

10.2.3. Нужно больше вариантов.

10.2.4. Нельзя строить без решения.

10.3. Команды:

```powershell
python tools\top.py cauldron-lanes <topic> --json
python tools\two_track.py board --json
python tools\two_track.py --track ratify --json
python tools\two_track.py --track detail --json
```

10.4. Котёл не должен быть архивом всего подряд. Он должен быть рабочим распределителем: что ратифицировать, что детализировать, что строить, что закрыть.

## 11. Новый недостающий мост: task materializer

11.1. По итогам проверки субагентов главный недостающий инструмент: безопасное превращение synthesis/cauldron результата в кандидатные задачи.

11.2. Это не должен быть auto-accept и не должен быть auto-build.

11.3. Нужен инструмент с dry-run по умолчанию:

```powershell
python tools\cauldron_task_materializer.py plan <synthesis-or-cauldron-file> [--json]
python tools\cauldron_task_materializer.py apply <synthesis-or-cauldron-file> --agent <agent> --only approved
```

11.4. Требования:

11.4.1. читает `new_task_candidates`, `decisions_needed`, `route.ratify_build`, `route.divergence_detail`;

11.4.2. проверяет evidence;

11.4.3. группирует дубли по смыслу, но не удаляет варианты;

11.4.4. печатает план задач без записи по умолчанию;

11.4.5. пишет `tasks/T-*.md` только с явным apply;

11.4.6. использует `tools/next_id.py` для ID;

11.4.7. не ставит decisions в accepted;

11.4.8. добавляет ссылки на исходный synthesis/cauldron файл;

11.4.9. после apply требует `python tools/generate.py` и `python tools/validate.py`.

11.5. Эта работа заведена как T-276.

## 12. Когда создавать задачу, решение или новый workflow

12.1. Создать задачу, если:

12.1.1. есть конкретное действие;

12.1.2. есть проверяемый результат;

12.1.3. есть владелец или owner pool;

12.1.4. можно указать next step.

12.2. Создать decision proposal, если:

12.2.1. меняется правило;

12.2.2. меняется governance;

12.2.3. есть 2+ варианта и нужен выбор;

12.2.4. результат влияет на многих агентов.

12.3. Создать новый workflow, если:

12.3.1. вопрос большой;

12.3.2. нужны независимые мнения;

12.3.3. надо прочитать много документов;

12.3.4. нужен fan-out.

12.4. Создать worktree build, если:

12.4.1. есть конкретный код;

12.4.2. есть hot/shared files;

12.4.3. нужен selective merge;

12.4.4. есть риск конфликтов.

12.5. Архивировать, если:

12.5.1. материал исторический;

12.5.2. он уже покрыт accepted решением;

12.5.3. нет действия;

12.5.4. есть краткое summary и ссылка.

## 13. Refill: как брать новые задания

13.1. После каждого цикла lead-agent должен пополнить очередь.

13.2. Источники refill:

13.2.1. ready tasks из `pipeline.py status`;

13.2.2. `new_task_candidates` из synthesis;

13.2.3. open `Q-*`;

13.2.4. divergence-detail;

13.2.5. drift/assurance/friction сигналы;

13.2.6. TODO/FIXME;

13.2.7. user request;

13.2.8. recovery diagnostics.

13.3. Приоритет:

```text
blocking human/governance issue
  -> safety/hygiene issue
  -> active user request
  -> T-273/T-274/T-275 class infrastructure task
  -> high-value read-only workflow
  -> build task with clean scope
  -> exploratory idea
```

13.4. Если верхний слой не успевает обрабатывать results, не увеличивать число агентов.

## 14. Режимы масштаба

14.1. Режим A: самостоятельные агенты в общем контуре.

14.1.1. Безопасный рабочий предел: 2-4.

14.1.2. Основной риск: конфликт правок и перегрузка synthesis/commit.

14.2. Режим B: оркестрируемый рой.

14.2.1. 3 workers + 1 coordinator — первый pilot.

14.2.2. 3 группы по 3 workers + observers — расширение.

14.2.3. 12-14 одновременных исполнителей возможно только если workers не коммитят и write scopes не пересекаются.

14.3. Режим C: read-only swarm.

14.3.1. Можно шире, потому что нет write contention.

14.3.2. Узкое место всё равно synthesis.

14.4. Формула ограничения:

```text
agents_running <= synthesis_capacity + review_capacity + commit_capacity
```

## 15. Anti-patterns

15.1. Запустить много агентов и не обработать landed outputs.

15.2. Считать landed output готовым решением.

15.3. Автоматически ставить accepted без человека.

15.4. Стирать divergence как дубль.

15.5. Писать несуществующие команды как готовые.

15.6. Класть большие сырые логи в `queues/inbox` без TTL.

15.7. Запускать внешний код до sandbox/preflight.

15.8. Коммитить чужую half-done работу.

15.9. Делать новый workflow внутри уже running workflow вместо новой ноды.

## 16. Минимальный практический цикл на сегодня

16.1. Проверить состояние:

```powershell
python tools\top.py status codex
python tools\pipeline.py status
python tools\top.py conveyor --target 3
```

16.2. Взять или выбрать задачу:

```powershell
python tools\top.py take codex T-276
```

16.3. Создать brief.

16.4. Запустить 2-3 read-only subagents или handoff-пакеты.

16.5. Собирать landed outputs:

```powershell
python tools\top.py process-landed --topic <topic>
```

16.6. Синтезировать:

```powershell
python tools\top.py synthesize-docs <topic> --with-streams --ready-only --out reports/<topic>-synthesis.md
python tools\top.py cauldron-lanes <topic> --out reports/<topic>-lanes.md
```

16.7. Обсудить с человеком и агентами.

16.8. Создать task candidates через будущий T-276 materializer или вручную через `next_id.py`.

16.9. Запустить следующий цикл.

## 17. Критерий готовности closed-loop системы

17.1. Один lead-agent может взять стратегический вопрос и провести его через весь цикл без неформальных догадок.

17.2. Субагенты получают узкие задания и возвращают structured reports.

17.3. Synthesis разделяет consensus/divergence/new_tasks.

17.4. Котёл показывает ratify-build и divergence-detail.

17.5. New tasks создаются безопасно, с dry-run и evidence.

17.6. Человек видит не сырой шум, а компактный decision board.

17.7. После завершения цикла нет orphan landed outputs, stale generated indexes и незакрытых follow-ups.

## 18. Следующие действия

18.1. Принять этот документ как proposed runbook.

18.2. Реализовать T-276: cauldron task materializer.

18.3. Связать runbook с T-274 tripwire, чтобы рост числа агентов автоматически поднимал advisory.

18.4. Связать runbook с T-275 instruction surface, чтобы новый агент видел этот цикл через `instruction-preflight`.

18.5. После T-276 сделать один демонстрационный цикл на T-273 или отдельной read-only теме.
