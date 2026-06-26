---
id: independent-variant-stream-policy
type: policy
status: proposed
owner: codex
date: 2026-06-25
related: [D-017, D-018, D-024, D-028, tools/stream.py, tools/doc_synthesis.py]
---

# Independent-first variant streams

## 00. File card

**Purpose.** Уточнить политику “дублей”: для содержательных вопросов, архитектуры, методологии и больших предложений похожая тема не останавливает агента. Сначала каждый агент раскрывает свой вариант в отдельном дереве/stream, потом варианты синтезируются.

**Status.** `proposed`: рабочий manual и уточнение к `D-017`; accepted-решение требует человека или назначенного integrator.

**Audience.** Люди, Codex, Claude, Lagrange, observer/synthesizer agents, scripts that create or inspect streams.

## 01. Главный принцип

```text
same title != duplicate
same question != duplicate
same topic != duplicate
same topic + same conditions + same evidence + no new risks + no new questions = duplicate noise
```

Для содержательных работ правильный порядок такой:

```text
independent variant -> complete potential -> ready-for-synthesis -> compare -> consensus/divergence -> adopt/build
```

Агент не должен отказываться от работы только потому, что кто-то уже написал похожую карточку. Иначе проект теряет возможность сравнить два независимых решения.

## 02. Почему “дубль” часто не дубль

Одинаковое название может скрывать разные книги. Для репозитория это означает:

| Совпадает | Может отличаться |
|---|---|
| название темы | условия применимости |
| первый вопрос | глубина ответа |
| 50% формулировок | evidence, команды, тесты |
| общий вывод | риски и edge cases |
| target-файл | способ реализации |
| статус `proposed` | степень готовности к adoption |

Поэтому dedup нельзя делать по названию, topic-id или первому абзацу. Dedup делается после synthesis.

## 03. Три режима независимой работы

### 03.1. Малый режим: variant note

Использовать для короткого мнения, вопроса, альтернативной формулировки.

Формат:

```text
topics/<topic>/forks/<agent>-<short>.md
```

Подходит, если нет кода, нет hot-files, нет больших документов.

### 03.2. Средний режим: stream packet

Использовать по умолчанию для содержательных вариантов.

Формат:

```text
streams/<topic>/<timestamp-agent>/
  STREAM.md
  notes.md        # optional
  evidence/       # optional
  files/          # optional proposed files, not mainline
```

Команды:

```powershell
python tools\stream.py create <topic> <agent> "why this independent variant exists"
# заполнить STREAM.md
python tools\stream.py mark <stream-id> ready-for-synthesis "variant completed"
python tools\stream.py list <topic> --ready-only
```

### 03.3. Большой режим: worktree branch

Использовать, если есть код, большие правки, hot-files, generated indexes, same-file collision или риск поломать mainline.

Формат:

```text
git worktree / branch agent/<agent>/<task-or-topic>
```

Параллельный код пишется в worktree, но concept/evidence всё равно отражается в stream/outbox, чтобы синтезатор видел смысл работы.

## 04. Что агент обязан раскрыть до synthesis

Перед статусом `ready-for-synthesis` stream должен отвечать минимум на 8 вопросов:

1. Какой вопрос решается?
2. При каких условиях вариант верен?
3. Какой полный независимый ответ агента?
4. Чем вариант похож на уже известные?
5. Чем вариант отличается?
6. Что он добавляет сверх уже написанного?
7. Какая evidence/проверка поддерживает вариант?
8. Какие пункты кандидат в consensus, а какие в divergence?

Если этих ответов нет, вариант ещё `proposed/developing`, а не готов к синтезу.

## 05. Как синтезатор сравнивает варианты

Синтезатор не считает “кто первый” и не считает простое большинство механически. Он строит карту:

| Lane | Что попадает | Что делать |
|---|---|---|
| `consensus` / `ratify-build` | повторяется в нескольких независимых вариантах, не имеет сильного спора | вынести в общий документ, задачу, код, тест, wrapper |
| `near-consensus` | смысл похож, но нужны термины, формат, scope | нормализовать, задать уточняющий вопрос, потом повторить synthesis |
| `divergence-detail` | разные условия, разные риски, несовместимые claims | оставить в stream/divergence, собрать evidence, спросить человека/integrator |
| `duplicate-noise` | нет новых условий/evidence/рисков/вопросов | закрыть как superseded/rejected с ссылкой, не удалять бесследно |

Повторение не является мусором: повторение может быть независимым подтверждением. Мусор начинается только там, где повторение не добавляет ни подтверждения, ни условий, ни детализации.

## 06. Общая папка и личные деревья

На ранней фазе агенты не должны писать все варианты в один общий файл. Правильнее:

```text
streams/topic-a/20260625-1010-codex/STREAM.md
streams/topic-a/20260625-1012-claude/STREAM.md
streams/topic-a/20260625-1014-lagrange/STREAM.md
streams/topic-a/divergence.md              # после synthesis
```

Общий файл появляется позже:

```text
docs/topic-a-consensus.md                  # только после synthesis/adoption
topics/topic-a-synthesis.md                # proposed synthesis scaffold
```

Так сохраняется независимость мышления и уменьшается риск “последний перезаписал предыдущего”.

## 07. Где проходит граница с dedup

Dedup остаётся обязательным для механики:

- `T-000`, `Q-000`, `D-000` id;
- generated indexes;
- locks/claims;
- manifests;
- канонические accepted decisions.

Fork сохраняется для смысла:

- архитектура;
- методология;
- ревью;
- варианты кода до adoption;
- большие ответы на один вопрос;
- разные условия применения одного принципа.

## 08. Как это связано с триадной методологией

Это частный случай триады:

```text
local/private    -> один агент раскрывает свой вариант
meso/portal      -> stream/topic cluster собирает варианты
 global/canonical -> consensus/adopted mainline после synthesis
```

Иммунная память тоже триадная:

- агентная память: почему этот агент предложил так;
- кластерная память: что повторилось в нескольких вариантах;
- глобальная память: что стало accepted/canonical.

## 09. Минимальный workflow для агента

```powershell
python tools\top.py repo-search "<topic>" --limit 5
python tools\stream.py create <topic> <agent> "parallel independent variant"
# заполнить streams/<topic>/<stream-id>/STREAM.md
python tools\stream.py mark <stream-id> ready-for-synthesis "variant completed"
python tools\stream.py list <topic> --ready-only
python tools\synthesis_helper.py report <topic> --out topics\<topic>-synthesis.md
```

Если тема уже представлена обычными `docs/` и `queues/outbox/`:

```powershell
python tools\doc_synthesis.py candidates <topic>
python tools\top.py synthesize-docs <topic> --with-streams
```

## 10. Минимальный workflow для observer/synthesizer

1. Найти все ready варианты.
2. Проверить, что каждый вариант раскрыл условия/evidence/risks.
3. Сформировать synthesis scaffold.
4. Общие пункты отправить в `ratify-build`.
5. Разногласия оформить в `divergence-detail`.
6. Не переводить решение в `accepted` без человека или назначенного integrator.
7. Для каждого закрытого stream поставить `adopted`, `superseded`, `rejected` или `archived` с причиной.

## 11. Анти-паттерны

- Остановить агента словами “это уже есть” до того, как он написал свой вариант.
- Писать три независимых ответа в один общий файл без разделов/ownership.
- Считать большинство голосов консенсусом без проверки условий и evidence.
- Удалить divergence как шум.
- Принять вариант в mainline без stream/adoption note.
- Оставить `ready-for-synthesis` без synthesis дольше agreed SLA.

## 12. Что автоматизировать следующим этапом

1. DONE in T-253: `stream.py check` проверяет минимальные секции для `ready-for-synthesis` и выводит `incomplete_ready`.
2. DONE in T-254/T-258: `top.py variant-start` создаёт stream first; `repo-search` теперь отложен по умолчанию и запускается только как следующий шаг или явно через `--search-now`.
3. DONE in T-255: `doc_synthesis.py` умеет читать custom streams topic as corpus напрямую (`streams/<topic>/*/STREAM.md`).
4. `variants.py` должен отличать `duplicate-noise` от independent confirmation.
5. `conveyor.py` должен уметь ставить observer-задачу, когда по topic появилось 2+ ready variants.


## 13. Реализация T-253: readiness guard

`tools/stream.py check` теперь возвращает три диагностических списка:

```json
{
  "stale": [],
  "broken": [],
  "incomplete_ready": []
}
```

`incomplete_ready` заполняется только для stream-пакетов, которые явно заявили готовность к synthesis: `status: ready-for-synthesis` или `synthesis_ready: true`.

Проверяются обязательные разделы:

- `01. Условия применимости`;
- `02. Независимый ответ агента`;
- `03. Потенциал, который нужно раскрыть до синтеза`;
- `04. Сравнение с известными вариантами`;
- `05. Evidence / проверки`;
- `06. Вопросы другим агентам и людям`;
- `07. Synthesis contract`.

Backwards-compatibility: `proposed`, `developing`, `ready-for-review`, `adopted`, `superseded`, `rejected`, `archived` не блокируются этой проверкой.

Команда:

```powershell
python tools\stream.py check --max-age-days 7
python tools\stream.py check --max-age-days 7 --json
```

## 14. Реализация T-254: variant-start apex command

`tools/top.py` теперь имеет верхнюю команду для старта independent-first варианта:

```powershell
python tools\top.py variant-start codex "architecture core" --task T-254
python tools\top.py variant-start codex "architecture core" --reason "parallel independent variant" --json
```

Команда делает один стартовый цикл:

1. создаёт stream-пакет до `repo-search`, чтобы агент сначала внёс независимый вариант;
2. печатает `repo-search` как next command; выполняет его сразу только при явном `--search-now`;
3. если указан `--task`, запускает `instruction-preflight`, если не указан `--no-preflight`;
4. возвращает путь stream-файла и next commands;
5. не делает synthesis, не ставит `accepted`, не принимает governance-решений.

Side effect: команда пишет новый пакет в `streams/<topic>/<stream-id>/STREAM.md`. Поэтому она явно помечена в `top.py buttons` как `writes stream packet`.

### 14.1. Уточнение T-258: порядок без раннего якорения

Для strict independent-first задач ранний `repo-search` создаёт методологический риск: агент видит чужой вариант до раскрытия своего. Поэтому актуальный порядок такой:

1. `variant-start` создаёт личный stream.
2. Агент заполняет independent draft, минимум секции 01-03.
3. Только после этого запускается `repo-search` / сравнение / synthesis.
4. Если ранний поиск нужен осознанно, используется явный `--search-now`.

Исторические outbox/stream T-254 не переписываются; они считаются предыдущим вариантом, уточнённым через T-258.
## Applied instructions

- AGENTS.md: proposed policy, no accepted governance.
- PROTOCOL.md: работа оформлена через T-252.
- D-017: содержательные дубли сохраняются как форки.
- D-024 / cauldron-synthesis: разногласия не стираются.
- T-251: триада local/meso/global применена к variant streams.

## Checks

- OK: `python -m py_compile tools\stream.py tools\test_stream.py tools\top.py tools\capabilities.py`
- OK: `python tools\test_stream.py` -> create/mark/list/ready-only/adopt + stale/broken check.
- OK: `python tools\stream.py create duplicate-policy codex "independent variant smoke" --root tmp-work\stream-smoke` -> created stream packet; temp directory removed after path check.
- OK: `python tools\top.py buttons --json` -> includes `stream-ready`.
- OK: `python tools\capabilities.py snapshot`
- OK: `python tools\capabilities.py --check`
- OK: `python tools\heading_check.py docs\independent-variant-stream-policy.md` -> 0 findings.
- OK: `python tools\heading_check.py docs\triadic-fractal-methodology.md` -> 0 findings.
- OK: `python tools\heading_check.py docs\parallel-work-policy.md` -> 0 findings.
- OK: `python tools\generate.py`
- OK: `python tools\validate.py` -> `OK=12 WARN=0 ERROR=0`.
- OK: `python tools\generate.py --check`

## 15. Реализация T-255: stream corpus for synthesis

После T-255 независимый вариант можно сразу довести до синтеза без ручного перечисления файлов:

```powershell
python tools\top.py variant-start codex doc-synthesis-stream-corpus --task T-255
# заполнить streams/doc-synthesis-stream-corpus/<stream-id>/STREAM.md
python tools\stream.py mark <stream-id> ready-for-synthesis "variant completed"
python tools\top.py synthesize-docs doc-synthesis-stream-corpus --json
```

Правило совместимости: исторический preset `architecture-core` без файлов остаётся preset-командой. Для custom topic без позиционных файлов `doc_synthesis.py` ищет `STREAM.md` в `streams/<topic>/...` и использует их как corpus.

Это закрывает разрыв между “агент создал личный stream” и “observer/synthesizer может сравнить варианты”: теперь верхний слой может поднять stream-пакеты в synthesis одной командой.
## 16. Реализация T-256: ready-only synthesis corpus

После T-256 observer/synthesizer может брать только дозревшие варианты:

```powershell
python tools\doc_synthesis.py scan <topic> --ready-only --json
python tools\top.py synthesize-docs <topic> --ready-only --json
python tools\top.py cauldron-lanes <topic> --ready-only
```

`--ready-only` включает только stream-пакеты с `status: ready-for-synthesis` или `synthesis_ready: true`. Это сохраняет свободу агентов писать developing/proposed варианты, но не загрязняет synthesis недозревшими черновиками.

Правило приоритета остаётся прежним: если files переданы явно, инструмент сканирует именно их. `--ready-only` применяется к автоматическому stream corpus, когда files не переданы.
## 15. Реализация T-259: batch barrier для sub-agents

`variant-start` защищает одиночный вариант от раннего якорения. Для нескольких агентов используется `variant-batch`:

```powershell
python tools\top.py variant-batch variant-batch-barrier --agents codex,subagent-worker --task T-259 --batch-id t259
```

Контракт:

1. Batch manifest хранится рядом с stream-корпусом: `streams/<topic>/_batches/<batch-id>.json`.
2. Manifest фиксирует expected agents, quorum, ready/missing agents и команды следующего шага.
3. Команда не создаёт `STREAM.md` за агентов; она только печатает per-agent `variant-start` команды.
4. Сравнение открывается после barrier: `ready_count >= quorum`.
5. Synthesis должен читать только готовые stream-пакеты через `--ready-only`.
6. Разногласия не стираются; observer/synthesizer переносит их в divergence-detail.

Историческое правило D-017/D-028 сохраняется: похожие темы не схлопываются как дубли до сравнения условий, evidence, рисков и открытых вопросов.
## 17. Реализация T-262: independent-first guard before repo-search

T-262 исправляет процессный дефект: агент может помнить правило, но всё равно начать с поиска существующего решения. Для методологических, архитектурных и variant/synthesis задач добавлен отдельный проверяемый guard:

```powershell
python tools\independent_first.py check <stream-id-or-path> --json
```

Что проверяется до `repo-search` / comparison:

1. `STREAM.md` существует.
2. Секции `01`, `02`, `03` присутствуют.
3. Секции не остались шаблонными placeholder-ами.
4. Секция `03` содержит признак алгоритма.
5. Секция `03` содержит признак псевдокода.

`tools/top.py variant-start` теперь добавляет эту команду в `next_commands` сразу после создания stream и перед `repo-search`. Это не заменяет человеческое мышление и не оценивает качество идеи; это ловит конкретное нарушение порядка: сравнение началось раньше собственного варианта.