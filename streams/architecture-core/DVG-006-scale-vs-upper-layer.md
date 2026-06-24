---
id: DVG-006-scale-vs-upper-layer-2026-06-24
topic: architecture-core
type: divergence-detail
status: proposed
agent: codex
date: 2026-06-24
related:
  - streams/architecture-core/divergence.md
  - docs/top-layer-throughput-methodology.md
  - docs/workflow-conveyor-policy.md
  - docs/agent-capacity-methodology.md
  - tools/top.py
  - tools/conveyor.py
  - tasks/T-222.md
---

# DVG-006 — расширять число агентов или сначала усиливать верхний слой

## 00. File card

**Purpose.** Детализировать спор DVG-006 так, чтобы его можно было перевести из `divergence-detail` в `ratify-build`, когда появится согласованный критерий масштабирования.

**Status.** `proposed`: это позиция Codex для котла, не accepted-решение.

## 01. Суть спора

Есть две рабочие интуиции:

1. **scale-agents** — запускать больше producer-агентов, чтобы быстрее покрывать корпус, генерировать варианты и искать идеи.
2. **scale-upper-layer-first** — сначала усилить верхний слой: intake, evidence, synthesis, drain, merge-gate и commit-band.

Проблема не в том, что один вариант всегда плохой. Проблема в порядке применения. Если запускать больше агентов до того, как верхний слой умеет принимать и проверять их результаты, система получает больше незавершённого шума, а не больше прогресса.

## 02. Evidence

- `docs/top-layer-throughput-methodology.md:13` — главный ограничитель описан как способность верхнего слоя обрабатывать, проверять, синтезировать и коммитить результаты.
- `docs/top-layer-throughput-methodology.md:30` — при превышении способности верхнего слоя растёт очередь landed и появляются повторы.
- `docs/top-layer-throughput-methodology.md:233` — масштабирование флота должно смотреть на метрики верхнего слоя, а не только на число агентов.
- `docs/top-layer-throughput-methodology.md:251` — если есть необработанные результаты, нужно process-landed, а не запуск новых агентов.
- `docs/workflow-conveyor-policy.md:117` — технические потолки фан-аута высоки, первым упирается полоса коммита.
- `docs/agent-capacity-methodology.md:97` — read-only анализ масштабируется широко, но потолок здесь всё равно обработка результата.
- `docs/agent-capacity-methodology.md:101` — build в общем дереве должен быть узким: не более одного build в shared tree, остальные через worktree.
- `docs/agent-capacity-methodology.md:258` — наращивать продюсеров можно, но ширину волны нужно держать под полосу коммита.

## 03. Варианты

### Вариант A — scale-agents

Запускать больше producer-агентов сразу, особенно на read-only анализ, поиск, ревью документации, генерацию вариантов.

**Плюсы:**

- быстро покрывает большой корпус;
- даёт несколько независимых вариантов;
- хорошо работает для read-only задач без конфликтов записи.

**Минусы:**

- увеличивает очередь результатов, которые нужно проверить;
- может размножать повторяющиеся советы без внедрения;
- для build-задач быстро упирается в git/index/merge/commit contention.

### Вариант B — scale-upper-layer-first

Сначала улучшать верхний слой: команды, synthesis, queue discipline, evidence gates, process-landed, merge-gate, capabilities, snapshot.

**Плюсы:**

- снижает потери результатов;
- делает работу агентов воспроизводимой;
- создаёт критерии, когда можно безопасно расширять флот.

**Минусы:**

- кажется медленнее на старте;
- может задержать полезный read-only fan-out;
- требует дисциплины: агентам нужно пользоваться обёртками, а не обходить их вручную.

### Вариант C — gated scale

Гибрид: увеличивать агентов только по классу задачи и только если верхний слой зелёный.

**Правило:**

| Класс работы | Когда можно расширять | Ограничение |
|---|---|---|
| read-only corpus/search/report | `landed == 0` или есть явный integrator | можно 3/9/27 producer-пакеты |
| divergence-detail | есть synthesis-owner и файл `streams/<topic>/...` | не больше того, что синтезатор успеет сравнить |
| build/code | есть worktree/merge-gate или один shared-tree исполнитель | shared tree target = 1 |
| governance/accepted | есть человек/integrator approval | не параллелить утверждение |

## 04. Proposed criterion для перехода в ratify-build

DVG-006 можно перевести в `ratify-build`, если котёл согласует такое правило:

1. **По умолчанию B:** сначала усиливать верхний слой, если есть необработанные landed/outbox/results, stale claims, failing validate/generate/drift/assurance или конфликтные hot files.
2. **A разрешён для read-only:** расширять producer-агентов можно, если результаты имеют output path, topic, expected synthesis owner и не требуют прямого commit.
3. **C для практики:** использовать gated scale как рабочий компромисс: read-only fan-out широкий, build узкий, governance серийный.
4. **Метрика перед запуском:** перед увеличением target агент должен проверить `top.py conveyor`, `top.py process-landed`, `top.py health`, `top.py assurance`.
5. **Stop rule:** если `landed > 0` без обработчика или появились stale/blocked integration tasks, новые агенты не запускаются, сначала drain/synthesis.

## 05. Рекомендация Codex

Моя позиция: принять **Вариант C — gated scale** как технически лучший компромисс.

Это не отменяет масштабирование агентов. Оно делает его управляемым:

- много агентов для чтения, поиска и вариантов;
- мало агентов для записи в общий tree;
- отдельный synthesis/drain слой перед commit;
- human gate для accepted/governance.

Такой критерий можно дальше ратифицировать как `ratify-build`: следующий кодовый шаг — добавить в верхний слой команду/проверку, которая перед расширением флота показывает stop/go по landed, checks, contention и классу задачи.