---
id: 20260625-subagent-worker
topic: variant-batch-barrier
agent: subagent-worker
status: ready-for-synthesis
variant_policy: independent-first
synthesis_ready: true
task: T-259
created: 2026-06-25
---

# Batch/barrier для нескольких independent-first sub-agents

## 00. Причина независимого варианта

Independent-first нужен, когда цель batch-запуска не "быстрее получить один ответ", а раскрыть несколько независимых траекторий мышления до того, как они начнут влиять друг на друга. Для T-259 это особенно важно: если первый агент описывает barrier как обычный "дождаться всех", остальные легко начинают спорить только с этой рамкой и теряют альтернативы вроде quorum, наблюдателя или двухфазного синтеза.

Мой вариант считает batch не набором параллельных задач, а управляемым экспериментом: сначала фиксируется manifest, затем участники пишут изолированные stream-ответы, затем observer закрывает фазу готовности, и только после этого synthesizer читает варианты вместе.

## 01. Условия применимости

Подход применим, если одновременно верны условия:

- у задачи есть несколько допустимых архитектурных ответов;
- раннее чтение чужого варианта может сузить пространство решений;
- результат должен быть сравнимым, а не просто разрозненными заметками;
- есть хотя бы один общий критерий synthesis: надежность, latency, governance, простота внедрения, auditability;
- можно заранее описать ownership путей для каждого агента;
- batch допускает формальный stop condition: all-ready, quorum или timeout fallback.

Подход не нужен для линейных задач вроде "починить один тест" или "добавить одно поле", где независимые варианты создают больше накладных расходов, чем пользы.

## 02. Независимый ответ агента

### Batch manifest

Batch должен начинаться с manifest-объекта, который нельзя молча менять после старта independent-фазы. Минимальная схема:

```yaml
batch_id: BB-YYYYMMDD-topic
task: T-259
created: 2026-06-25
topic: variant-batch-barrier
variant_policy: independent-first
participants:
  - agent: codex
    stream_path: streams/variant-batch-barrier/<stream-id>/STREAM.md
  - agent: subagent-worker
    stream_path: streams/variant-batch-barrier/20260625-subagent-worker/STREAM.md
phase_policy:
  phases: [manifest-freeze, independent-write, readiness-barrier, synthesis, adoption]
  read_sibling_streams_before_ready: false
barrier:
  mode: all-ready
  quorum: null
  timeout: null
observer:
  role: readiness-and-protocol-check
synthesizer:
  role: compare-consensus-dissent
evidence_required:
  - front_matter
  - sections_00_07
  - applied_instructions
  - checks
```

Manifest решает три практические проблемы: кто участвует, куда каждый пишет, и какой barrier считается завершением фазы. Без manifest batch превращается в набор случайных файлов, а synthesizer вынужден угадывать, кого ждать и какие ответы считать валидными.

### Phase barrier

Я предлагаю пять фаз:

1. `manifest-freeze`: фиксируются участники, ownership, критерии, barrier mode и крайние сроки.
2. `independent-write`: агенты пишут только свои stream-файлы и не читают sibling streams.
3. `readiness-barrier`: observer проверяет наличие required outputs, front-matter, status и evidence.
4. `synthesis`: synthesizer читает все ready streams, выделяет consensus, dissent и unresolved assumptions.
5. `adoption`: человек или назначенный сборщик переводит выбранный вариант в mainline или решение.

Barrier стоит именно между `independent-write` и `synthesis`. До barrier запрещена cross-pollination, после barrier она обязательна: варианты должны сравниваться явно, иначе independent-first превращается в набор несвязанных монологов.

### Observer и synthesizer

Observer и synthesizer должны быть разными логическими ролями, даже если их выполняет один человек в маленьком запуске.

Observer:

- следит за manifest и ownership;
- проверяет, что stream готов формально;
- фиксирует опоздавших или заблокированных участников;
- не выбирает лучший вариант и не переписывает выводы агентов.

Synthesizer:

- начинает работу только после barrier condition;
- читает ready streams;
- сохраняет меньшинство и противоречия, а не сглаживает их;
- формирует proposed synthesis, но не утверждает accepted decision без назначенного права.

Такое разделение снижает риск, что "дежурный сборщик" начнет подгонять readiness под понравившийся вариант.

### All-ready vs quorum

`all-ready` должен быть режимом по умолчанию для малых batch-запусков с 2-5 агентами и высокой ценностью независимости. Он прост: synthesis стартует, когда каждый участник из manifest поставил `synthesis_ready: true` или явно стал `blocked`. Если кто-то заблокирован, observer добавляет blocked state, и synthesizer обязан учесть пропуск как evidence gap.

`quorum` нужен, когда batch большой, сроки жесткие или ожидаются отказы агентов. В manifest заранее задается `quorum: N of M`, например `3 of 5`, и timeout. После достижения quorum synthesis может стартовать, но поздние stream-варианты не теряются: они попадают в отдельное "late dissent / late evidence" окно и могут повлиять на adoption до финального решения.

Ключевое правило: нельзя молча понизить `all-ready` до `quorum`, когда один неудобный агент задерживается. Fallback допустим только если он заранее описан в manifest или отдельно утвержден человеком.

## 03. Потенциал, который нужно раскрыть до синтеза

До synthesis важно получить от каждого участника не только итоговый ответ, но и форму мышления:

- какая модель barrier выбрана и почему;
- какие failure modes считаются главными;
- где участник ставит границу между coordination и over-orchestration;
- какие metadata нужны в manifest;
- что делать с late, blocked и invalid streams;
- какие права есть у observer и synthesizer;
- какие критерии должны решать спор all-ready vs quorum.

Если эти элементы не раскрыты до чтения соседних вариантов, synthesis будет сравнивать формулировки, а не архитектурные различия.

## 04. Сравнение с известными вариантами

Я не открывал соседний stream `streams/variant-batch-barrier/20260625-1913-codex/`, чтобы сохранить independent-first. Известен только факт его существования в директории темы.

Сравнение с типовыми вариантами:

| Вариант | Сильная сторона | Риск | Моя позиция |
|---|---|---|---|
| Fire-and-forget batch | Минимальная координация | Непонятно, кого ждать и что считать готовым | Недостаточно для T-259 |
| Sequential review | Простая цепочка ответственности | Первый ответ якорит всех остальных | Противоречит independent-first |
| All-ready barrier | Максимальная полнота независимых ответов | Один зависший агент блокирует synthesis | Хороший default для малых batch |
| Quorum barrier | Устойчивость к отказам и срокам | Можно потерять важное меньшинство | Нужен как явный режим, не silent fallback |
| Observer-led synthesis | Быстрая сборка | Readiness и judgment смешиваются | Разделить observer и synthesizer |
| Synthesizer-only | Меньше ролей | Нет независимой проверки готовности | Допустимо только для маленьких low-risk запусков |

Отличие моего варианта: manifest является источником истины для barrier, observer проверяет phase transition, а synthesizer вступает только после формального ready condition.

## 05. Evidence / проверки

Evidence для этого stream-варианта:

- stream создан в отдельном ownership path, указанном пользователем;
- чужой stream темы не читался и не редактировался;
- вариант содержит явную модель `batch manifest -> phase barrier -> observer -> synthesizer -> adoption`;
- all-ready и quorum описаны как разные режимы с запретом silent downgrade;
- результат не меняет mainline, TASKS, indexes, tools или чужие streams.

Проверяемые признаки readiness:

- front-matter содержит `topic`, `agent`, `status`, `variant_policy`, `synthesis_ready`, `task`;
- секции `00`-`07` присутствуют;
- status стоит `ready-for-synthesis`;
- synthesis_ready стоит `true`;
- в конце есть машинный подвал `Applied instructions` и `Checks`.

## 06. Вопросы другим агентам и людям

Блокирующих вопросов нет; этот stream готов к синтезу.

Неблокирующие вопросы для сравнения вариантов:

- Должен ли `all-ready` быть default для всех independent-first batch, или только для малых batch?
- Какой минимальный quorum допустим, чтобы synthesis не стал мнением большинства без учета меньшинства?
- Может ли observer быть тем же агентом, что synthesizer, если manifest явно фиксирует роли?
- Должен ли manifest быть отдельным файлом или записью в задаче/stream summary?
- Как фиксировать late streams: как appendix к synthesis или как повод открыть новую synthesis pass?

## 07. Synthesis contract

Synthesizer, который использует этот stream, может считать его самостоятельным вариантом со следующими условиями:

- не выводить consensus, пока не проверен выбранный barrier mode;
- не считать отсутствие ответа согласием;
- сохранять dissent как отдельный результат, если варианты расходятся по all-ready/quorum, роли observer или праву поздних stream-вариантов;
- сравнивать варианты по критериям: independence preservation, failure handling, auditability, overhead, adoption path;
- не менять этот stream при synthesis; итог писать отдельным synthesis-файлом или в назначенное место;
- если из этого варианта берется решение, оформлять его как `proposed` до явного человеческого или назначенного accepted-step.

## Applied instructions

- `PROTOCOL.md`: использован stream packet вместо mainline-правки.
- `docs/protocol-machine-layer.md`: добавлены формальные `Applied instructions` и `Checks`.
- `docs/commit-stream-policy.md`: соблюден L2 stream packet и изоляция варианта.
- User ownership constraints: изменяется только новый `STREAM.md` в назначенном path.
- Skills: none.

Checks:
- `type PROTOCOL.md` -> OK
- `type docs\protocol-machine-layer.md` -> OK
- `type docs\commit-stream-policy.md` -> OK
- `dir streams\variant-batch-barrier` -> OK
- `mkdir streams\variant-batch-barrier\20260625-subagent-worker` -> OK
