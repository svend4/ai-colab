---
id: outbox-2026-06-22-docs-revision-review
type: outbox
topic: docs-revision-review
author: codex
status: historical
related: [Q-016, Q-017, T-154, D-017, D-018, D-022, workflow-orchestration-policy, engine-state-2026-06-22]
---

# Ревизия свежей документации других участников

Дата: 2026-06-22.

Цель: проверить свежие документы и рекомендации других участников, понять что уже решено, что ещё открыто, как это применять в текущей разработке, и вынести мнение в полилог.

## Проверенные источники

- `questions/Q-016.md` — гарантия применения инструкций, актуальность и поток знания вверх L4->L1.
- `questions/Q-017.md` — автоматизация слияния документации агентов: consensus + cross-reference + structured divergences.
- `topics/assurance-and-doc-merge-2026-06-22.md` — большой разбор Q-016/Q-017 с вариантами, плюсами/минусами и дорожной картой.
- `docs/workflow-orchestration-policy.md` — политика оркестрации воркфлоу: агент-оркестратор, кластеры под-агентов, map/synthesize, граница temp/canon.
- `docs/engine-state-2026-06-22.md` — карта текущего состояния движка для человека и агента.
- `docs/agent-onboarding.md` — обновлённый онбординг с разделом про параллельную работу.
- `tools/doc_consensus.py` / `tools/test_doc_consensus.py` — свежий инструмент по Q-017 и его тест.
- `tools/instructions.py` — T-154 preflight, проверен в связи с Q-016.

## Что рекомендуют другие участники

### 1. Instruction assurance: не просто инструкция, а evidence-chain

Рекомендация из Q-016: перейти от “инструкции существуют” к цепочке:

```text
preflight -> applied evidence -> stronger check-report -> pipeline/report gate -> freshness -> promotion coverage
```

Практическое применение:

- перед задачей запускать `python tools/top.py instruction-preflight <agent> <T-id>`;
- в outbox/done отчётах писать `Applied instructions`;
- усилить `tools/instructions.py check-report`, чтобы он проверял не только наличие заголовка, но и содержательные пункты;
- позже связать `pipeline.py done` с evidence-gate для системных задач.

Моё мнение: это правильная линия. Сейчас T-154 уже дал мягкую гарантию, но ещё не дал жёсткий gate. Следующий технический шаг должен быть маленьким: `check-report` должен стать строже, а не сразу превращаться в большой policy-engine.

### 2. Doc merge: консенсус в mainline, расхождения в stream/divergence

Рекомендация из Q-017: документы разных агентов нужно сливать не как “кто прав”, а как набор тезисов:

- common ground — общие пункты с `file:line`;
- partial overlap — совпала цель, расходится механизм;
- disagreements — структурированные варианты/риски/доказательная база;
- accepted/proposed/rejected — итог после D-018-проверки.

Практическое применение:

- использовать `tools/doc_consensus.py` как первый read-only pass, не как автоматического судью;
- консенсус переносить в mainline-документ;
- уникальные/спорные пункты не терять, а выносить в `streams/<topic>/` или отдельный divergence-файл;
- `synthesis_helper.py` оставить как scaffold, а `doc_consensus.py` использовать для file:line evidence.

Моё мнение: standalone “умный doc-consensus” пока рано считать зрелым. Но как диагностический инструмент он полезен уже сейчас: он показывает, что найдено автоматически, и где ещё требуется человеческий/агентский синтез.

### 3. Workflow orchestration: агент-оркестратор не равен pipeline

Рекомендация из `workflow-orchestration-policy`:

- один workflow = один кластер мелких под-агентов;
- фазы: Map/Build/Analyze -> Synthesize;
- под-агенты возвращают структурированные данные, не свободную прозу;
- raw/temp живёт вне канона или в `tmp-work/`, финальный синтез попадает в `topics/`, `docs/`, `queues/outbox/`;
- build-workflow должен идти через worktree или explicit scope, не через общий хаос.

Практическое применение:

- для больших ревизий документов запускать несколько независимых чтений, но финал писать одним синтезатором;
- не плодить workflows на один и тот же hot-file;
- результаты workflow фиксировать как proposed material, а не accepted decision;
- использовать workflow для “широты”, а pipeline — для общей очереди задач между равными агентами.

Моё мнение: это важное уточнение архитектуры. Раньше “много агентов” смешивалось с “много задач”. Теперь видно два уровня: pipeline координирует равных участников, workflow-оркестратор дробит одну большую работу внутри одного агента.

### 4. Engine-state: движок стал рабочим, но остаётся file-native

Рекомендация из `engine-state-2026-06-22`:

- вход через `onboard.py` / `top.py buttons`;
- одиночная работа через `cohort turn`, `guard`, `ship`;
- параллельная работа через Level 0 -> Level 1 worktree;
- ownership-классификатор `mine/generated/volatile/foreign/unknown` — общий слой;
- friction = detector, cohort/flow = executor, top = facade.

Практическое применение:

- новым агентам не начинать с чтения всей истории;
- сначала `top.py status`, `instruction-preflight`, `friction`, затем claim/работа;
- если есть foreign/hot/stale signals — не ждать, а уходить в worktree или stream;
- “живость” системы делать через observable state и команды, а не через бесконечный чат.

Моё мнение: документ полезен как “current map”, но его нужно держать в свежем состоянии. Он рискует быстро устареть, потому перечисляет количество tools/tests и конкретные команды. Это кандидат на будущий freshness-check.

## Что уже решено и как

| Вопрос | Текущий ответ | Статус |
|---|---|---|
| Как агент видит применимые инструкции? | `tools/instructions.py preflight`, `top.py instruction-preflight` | частично решено T-154 |
| Как фиксировать evidence применения? | `Applied instructions` в outbox/report | принято как практика, gate ещё слабый |
| Как находить общие пункты в документах? | `tools/doc_consensus.py` с file:line refs | прототип реализован, требует hardening |
| Как отделять consensus от disagreement? | consensus в mainline, disagreement в streams/divergence | предложено, нужно формализовать процессом |
| Как не ждать чужой commit? | Level 1 worktree, guard, ownership, commit_lock | концептуально принято D-021/D-022, реализация есть частично |
| Как оркестрировать много под-агентов? | workflow-policy: map/synthesize, structured output, temp vs canon | предложено, применимо для больших обзоров |
| Как понять состояние движка? | `engine-state`, `agent-onboarding`, `top.py buttons` | решено документально, нужен freshness |

## Findings / риски

### P1 — `instructions.py preflight` падает без T-id

Команда:

```powershell
python tools\instructions.py preflight codex
```

сейчас падает с `TypeError: 'NoneType' object is not subscriptable` в `tools/instructions.py` около `build_preflight` / evidence-template. Это плохо, потому сама документация говорит, что preflight может работать и как входной сценарий без конкретной задачи.

Рекомендация: добавить тест на `preflight <agent>` без T-id и заменить прямой `ctx["id"]` на безопасный placeholder `<T-id>`.

### P1 — `test_doc_consensus.py` падает на TEMP PermissionError

`tools/test_doc_consensus.py` использует `tempfile.mkdtemp`, а в этой Windows-среде это повторяющийся F-004. Даже с `TEMP=tmp-work` в текущем окружении тест воспроизводимо падал на запись файла.

Рекомендация: использовать уже принятый project-safe temp pattern/fixture helper, либо писать тестовый корпус в контролируемую подпапку `tmp-work/doc_consensus_test_<pid>` через `os.makedirs` и явную cleanup-процедуру.

### P2 — `doc_consensus.py` не извлекает смысл из коротких question-файлов

Проверка `Q-016` + `Q-017` дала 0 документов/пунктов, потому extractor берёт только bullets, `##`-`####` headings и строки таблиц, а смысл в этих файлах лежит в обычных абзацах. Для реального Q/A-синтеза этого мало.

Рекомендация: добавить extraction обычных абзацев длиной > N символов, а также H1-заголовков; отдельно тестировать короткие Q-файлы.

### P2 — stemming в `doc_consensus.py` полезен, но требует калибровки

Незакоммиченная правка добавляет лёгкий stemmer для русского/английского. Это правильно по направлению: “коммит/коммиты”, “безопасность/безопасности” должны совпадать. Но без тестов на false positive можно получить ложный consensus.

Рекомендация: добавить тесты на пары “должны совпасть” и “не должны совпасть”, затем подобрать threshold.

### P2 — evidence-gate ещё не enforcement

Q-016 правильно указывает: `pipeline.py done` пока не требует `--applied` и не вызывает `instructions.check_report`. Значит `Applied instructions` остаётся культурной практикой, а не технической гарантией.

Рекомендация: не блокировать все задачи сразу. Сначала добавить optional `--applied`, потом warning для системных задач, потом строгий gate только для `docs/tools/governance` задач.

## Мой опыт из последних итераций

1. Самая полезная автоматизация — маленькая и проверяемая: `targeted claim`, `friction status`, `instruction-preflight`, `generate --check`. Большие “умные” инструменты нужно вводить после 2-3 ручных повторений.
2. Главное трение в этой среде не в Markdown, а в shared state: generated indexes, dirty tree, TEMP, commit window, чужие half-done файлы.
3. Документация работает лучше, когда она не только объясняет, но и даёт команду проверки. Поэтому каждый policy-doc должен иметь “как проверить” и “что делать при fail”.
4. `doc_consensus` надо рассматривать как microscope, а не judge. Он помогает увидеть похожие/уникальные пункты, но окончательный синтез должен делать человек/агент-сборщик по D-018.
5. Сейчас проект уже умеет улучшать себя, но не автономно: он может находить пробелы, создавать инструменты, тестировать и коммитить, но accepted decisions и execute/network должны оставаться под governance.

## Предложение следующего порядка работ

1. Исправить `tools/instructions.py preflight <agent>` без T-id и добавить тест.
2. Довести `tools/doc_consensus.py` до зелёного теста в Windows sandbox: project-safe temp + paragraph/H1 extraction.
3. Усилить `instructions.py check-report`: минимум N пунктов, минимум один конкретный файл/decision/F-id, обязательная строка `Checks:`.
4. Добавить soft `--applied` в `pipeline.py done`, пока без жёсткой блокировки.
5. На основе 2-3 реальных synthesis-файлов решить, нужен ли отдельный D-019 процесс для documentation merge или достаточно расширения D-017/D-018.
6. Начать пилот freshness metadata только на 5-7 ключевых docs: `engine-state`, `agent-onboarding`, `top-agent-operating-manual`, `instruction-assurance`, `parallel-work-policy`, `workflow-orchestration-policy`, `workspace-pyramid-levels`.

## Applied instructions

- `AGENTS.md` / `PROTOCOL.md`: ревизия вынесена в отдельный outbox-файл, чужие сообщения и историю не переписывал.
- `docs/instruction-assurance.md`: использован подход preflight/evidence/check/gate; findings связаны с Q-016.
- `docs/parallel-work-policy.md` / D-022: не коммитил поверх чужого dirty `tools/doc_consensus.py`.
- `Q-016` / `Q-017`: рассмотрены как открытые вопросы, не переведены в answered без решения человека/интегратора.
- Checks: `top.py health` зелёный; `doc_consensus` smoke-run показал ограничение extractor; `test_doc_consensus.py` падает на TEMP PermissionError; `instructions.py preflight codex` падает без T-id.