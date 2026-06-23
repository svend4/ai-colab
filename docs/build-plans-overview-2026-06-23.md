---
id: build-plans-overview-2026-06-23
type: doc
status: proposed
date: 2026-06-23
related: [q017-semantic-consolidated-2026-06-23, pyramid-grounding-consolidated-2026-06-23, build-specs-2026-06-23]
---

# Build-plans overview (2026-06-23)

Этот документ — L2-сведение трёх ратифицированных-к-сборке планов в один обзор с единой
таблицей порядка сборки. Источники — три condensed-артефакта одной сессии:

- **Q-017 — semantic** (`темы/q017-semantic-consolidated-2026-06-23.md`): семантический гибрид
  для слияния документации в `tools/doc_consensus.py`.
- **Pyramid grounding** (`темы/pyramid-grounding-consolidated-2026-06-23.md`): честное
  scan-derived покрытие L2→L1 (`derive_reuse`) + наполнение реальными порталами.
- **Build-specs** (`темы/build-specs-2026-06-23.md`): три symbol-anchored, строго аддитивных,
  advisory edit-спеки, готовые в worktree без повторной разведки.

**Общая позиция всех трёх планов.** Аддитивно, advisory/non-blocking, symbol-anchored,
read-only by construction. Никто не утверждается соло: каждый отчёт остаётся `status: proposed`,
ратификация — через котёл по D-017 (`decisions/D-017.md:26-29`, fork-and-synthesize) и D-018
(`decisions/D-018.md:28-30`, коллективное принятие + двойная перепроверка). `permissions.py` для
governance-правок = signal-not-block; человек промоутит по D-006. Котёл по этим материалам уже
отрабатывал в T-136 / T-137 (обе `done`, governance закрыт D-021) — это прецедент режима «ratify».

**Легенда таблицы.** `mode` — режим выкатки: `worktree` (изолированная ветка/дерево, аддитивно),
`inline` (мелкая правка в общем дереве), `ratify` (применять ТОЛЬКО после ратификации котлом),
`optional` (не обязателен для целевого результата). `spec` — где лежит подробная привязка к
символам/строкам.

---

## План 1 — Q-017: semantic hybrid для `doc_consensus`

**Что строим.** Opt-in стадию `--semantic`, наслоённую на `tools/doc_consensus.py`. Чистый
лексический режим (stdlib) остаётся no-cost дефолтом. Эффорт M. Сейчас НЕ реализовано: `main()`
(`tools/doc_consensus.py:217-245`) парсит только `report/--thr/--out/--files/--topic`; флага
`--semantic` и функций `_semantic_pass`/`_merge` на диске нет (подтверждено grep'ом — 0 совпадений).

**Зачем.** Token-set Jaccard (`_norm_tokens:63-68`, `_jaccard:138-141`, `_stem:53-60`) слеп к
парафразу/синонимам — эмпирически 307 units / 0 consensus при thr 0.4 и 0.3 на двух policy-доках
против ≥7 реальных согласий (D-023). Без внешнего ML/embeddings — только stdlib + subprocess-агент
(тот же паттерн, что `variants.py` / `synthesis_helper.py`).

**Buildables.**

1. **Stage 0-1 — механический high-thr pre-cluster** [worktree]: гоним существующий `analyze()`
   (`:144-165`) при HIGH `--thr` ~0.65 (диапазон 0.6-0.7) через имеющийся `--thr` (`:222`),
   переиспользуя `units()` (`:80-135`). Даёт (a) high-confidence кластеры в ≥2 доках = settled
   consensus (агенту НЕ шлём) и (b) residue = синглтоны + один longest-token представитель на
   мульти-кластер (тот же `max(c["members"], key=len tokens)`, что в `render()` `:181`). Вперёд
   идёт только residue+reps — это и есть cost-slice.
2. **`_semantic_pass(residue)` — NEW, за флагом `--semantic`** [worktree]: сериализуем residue в
   компактный JSON (на unit: `id, doc, where, text`), shell-out к агенту-синтезатору тем же
   `subprocess`+`json.loads` паттерном, что `_topic_files`→`variants.py` (`:202-210`) и
   `synthesis_helper.py:44-52`. Агент судит КОНЦЕПТУАЛЬНУю идентичность (не лексику), возвращает
   structured JSON по фиксированной схеме: GROUPS (списки unit-id + `rationale`) и DIVERGENCES
   (D-017 sub-points: claim / в каком доке / почему standalone / что разрешает). Батч ~40-60
   units/вызов; кросс-батч группы мерджим объединением по общему unit-id (cost bound).
3. **`_merge(mechanical_clusters, semantic_groups)` — NEW** [worktree]: механические high-confidence
   кластеры принимаются как есть; семантические группы мерджатся по unit-id ТРАНЗИТИВНЫМ
   объединением — если семантическая группа ссылается на представитель механического кластера,
   складывается весь кластер. Каждый consensus-item несёт ОБА доказательства (Jaccard overlap +
   agent rationale) плюс `file:line` cross-refs; не сгруппированное = divergence.
4. **Расширить `render()` (`:168-199`)** [worktree]: consensus-секция = текст представителя +
   «встречается в N док.» с `file:line` cross-refs (как `:183-184`) ПЛЮС строка agent-rationale
   «почему это одна идея» (пусто/«(механический матч)» для безагентных кластеров); divergences по
   докам (как `:186-198`) разворачиваются в D-017 sub-points; provenance front-matter
   `status: proposed` + source-доки + какой агент гонял семантику + явное «nothing auto-accepted».
5. **Regression gate** [ratify, mandatory]: добавить fixture «одна идея — разные слова» в
   `tools/test_doc_consensus.py`, который лексический режим ДОКАЗУЕМО проваливает, а `--semantic`
   ловит — слепое пятно превращается в regression-тест. Текущие тесты проходят только на verbatim
   общих фразах (`test_doc_consensus.py:34,37,58,60`, consensus `:43,63`).
6. **Документировать opt-in/scoped природу** [worktree] в `docs/workflow-orchestration-policy.md`
   (Map→Synthesize, sub-агенты возвращают JSON, вывод агента не-canon до extract —
   `:25-27,61-74,120-121`).

**Файлы.** `tools/doc_consensus.py`, `tools/test_doc_consensus.py`,
`docs/workflow-orchestration-policy.md`.

**Ограничения.** Дефолт — pure-stdlib no-cost; `--semantic` opt-in/scoped из-за стоимости
LLM-вызова; cost ограничен high-thr pre-cluster + батчами ~40-60 units + union по unit-id; отчёт
всегда `status: proposed`, ратифицируется котлом, никогда не auto-accepted.

---

## План 2 — Pyramid grounding: scan-derived покрытие L2→L1 + реальные порталы

**Что строим.** Замену self-declaration честным, existence-checked, scan-derived покрытием
(`derive_reuse`) ПЛЮС наполнение реальных L2-порталов, чтобы поднять счётчик `порталов`. Принцип —
«Честная нерешённость»: открыто показываем нерешённый orphan-L1, а не фабрикуем `reused_in`.

**Зачем.** Текущий `reused_in`-чек сломан: писателей поля в репозитории ноль (читается только в
`promote.py:140` и `assurance.py:267`), а L1 объявлял переиспользование сам про себя. Заменяем на
измеряемое сканом число различных порталов.

**Buildables.**

- **`derive_reuse` primitive** [worktree, M]: добавить `derive_reuse(root)` в `tools/promote.py`
  рядом с `_list_field`: собрать L1-инвентарь из engine-manifest `files:` + `core/*.md`
  (token = basename), сканировать каждый `portals/*/portal.md` `l1_basis` + тела каталог-markdown
  по basename-substring (тот же concat/substring, что `assurance._portal_text`), вернуть
  `token -> set(portal-ids)`. Refs: `pyramid-grounding-plan-2026-06-23.md:44-48,66-72`.
- **Переписать `_gate_L2_L1` (`tools/promote.py:139-149,201-217`)** [worktree]: заменить сломанный
  `reused_in`-чек на distinct-portal count через `derive_reuse`, пропуск при `>= 2`, с override по
  decision-ref `D-018` (ратифицированный явный список тоже проходит). Штамповать **вычисленный**
  `reused_in` как scan-provenance в `_stamp_fm`.
- **Производный `section_coverage` в `tools/assurance.py:240-274`** [worktree]: итерировать
  orphan-L1 по манифест `files:` ТОЛЬКО, не по `candidates:` (`:245`); заменить any-non-empty
  grounding-чек (`:267`) на derived: grounded только если basename из `l1_basis` резолвится в
  инвентаре или встречается как basename-substring в телах порталов (`:248-253`). Эмитить **`high`**
  finding на любой неразрешённый `l1_basis` (stale/typo L1 basis).
- **Разделить `core/engine-manifest.md` `files:`/`candidates:`** [worktree]: сузить `files:` с 10 до
  8 портируемых engine-tools (`_canon, validate, generate, next_id, commit_lock, pipeline,
  dispatch, merge_gate`); добавить `candidates: [tools/knowledge.py, tools/text_extract.py]`;
  тест-файлы держать вне reuse-grading. `knowledge.py` сознательно остаётся ВНЕ `files:` — это
  настоящий L2-reused артефакт. Refs: `pyramid-grounding-plan-2026-06-23.md:26-30,62-64`.
- **Структурный `l1_basis` в `portals/example/portal.md`** [worktree]: добавить однострочный
  `l1_basis: [tools/knowledge.py, tools/text_extract.py]` (оба на диске); freeform `core:` прозу
  (`portal.md:7`) оставить, но `l1_basis` сделать machine-checkable каналом, парсимым `_list_field`.
- **Supporting edits** [worktree]: переформулировать `docs/promotion-rules.md:52`, чтобы
  `reuse_across_portals` читался как *derived* (измеряется `derive_reuse`, override разрешён,
  намеренно недостижим до второго портала); расширить `tools/test_assurance.py` `_build_pyramid`,
  чтобы запинить новые контракты (structural grounding без прозы, stale-basis high finding,
  исключение candidate, flip гейта 1-vs-2 портала).
- **Portal 1 — `bridge-knowledge`** [inline/worktree, S]: чистый L2-портал над существующим
  `data/knowledge-corpus/` (8 файлов), ноль новых данных/кода. Навести `corpus_ref:` на него
  (`tools/portal.py:71`); переиспользовать `knowledge.py` через `portal.py` (`build()`:119,
  `report()`:123-138). Счётчик 1→2. Ref: `fleet-designs-2026-06-23.md:37-44`.
- **Portal 2 — `repo-inventory`** [worktree, M]: read-only repo-inventory портал, единственный
  кандидат с готовым дизайном (`tasks/T-024.md`, status done, без run/test). Заголовочный
  driver-reuse: композит двух готовых read-only драйверов помимо `files:` — `repo-runner`
  (`drivers/index.json:70`) + `git-log` (`drivers/index.json:59`). **Поправка плана:** у `git-log`
  НЕТ `fixture-report.json` (существует только `drivers/repo-runner/fixture-report.json`) — seed
  repo-runner из его fixture, seed git-log запуском его read-only `git_log.py`. Счётчик 2→3.
  Ref: `fleet-designs-2026-06-23.md:47`, `docs/pyramid-candidate-map.md:47-48`.
- **Portal 3 — `app-data`** [worktree, M, optional]: read-only SQLite-портал, гоняющий `sqlite`
  драйвер (`drivers/index.json:81`, `drivers/sqlite/`); `corpus_ref` = sample read-only `.db`, без
  живых данных. Доводит `порталов = 3`. Ref: `fleet-designs-2026-06-23.md:48`.
- **Честный orphan-L1** [ratify/document, не код]: план НЕ заявляет, что orphan-L1 падает в ноль —
  12 orphans это kernel coordination primitives (`commit_lock.py`, `merge_gate.py`), которые
  data-корпуса легитимно не цитируют. Порталы поднимают счётчик, но не сбрасывают orphan-12; именно
  split `files:`/`candidates:` легитимно ретайрит orphans. L1 остаётся `proposed`, гейтован на Q2
  (open) + `D-018` (коллективная ратификация). Refs: `fleet-designs-2026-06-23.md:50-55`,
  `decisions/D-018.md`.

**Ограничения.** Всё stdlib, root-hermetic, переиспользует
`_list_field`/`parse_front_matter`/`_portal_text`/`_stamp_fm`.

---

## План 3 — Build-specs: три symbol-anchored advisory спеки

**Что строим.** Три symbol-anchored, строго аддитивных, advisory/non-blocking edit-спеки из
`темы/build-specs-2026-06-23.md`, готовые к передаче в worktree без повторной разведки.

### S1 — Подключить `assurance.py` в апекс `top.py` [worktree / Codex-hot]

Пять аддитивных, symbol-anchored правок в `tools/top.py` (co-owned файл; строки — только для
ориентира). Advisory-only, эксплуатирует exit-контракт `assurance.py`:
`return 1 if (strict and hard > 0) else 0` (`tools/assurance.py:382`):

- **`_BUTTONS`** (после финального `work-mode` dict, перед закрывающим `]` ~206): добавить
  button-row dict `id:"assurance"`, `audience:"both"`, `effect:"read-only"`, cmd
  `python tools/top.py assurance [section] [--json] [--strict] [--max-age N]`; хвостовая запятая.
- **`cmd_assurance`** (NEW handler, после `cmd_friction` ~284): shell к `assurance.py` через
  `_tool`+`_run`, форма как `cmd_friction`; ключ `fail_ok=not args.strict` (advisory по умолчанию).
- **`build_parser`** (NEW subparser, после блока `friction` ~497, перед `health`):
  `add_parser("assurance", ...)` с позиционным `section choices=[applied,currency,coverage,flow,all]`,
  `--json/--strict/--max-age(int)`, `set_defaults(func=cmd_assurance)`.
- **`cmd_health`** (между `drift check` `_run`:298 и `return rc`:299): одна warning-строка
  `_run("assurance (warning layer)", _tool("assurance.py","all"), timeout=90, fail_ok=True)`, без
  `--strict`; список checks не трогаем.
- **`cmd_agent_start`** (между `top status`:304 и `if args.context:`:305): одна advisory
  `_run("assurance (advisory)", ..., timeout=90, fail_ok=True)`; onboard `rc` без изменений.

### S2 — Вплести governance-решения в инструкции (D-008/D-004/D-009/D-002) [ratify — применять ТОЛЬКО после ратификации по D-006/D-018]

Восемь вставок в три файла; каждая вставка дописывается/инлайнится рядом с exact-match anchor,
без rewrites/deletes:

- **`AGENTS.md`** (3): D-008 после novax-строки реестра, кончающейся «…правки служебных файлов — с
  обоснованием по D-003» (`AGENTS.md:26-27`); D-009 после «Автоматический агент может добавлять
  решения со статусом `proposed`…»; D-002 inline `<!-- -->` на «Для больших тем писать отдельные
  сообщения в `темы/<topic>/messages/`.»
- **`PROTOCOL.md`** (3): D-008 конец §7 после абзаца «видимый след» (`PROTOCOL.md:133,161`); D-004 в
  §8 рядом с «Правило D-006:» (`PROTOCOL.md:173`, template `templates/decision-options.md`); D-002
  inline на «Правило: **одно сообщение = один файл**.» (`PROTOCOL.md:42`).
- **`docs/agent-onboarding.md`** (1): D-009 после §2 «Граница (важно)» абзаца «агент **предлагает**
  решения…» (`docs/agent-onboarding.md:94`).

Safety: `permissions.py` помечает new-agent governance-правки как signal-not-block; решения остаются
`proposed` (человек промоутит по D-006). Anchors из `governance-proposals-2026-06-23.md`,
перепроверены на диске.

### S3 — Усилить `check-report`: advisory reference verification [worktree / inline — non-gating]

Всё в `tools/instructions.py`. `check_report_text()` (`tools/instructions.py:369-382`) НЕ ТРОГАТЬ —
это hard-сигнал на `tools/assurance.py:137`, `:148`, `tools/pipeline.py:343`, а тесты пинят его
returns (`tools/test_instructions.py:71-77`). Шаги:

1. Добавить `import re` (сейчас :14-18).
2. NEW advisory `report_reference_findings(text, root=ROOT) -> list[str]`: извлечь backticked +
   bare path-кандидаты (repo-расширения `.md/.py/.json/.txt/.ps1/.ya?ml`, `dir/...`), отфильтровать
   (есть `/` или известный ext, не URL/absolute/`..`, `^[\w./-]+$`), де-дуп, нормализовать `\`→`/`,
   `os.path.exists` → `"referenced path not found: <ref>"` (cap ~20); извлечь `Checks:` команды,
   флагать только no-runner-prefix → `"checks command not runnable-shape"` и отсутствующий
   `python tools/<x>.py` скрипт → `"checks command references missing script"`. Read-only, ничего не
   исполняется.
3. Подключить в `cmd_check_report` (:404-417) ТОЛЬКО: `missing`/MISSING/OK/rc 1/0 без изменений;
   добавить `advisories = report_reference_findings(text)`, печатать как `ADVISORY:` блок; rc по-
   прежнему по токену `missing`. Опциональный будущий `--strict` (default off).

Тесты: расширить main в `tools/test_instructions.py` (existing-doc → `[]`; `does-not-exist.md` →
«referenced path not found»; checks-command кейсы; регрессия :71-77 без изменений). Docs:
`docs/instruction-assurance.md:100` пометить item-2 implemented/advisory;
`docs/top-layer-command-groups.md:139` отметить advisory findings.

---

## Единая таблица порядка сборки

| # | Buildable | mode | spec |
|---|-----------|------|------|
| **Q-017 — semantic** ||||
| 1 | Stage 0-1 механический high-thr pre-cluster (`doc_consensus.analyze` @ thr ~0.65) | worktree | `q017-semantic-consolidated-2026-06-23.md` · `tools/doc_consensus.py:144-165,222` |
| 2 | `_semantic_pass(residue)` NEW за `--semantic` (subprocess-агент, JSON-схема, батчи 40-60) | worktree | `tools/doc_consensus.py:202-210`; `synthesis_helper.py:44-52` |
| 3 | `_merge(mechanical, semantic)` NEW — транзитивное объединение по unit-id | worktree | `q017-semantic-consolidated-2026-06-23.md` |
| 4 | Расширить `render()` — cross-refs + rationale + provenance `status: proposed` | worktree | `tools/doc_consensus.py:168-199` |
| 5 | Regression fixture «одна идея — разные слова» (lexical fails, semantic ловит) | ratify | `tools/test_doc_consensus.py:34,37,58,60,43,63` |
| 6 | Документировать opt-in/scoped природу | worktree | `docs/workflow-orchestration-policy.md:25-27,61-74,120-121` |
| **Pyramid grounding** ||||
| 7 | Portal 1 `bridge-knowledge` (over `data/knowledge-corpus/`, счётчик 1→2) | inline/worktree (S) | `fleet-designs-2026-06-23.md:37-44`; `tools/portal.py:71,119,123-138` |
| 8 | `derive_reuse(root)` primitive в `tools/promote.py` | worktree (M) | `pyramid-grounding-consolidated-2026-06-23.md`; `pyramid-grounding-plan-2026-06-23.md:44-48,66-72` |
| 9 | Переписать `_gate_L2_L1` → distinct-portal count, pass `>=2`, D-018 override | worktree | `tools/promote.py:139-149,201-217` |
| 10 | Производный `section_coverage` + `high` finding на stale `l1_basis` | worktree | `tools/assurance.py:240-274` |
| 11 | Split `engine-manifest` `files:` (10→8) + `candidates:` | worktree | `pyramid-grounding-plan-2026-06-23.md:26-30,62-64` |
| 12 | Структурный `l1_basis` в `portals/example/portal.md` | worktree | `portals/example/portal.md:7` |
| 13 | Supporting: `promotion-rules.md:52` derived-формулировка + `test_assurance` контракты | worktree | `docs/promotion-rules.md:52`; `tools/test_assurance.py` |
| 14 | Portal 2 `repo-inventory` (repo-runner + git-log, счётчик 2→3; git-log без fixture) | worktree (M) | `fleet-designs-2026-06-23.md:47`; `docs/pyramid-candidate-map.md:47-48`; `tasks/T-024.md` |
| 15 | Portal 3 `app-data` (read-only SQLite, `порталов=3`) | worktree (M, optional) | `fleet-designs-2026-06-23.md:48`; `drivers/index.json:81` |
| 16 | Честный orphan-L1 (документировать, не код; L1 остаётся `proposed`) | ratify/document | `fleet-designs-2026-06-23.md:50-55`; `decisions/D-018.md` |
| **Build-specs** ||||
| 17 | S1 — подключить `assurance.py` в `top.py` (5 аддитивных правок, advisory) | worktree / Codex-hot | `build-specs-2026-06-23.md` §S1; `tools/top.py:~206,~284,~497,298-299,304-305`; `tools/assurance.py:382` |
| 18 | S2 — вплести D-008/D-004/D-009/D-002 в инструкции (8 вставок) | ratify (D-006/D-018) | `build-specs-2026-06-23.md` §S2; `AGENTS.md:26-27`; `PROTOCOL.md:42,133,161,173`; `docs/agent-onboarding.md:94` |
| 19 | S3 — `report_reference_findings()` + `ADVISORY:` блок в `cmd_check_report` | worktree / inline | `build-specs-2026-06-23.md` §S3; `tools/instructions.py:404-417` (НЕ трогать `:369-382`) |

**Сквозная нота.** Все 19 buildables аддитивны, advisory/non-blocking, symbol-anchored,
read-only by construction. `worktree`/`inline` пункты строятся изолированно; `ratify` пункты
(5, 16, 18) и любой переход отчёта в `accepted` идут через котёл по D-017 + D-018 — nothing
auto-accepted, `proposed` держится до коллективного консенсуса и двойной (технической +
гуманитарной) перепроверки.
</doc_content>
</invoke>
