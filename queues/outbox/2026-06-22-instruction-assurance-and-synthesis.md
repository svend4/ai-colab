---
id: outbox-2026-06-22-instruction-assurance-and-synthesis
type: outbox
topic: instruction-assurance-and-agent-synthesis
author: codex
related: [T-153, D-017, D-018, D-022, docs/friction-retrospective-2026-06-22.md]
---

# Instruction assurance and multi-agent synthesis questions

Статус: рабочая outbox-заметка. Не canonical decision. После T-154 стала также implementation-report для instruction preflight.

## 1. Главный вопрос

Проблема не в том, что инструкций мало. Проблема в доказуемости:

- агент действительно прочитал нужные инструкции;
- агент понял, какие инструкции актуальны именно для текущей задачи;
- агент применил их в действиях;
- после работы можно проверить, какие правила были соблюдены, какие нарушены, какие устарели;
- документы разных агентов не превращаются в склад, а сводятся в общий синтез: совпадения, частичные совпадения, расхождения, вопросы.

Без такого слоя инструкции остаются “текстом внизу пирамиды”, который может не доходить до верхушки.

## 2. Модель: как основание пирамиды должно доходить до верхушки

Нужна не надежда, а pipeline знания:

```text
raw/base docs
  -> canonical index
  -> task-scoped retrieval
  -> agent preflight checklist
  -> evidence of use
  -> output/commit/report
  -> post-check/drift-check
```

### Уровень 1. Источник

Документы должны иметь metadata:

- `id`;
- `type`;
- `status`;
- `scope`;
- `owner`;
- `last_verified`;
- `applies_to`;
- `supersedes` / `superseded_by`;
- `related`.

Если документ без metadata, агент может его прочитать, но не может уверенно понять актуальность.

### Уровень 2. Индекс

`index.json` уже решает часть задачи, но нужен более строгий слой instruction index:

- какие инструкции являются обязательными;
- какие применяются только к code tasks;
- какие применяются к docs tasks;
- какие применяются к commit/integration;
- какие применяются к external code/sandbox;
- какие устарели.

### Уровень 3. Preflight агента

Перед задачей агент должен явно назвать:

- какие инструкции применимы;
- какие команды проверки будут запущены;
- какие риски есть;
- можно ли работать в shared tree или нужен worktree;
- есть ли чужой active claim.

Пример:

```text
Instruction preflight:
- AGENTS.md: yes
- PROTOCOL.md: yes
- task T-XXX: yes
- D-022 parallel policy: yes/no
- friction status: yes/no
- validate/generate: before commit
- commit mode: selective-add only
```

### Уровень 4. Evidence of use

В отчёте агент должен писать не только “сделал”, а “какие правила применил”.

Пример:

```text
Applied instructions:
- D-022: did not use git add -A because generated indexes were dirty.
- F-013: ran stream.py check.
- F-016: used targeted claim instead of next.
```

Это и есть гарантия применения: не абсолютная, но проверяемая.

## 3. Где гарантии, что инструкции используются

Абсолютной гарантии нет, если агент автономен и работает только по тексту. Но можно построить инженерные гарантии разных уровней.

| Уровень гарантии | Механизм | Что доказывает | Ограничение |
|---|---|---|---|
| Мягкая | onboarding/checklist | агент видел инструкции | не доказывает применение |
| Средняя | preflight + outbox evidence | агент сопоставил правила с задачей | можно написать формально |
| Жёсткая | validate/generate/merge_gate/friction/permissions | часть правил проверяется машинно | покрывает только формализованные правила |
| Очень жёсткая | guard blocks commit/action | опасное действие невозможно без исправления | требует точных правил, иначе будет мешать |

Моё мнение: проекту нужен не один “большой гарант”, а лестница:

1. Сначала instruction preflight.
2. Потом evidence in report.
3. Потом machine checks для повторяющихся правил.
4. Потом blocking gates только для data-loss/commit-risk.

## 4. Слияние работ разных агентов: не только code, но и docs

Документы разных агентов нужно сравнивать не как “кто прав”, а как несколько вариантов evidence.

Нужен формат синтеза:

```text
input docs -> claim extraction -> grouping -> agreement map -> disagreement map -> decision candidates -> accepted/proposed/rejected
```

## 5. Как находить общие пункты

Для каждого документа/агента извлекать тезисы в нормализованном виде:

```yaml
claim_id: C-001
claim: "targeted claim нужен, чтобы не брать wrong-next"
source: docs/friction-retrospective-2026-06-22.md
agent: codex
confidence: high
evidence: [T-149, F-016, T-152]
status: implemented
```

Потом группировать похожие тезисы:

| Группа | Общий тезис | Источники | Статус |
|---|---|---|---|
| G-001 | Нужен targeted claim | Codex friction retrospective; complaints log; T-152 | implemented |
| G-002 | Нужна классификация dirty files | Codex T-153; Claude synthesis; D-022 | active |
| G-003 | Не коммитить foreign half-done | D-022; friction ledger; cohort guard | accepted |

Общие пункты нужно подчёркивать как consensus:

- `agreed` — совпали независимо;
- `partial` — совпала цель, расходится механизм;
- `conflict` — разные цели или разные safety assumptions;
- `obsolete` — один вариант устарел после реализации;
- `needs-evidence` — недостаточно фактов.

## 6. Как работать с расхождениями

Расхождение нельзя просто стирать. Его надо превратить в структурированный вопрос.

Пример:

```text
Conflict X:
- Variant A: friction.py остаётся read-only detector.
- Variant B: cohort.py может принимать L0/L1 решение и запускать worktree flow.
- Совместимость: A наблюдает, B мутирует.
- Риск A: слишком пассивно, не ускоряет работу.
- Риск B: слишком активно, может мутировать без достаточного governance.
- Предложение: read/write boundary. friction = evidence; cohort = action; top/preflight = фасад.
```

## 7. Документ для синтеза должен иметь такую структуру

```md
# Synthesis: <topic>

## Inputs
| Source | Author | Status | Scope | Date |

## Common Ground
| Claim | Sources | Evidence | Decision status |

## Partial Overlap
| Claim | Same | Different | What to test |

## Disagreements
| Question | Variant A | Variant B | Risks | Evidence needed | Proposed resolution |

## Accepted / Proposed / Rejected
| Item | Result | Why | Links |

## Tasks Created
| Task | Why | Done criteria |
```

## 8. Какие вопросы надо задать сейчас

### Q1. Как доказать, что агент применил инструкции?

Предложение: каждый task report должен иметь секцию `Applied instructions`. Для code/commit tasks минимум:

- claim id;
- relevant decisions;
- friction/preflight result;
- validation commands;
- commit scope rule.

### Q2. Как понять, что инструкция актуальна?

Предложение: добавить metadata `last_verified`, `status`, `supersedes`, `applies_to`. Старые docs без этого считаются historical/context, а не mandatory.

### Q3. Как сливать документы разных агентов?

Предложение: делать synthesis file через таблицы `Common Ground`, `Partial Overlap`, `Disagreements`, `Tasks Created`.

### Q4. Кто имеет право переводить proposed в accepted?

Предложение: агент может предложить `proposed`; accepted делает человек или явно назначенный integrator. Это уже соответствует AGENTS.md.

### Q5. Как не утонуть в инструкциях?

Предложение: top-level preflight должен выбирать task-scoped инструкции, а не заставлять агента читать всё.

## 9. Практические предложения для проекта

### P0. Instruction preflight report

Добавить в `tools/top.py agent-start` или отдельный `tools/instructions.py preflight <task>`:

- читает task metadata;
- показывает применимые docs/decisions/skills;
- печатает checklist;
- предупреждает о stale/superseded docs.

### P0. Synthesis helper v2

Улучшить `tools/synthesis_helper.py` или создать `tools/claims.py`:

- извлекает claim-карточки из markdown;
- группирует по теме;
- строит таблицы common/partial/conflict;
- не принимает решения автоматически.

### P1. Instruction evidence in done marker

`pipeline.py done` может принимать `--applied` или report template:

```powershell
python tools\pipeline.py done codex T-XXX --claim ... --report "..." --applied "D-022,F-016,validate,generate"
```

Либо проще: договориться, что outbox report всегда содержит `Applied instructions`.

### P1. Instruction freshness check

Добавить `tools/instructions_check.py`:

- нет `status` у важного doc;
- doc ссылается на старую команду;
- skill не ссылается на canonical docs;
- accepted decision противоречит current tools.

### P2. Claim registry

Для больших синтезов нужен не только Markdown, но и machine-readable claims:

```text
claims/<topic>/<claim-id>.md
```

Но начинать лучше не с новой большой системы, а с одного synthesis template и 1-2 ручных примеров.

## 10. Ответ на исходный вопрос коротко

Гарантия не появляется от количества инструкций. Гарантия появляется от цепочки:

```text
metadata -> retrieval -> preflight -> evidence -> machine check -> gate
```

Слияние мнений разных агентов не должно быть “склеить все тексты”. Нужно:

1. извлечь тезисы;
2. найти совпадения;
3. выделить частичные совпадения;
4. вынести расхождения в отдельные вопросы;
5. принять/отклонить через evidence и governance;
6. создать задачи только по согласованным или явно спорным пунктам.

Моё мнение: следующий лучший шаг после T-153 — не новый большой агент, а маленький `instruction preflight` + `synthesis template`. Это даст проверяемость применения инструкций и нормальную культуру слияния документов.
## 11. Update 2026-06-22 — T-154 implementation

Сделано как первый практический шаг:

- добавлен `docs/instruction-assurance.md`;
- добавлен read-only инструмент `tools/instructions.py`;
- добавлена верхняя кнопка `python tools/top.py instruction-preflight <agent> [T-id]`;
- добавлен тест `tools/test_instructions.py`;
- `tools/capabilities.py` и `docs/top-layer-command-groups.md` обновлены, чтобы команда была видна в верхнем слое.

Это не заменяет синтез документов и не принимает решений. Это создаёт проверяемый входной шаг: агент перед задачей видит релевантные правила, а после задачи оставляет evidence.

## Applied instructions

- `AGENTS.md` / `PROTOCOL.md`: работал в зоне `docs/`, `tools/`, `tasks/`, `queues/outbox/`; чужие сообщения и историю не переписывал.
- `tasks/T-154.md`: реализованы критерии done для preflight-документа, read-only CLI, top-level команды, теста и outbox-отчёта.
- `docs/instruction-assurance.md`: применена модель `metadata -> task-scoped retrieval -> preflight -> evidence -> machine check -> gate`.
- `docs/parallel-work-policy.md` / `docs/commit-stream-policy.md`: из-за dirty shared tree использовал selective-add scope; `git add -A` не применялся.
- Friction: учтены F-006/F-015 — dirty tree и generated/shared files требуют явного списка файлов перед commit.
- Checks: `tools/test_instructions.py`, `tools/test_top.py`, `tools/instructions.py preflight`, `generate.py --check`, `validate.py`, `capabilities.py --check` должны быть зелёными перед закрытием/коммитом.
