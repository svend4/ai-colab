---
id: q017-semantic-consolidated-2026-06-23
type: topic
title: Q-017 — семантический гибрид слияния документации (consolidated, implementation-ready)
status: proposed
date: 2026-06-23
related: [Q-017, D-017, D-023, q017-docmerge-semantic-2026-06-23]
---

# Q-017 — семантический гибрид слияния документации (consolidated)

Это сводный, готовый-к-реализации канон-документ по Q-017: он объединяет три producer-разбора в один контракт — (1) **почему** механический режим `tools/doc_consensus.py` слеп к концептуальному консенсусу, (2) **как** устроен гибридный конвейер `doc_consensus report --semantic` (механический pre-cluster → agent-pass → merge → render), и (3) **на каких условиях приёмки и стоимости** он сдаётся. Направление утверждено как opt-in расширение, НЕ замена: чистый pure-stdlib лексический режим остаётся no-cost default, семантика опциональна и scoped из-за стоимости LLM-вызовов; без внешних ML/embeddings — только stdlib + subprocess-agent-вызов (тот же паттерн, что `variants.py` / `synthesis_helper.py`). Источник дизайна — `topics/q017-docmerge-semantic-2026-06-23.md`; остаётся реализация (effort **M**).

Важно о состоянии кода: на момент написания `tools/doc_consensus.py` (250 строк) реализует **только** механический лексический конвейер. Ни `_semantic_pass`, ни `_merge`, ни флаг `--semantic` в коде не существуют — `main()` (`:217-245`) парсит лишь `report`, `--thr`, `--out`, `--files`, `--topic`. Всё «семантическое» ниже — это buildable-цель, а не текущее поведение.

## 1. doc_consensus mechanics и лексическое слепое пятно

`tools/doc_consensus.py` автоматизирует синтез мнений: сканирует ≥2 markdown-дока по одной теме, кластеризует похожие «units» и делит их на **consensus** (units в ≥2 доках → кандидаты в mainline) и **divergence** (single-doc units → детализация/обоснование по D-017). Всё суждение о похожести держится на token-set Jaccard — именно здесь оно слепо к концептуальному cross-agent согласию.

### Конвейер по функциям

- **`units(path)`** (`tools/doc_consensus.py:80-135`) извлекает дискретные units: bullets, заголовки `#`–`####`, строки таблиц и значащие абзацы (`:120-124`), пропуская YAML front-matter (`:103-109`) и code-fences (`:110-114`). Каждый выживший unit становится dict `{text, tokens, where=file:line, doc}` через `_append_unit` (`:71-77`).
- **`_norm_tokens(text)`** (`:63-68`) lowercase, срезает inline-code и markdown-URL ссылок, выбрасывает не-alphanumeric и возвращает **множество** стеммированных слов длиннее 2 символов, не входящих в stop-words (`STOP`, ru+en, `:27-31`). Выход — неупорядоченное token-*множество*: порядок слов, фразировка и структура отброшены.
- **`_stem(w)`** (`:53-60`) — грубый суффикс-обрезатель: longest-match-first по русскому `_RU_SUF` (`:46-49`), затем английскому `_EN_SUF` (`:50`), обрезает только при остатке ≥4 символов. По дизайну «складывает лишь словоформы одного слова, не синонимы/парафраз» (`topics/q017-docmerge-semantic-2026-06-23.md:12`).
- **`_jaccard(a, b)`** (`:138-141`) — буквальный set-Jaccard: `|a ∩ b| / |a ∪ b|`. Без общих токенов значение ровно `0.0`.
- **`analyze(paths, thr=0.4)`** (`:144-165`) — жадная single-pass кластеризация: unit входит в существующий кластер с максимальным Jaccard ≥ `thr` против **замороженного представителя** этого кластера (`rep` = токены *первого* члена, `:151-160`); иначе заводит новый кластер. Consensus = кластеры в ≥2 доках (`:161-162`); divergence = single-doc кластеры (`:163`).
- **`render(res)`** (`:168-199`) формирует отчёт; для каждого consensus-кластера печатает longest-token члена как представителя (`max(c["members"], key=lambda u: len(u["tokens"]))`, `:181`) плюс `file:line` cross-refs всех членов.

### Почему token-Jaccard не ловит концептуальный консенсус

Два агента могут утверждать *одну идею разными словами*. Поскольку `_norm_tokens` сводит unit к мешку стеммированных поверхностных слов, а `_stem` складывает лишь инфлексии *одного лексема* — никогда синонимы/парафраз — такие units делят мало или ноль токенов, `_jaccard` возвращает ~0, падает ниже любого разумного `thr`, и units метятся как **divergence**, а не consensus. Проверено живьём против `tools/doc_consensus.py`:

- Одна идея, разная форма — «каждый агент работает в изолированном worktree» vs «параллельные ветки не пересекаются на диске»: множества `{worktree, агент, изолированн, кажд, работа}` и `{ветк, диск, параллельн, пересекаются}`, пересечение `∅`, **Jaccard 0.0**.
- Пара синонимов — «атомарный коммит на каждое изменение» vs «единичная фиксация для каждой правки»: `{атомарн, изменени, кажд, коммит}` vs `{единичн, каждой, правк, фиксация}`, пересечение `∅`, **Jaccard 0.0**.

Это потолок метода, а не вопрос подкрутки порога (`topics/q017-docmerge-semantic-2026-06-23.md:12`): понижение `thr` не может произвести overlap из token-множеств, которые искренне не делят ничего. Грубый стеммер усугубляет — `_stem` непоследователен даже к своей цели: `безопасность → безопасн`, но `безопасности → безопасност` (разные `_RU_SUF` под guard ≥4), так что две инфлексии одного слова сами могут не объединиться.

### Эмпирическое подтверждение (воспроизведено)

Прогон `analyze` по двум реальным policy-докам `docs/parallel-work-policy.md` + `docs/commit-stream-policy.md` воспроизводит точную цифру: **307 units, 0 consensus-кластеров при thr 0.4 и 0 при thr 0.3.** Все 307 units помечены divergence, хотя доки покрывают пересекающуюся policy-территорию. (По всем тестированным policy-парам: концептуально-связанные доки коллапсируют в 0 consensus; только пары с дословной фразировкой дают кластеры, напр. orchestration+conveyor = 2.) Ручной синтез и D-023 при этом фиксируют ≥7 реальных согласий — расхождение метода и реальности.

### Слепое пятно замаскировано тестом

`tools/test_doc_consensus.py` проходит лишь потому, что его фикстуры делят *дословные* токены. Фикстуры «консенсус безопасность коммитов commit_lock» и «консенсус безопасность коммитов всегда» (`tools/test_doc_consensus.py:34-38`) токенизируются в `{commit_lock, безопасн, коммит, консенсус}` и `{безопасн, всегд, коммит, консенсус}` — три общих стема, **Jaccard 0.6**, комфортно ≥ 0.4 — поэтому assertion `len(res["consensus"]) == 1` (`:43`) держится. Аналогично `q1.md`/`q2.md` оба буквально содержат «Общий пункт: применять инструкции через evidence gate.» (`:58,60`), consensus утверждается (`:63`) чисто на общих литералах. Тест упражняет лексический overlap, не концептуальное тождество — реальный провал остаётся невидимым. Q-017 предлагает превратить этот gap в регрессионный тест (см. раздел 3).

### Ключевые file:line ссылки

- `tools/doc_consensus.py`: `_stem` `:53-60`, `_RU_SUF/_EN_SUF` `:46-50`, `_norm_tokens` `:63-68`, `_jaccard` `:138-141`, `units` `:80-135`, жадный кластер vs frozen rep `:151-160`, split consensus/divergence `:161-163`, `render` longest-token rep `:181`, `--thr` default 0.4 `:222`.
- `topics/q017-docmerge-semantic-2026-06-23.md:12` — формулировка концептуального gap и эмпирика 307-units/0-consensus; `:46` — резолюция Q-017, что token-Jaccard не ловит концептуальный cross-agent консенсус.
- `tools/test_doc_consensus.py:34-38,43,58,60,63` — дословно-токенные фикстуры, маскирующие слепое пятно.

## 2. Дизайн семантического гибрида `doc_consensus report --semantic`

Дизайн добавляет opt-in семантическую стадию к `tools/doc_consensus.py`, сохраняя pure-stdlib лексический режим как no-cost default. Он специфицирован в `topics/q017-docmerge-semantic-2026-06-23.md` и переиспользует repo-паттерн «механический extract → agent synthesize». Мотивирующий gap — раздел 1: units сравниваются только по token-overlap, поэтому два агента, утверждающие одну идею разными словами, дают Jaccard ≈ 0 и ошибочно метятся как divergence (эмпирика: 307 units, 0 consensus при thr 0.4/0.3).

### Стадия 0-1 — механический high-thr pre-cluster (stdlib, без изменений ядра)

Reuse `units()` (`tools/doc_consensus.py:80-135`) для извлечения units `{text, tokens, where=file:line, doc}` (front-matter и code-fences пропущены, мусор отброшен через `_append_unit` `:71-77`), затем reuse `analyze()` (`:144-165`), запущенный с **ВЫСОКИМ порогом (~0.65, диапазон 0.6-0.7)** — однострочный конфиг существующего `--thr` (`:222`). Высокий порог сливает только очевидно-идентичные units (парафраз + стемминг). Это даёт две корзины (`topics/q017-docmerge-semantic-2026-06-23.md:16,27`):
- **(a)** high-confidence механические кластеры в ≥2 доках = settled consensus, агенту **НЕ** отправляются;
- **(b)** **резидуум** = одиночки + по одному **представителю** на multi-member кластер (longest-token член, ровно как уже выбирает `render()` через `max(c["members"], key=lambda u: len(u["tokens"]))` `:181`).

Только резидуум + представители идут дальше — это срез стоимости: агент не пересуживает дешёвые очевидные матчи.

### Стадия 2 — `_semantic_pass(residue)` через subprocess-агента (новая, за `--semantic`)

Новая `_semantic_pass(residue)` сериализует резидуум в компактный JSON (на unit: `id, doc, where, text`) и shell-out к агенту-синтезатору **тем же `subprocess` + `json.loads` паттерном**, которым файл уже зовёт `_topic_files` → `variants.py` (`tools/doc_consensus.py:202-210`) и который использует `synthesis_helper.py:44-52` (`topics/q017-docmerge-semantic-2026-06-23.md:17,29`). `tools/doc_consensus.py:18-22` уже импортирует `subprocess`/`json`, паттерн на месте. Промпт агента: судить **концептуальное тождество** между доками (не лексику) и вернуть **структурный JSON** по фикс-схеме (policy: суб-агенты возвращают JSON, не прозу):
- **consensus GROUPS** — списки unit-id, выражающих одну идею, каждый с `rationale` («почему это одна идея»);
- **DIVERGENCES** — детализированные в **D-017 sub-points**: claim / какой док / почему стоит особняком / что разрешит спор.

Резидуум бьётся на батчи ~40-60 units/вызов, группы объединяются **union по общему unit-id** между батчами — это bound стоимости (`topics/q017-docmerge-semantic-2026-06-23.md:17,29`).

### Стадия 3 — `_merge` (транзитивный union по unit-id)

Новая `_merge(mechanical_clusters, semantic_groups)`: механические high-confidence кластеры приняты как есть; семантические группы сливаются **по unit-id** — если семантическая группа ссылается на представителя механического кластера, **весь кластер транзитивно вливается в группу** (`topics/q017-docmerge-semantic-2026-06-23.md:18,31`). Итог: один consensus-набор, где членство = union механических + семантических связей, и каждый consensus-пункт несёт **оба свидетельства** — дешёвый Jaccard-overlap **и** семантический rationale агента, плюс `file:line` cross-refs. Что агент не сгруппировал и не пометил — остаётся divergence.

### Выход — `render()` расширен, `status: proposed`, never auto-accepted

`render()` (`tools/doc_consensus.py:168-199`) расширяется по D-017 + конвенциям `synthesis_helper` (`topics/q017-docmerge-semantic-2026-06-23.md:19,33`):
- **Consensus-секция**: на идею — текст представителя, «встречается в N док.» с `file:line` cross-refs всех членов (как сегодня `:183-184`), **плюс** строка «почему это одна идея» с rationale агента (пусто / «(механический матч)» для кластеров без агента) — кандидаты в mainline.
- **Divergences**: сгруппированы по доку как сейчас (`:186-198`), но каждый уникальный unit развёрнут в D-017 sub-points (claim · док(и) · причина · что разрешит).
- **Provenance**: front-matter `status: proposed`, список source-доков и какой агент гнал семантику, явная пометка что **ничего не auto-accepted** — инструмент готовит материал, «котёл» решает (правило synthesis_helper / D-018).

### Scope, карта reuse и buildability

Default остаётся pure-stdlib no-cost; семантика opt-in и scoped из-за стоимости LLM-вызовов — без внешних ML/embeddings, только stdlib + subprocess-агент. Effort **M**, трогает `tools/doc_consensus.py`, `tools/test_doc_consensus.py`, `docs/workflow-orchestration-policy.md`. Reuse-якоря (`topics/q017-docmerge-semantic-2026-06-23.md:42`): `units()` (`doc_consensus.py:80-135`); `analyze()` + `--thr` (`:144-165,222`); longest-token представитель в `render()` (`:181`); subprocess + `json.loads` agent-call паттерн (`_topic_files` `:202-210`, `synthesis_helper.py:44-52`); `status: proposed` / D-018 double-recheck стойка (`synthesis_helper.py:99-142`); D-017 контракт consensus→mainline / divergence→sub-points (`decisions/D-017.md:25-30`); policy Map→Synthesize, суб-агенты возвращают JSON, agent-вывод non-canon до extract (`docs/workflow-orchestration-policy.md:25-27,61-74,120-121`).

## 3. Условия приёмки и cost-bounding для `--semantic`

Q-017's `--semantic` — **proposed** направление (`topics/q017-docmerge-semantic-2026-06-23.md:6`), ещё не реализованное в `tools/doc_consensus.py`. Критерии приёмки и cost-bounds ниже — это design-обязательства, записанные в теме, к исполнению при приземлении buildable.

### Обязательная fixture «одна идея — разные слова» (gate приёмки)

Жёсткое условие приёмки — регрессионная fixture, которую текущий лексический режим **доказуемо проваливает**, а `--semantic` обязан поймать. Тема формулирует это дважды как binding-требование:
- «Обязательное условие приёмки: добавить fixture 'одна идея — разные слова', которую текущий лексический режим доказуемо проваливает … а `--semantic` ловит» (`topics/q017-docmerge-semantic-2026-06-23.md:46`).
- «Новый test-fixture 'одна идея — разные слова', который текущий лексический режим ПРОВАЛЯЕТ, а `--semantic` ловит — превращает слепое пятно в регрессионный тест» (`:39`; также `:21`).

Почему лексический режим её провалит (заземлено в коде): units сравниваются **только по token-overlap** (`_norm_tokens` `:63-68`, `_jaccard` `:138-141`, жадная кластеризация против frozen rep при Jaccard ≥ thr `:144-165`); `_stem` (`:53-60`) складывает лишь инфлексии *одного* слова, не синонимы/парафраз; эмпирика на двух policy-доках — 307 пунктов, **0 consensus при thr 0.4 и 0.3**, тогда как ручной синтез / D-023 фиксируют ≥7 реальных согласий (`:12`, `:46`). Существующий тест маскирует это: фикстуры проходят только из-за дословных фраз (`test_doc_consensus.py:34,37,58,60`, consensus `:43,63`); парафраз-кейса пока нет.

### Батчинг ~40-60 units/call с union по unit-id (cost bound)

`--semantic` не шлёт всё агенту. Два рычага стоимости:
1. **High-thr механический pre-cluster** (~0.65, существующий `--thr`) settl-ит очевидные матчи, оставляя агенту только **резидуум** (одиночки + по одному longest-token представителю на multi-member кластер) — «срез стоимости, агент не пересуживает очевидное» (`topics/q017-docmerge-semantic-2026-06-23.md:16,27`; reuse `units()` `:80-135`, `analyze()`+`--thr` `:144-165,222`, longest-token rep `:181`).
2. **Батчи** резидуума ~40-60 пунктов/вызов; consensus-группы, пересекающие батчи, сливаются **union по общему unit-id**; `_merge` делает транзитивный union механики + семантики по unit-id (`:17,18,29,31,39`).

### Opt-in `--semantic` держит pure-stdlib default no-cost

Семантический pass за флагом; лексический режим остаётся cost-free default. Подтверждено многократно: «Семантический agent-pass (новый, за флагом `--semantic`; pure-stdlib режим остаётся no-cost default)» (`:17`); «чистый no-cost механический режим остаётся default» (`:29`); «Default остаётся pure-stdlib no-cost; семантика опциональна и scoped из-за стоимости LLM-вызовов» (`:46`). Без внешних ML/embeddings — «только stdlib + subprocess-agent-вызов (тот же паттерн, что variants.py/synthesis_helper)» (`:23,46`); агент зовётся тем же `subprocess` + `json.loads`, что `_topic_files` → `variants.py` (`doc_consensus.py:202-210`) и `synthesis_helper.py:44-52`.

### Never auto-accepted (D-017 / D-018 — котёл решает)

Merge-отчёт — материал, не вердикт. Тема: выход `status: proposed`, «ничего не auto-accepted — котёл решает (D-018)» (`:19,33,39,46`). Заземлено в самих решениях:
- **D-017** (`decisions/D-017.md`, `status: accepted`) задаёт fork-and-synthesize контракт, которому следует отчёт: консенсус-пункты → в очередь реализации, спорные → на доказательное обсуждение как sub-points (`D-017.md:26-29`); снимать вопрос «потому что кто-то уже делает» запрещено до синтеза (`:29`).
- **D-018** (`decisions/D-018.md`, `status: accepted`) — правило котла: агент не утверждает спорное соло, приносит форк (D-017), обоснование и двойную перепроверку (техническую + гуманитарную); promotion в `accepted` — результат коллективного синтеза, `proposed` держится до консенсуса (`D-018.md:28-30`); существенные изменения идут через котёл `pipeline.py` (`:20-22`).

### Сводка контракта приёмки/стоимости

| Измерение | Обязательство | Источник |
|---|---|---|
| Gate приёмки | fixture «одна идея, разные слова»; лексика доказуемо валит (0 consensus на 307 пт @ thr 0.4/0.3), `--semantic` ловит | `q017-...md:12,21,39,46` |
| Текущее слепое пятно | существующие тесты проходят лишь через дословные общие фразы | `q017-...md:12`; `test_doc_consensus.py:34,37,58,60` |
| Cost bound | high-thr механический pre-cluster (~0.65) → агенту только резидуум/представители; батчи ~40-60 units/call; union по unit-id | `q017-...md:16,17,27,29` |
| Default cost | opt-in `--semantic`; pure-stdlib режим — no-cost default; без ML/embeddings, только subprocess-агент | `q017-...md:17,23,29,39,46`; `doc_consensus.py:202-210` |
| No auto-accept | `status: proposed`, ничего не auto-accepted — котёл решает | `q017-...md:19,33,39,46`; `D-017.md:26-29`; `D-018.md:28-30` |

## Порядок сборки (build order)

1. **Стадия 0-1** (stdlib, без изменений ядра): сконфигурировать `analyze()` на ВЫСОКИЙ `--thr` (~0.65) для механического pre-cluster; выделить резидуум (одиночки + longest-token представители) — раздел 2. 2. **`_semantic_pass(residue)`** за флагом `--semantic`: сериализация в JSON, subprocess-агент тем же паттерном что `variants.py`, батчи ~40-60 units, union по unit-id, структурный JSON (consensus GROUPS + rationale; DIVERGENCES в D-017 sub-points). 3. **`_merge`**: транзитивный union механики + семантики по unit-id, оба свидетельства на пункт. 4. **`render()` расширить**: consensus c Jaccard-evidence + rationale + `file:line`, divergences в D-017 sub-points, front-matter `status: proposed`, never auto-accepted. 5. **Регрессионный gate**: добавить в `tools/test_doc_consensus.py` fixture «одна идея — разные слова», которую лексический режим проваливает, а `--semantic` ловит. 6. **Зафиксировать** opt-in/scoped природу семантики в `docs/workflow-orchestration-policy.md`. Файлы: `tools/doc_consensus.py`, `tools/test_doc_consensus.py`, `docs/workflow-orchestration-policy.md`. Default остаётся pure-stdlib no-cost; отчёт идёт `status: proposed` в котёл (D-017/D-018), ничего не auto-accepted.
