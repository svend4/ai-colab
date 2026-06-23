---
id: session-master-2026-06-23
type: doc
status: proposed
date: 2026-06-23
related: [engine-subsystems-overview-2026-06-23, build-plans-overview-2026-06-23, orchestration-architecture-2026-06-23, nested-orchestration-3to1]
---

# Session master (2026-06-23) — единый верхний вход

> **proposed** — апекс-карта сессии. Сводит три L2-обзора-свода в один экран: **что есть** (движок + три подсистемы), **что строить** (планы сборки), **как оркеструется** (конвейер / бригады / 3:1). Это самый верхний вход: отсюда вниз — три обзора, под каждым из них — по три канонических state-документа / плана. Статус `proposed` за всем деревом: описанные механизмы по большей части accepted и подкреплены кодом, но перевод сводок в `accepted` идёт через котёл (`D-018`, accepted).

Три ветви сессии отвечают на три ортогональных вопроса и сходятся в одной инвариантной идее — **дорогая мысль параллелится свободно; единственная серийная точка — дешёвая запись в одну git-историю**:

| Ветвь | Вопрос | Обзор (L2-свод) | Каноны под ним (L1) |
|---|---|---|---|
| **Что есть** | какой субстрат движка уже построен | `docs/engine-subsystems-overview-2026-06-23.md` | collab-safety · drivers/AI-OS Bridge · Q-016 assurance |
| **Что строить** | какие ратифицированные-к-сборке планы в очереди | `docs/build-plans-overview-2026-06-23.md` | Q-017 semantic · pyramid-grounding · build-specs |
| **Как оркеструется** | как N воркфлоу производятся и сливаются в один канон | `docs/orchestration-architecture-2026-06-23.md` | conveyor-policy · orchestration-policy · D-018 (+ `nested-orchestration-3to1`) |

Сквозная нить всех трёх ветвей — **advisory-по-умолчанию, strict-по-триггеру**: дешёвый наблюдательный дефолт, который ужесточается до блокирующего только по явному триггеру. И общий потолок — **котёл `D-018`**: ничто не становится `accepted` соло, всё спорное проходит двойную перепроверку (техническую + гуманитарную).

---

## 1. Что есть — движок и его три подсистемы

> Канон: `docs/engine-subsystems-overview-2026-06-23.md`. Операционный субстрат как один контур: *безопасно работать → безопасно подключать внешний мир → доказуемо удерживать инструкции свежими.*

- **Collaboration-safety / параллельная работа** (`темы/collab-safety-subsystem-2026-06-23.md`; gov `D-021`/`D-022`/`D-023`; матрица `docs/parallel-work-policy.md`). Три слоя: (1) атомарные примитивы конкурентности через ФС (`O_CREAT|O_EXCL` + `os.replace` + TTL-лиза + fencing) — `commit_lock.py` сериализует `git commit` (TTL 120с), `next_id.py` атомарная выдача id, `pipeline.py` claim-fencing (`uuid4hex[:12]`, лиза 30 мин, второй эксклюзивный `.take.<old>` → ровно один winner; доказано `test_pipeline_fencing.py` 8×16 гонка → `len(winners)==1`); (2) ownership-классификатор `tools/ownership.py` (mine/generated/volatile/foreign/unknown — **только `foreign` форсит L1**), `cohort.py guard` (4 L1-триггера), advisory `friction.py` F-001..F-019; (3) бинарная изоляция **L0** (общее дерево + commit_lock + selective-add, дефолт) vs **L1** (per-agent worktree `agent/<agent>/<task>` + `merge_gate`), эскалация по `D-022` триггерам A–E + gate-poison + load.

- **Drivers / AI-OS Bridge** (`темы/drivers-subsystem-state-2026-06-23.md`; gov `D-010` staged B→E + `D-013` schema v1 variant B; safety `docs/driver-safety-policy.md`). Состояние «early L2»: **9 драйверов, 8 ready, 1 (`file-inventory`) draft**. Схема = проверяемый манифест, **19 обязательных полей**, энфорс в `validate.py` (`check_drivers`/`check_driver_tools`); `mode: execute` требует реальной песочницы иначе ERROR. **Read-only-intake, execute-gate ЗАКРЫТ** (`docs/execute-sandbox-preflight.md` 10-строчный hard-gate, variant C дефолт, активных execute-драйверов ноль). Audit `drivers/audit.py` (append-only JSONL) + redaction `drivers/redaction.py`. L2-мост в два слоя: `gateway` (`drivers/gateway/mcp_server.py`, имя `ai-os-bridge`, 6 инструментов, `ready-except-mcp-stdio-call-acceptance` — Windows async-stdio `call_tool` ещё BLOCKED) и порталы (drivers → `tools/knowledge.py` FTS5+bm25 → `tools/portal.py`, D-016, домен как данные).

- **Q-016 assurance** (`темы/q016-assurance-state-2026-06-23.md`; лестница S0→S4 в `темы/assurance-hardening-plan-2026-06-23.md`). **Построено = 5 апекс-компонентов** (1 read-only дашборд + 4 интеграции): `assurance.py` (секции applied/currency/coverage/flow, advisory exit 0, `--strict`→1), `pipeline.py done --strict` (S3), `validate.py` driver age-WARN (S2), `drift_check.py` currency-дрейф HIGH-only exit 1 (S1), `top.py` апекс-проводка. **Осталось = 9 пунктов**: S0 last_verified-штамп (#1, ratify), S4 blocking currency-gate (#2, заблокирован #1+квартал), build-specs (#3/#4), pyramid derive_reuse-ship (#5+#6+#7), `reconcile_state.py fix` (#8), два реальных портала (#9). Критический путь = derive_reuse-ship (#5-7+9) + две ратификации (#1,#4).

**Общий хребет:** `tools/pipeline.py`, `tools/validate.py`, `tools/merge_gate.py`, `tools/top.py` фигурируют во всех трёх подсистемах — один backbone, не три параллельных набора. `validate.py` + `generate.py --check` — единый freshness-шов; пирамида (`knowledge.py`→`portal.py`→`portals/example`) связывает drivers ↔ assurance.

---

## 2. Что строить — три плана сборки

> Канон: `docs/build-plans-overview-2026-06-23.md`. **19 buildables**, все аддитивные / advisory-non-blocking / symbol-anchored / read-only by construction. Легенда mode: `worktree` (изолированно), `inline` (мелкая правка в общем дереве), `ratify` (только после котла), `optional`.

- **План 1 — Q-017 semantic** (effort M): opt-in `--semantic` стадия над `tools/doc_consensus.py`; pure-lexical stdlib остаётся no-cost дефолтом. Token-set Jaccard слеп к парафразу (307 units / 0 consensus при thr 0.4/0.3 vs ≥7 реальных согласий). Buildables: механический high-thr pre-cluster (thr ~0.65) → `_semantic_pass` (NEW, subprocess-агент, JSON GROUPS+DIVERGENCES, батчи 40-60) → `_merge` (транзитивное объединение по unit-id) → расширить `render()` (cross-refs + rationale + provenance) → regression fixture [ratify] → документировать opt-in.

- **План 2 — Pyramid grounding**: заменить сломанный self-declared `reused_in` (писателей ноль) на scan-derived `derive_reuse`, принцип «честная нерешённость». `derive_reuse(root)` в `promote.py` → переписать `_gate_L2_L1` (distinct-portal count, pass `>=2`, D-018 override) → derived `section_coverage` в `assurance.py` + `high` finding на stale `l1_basis` → split `engine-manifest.md` `files:` 10→8 + `candidates:` → структурный `l1_basis` в `portals/example/portal.md` → supporting edits. Порталы поднимают счётчик: `bridge-knowledge` (1→2), `repo-inventory` (2→3, git-log без fixture — seed запуском), `app-data` (optional). Orphan-12 — kernel primitives, легитимно не цитируются корпусами.

- **План 3 — Build-specs**: три symbol-anchored advisory edit-спеки. **S1** [worktree]: 5 аддитивных правок врезают `assurance.py` в апекс `tools/top.py` (advisory, exit-контракт `assurance.py:382`). **S2** [ratify — только после D-006/D-018]: 8 anchor-вставок вплетают D-008/D-004/D-009/D-002 в `AGENTS.md`/`PROTOCOL.md`/`docs/agent-onboarding.md`, без rewrites. **S3** [worktree/inline]: NEW advisory `report_reference_findings()` в `tools/instructions.py` (НЕ трогать pinned `check_report_text:369-382`), `ADVISORY:` блок в `cmd_check_report`, rc без изменений.

**Ratify-пункты** (5, 16, 18) и любой переход в `accepted` — через котёл D-017 (fork-and-synthesize) + D-018 (коллективное + двойная перепроверка). Прецедент: T-136/T-137 (done, закрыты D-021). Полная таблица порядка сборки — в обзоре §«Единая таблица».

---

## 3. Как оркеструется — конвейер, бригады, 3:1

> Канон: `docs/orchestration-architecture-2026-06-23.md` (+ `docs/nested-orchestration-3to1.md`). Узкое место — **не параллелизм воркеров, а полоса коммита одного оркестратора.** Четыре слоя держат дорогую мысль под параллельным фронтом, а серийной оставляют только дешёвую запись.

- **Конвейер** (`docs/workflow-conveyor-policy.md`, `tools/conveyor.py`): producers (широкий фронт) → очередь `landed` (output-ref) → integrator-workflow (composer на каждый output, параллельно) → оркестратор write + **когортный commit** (узкая, но дешёвая серийная точка). `.output` — ПРЕТЕНЗИЯ, не факт; очередь дренируется в порядке зависимостей. **Поток ≠ партия**: пополнять ЗАРАНЕЕ, никогда не осушать in-flight до нуля (target N≥2-4), backlog-scanner само-кормит следующую волну.

- **Надзиратель `conveyor.py`** — внешний read-mostly глаз, который только **сигналит** (не запускает; аналогия — `friction.py` сигналит, `cohort.py` исполняет). Реестр `logs/conveyor.json` (gitignored). `status` = вердикт + exit-код (1=нужно действие, 0=healthy) через чистую `assess()`: **REFILL** (deficit>0), **PROCESS** (landed ждут), **PROCESS-MISSING-OUTPUT**, **IDLE** (heartbeat протух). Дефолты `target=2`, `idle_min=20`. Живой оркестратор: нотификации ре-инвокируют + `Stop`-hook + `ScheduleWakeup`/cron.

- **Бригада** = `{ N producer-агентов + 1 integrator }` — самодостаточная ячейка, обрабатывающая один кластер от сырья до готового триплета `{doc_path, doc_content, commit_msg}` (`proposed`-Markdown). Обе фазы (PRODUCE-фан-аут + INTEGRATE-композиция) параллелятся свободно; бригада НЕ пишет в git сама. Топ-оркестратор сводится к **спавнеру + коммиттеру**. Живой демо: коммит `d342366`, артефакт `темы/build-specs-2026-06-23.md` (3 producers + 1 integrator → 1 commit). Синонимы: ячейка/cell/звено/pod; канон предпочитает **бригада/brigade**.

- **3:1 рекурсия** (`docs/nested-orchestration-3to1.md`): когда бригад >3, они становятся листьями следующего уровня — **дирижёр** сливает ≤3 бригадных артефакта, **chief-conductor** сливает ≤3 дирижёрских (span-of-control reduce-дерево, фан-ин 3, число уровней ∝ log N). Все уровни L1..Lk делают одно и то же — «≤3 выхода детей → 1 чистый артефакт»; особый только верх (человек) — добавляет дешёвую серийную интеграцию в git. Этот самый master-документ — пример уровня выше: L3-chief-merge трёх L2-обзоров в один.

**Граница автономии = D-018:** интегратор/бригада выдаёт `proposed`, не `accepted`. Триплет — всё ещё ПРЕТЕНЗИЯ: топ гейтит его (`cohort.py guard` → L0 ship / L1 worktree+`merge_gate`, `commit_lock.py` TTL self-heal). Перевод в `accepted` — через котёл (`pipeline.py`), двойная перепроверка, не один агент.

---

## Навигация вниз по дереву

```
docs/session-master-2026-06-23.md  ← вы здесь (L3-апекс)
├─ ЧТО ЕСТЬ      → docs/engine-subsystems-overview-2026-06-23.md
│    ├─ темы/collab-safety-subsystem-2026-06-23.md
│    ├─ темы/drivers-subsystem-state-2026-06-23.md
│    └─ темы/q016-assurance-state-2026-06-23.md
├─ ЧТО СТРОИТЬ   → docs/build-plans-overview-2026-06-23.md
│    ├─ темы/q017-semantic-consolidated-2026-06-23.md
│    ├─ темы/pyramid-grounding-consolidated-2026-06-23.md
│    └─ темы/build-specs-2026-06-23.md
└─ КАК ОРКЕСТРУЕТСЯ → docs/orchestration-architecture-2026-06-23.md
     ├─ docs/workflow-conveyor-policy.md  (tools/conveyor.py)
     ├─ docs/workflow-orchestration-policy.md
     └─ docs/nested-orchestration-3to1.md  (3:1 reduce-дерево)
```

**Инвариант сессии:** один контур «advisory-по-умолчанию → strict-по-триггеру», один backbone инструментов, один governance-потолок `D-018`. Движок построен и подкреплён кодом; планы аддитивны и ждут котла; оркестрация удерживает всё это под параллельным фронтом с единственной дешёвой серийной точкой — записью в одну git-историю. Статус `proposed`: сведение выносится в котёл на коллективную перепроверку (D-018) до перевода в `accepted`.
