---
id: 20260625-1913-codex
topic: variant-batch-barrier
agent: codex
status: ready-for-synthesis
created: 2026-06-25
variant_policy: independent-first
synthesis_ready: true
task: T-259
phase: independent-before-comparison
---

# Variant batch barrier - independent Codex variant

## 00. Причина независимого варианта

T-258 решил одиночный старт варианта, но пользовательская цель шире: несколько sub-agents должны работать параллельно и не простаивать. При этом новая политика требует, чтобы они сначала раскрывали собственный потенциал, а уже потом видели чужие тексты, repo-search и synthesis. Нужен batch/barrier слой: он не заменяет агентов, а задаёт фазовую дисциплину.

## 01. Условия применимости

Механизм нужен, когда:

- есть одна большая тема и несколько агентов/людей должны дать независимые варианты;
- варианты должны быть сравнимы, но не должны заранее копировать друг друга;
- нужна доказательная база для consensus/divergence;
- верхний слой должен видеть, кто уже сдал independent draft, кто ещё не сдал, и когда можно открывать comparison.

Не нужен для одиночного bugfix, механической генерации индексов, validate/generate/check или задачи с уже заданным конкретным patch.

## 02. Независимый ответ агента

Мой вариант: добавить верхний сценарий `variant-batch`, который работает как фазовый протокол.

Фаза 1 - plan:

1. Создать batch manifest для темы.
2. Указать topic, task, agents, required sections, policy, created time.
3. Для каждого агента напечатать или создать личный target stream path.
4. Не запускать repo-search и не показывать чужие streams в этой фазе.

Фаза 2 - draft:

1. Каждый агент пишет свой `streams/<topic>/<id-agent>/STREAM.md`.
2. Статус может быть `developing` или `ready-for-synthesis`.
3. Barrier считает готовыми только streams с `ready-for-synthesis` или `synthesis_ready: true`.

Фаза 3 - barrier:

1. Проверить, сколько expected agents сдали ready stream.
2. Если не все сдали, показать missing agents и не запускать synthesis автоматически.
3. Если quorum/required count достигнут, открыть comparison phase.

Фаза 4 - compare/synthesis:

1. Запустить `cauldron-lanes` / `synthesize-docs` по topic с `--ready-only`.
2. Consensus вынести в ratify-build.
3. Divergence вынести в detail tasks/questions.

Минимальная реализация для этого шага: `python tools/top.py variant-batch <topic> --agents a,b,c --task T-id --json` как read/write wrapper, который создаёт manifest и печатает per-agent next commands. Отдельный `variant-batch-status <topic>` можно отложить, если первая команда уже умеет показывать status.

## 03. Потенциал, который нужно раскрыть до синтеза

Полезный потенциал:

- batch manifest становится общей точкой управления, а не случайной перепиской в чате;
- люди видят “кто должен сдать вариант” и “кто уже готов”;
- агенты получают одинаковый контракт, но не получают чужие ответы заранее;
- observer может начинать synthesis только после barrier;
- система начинает превращать sub-agent работу в воспроизводимый workflow.

## 04. Сравнение с известными вариантами

Сравнение выполнено после первичной независимой записи.

Consensus:

- Codex, Ramanujan, Anscombe и Boyle сходятся: batch/barrier нужен после T-258 для пачки independent-first агентов.
- Stream-файлы за других агентов создавать нельзя по умолчанию; это создаёт ghost ownership и пустые stale streams.
- Batch должен писать manifest и per-agent commands, а сами агенты должны запускать `variant-start` и заполнять свои `STREAM.md`.
- Repo-search, чтение sibling streams и synthesis открываются после ready barrier.
- Synthesis должен использовать `--ready-only`, чтобы не смешивать developing/proposed черновики с готовыми вариантами.

Принятые уточнения:

- Manifest хранится в `streams/<topic>/_batches/<batch-id>.json`, а не прямо в `streams/<topic>/BATCH.json`. Это рядом с corpus, но не выглядит как содержательный stream-пакет.
- `all-ready` остаётся default для малых batch; `--quorum N` допустим только как заранее объявленный режим, не как silent downgrade.
- Минимальная команда T-259: `python tools\top.py variant-batch <topic...> --agents a,b,c [--task T-id] [--quorum N] [--batch-id ID]`.

Divergence / future work:

- Нужна ли отдельная `variant-batch-status`, если текущая `variant-batch` уже создаёт/обновляет manifest и показывает status?
- Нужно ли формально разделять observer и synthesizer в manifest schema v2?
- Как фиксировать late streams после quorum synthesis: appendix, second synthesis pass или divergence-detail?

Dogfood result:

- `python tools\top.py variant-batch variant-batch-barrier --agents codex,subagent-worker --task T-259 --batch-id t259 --json` создал `streams/variant-batch-barrier/_batches/t259.json`.
- Manifest увидел два ready stream и открыл `phase: comparison-open`.

## 05. Evidence / проверки

Ожидаемые проверки после реализации:

- `python -m py_compile tools\top.py tools\test_top.py`
- `python tools\test_top.py`
- `python tools\top.py variant-batch variant-batch-smoke --agents codex,mavis --task T-259 --json --root tmp-work/...`
- `python tools\stream.py check --max-age-days 7 --json`
- `python tools\generate.py`
- `python tools\validate.py`

## 06. Вопросы другим агентам и людям

1. Должен ли batch manifest жить в `streams/<topic>/BATCH.json`, `queues/outbox/`, `logs/` или `topics/`?
2. Должен ли wrapper создавать пустые stream-файлы за агентов или только печатать команды для них?
3. Достаточен ли ready-count, или нужен список expected agents с обязательным quorum?
4. Нужна ли отдельная команда `variant-batch-status`, или достаточно `cauldron-lanes --ready-only`?
5. Когда можно автоматически запускать synthesis: all ready, quorum ready, или только human command?

## 07. Synthesis contract

Consensus candidates:

- batch/barrier нужен после T-258 для параллельных sub-agents;
- ранний repo-search остаётся запрещённым до independent draft;
- comparison открывается после ready barrier;
- ready streams читаются через существующий stream/doc_synthesis слой.

Divergence candidates:

- место хранения batch manifest;
- создавать ли stream-файлы автоматически;
- all-ready vs quorum-ready;
- нужен ли отдельный status-command.

Adoption target: `tools/top.py`, `tools/test_top.py`, docs/capabilities, optional `streams/<topic>/BATCH.json` contract.

Reject/supersede condition: если существующий `cauldron-lanes` уже полностью закрывает batch/barrier без нового wrapper, этот вариант должен быть сужен до документации и тестов.