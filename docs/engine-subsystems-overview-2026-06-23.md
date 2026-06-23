---
id: engine-subsystems-overview-2026-06-23
type: doc
status: proposed
date: 2026-06-23
related: [collab-safety-subsystem-2026-06-23, drivers-subsystem-state-2026-06-23, q016-assurance-state-2026-06-23]
---

# Engine subsystems overview (2026-06-23)

> **proposed** — единый обзор-свод трёх подсистем движка. Сводит три авторитетных state-документа в одну картину: **безопасная коллаборация / параллельная работа** (`collab-safety-subsystem-2026-06-23`), **drivers / AI-OS Bridge** (`drivers-subsystem-state-2026-06-23`) и **Q-016 assurance** (`q016-assurance-state-2026-06-23`). Каждый ребёнок остаётся каноном по своей подсистеме; этот документ — карта верхнего уровня и стык между ними. Статус `proposed` за всеми тремя — ещё не через котёл (`D-018`); описанные механизмы по большей части accepted и подкреплены кодом.

Эти три подсистемы — операционный субстрат движка мульти-агентной коллаборации. Их можно прочесть как один контур «безопасно работать → безопасно подключать внешний мир → доказуемо удерживать инструкции в актуальном состоянии»:

1. **Collaboration-safety** отвечает на вопрос *как N агентов работают над одним репозиторием параллельно, не теряя чужую работу, не блокируя друг друга и не вливая «грязное» состояние в общую историю* — атомарные примитивы конкурентности + ownership-классификация + бинарная изоляция L0/L1.
2. **Drivers / AI-OS Bridge** отвечает на вопрос *как агент безопасно дотягивается до внешних возможностей (файлы, репо, БД, память)* — проверяемый driver-манифест + read-only-intake с закрытым execute-гейтом + L2-мост из готовых драйверов в тематические порталы.
3. **Q-016 assurance** отвечает на вопрос *как доказать, что инструкции применяются и остаются свежими* — единый read-only апекс-дашборд + четыре точки интеграции в существующие инструменты + лестница ужесточения S0→S4.

Сквозная нить всех трёх — **advisory-по-умолчанию, strict-по-триггеру**: дешёвый наблюдательный дефолт (commit_lock без изоляции, драйвер в read-only, дашборд с exit 0), который ужесточается до блокирующего только когда сработал явный триггер (foreign-source → L1, execute → 10-строчный гейт, currency-gap → `--strict`).

---

## 1. Подсистема безопасной коллаборации / параллельной работы

**Канон:** `topics/collab-safety-subsystem-2026-06-23.md`. **Governance:** `D-021` (Уровень-1 принят), `D-022` (триггеры), `D-023` (ownership за индексы); матрица «ситуация → механизм» — `docs/parallel-work-policy.md`. Три слоя, разделяющие одну идею: **лиза истекает по времени** (без liveness-пинга), реклеймится winner-take-all атомарным созданием, а **fencing-токен** не даёт зомби-холдеру закоммитить устаревший результат.

### Слой 1 — атомарные примитивы конкурентности
Координация целиком через атомарные операции ФС — БЕЗ потоков, замков ОС или БД: `os.open(O_CREAT|O_EXCL)` («выигрывает один создатель») + `os.replace` (атомарный своп) + дисциплина TTL-лиза + fencing-токен.
- **Commit-lock** сериализует `git commit` через единственный файл `queues/commit.lock` (`commit_lock.py:67`); TTL 120с (`:58-62`), release с проверкой владельца (`:101-103`). Это **сериализация, а не изоляция** — изоляцию даёт отдельное правило selective-add + worktree (`:10-12`).
- **Атомарная выдача id** (`next_id.py:117-124`) тем же `O_EXCL`-паттерном не даёт двум агентам выпустить одинаковый `T-/Q-/D-` id.
- **Pipeline-claim** фехтует задачи: claim-файл с `claim_id = uuid4().hex[:12]` как fencing-токен (`pipeline.py:133`), лиза 30 мин. Stale-takeover гейтируется **вторым** эксклюзивным замком по имени `<p>.take.<old claim_id>` + re-check под замком + `os.replace` (`pipeline.py:148-176`) — ровно один победитель. Done/fail проверяют agent-имя и `claim_id` (`pipeline.py:308-322`), не давая зомби-холдеру закрыть устаревшую работу. Windows-харднинг: retry `os.replace` 5×0.02с, возврат None вместо краша.
- **Доказательства неутраты работы:** `test_commit_lock.py:41-54` (takeover замка с `lease_epoch: 1`); `test_pipeline_fencing.py` — 8 потоков × 16 раундов гонки дают `len(winners) == 1` (`:155-175`) + отказ неверного `claim_id=deadbeef00` на done (`:57-71`).

### Слой 2 — ownership-классификация и детекторы трения
Общий классификатор `tools/ownership.py` (T-153) — единственный источник истины «моё vs чужое», импортируемый детектором `friction.py` и исполнителем `cohort.py guard`. `classify()` возвращает одну из **mine | generated | volatile | foreign | unknown** по приоритету (`ownership.py:62-89`); ключевое правило: **только `foreign`** обязывает эскалацию до L1 (`:17`); unknown намеренно не = foreign.
- **`cohort.py guard`** (`:336-394`) — ownership-aware, 4 L1-триггера: foreign-source, hot-tool (`HOT_FILES`), stale-index (`generate.py --check`), gate-poison (`validate.py ERROR=N>0`). Путь **ship** — L0 safe-commit-цикл: `commit_lock acquire` → selective `git add` (никогда `-A`) → `generate.py` → commit → release (`cohort.py:246-281`).
- **`friction.py`** — read-only F-001..F-020 ledger (advisory, не авто-чинит). **F-020 / gate-poison ПОДКЛЮЧЁН** (SHIPPED 2026-06-23, commit `67fa8b5`): REGISTRY-запись `friction.py:276` + детектор `check_gate_poison()` `:479`, прогоняется в `collect_status` `:634` и учитывается в `recommendation` `:650`. Прежнее замечание о дрейфе (F-020 только как cohort-триггер + предложение в `topics/friction-subsystems-synthesis-2026-06-22.md:94,101,105-111`) закрыто.

### Слой 3 — изоляция + слияние (бинарная модель)
- **L0** (общее дерево + `commit_lock` + selective-add) — дешёвый дефолт (`D-021:23-24`, `parallel-work-policy.md:30`); `stream.py` переиспользует ту же L0-сериализацию для fork-пакетов `streams/<topic>/<id>/STREAM.md` под тем же commit-lock (`stream.py:34,231-238`).
- **L1** (per-agent git worktree на ветке `agent/<agent>/<task>` + `merge_gate`) — обязателен по триггеру. `worktree.py` safe-by-default (печать без `--run`), worktree-сиблинг репозитория. `merge_gate.py` даёт green(0)/red(1), прогоняя те же read-only стадии (`validate.py` + `generate.py --check` + `permissions.py`); тесты ВЫКЛ по умолчанию (`:11-14`).
- **Эскалация L0→L1** (`D-022:23-27`) — 5 триггеров A–E (чужой uncommitted source / STALE не-своего / правка HOT-файла / явный запрос Stefan на fork-and-synthesize / предсказанная same-file-коллизия) + gate-poison (триггер F) + load (commit_lock BUSY >2× / >120с, generate >5 рестартов). Same-file: Вариант 1 (worktree + 3-way merge для 500+ строк/кода, кейс LS-2 `text_extract.py`), Вариант 2 (один-claim + форк-ревью), Вариант 3 (перезапись + обязательный синтез).
- **D-023** разрешает расхождение Claude «commit-your-own» vs Codex «интегратором» (Q-017) как «дефолт vs граничное условие» одного правила: автор source отвечает за свежесть своего генерируемого индекса; чистый случай (mine) — регенерировать и коммитить индекс в том же changeset; загрязнённый (foreign) — индекс НЕ коммитить, оставить владельцу/интегратору. Различение автоматическое через `cohort guard` / `ownership.py` (`D-023.md:22-33`).

**Ключевые файлы:** `tools/commit_lock.py`, `tools/next_id.py`, `tools/pipeline.py`, `tools/ownership.py`, `tools/cohort.py`, `tools/friction.py`, `tools/stream.py`, `tools/worktree.py`, `tools/merge_gate.py`, `decisions/D-021..D-023.md`, `docs/parallel-work-policy.md`.

---

## 2. Подсистема Drivers / AI-OS Bridge

**Канон:** `topics/drivers-subsystem-state-2026-06-23.md`. **Governance:** `D-010` (AI-OS Bridge strategy, staged B→E / L1→early L2) + `D-013` (driver schema v1, variant B, accepted). Safety-контракт — `docs/driver-safety-policy.md`. Bottom line: каталог в состоянии D-010 «early L2» — **9 драйверов зарегистрировано, 8 ready, 1 (`file-inventory`) draft**.

### Схема, валидация, свежесть
- **Схема = проверяемый манифест, не проза** (`drivers/SCHEMA.md:10-14`). **19 обязательных полей** определены идентично в схеме и D-013 (`SCHEMA.md:18-38`, `D-013.md:24-44`); variant B = minimal + `source_last_verified` / `timeout_seconds` / `max_output_bytes` / `audit`, откладывает полную MCP-метадату. Схема-док всё ещё self-labeled **draft** (`SCHEMA.md:12`), хотя D-013 accepted — флаг дрейфа.
- **`tools/validate.py` энфорсит контракт** (`check_drivers()` :296-384; `check_driver_tools()` :409-444). Отсутствие required-поля, дубль id, плохой формат даты, не-положительные лимиты, medium/high без `audit:true` → ERROR; enum-несовпадения → WARN. **Execute/sandbox-правило (T-078 finding G, :375-382):** `mode: execute` требует реальной изоляции (container/docker/nsjail/firejail/gvisor/sandboxed-vm) или ERROR. Optional-поле `tools` кросс-чекается против реальных `@mcp.tool()`-имён в `mcp_server.py`. Сборка падает только на ERROR.
- **Freshness — advisory:** `driver_freshness_warning(...)` (`validate.py:24-40`), SLA `DRIVER_FRESHNESS_DAYS = 30`; строго `> 30` дней → WARN, битая дата → ERROR. Контракт детерминированно залочен в `tools/test_validate_freshness.py` (today=2026-06-23). Генератор каталога `tools/drivers_catalog.py` (T-030) зеркалит front-matter в `index.json`/`CATALOG.md`, но **схему не валидирует**.

### Safety-posture: read-only-intake, execute-gate закрыт
Новые драйверы стартуют `mode: read-only`; записи требуют dry-run+confirm; внешний код карантинится через staged S0–S7 sandbox intake (`docs/external-code-sandbox.md`), никогда не мёржится автоматически. `docs/execute-sandbox-preflight.md` — только preflight (не грант): **10-строчный hard-gate** (decision / source / sandbox / permissions / network / limits / logs / rollback / validation / human) должен быть полностью закрыт, иначе режим остаётся read-only. Variant C (no execute) — дефолт; **активных execute-драйверов не существует**. Risk-лестница: low→AUTO, medium→REVIEW+audit, high→HUMAN+audit+sandbox.

### Audit + redaction
- `drivers/audit.py`: append-only JSONL-журнал на `DRIVER_AUDIT_LOG` иначе `logs/driver-audit.jsonl`, атомарный single-line append, никогда не пробрасывает наружу (T-078 finding E).
- `drivers/redaction.py`: единственный источник истины для маскирования `SECRET_RE`/`AWS_KEY_RE` (T-078 finding L), вшит в драйверы `data` и `files` (per-cell / per-read, файловый вывод усечён до 300 символов). Byte-лимиты: data `MAX_OUTPUT_BYTES=1_048_576`, files=1_000_000 с флагом truncation (Q-008/B, `docs/driver-safety-policy.md:11-13`).

### L2-мост реализован в двух слоях
1. **`gateway` — композиция, не leaf:** один MCP-сервер (`drivers/gateway/mcp_server.py`, имя `ai-os-bridge`) фронтит files + repo-runner + workbench (query-only), экспонирует 6 инструментов. Статус-нюанс: **`ready-except-mcp-stdio-call-acceptance`** — полный `call_tool` поверх async stdio на Windows всё ещё **заблокирован** (`drivers/gateway.md:59-61`); in-process регресс-тест — текущая гарантия. Зафайлен как L2 из-за L1/L2/L3-ограничения схемы. `files` — named первый L2 PoC (`drivers/files.md:28`).
2. **Порталы переиспользуют драйверы без изменений:** drivers → `tools/knowledge.py` (generic L6 engine) → `tools/portal.py` (L2-порталы). knowledge.py грузит `workbench.py`/`files_driver.py` напрямую как движки (ingest→query→report, FTS5+bm25 с LIKE-fallback, без vector/RAG до спроса по D-010). portal.py (D-016) делегирует целиком в knowledge как универсальный движок; домен живёт как данные в `portal.md`, не в core-коде. Q4 portal-location закрыт через D-021/T-145 (манифест в `portals/example/`, корпус в `data/portals/example` через `corpus_ref`).

### Открытые пункты
(1) рассинхрон SCHEMA.md draft vs accepted D-013; (2) gateway Windows-stdio `call_tool`-блокер; (3) `file-inventory` всё ещё draft — промоутить или свернуть в files/gateway-путь; (4) execute остаётся закрыт, пока 10-строчный гейт не очищен за отдельным accepted-решением.

**Ключевые файлы:** `drivers/SCHEMA.md`, `drivers/CATALOG.md`, `drivers/index.json`, `tools/validate.py`, `tools/drivers_catalog.py`, `drivers/audit.py`, `drivers/redaction.py`, `drivers/gateway.md`, `tools/knowledge.py`, `tools/portal.py`, `decisions/D-010.md`, `decisions/D-013.md`, `docs/driver-safety-policy.md`, `docs/external-code-sandbox.md`, `docs/execute-sandbox-preflight.md`, `docs/pyramid-candidate-map.md`.

---

## 3. Подсистема Q-016 assurance — «построено vs осталось»

**Канон:** `topics/q016-assurance-state-2026-06-23.md`. Канонический срез проверяемости инструкций Q-016, сверен по живому репо на 2026-06-23. Лестница ужесточения S0→S4 названа в `topics/assurance-hardening-plan-2026-06-23.md`. Все коммиты — Max, 2026-06-23.

### Построено — 5 компонентов апекс-слоя (1 READ-ONLY дашборд + 4 точки интеграции)
- **`tools/assurance.py`** — апекс-дашборд, 4 секции, переиспользует существующее, advisory по умолчанию (exit 0), `--strict`→exit 1; вердикт PASS / WARN / ATTENTION. Секции: **applied** (`:123`, % done-задач с реальным evidence, `CONVENTION_MIN=156`/T-156), **currency** (`:192`, свежесть D-*/политик, битые структурные ссылки = HIGH, дефолт `--max-age` 180 дн.), **coverage** (`:240`, orphan-L1 medium / ungrounded-L2 HIGH), **flow** (`:279`, реестр INSTRUCTIONS + висячие accepted-D-NNN). Коммит `9465956`; якорь `docs/instruction-assurance.md`.
- **`pipeline.py done --strict`** — opt-in applied-evidence done-gate (`cmd_done` :356; гейт :325/:333; ОТКАЗ/WARN :368-376; CLI :662/:675). Дефолт мягкий (S3). Коммит `78da3a3`.
- **`validate.py`** — driver `source_last_verified` age-WARN (`driver_freshness_warning` :24, `DRIVER_FRESHNESS_DAYS=30` :21, вызов :363-365, формат-ERROR :361); advisory, exit 0 (S2). Коммит `291f9a4`.
- **`drift_check.py`** — currency-дрейф: вызывает `assurance currency --json` (:116) через `_assurance_currency_drift` (:67), тянет ТОЛЬКО HIGH (битые/superseded ссылки); info/orphan/flow намеренно не тянутся; exit 1 при дрейфе (S1). Коммит `c135b4e`.
- **`top.py`** — апекс-проводка: `top.py assurance [section] [--json] [--strict] [--max-age N]` (`cmd_assurance` :295, парсер :520, агрегат :318/:325, `fail_ok=not args.strict` :303).

### Осталось — 9 открытых пунктов (режимы inline / worktree / ratify; приземлённые S1/S2/S3 исключены)
- **A. Hardening-лестница.** #1 **S0** — штамп `last_verified: 2026-06-23` на 20 accepted-решениях (D-001..D-013, D-015..D-018, D-021..D-023) + 4 политики, не back-date, не трогать proposed D-014/D-019/D-020, согласовать SLA 90d и убрать рассинхрон с `assurance.py:361 --max-age=180` (**ratify**, котёл D-018). #2 **S4** — blocking currency-gate в `merge_gate.gate_stages` (сейчас `merge_gate.py:56-57` только validate+generate --check); предусловие: закрыты last_verified-gap (#1) + прошёл 90d квартал (**worktree**, заблокирован).
- **B. Build-specs.** #3 hardening `check-report` — новая `report_reference_findings(text, root)` в `instructions.py`, строго аддитивно (не трогать `check_report_text:369`, контракт пинят `test_instructions.py:71-77` + хард-колл `assurance.py:137,148`/`pipeline.py:343`), вывод блоком ADVISORY (**worktree**). #4 вплести 4 governance-решения (D-008/D-004/D-009/D-002) — 8 symbol-anchor insertion'ов в AGENTS.md/PROTOCOL.md/`docs/agent-onboarding.md`, только после ратификации D-006/D-018 (**ratify**).
- **C. Заземление пирамиды** (один связный derive_reuse-ship #5+#6+#7). #5 `derive_reuse(root)` в `promote.py`, заменить самодекларированный `reused_in` в `_gate_L2_L1:139-143` на счёт ≥2 порталов + D-018 override; #6 `assurance.py section_coverage` — orphan-L1 по `files:` only, ungrounded-L2 (`260-269`) через l1_basis-резолв; #7 сузить `core/engine-manifest.md` (10 записей вкл. 2 теста → 8 files: + candidates), добавить структурный `l1_basis` в `portals/example/portal.md`, обновить `docs/promotion-rules.md:52` + `test_assurance.py`. Спека: `topics/pyramid-grounding-plan-2026-06-23.md`.
- **D. Fleet-designs.** #8 ~~реализовать `reconcile_state.py fix`~~ **SHIPPED 2026-06-23, commit `94c3c35`**: `cmd_fix()` `reconcile_state.py:259` — dry-run по умолчанию + `--apply`, пишет только производные (`DERIVED_CODES` `:237`), PRIMARY-дрейф=отказ (`:284-288`), utf-8/`newline="\n"`; #9 наполнить L2 двумя реальными порталами (`bridge-knowledge`, `repo-inventory` из T-024), порталов 1→2-3, кормит #5 (**worktree**). Спека: `topics/fleet-designs-2026-06-23.md`.

### Зависимости / вердикт
#5+#6+#7 — один ship; #9 даёт ему реальный второй портал (иначе gate `reuse_across_portals` непроходим, L1 остаётся proposed); #1(S0) разблокирует #2(S4); #1 и #4 — единственные ratify-пункты, остальные через worktree (symbol-anchored). Inline-only пунктов нет. Итог: апекс-слой построен и проведён через 5 точек (S1-S3); критический путь — derive_reuse-ship (#5-7+9) и две ратификации (#1,#4); S4-гейт (#2) заблокирован квартальным предусловием.

**Ключевые файлы:** `tools/assurance.py`, `tools/pipeline.py`, `tools/validate.py`, `tools/drift_check.py`, `tools/top.py`, `tools/promote.py`, `tools/instructions.py`, `tools/merge_gate.py`, `tools/reconcile_state.py`, `docs/instruction-assurance.md`; спеки в `topics/{assurance-hardening-plan,build-specs,pyramid-grounding-plan,fleet-designs,governance-proposals}-2026-06-23.md`.

---

## Cross-cutting summary — как три подсистемы смыкаются

Три подсистемы — не изолированные башни, а один контур с общими швами:

- **Общий паттерн «advisory-по-умолчанию → strict-по-триггеру».** Collab-safety: L0 — дешёвый дефолт, L1 обязателен только по триггеру. Drivers: read-only-intake, execute-gate закрыт до 10-строчного hard-gate. Assurance: дашборд exit 0, `--strict`/S4-gate ужесточают до блока. Один и тот же дизайн-инстинкт «не блокировать, пока не доказано, что надо».

- **`validate.py` + `generate.py --check` — общий freshness-шов всех трёх.** Collab-safety `merge_gate` и `cohort guard` шеллят в них как gate-стадии; drivers энфорсит driver-схему внутри `validate.py` (`check_drivers`); assurance вешает на них driver-WARN (S2) и предлагает S4 currency-стадию прямо в `merge_gate.gate_stages`. То есть `validate.py` — единая точка, через которую assurance-лестница и collab-гейт смотрят на здоровье дерева.

- **Пирамида связывает drivers ↔ assurance.** L2-мост drivers (`knowledge.py` → `portal.py` → `portals/example`) — ровно тот объект, который assurance-секция `coverage` пытается заземлить: orphan-L1 / ungrounded-L2-находки и derive_reuse-ship (#5-7+9) измеряют, насколько реально драйверы переиспользуются порталами. Пункт #9 (два реальных портала) — это одновременно рост drivers-флота и разблокировка assurance-гейта `reuse_across_portals`.

- **Котёл D-018 — общий governance-потолок.** Все три подсистемы в статусе `proposed` именно потому, что финальный перевод в accepted идёт через котёл D-018 (коллективное принятие + двойная перепроверка). Assurance-пункты #1/#4 явно «ratify»-режима по той же причине; collab-safety streams откладывают adopt до D-018; drivers-схема ждёт ратификации, чтобы снять draft-лейбл.

- **Единый инструментальный стек.** `tools/pipeline.py` (claim-fencing + done-gate), `tools/validate.py` (driver-схема + freshness), `tools/merge_gate.py` (L1-гейт + будущая currency-стадия), `tools/top.py` (апекс-проводка) фигурируют сразу в нескольких подсистемах — это общий хребет, а не три параллельных набора инструментов.

**Источники-дети (каноны по подсистемам):**
- `topics/collab-safety-subsystem-2026-06-23.md`
- `topics/drivers-subsystem-state-2026-06-23.md`
- `topics/q016-assurance-state-2026-06-23.md`
