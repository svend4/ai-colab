---
id: q016-assurance-state-2026-06-23
type: topic
status: proposed
date: 2026-06-23
related: [Q-016, assurance-hardening-plan-2026-06-23]
---

# Q-016 assurance — состояние «построено vs осталось» (2026-06-23)

Канонический срез проверяемости инструкций по вопросу **Q-016**. Один документ — две половины: что уже стоит в репозитории (пять компонентов апекс-слоя проверяемости) и что ещё не сделано (9 открытых пунктов в 4 рабочих режимах). Всё сверено по живому репозиторию `C:/Users/stefan/Documents/New project ai colab` на 2026-06-23. Лестница ужесточения S0→S4 названа в `topics/assurance-hardening-plan-2026-06-23.md`.

## Построено (Q-016 assurance)

Пять компонентов сводят проверяемость инструкций в единый апекс-слой: один READ-ONLY дашборд (`assurance.py`) плюс четыре точки интеграции в существующие инструменты (`pipeline.py`, `validate.py`, `drift_check.py`, `top.py`). Все коммиты — `Max`, 2026-06-23.

### 1. `tools/assurance.py` — апекс-дашборд (4 секции)
Единый READ-ONLY дашборд проверяемости (ничего не мутирует, граница read/observe как у `friction.py`). Переиспользует существующее (`_canon.parse_front_matter`, `pipeline._needs_applied_evidence`, `instructions.check_report_text`/`INSTRUCTIONS`, `promote.level_of`/`_list_field`) — без новых парсеров. По умолчанию advisory (exit 0); `--strict` даёт exit 1 при находках. Вердикт: PASS / WARN (только low/info) / ATTENTION (есть high/medium).

Четыре секции:
- **applied** (`section_applied`, `assurance.py:123`) — applied-evidence: % служебных задач из `queues/done/*.done.md`, закрытых с реальным evidence. Фильтрует через `pl._needs_applied_evidence`, отсекает легаси до конвенции `--applied` (`CONVENTION_MIN = 156`, T-156), ловит пустое/boilerplate/слабое evidence.
- **currency** (`section_currency`, `assurance.py:192`) — актуальность `decisions/D-*.md` + политик: accepted без `last_verified` (info), возраст > `--max-age` (дефолт 180 дн.), ссылки на rejected/superseded решения (HIGH), битые **структурные** ссылки на файлы (HIGH; только front-matter + markdown-линки, не проза — иначе ложные срабатывания на примерах).
- **coverage** (`section_coverage`, `assurance.py:240`) — поток вверх по пирамиде: orphan-L1 (ядро из `core/engine-manifest.md` без ссылок из порталов, medium) и ungrounded-L2 (`portals/*/portal.md` без `l1_basis`/`reused_in`/`core`, HIGH).
- **flow** (`section_flow`, `assurance.py:279`) — база→вершина: существование файлов реестра `instructions.INSTRUCTIONS` (HIGH при отсутствии) + accepted-`D-NNN`, не упомянутые в поверхности инструкций (висячие решения, medium).

Коммит: `9465956` feat: assurance.py — единый read-only апекс-дашборд (Q-016: applied/currency/coverage/flow). Якорный док: `docs/instruction-assurance.md`.

### 2. `pipeline.py done --strict` — applied-evidence done-gate
Opt-in строгий гейт на закрытие служебных задач (`cmd_done`, `pipeline.py:356`). Для задач, где `_needs_applied_evidence(...)` истинно (`pipeline.py:325`), считаются `_evidence_gaps(...)` (`pipeline.py:333`, переиспользует `instructions.check_report_text` + проверку на формальное boilerplate-evidence). Поведение (`pipeline.py:368-376`): при `--strict` и наличии пробелов — **ОТКАЗ** (return 1, задача не закрывается); без флага — мягкий **WARN**, дефолт остаётся не блокирующим (S3 лестницы Q-016). Флаг разбирается в CLI (`pipeline.py:662`, прокидывается в `pipeline.py:675`).

Коммит: `78da3a3` feat: Q-016 done-gate — opt-in --strict applied-evidence gate в pipeline.py done (дефолт мягкий).

### 3. `validate.py` — driver source_last_verified age-WARN
Advisory-проверка свежести драйверов: `driver_freshness_warning(...)` (`validate.py:24`) возвращает WARN, если `source_last_verified` старше `DRIVER_FRESHNESS_DAYS = 30` (`validate.py:21`). `today` параметризован для детерминированных тестов; на мусоре не падает. Вызов на драйверах — `validate.py:363-365` (формат YYYY-MM-DD валидируется отдельно как ERROR на `validate.py:361`). WARN не валит сборку (exit 0). Это S2-ступень: драйверы (код-backed) идут на SLA 30 дней, тогда как решения/политики — на своём SLA через `assurance.py currency`.

Коммит: `291f9a4` feat: validate — driver source_last_verified age-WARN (>30 дн., advisory; S2 лестницы Q-016).

### 4. `drift_check.py` — currency-drift wiring в assurance
Детектор дрейфа docs↔факт подключает секцию currency дашборда: вызывает `assurance.py currency --json` (`drift_check.py:116`) и через `_assurance_currency_drift(...)` (`drift_check.py:67`) поднимает в строки дрейфа **только HIGH**-находки — битые структурные ссылки и ссылки на superseded-решения (настоящий content-дрейф). Info-нудж «без last_verified» и структурные orphan-L1/flow намеренно НЕ тянутся (известное состояние, а не дрейф — чтобы не шуметь). Парсинг защищён, никогда не падает. exit 1 при любом дрейфе.

Коммит: `c135b4e` feat: drift_check — content-дрейф ссылок через assurance currency (битые/superseded, только HIGH; S1 чистая половина).

### 5. (бонус) `top.py` — апекс-проводка
Дашборд выставлен в верхнюю панель: подкоманда `top.py assurance [section] [--json] [--strict] [--max-age N]` (`cmd_assurance`, `top.py:295`; парсер `top.py:520`). Включён в агрегаты как warning-слой / advisory (`top.py:318`, `top.py:325`; `fail_ok=not args.strict` на `top.py:303`).

---
**Файлы (абсолютные пути):**
- `C:/Users/stefan/Documents/New project ai colab/tools/assurance.py`
- `C:/Users/stefan/Documents/New project ai colab/tools/pipeline.py`
- `C:/Users/stefan/Documents/New project ai colab/tools/validate.py`
- `C:/Users/stefan/Documents/New project ai colab/tools/drift_check.py`
- `C:/Users/stefan/Documents/New project ai colab/tools/top.py`
- `C:/Users/stefan/Documents/New project ai colab/docs/instruction-assurance.md`

## Осталось (Q-016 assurance — что ещё не сделано)

Сверено по живому репозиторию `C:/Users/stefan/Documents/New project ai colab` на 2026-06-23. **Уже приземлено** (исключено из списка ниже, чтобы не дублировать половину «Построено»): S1 apex-wiring (`top.py:83-85,295-325,520-525` + `drift_check.py:67-117` currency-дрейф), S2 driver-30d-WARN (`validate.py:21-39` + проводка на `validate.py:363`), S3 opt-in `--strict` в `pipeline.py cmd_done` (`pipeline.py:356-376`). Лестница S0→S4 названа в `topics/assurance-hardening-plan-2026-06-23.md`.

Остаются открытыми **9 пунктов** в 4 рабочих режимах: **inline** (мелкая аддитивная правка, можно прямо), **worktree** (symbol-anchored сборка в отдельном worktree, т.к. файлы co-owned / много правок), **ratify** (заблокировано котлом D-018/D-006 — сначала коллективное принятие, потом правка базовых общих файлов).

### A. Лестница hardening (assurance-hardening-plan)

| # | Пункт | Режим | Где спека |
|---|---|---|---|
| 1 | ~~**S0 — миграция `last_verified`.**~~ **SHIPPED 2026-06-23 (commit `9ffb509`).** `last_verified`-штамп приземлён на 20 accepted-решениях (`grep -rl last_verified decisions/` = 20). Историческая спека ниже. Штамп `last_verified: 2026-06-23` в front-matter на 20 accepted-решениях (D-001..D-013, D-015..D-018, D-021..D-023 — проверено: все без `last_verified`; хиты в D-013/D-015 — это проза про `source_last_verified`, не стамп) + 4 политики (`docs/parallel-work-policy.md`, `docs/promotion-rules.md`, `docs/workflow-orchestration-policy.md`, `docs/instruction-assurance.md` — проверено: ни в одной нет front-matter `last_verified`). НЕ back-date, НЕ трогать proposed D-014/D-019/D-020. Один governance-коммит, без кода. Плюс: согласовать один SLA (90d governance) и убрать рассинхрон дефолта `assurance.py:361 --max-age=180`. | ~~ratify~~ **done** (`9ffb509`; правка реестра решений/политик) | `topics/assurance-hardening-plan-2026-06-23.md` (строка S0 + блок «Стадии», таблица); конвенция и правила в `topics/governance-proposals-2026-06-23.md` §2 |
| 2 | **S4 — blocking currency-gate.** Добавить `('assurance currency --strict', 'assurance.py', ('currency','--strict'))` в `merge_gate.gate_stages` (проверено: `tools/merge_gate.py:56-57` сейчас только `validate` + `generate --check`, currency-стадии нет). Это финал лестницы warn→block из Q-016:49. **Предусловие:** закрыты все `last_verified`-gap (п.1) И прошёл один 90d квартал — поэтому пока не строить. НЕ ужесточать driver-WARN до ERROR. | **worktree** (после предусловия; `merge_gate.py` + апдейт `questions/Q-016.md`) | `topics/assurance-hardening-plan-2026-06-23.md` (строка S4) |

### B. Build-specs (worktree-ready сборки)

| # | Пункт | Режим | Где спека |
|---|---|---|---|
| 3 | ~~**Hardening `check-report` — advisory reference-verification.**~~ **SHIPPED (commit `763691b`).** Функция `report_reference_findings(text, root)` существует в `tools/instructions.py:526` (вызов в `cmd_check_report:571`). Проверяет, что цитируемые в отчёте пути/команды реально существуют на диске. Строго аддитивно: `check_report_text:369` НЕ трогать (его контракт пинят тесты `test_instructions.py:71-77` и 3 hard-call-site в `assurance.py:137,148` + `pipeline.py:343`); rc остаётся по token-`missing`, новые находки печатаются блоком `ADVISORY:`. + тесты в `test_instructions.py`, доки `docs/instruction-assurance.md:100`, `docs/top-layer-command-groups.md:139`. | ~~worktree~~ **done** (`763691b`; отдельная функция + проводка через `cmd_check_report` + тесты/доки) | `topics/build-specs-2026-06-23.md` §«Hardening check-report» |
| 4 | **Вплести 4 governance-решения в поверхность инструкций (D-008/D-004/D-009/D-002).** 8 аддитивных insertion'ов по symbol-anchor: `AGENTS.md` (3: D-008 после novax-строки `:26-27`, D-009, D-002), `PROTOCOL.md` (3: D-008 §7 `:133,161`, D-004 §8 `:173`, D-002 `:42`), `docs/agent-onboarding.md` (1: D-009 после §2 `:94`). Проверено по `assurance.py section_flow` — это flow-сироты. Применять **только после ратификации** (D-006/D-018). | **ratify** (базовые общие файлы AGENTS/PROTOCOL/onboarding — котёл) | спека правок: `topics/build-specs-2026-06-23.md` §«Weave governance decisions»; диспозиция/что-вплести-что-фоном: `topics/governance-proposals-2026-06-23.md` §1 |

### C. Заземление пирамиды — derive_reuse (pyramid-grounding-plan)

| # | Пункт | Режим | Где спека |
|---|---|---|---|
| 5 | ~~**`derive_reuse(root)` + derived L2→L1 gate.**~~ **SHIPPED (commit `6ede574`).** `derive_reuse` приземлён в `tools/promote.py:106` (инвентарь L1 из manifest `files:` + `core/*.md`, скан кто ссылается на basename → token→portals); `_gate_L2_L1:181-198` считает ≥2 разных порталов через `derive_reuse` (с D-018 decision-ref override), computed `reused_in` штампуется через `_stamp_fm` как provenance. | ~~worktree~~ **done** (`6ede574`; `promote.py` — связный ship) | `topics/pyramid-grounding-plan-2026-06-23.md` §«tools/promote.py» + блок «Buildable» |
| 6 | **`assurance.py section_coverage` — existence-checked grounding.** orphan-L1 итерировать по `files:` ONLY (не `candidates:`); ungrounded-L2 (`260-269`) заменить any-non-empty на l1_basis-резолв против инвентаря + `high`-находка на нерезолвящийся/typo-basis. | **worktree** (тот же ship, что #5; `tools/assurance.py`) | `topics/pyramid-grounding-plan-2026-06-23.md` §«tools/assurance.py» |
| 7 | **Сузить `core/engine-manifest.md` + структурный `l1_basis`.** Проверено: manifest `files:` сейчас 10 записей вкл. 2 тест-файла → разделить на `files:` (8 инструментов) и `candidates: [knowledge.py, text_extract.py]`. В `portals/example/portal.md` добавить `l1_basis: [tools/knowledge.py, tools/text_extract.py]` (сейчас только freeform `core:` на `:7`). Обновить `docs/promotion-rules.md:52` (derived-семантика) + `tools/test_assurance.py`. | **worktree** (часть того же derive_reuse-ship'а; manifest/портал/доки/тесты) | `topics/pyramid-grounding-plan-2026-06-23.md` §«core/engine-manifest.md», §«portals/example/portal.md», §«docs/promotion-rules.md», §«tools/test_assurance.py», «Решение по манифесту» |

### D. Дизайны флота (fleet-designs)

| # | Пункт | Режим | Где спека |
|---|---|---|---|
| 8 | ~~**`reconcile_state.py fix` — реализовать.**~~ **SHIPPED 2026-06-23 (commit `94c3c35`).** `cmd_fix(apply=False)` реализован в `tools/reconcile_state.py:259` (диспетчер `:295`): dry-run по умолчанию + обязательный `--apply`, поверх `reconcile()`, ключевание по `items[].code`, только производные (`index.json` + pipeline-пара), PRIMARY-дрейф — отказ, exit через `exit_code(report)`. Дизайн (ниже) реализован полностью. Дизайн: dry-run по умолчанию + обязательный `--apply`; строить поверх `reconcile():154`, ключевать по `items[].code`; писать ТОЛЬКО 4 производных (`index.json`, `TASKS.md`, `PIPELINE.md`, `logs/pipeline.json`); PRIMARY-дрейф (маркеры/claim'ы) — отказ, не авто-фикс; exit через `exit_code(report):223`; utf-8 + `newline="\n"` (CRLF-риск). | ~~worktree~~ **done** (`tools/reconcile_state.py` + импорт `generate`/`pipeline`, `docs/state-reconciliation-layer.md`) | `topics/fleet-designs-2026-06-23.md` §1 |
| 9 | ~~**Наполнить L2 двумя реальными порталами.**~~ **SHIPPED 2026-06-23 (commits `144bb7b`+`a47e8c9`).** Построены `portals/bridge-knowledge/` (обёртка `data/knowledge-corpus/`) и `portals/repo-inventory/` (драйверы `repo-runner` + `git-log`) → порталов=3, assurance coverage показывает orphan-L1: 0. Историческая спека ниже. Построить `bridge-knowledge` (effort S, обёртка готового `data/knowledge-corpus/`) и `repo-inventory` (effort M, дизайн готов в `tasks/T-024.md`, переиспользует драйверы `repo-runner` + `git-log`). Кормит derive_reuse (#5) реальным вторым порталом. | ~~worktree~~ **done** (`144bb7b`+`a47e8c9`; `portals/bridge-knowledge/`, `portals/repo-inventory/` через `portal.py`) | `topics/fleet-designs-2026-06-23.md` §2 |

### Порядок / зависимости

- **#6+#7** — остаток grounding-качества derive_reuse-слоя (#5 derive_reuse + #9 второй портал уже **SHIPPED**, gate reuse_across_portals теперь проходим по построению; #6 section_coverage-резолв и #7 structural l1_basis ещё не внедрены).
- **#1 (S0)** SHIPPED (`9ffb509`) → **#2 (S4)** теперь блокирован только квартальным предусловием (нужно, чтобы прошёл квартал с проштампованным `last_verified`).
- **#4** — единственный оставшийся **ratify**-пункт (#1 уже SHIPPED); остальные технические и идут через **worktree** (co-ownership `top.py`/общих файлов и многофайловость → symbol-anchored worktree-сборка, anchor по именам символов, не по номерам строк).
- Inline-only пунктов в остатке нет: **#4** затрагивает governance-реестр (ратификация), **#6/#7** — многофайловые worktree-правки.

---
**Вердикт:** апекс-слой проверяемости Q-016 построен и проведён через 5 точек (S1-S3 лестницы). Бо́льшая часть остатка зашиплена 2026-06-23 (#1 S0, #3 report-findings, #5 derive_reuse, #8 reconcile-fix, #9 порталы); остаются 4 пункта — #6/#7 (grounding-качество derive_reuse-слоя, genuinely undone), #4 (governance-ратификация), #2 (S4, заблокирован квартальным предусловием).
