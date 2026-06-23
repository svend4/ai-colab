---
id: pyramid-grounding-consolidated-2026-06-23
type: topic
title: Заземление пирамиды (L2→L1) — consolidated plan (derive_reuse + наполнение порталов)
status: proposed
date: 2026-06-23
related: [Q-016, D-016, D-018, pyramid-grounding-plan-2026-06-23, fleet-designs-2026-06-23, promotion-rules, pyramid-candidate-map]
---

# Заземление пирамиды (L2→L1) — consolidated plan

Это сводный канон-документ двух согласованных дизайнов (оба `proposed`): механики **`derive_reuse`** — derived L2→L1 coverage вместо самодекларации (`темы/pyramid-grounding-plan-2026-06-23.md`) — и **наполнения L2-порталов** реальными порталами, которые эту coverage поднимают (`темы/fleet-designs-2026-06-23.md:37-55`). Обе карты сходятся на одном корне: сегодня «grounding» проходит по двум слабым каналам (over-broad манифест с одной стороны и freeform-проза `core:` с другой), структурного ребра L2→L1 нет, а портал ровно один (`portals/example`). Чинится так, чтобы покрытие шло по реальным ссылкам, проверяемым на существование, и чтобы счётчик `порталов` рос за счёт настоящего переиспользования драйверов сверх `files`.

Ключевой принцип обоих дизайнов — **«Честная нерешённость»**: неразрешённая часть (orphan-L1) поверхностно вскрыта, а не замаскирована фабрикацией поля `reused_in`. См. раздел «Честная область orphan-L1».

## `derive_reuse` — derived L2→L1 coverage

`derive_reuse` — единственный shared-примитив, заменяющий самодекларацию пирамидного grounding на **existence-checked, scan-derived coverage**. Это load-bearing часть L2→L1 плана (`pyramid-grounding-plan-2026-06-23.md:20`, build-гайд `:66-72`), питаемая флот-дизайном, который строит измеряемые ею порталы (`fleet-designs-2026-06-23.md:37-55`).

### Что меняется

**1. `tools/promote.py` — новый `derive_reuse(root)` + переписанный `_gate_L2_L1`** (`pyramid-grounding-plan-2026-06-23.md:44-48`)
- Добавить `derive_reuse(root)` рядом с `_list_field`: построить L1-инвентарь из engine-manifest `files:` + `core/*.md` (token = basename); для каждого `portals/*/portal.md` собрать его список `l1_basis` плюс markdown-тела каталога портала, отметить token reused-by-portal по basename-substring (тот же concat/substring-механизм, что в `assurance._portal_text`) и вернуть `token -> set(portal-ids)`.
- Текущий гейт — это и есть чинимая проблема: `tools/promote.py:140-143` читает `reused = _list_field(fm.get("reused_in"))` и пропускает `reuse_across_portals` при `len(reused) >= 2`. У `reused_in` **ноль writer-ов** во всём репозитории (читается только в `promote.py:140` и `assurance.py:267`, документируется в `docs/promotion-rules.md:52`), значит критерий сегодня непроходим, а правка поля руками могла бы его подделать.
- Переписать `_gate_L2_L1` (`promote.py:139-149`): считать **distinct-порталы**, ссылающиеся на basename артефакта через `derive_reuse`, пропуск при `>= 2`, с `D-018` decision-ref override (ратифицированный явный список тоже проходит). В пути `move()`/`_stamp_fm` штамповать **вычисленный** `reused_in` во front-matter как scan-provenance, а не авторскую заявку (`_stamp_fm` на `promote.py:201-217` уже пишет computed-поля).

**2. `tools/assurance.py` — derived `section_coverage`** (`pyramid-grounding-plan-2026-06-23.md:38-42`)
- В `section_coverage` итерировать orphan-L1 по manifest `files:` **только**, не по `candidates:`, чтобы инструменты второго экспорта перестали давать шум. Сейчас итерируется весь `files:`: `assurance.py:245` читает `pr._list_field(mfm.get("files"))`, а `:250-253` флагает любой basename, отсутствующий в тексте портала — источник всех 12 orphan-L1 находок.
- Заменить any-non-empty grounding-проверку на `assurance.py:267` (`grounded = any((fm.get(k) or "").strip() for k in ("l1_basis", "reused_in", "core"))`) на derived-проверку: построить L1-инвентарь, распарсить `l1_basis` портала через `pr._list_field` и пометить grounded **только если** хотя бы один basename из `l1_basis` резолвится в элемент инвентаря (или появляется как basename-substring в markdown-телах портала). Для каждой объявленной записи `l1_basis`, чей basename не резолвится ни во что, эмитить **`high`**-находку (`stale/typo L1 basis: <entry> not in core inventory`). Переиспользует точный basename-substring-механизм, уже отгруженный на `assurance.py:248-253` — без нового парсера/индекса.

**3. `core/engine-manifest.md` — split `files:` / `candidates:`** (`pyramid-grounding-plan-2026-06-23.md:26-30`, `:62-64`)
- Сузить `files:` с сегодняшних 10 записей (вкл. 2 тест-файла) до 8-инструментного переносимого engine координации, который и грейдится на reuse: `_canon, validate, generate, next_id, commit_lock, pipeline, dispatch, merge_gate`. Добавить отдельный `candidates: [tools/knowledge.py, tools/text_extract.py]` для SQLite/MCP-связанного второго экспорта. Тест-файлы (`test_commit_lock.py`, `test_merge_gate.py`) остаются вне reuse-grading-набора. `promote.py` читает `files:` для core-export (`pyramid-grounding-plan-2026-06-23.md:30`), поэтому суженный набор должен оставаться чистым экспортируемым списком.
- `knowledge.py` **намеренно не** продвигается в `files:` — это и есть genuinely L2-reused-артефакт; он заземляет L2 через структурный `l1_basis` портала + `derive_reuse`, а не через объявление core.

**4. `portals/example/portal.md` — структурный `l1_basis`** (`pyramid-grounding-plan-2026-06-23.md:32-36`)
- Добавить однострочный bracket-list `l1_basis: [tools/knowledge.py, tools/text_extract.py]` (оба файла существуют на диске; ровно то, что называет `current-state.md:13`). Сохранить freeform `core:`-предложение как человеческую прозу (`portals/example/portal.md:7`), но сделать `l1_basis` machine-checkable-каналом, парсимым `_list_field`. Это превращает prose-grounding в проверяемое ребро к реальным L1-артефактам.

**Поддерживающие правки:** `docs/promotion-rules.md:52` переформулировать так, чтобы `reuse_across_portals` читался как **derived** (измеряется `derive_reuse`, а не самодекларацией, ратифицированный override допускается), плюс заметка, что критерий намеренно недостижим, пока не приземлится 2-й портал. `tools/test_assurance.py` расширяет `_build_pyramid`, чтобы зафиксировать новые контракты (структурный grounding без прозы, stale-basis `high`-находка, исключение candidate, флип гейта 1-vs-2 портала).

## L2 Portal Population Plan — какие 2–3 портала строить

Сегодня ровно один реальный портал: `portals/example` (generic demo). Корень orphan-L1 и низкий счётчик идут из одного факта — `assurance.py:262` считает порталы глоббингом `portals/*/portal.md`, а `assurance.py:272` эмитит метрику `"L1-инвентарь: %d, порталов: %d, orphan-L1: %d"`. Чтобы перевести `порталов` с 1 → 2–3, добавляем реальные `portals/<name>/portal.md`-манифесты, каждый заземлён на L1 и доказывает, что универсальный engine обобщается за пределы 2-файлового demo. Источник: `fleet-designs-2026-06-23.md:37-55`; карта кандидатов: `docs/pyramid-candidate-map.md:42-55`.

### Портал 1 — `bridge-knowledge` (effort S) — обернуть существующий корпус, ноль новых данных

- **Что:** чистый L2-портал поверх **уже существующего** корпуса `data/knowledge-corpus/`. Проверенное содержимое = 8 файлов (`agent-handbook.md`, `corpus-manifest.json`, `glossary.md`, `operations-note.txt`, `pipeline-faq.md`, `README.md`, `risk-register.txt`, `workflow-table.csv`), с готовым отчётом `reports/knowledge-corpus-report.md`. Совпадает с claim «8 файлов» на `fleet-designs-2026-06-23.md:42-44`.
- **Корпус:** новый не нужен. Указать `corpus_ref:` на `data/knowledge-corpus/` (резолюция `_corpus_ref` манифеста — `tools/portal.py:71`).
- **Как строится:** чистое переиспользование `knowledge.py` через `portal.py` — `build()` вызывает `kn.build(db, corpus)` на `tools/portal.py:119`; `report()` регенерирует + FTS-покрывает темы на `tools/portal.py:123-138`. Нового кода нет.
- **Зачем:** доказывает, что L2 обобщается за пределы 2-файлового `example`-корпуса на реальный 8-файловый knowledge-корпус с **нулём** новых данных и без правок engine.

### Портал 2 — `repo-inventory` (effort M) — единственный кандидат с готовым дизайном, переиспользует два не-`files`-драйвера

- **Что:** read-only repo-inventory-портал. Это единственный кандидат с уже готовым buildable-дизайном — `tasks/T-024.md` (status `done`, scope = карта папок / языки / package-файлы / тесты / run-команды / риски / agent summary, явно **без** `run`/`test`) — и слотом в карте кандидатов на `docs/pyramid-candidate-map.md:47-48`.
- **Driver reuse (load-bearing-пункт):** уникально композирует два **ready, read-only** драйвера поверх `knowledge.py` — `repo-runner` (`drivers/index.json:70`, status `ready`) и `git-log` (`drivers/index.json:59`, status `ready`). Оба — реальные driver-каталоги: `drivers/repo-runner/` (`inventory.py`, `mcp_server.py`) и `drivers/git-log/` (`git_log.py`, `mcp_server.py`). Это конкретное доказательство «переиспользования драйверов сверх `files`».
- **Корпус:** seed из driver-фикстур, внешних данных не нужно. **Поправка к плану:** `fleet-designs-2026-06-23.md:47` говорит, что он «сидится из `drivers/*/fixture-report.json`» для обоих драйверов, но существует только `drivers/repo-runner/fixture-report.json` (рядом с `drivers/file-inventory/fixture-report.json`); **у `drivers/git-log/` нет `fixture-report.json`** (проверено). Поэтому seed repo-runner из его fixture-report, а git-log-вывод сидить, прогнав его read-only `git_log.py` по этому репозиторию (или сначала сгенерировав фикстуру) — не предполагать, что git-log-фикстура существует.

### Портал 3 (опционально) — `app-data` (effort M) — задействует драйвер `sqlite`

- **Что:** опциональный третий портал поверх read-only SQLite-источника, чтобы достичь `порталов = 3`.
- **Driver reuse:** задействует драйвер `sqlite` (`drivers/index.json:81`, status `ready`, `drivers/sqlite/sqlite_driver.py` + `mcp_server.py`) — read-only-драйвер, которого `example`-портал не касается. Источник: `fleet-designs-2026-06-23.md:48`.
- **Корпус:** sample read-only `.db` (например, фикстурная SQLite-база) как `corpus_ref`; без live/production-данных.

### Как реально растёт счётчик (1 → 2–3)

- `assurance.py:262` инкрементит `n_portals` один раз на каждый `portals/*/portal.md`. Каждый новый манифест под `portals/` (не только под `data/portals/`) добавляет один, так что метрика на `assurance.py:272` идёт 1 → 2 (bridge-knowledge + repo-inventory) → 3 (с app-data).
- **Каждый манифест должен быть заземлён**, иначе он триггерит high-находку: `assurance.py:267` требует front-matter `l1_basis` / `reused_in` / `core`, или литеральный `core/` в теле. Отгруженный `portals/example/portal.md:7` уже моделирует это (`core: knowledge.py + драйвер files (универсальное ядро L1)`). Новые манифесты должны ставить, например, `core: knowledge.py` плюс `l1_basis:` именующий переиспользуемые драйверы (`repo-runner`, `git-log`, `sqlite`).

## Честная область orphan-L1

План **не** утверждает, что `derive_reuse` + новые порталы обнулят orphan-L1, и флот-дизайн явно объясняет почему (`fleet-designs-2026-06-23.md:50-55`): 12 сирот — это **координационные примитивы ядра** (`commit_lock.py`, `merge_gate.py` из manifest `files:`), и data-корпус законно не имеет причины их цитировать. Поскольку `assurance.py:251-253` credits покрытие только при **буквальном basename-совпадении**, принуждение data-порталов именовать kernel-примитивы было бы фейковым grounding, а не реальным reuse.

Поэтому два механизма честно разведены по разным задачам:
- **Новые data-порталы** поднимают счётчик порталов (`порталов: 1 → 2-3`) и доказывают driver-reuse сверх `files:` — но механически **не** роняют orphan-12.
- **Split манифеста `files:`/`candidates:`** — вот что легитимно ретайрит сирот: сужение `files:` до 8 продемонстрированных инструментов делает orphan-L1 честным значением «обещано-переносимым-но-неиспользуемым», а не инцидентным отсутствием слова (`pyramid-grounding-plan-2026-06-23.md:16,64`).
- Пока не приземлился второй портал, `reuse_across_portals` **намеренно недостижим**, и L1 остаётся `proposed` — задокументировано, а не замаскировано (`pyramid-grounding-plan-2026-06-23.md:22,52`).

Это и есть принцип «Честная нерешённость»: неразрешённая часть вскрыта (сироты закрываются doc/manifest-перекрёстной ссылкой, а не принуждением порталов цитировать внутренности ядра), а не папируется фабрикованным `reused_in`.

## Статус и зависимости

- **Спроектировано / build-гайд готов, не построено.** Оба источника `status: proposed` (`pyramid-grounding-plan-2026-06-23.md:5`, `fleet-designs-2026-06-23.md:5`). План несёт самодостаточную **Buildable**-карточку `derive_reuse … (effort M)` с полным списком файлов (`pyramid-grounding-plan-2026-06-23.md:66-72`).
- **Ожидающее решение:** L1-promotion-статус остаётся `proposed` — гейтится на `Q2` (open) и `D-018` (collective ratification) по `pyramid-grounding-plan-2026-06-23.md:16,22,64`. `D-018` выживает как decision-ref override: derived-by-default, но ратифицированный явный список тоже валиден.
- **Зависит от флот-порталов:** `derive_reuse` флипает `>=2`-гейт только когда существует второй реальный портал; companion-флот-дизайн (`fleet-designs-2026-06-23.md:37-48`) специфицирует `bridge-knowledge` (effort S) и `repo-inventory` (effort M) как эти порталы — тоже `proposed`.

## Build order

1. **`bridge-knowledge` (S)** — быстрейший, ноль данных, чистый `knowledge.py`+`portal.py` reuse → счётчик 1→2.
2. **`derive_reuse` (M)** — `tools/promote.py`, `tools/assurance.py`, `core/engine-manifest.md`, `portals/example/portal.md`, `docs/promotion-rules.md`, `tools/test_assurance.py`; всё stdlib, root-hermetic, переиспользует `_list_field`/`parse_front_matter`/`_portal_text`/`_stamp_fm`. Флипает derived-гейт, как только существует 2-й портал.
3. **`repo-inventory` (M)** — готовый дизайн (`tasks/T-024.md`), переиспользует `repo-runner` + `git-log` → счётчик 2→3 и headline-доказательство driver-reuse (учесть отсутствующую git-log-фикстуру).
4. **`app-data` (M, опционально)** — добавляет драйвер `sqlite` → третья точка данных.

**Ключевые файлы:** `tools/promote.py:139-149,201-217`, `tools/assurance.py:240-274`, `core/engine-manifest.md`, `portals/example/portal.md`, `docs/promotion-rules.md:52`, `tools/test_assurance.py`, `tools/portal.py:113-144`, `tasks/T-024.md`, `drivers/index.json:58-90`, `data/knowledge-corpus/` (8 файлов), `drivers/repo-runner/fixture-report.json`, `docs/pyramid-candidate-map.md:42-55`, `decisions/D-018.md`.
