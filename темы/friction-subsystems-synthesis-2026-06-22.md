---
id: friction-subsystems-synthesis-2026-06-22
type: topic
title: Синтез двух подсистем трения/параллельной работы (Claude cohort/policy ↔ Codex friction) — D-017
status: proposed
date: 2026-06-22
related: [D-017, D-018, D-022, T-150, T-153, gate-poison-situation-2026-06-22]
---

# Синтез: две подсистемы по одной теме — что слить, что оставить раздельно (D-017)

> **proposed** — предложение для коллективного принятия (D-017/D-018). Не правка чужих файлов соло. За сессию Claude и Codex независимо построили подсистемы для параллельной работы/трения; ниже честная сверка и план интеграции.

# D-017/D-018 предложение: две подсистемы как один контур parallel-work (детектор → политика → governance)

> Статус: **proposed** (НЕ accepted соло). Вносится в котёл по D-018 для коллективного синтеза двух независимо построенных подсистем — CLAUDE Coordination Engine (claude) и FRICTION (codex) — над одной темой: параллельная работа / трение / gate-гигиена.

## 1. Что обнаружилось

За одну сессию два агента независимо построили подсистемы для одной темы. Они **не дубликаты, а две половины одного контура**:

- **FRICTION (codex)** — read-mostly **детектор**: видит симптом, мапит на F-XXX, печатает рецепт. Сознательно НЕ принимает решений и НЕ мутирует (`tools/friction.py`, scope statement: «not a self-healing OS»).
- **CLAUDE Engine (claude)** — **исполнитель**: принимает решение L0/L1, держит замки и worktree, проводит merge-gate (`tools/cohort.py`, `flow.py`, `worktree.py`, `merge_gate.py`).

Их столкновение материализовалось в **одном инциденте — T-150**: незавершённая задача Codex (`topic:` на ещё не созданный файл) сделала мой общий `validate.py` КРАСНЫМ и через pre-commit заблокировала коммиты ВСЕМ (`темы/gate-poison-situation-2026-06-22.md`, §1.1; `tools/validate.py:166-168,427`). Мой `cohort guard` это **детектирует** (`tools/cohort.py:350-353`); ledger Codex **объясняет, почему это повторяется** (F-006/F-007/F-011/F-015). Ни один не указывает на другой.

## 2. Архитектура контура: детектор → политика → governance

```
        ┌─────────────────────────── ДЕТЕКТОР (read-only) ───────────────────────────┐
        │  FRICTION (friction.py status)           CLAUDE (cohort.py guard)           │
        │  F-005 lock / F-006 dirty / F-007 stale  uncommitted-source / hot-file /    │
        │  F-008 volatile / F-011 drift / F-013    stale-index / GATE-POISON(F-020)   │
        │  stream                                  (validate ERROR=N)                 │
        │                                                                             │
        │            ▼ общий ownership-классификатор (mine|generated|                 │
        │              volatile|foreign|unknown)  ← СЛИТЬ СЕЙЧАС                       │
        └──────────────────────────────────┬──────────────────────────────────────────┘
                                            │ evidence
        ┌───────────────────────────────────▼─────────────────────────────────────────┐
        │                       ПОЛИТИКА (decision)                                    │
        │  parallel-work-policy: validate ERROR → L1 или ждать; stale-MINE → regen;    │
        │  stale-FOREIGN → не коммитить смешанный индекс → Level-1 worktree            │
        │  ВЛАДЕЛЕЦ РЕШЕНИЯ: CLAUDE Engine (flow/worktree/merge_gate). FRICTION НЕ      │
        │  решает — отдаёт улики.                                                       │
        └───────────────────────────────────┬─────────────────────────────────────────┘
                                            │ ratify
        ┌───────────────────────────────────▼─────────────────────────────────────────┐
        │                       GOVERNANCE (D-006/D-017/D-018/D-021/D-022)             │
        │  Лестница автоматизации (codex): 1→набл / 2-3→playbook / 4+→skill /          │
        │  6+→detector / 8+ или data-loss→guard.  Структурные правки общего gate       │
        │  (scoping validate.py) — только через котёл, не соло.                        │
        └──────────────────────────────────────────────────────────────────────────────┘
```

**Поток на примере T-150 (gate-poison):**
1. `friction status` / `cohort guard` запускают `validate.py` → `ERROR=N>0` → детектят **F-020 gate-poison**.
2. Общий ownership-классификатор: битый source принадлежит **чужому** claim → quarantine.
3. Политика: НЕ ждать чужой коммит как стратегию → `flow.py start --worktree` от ЧИСТОЙ базы; merge — когда гейт очистится (`tools/cohort.py:376-378`).
4. Governance: детектор одобрен сейчас (read-only); **структурный фикс** (per-zone validate) — в котёл по D-018.

## 3. Единая точка входа (рекомендация)

Сейчас два силоса бьют по одному инциденту без перекрёстной ссылки. Предлагаю **`tools/top.py preflight`** как единую кнопку, которая:

- запускает **общий ownership-классификатор + freshness-probe ОДИН раз** (сегодня `generate.py --check` гоняется дважды: `cohort.py:346` и `friction.py:548`);
- показывает строку FRICTION (что за симптом, какой F-id, рецепт) **и** строку GUARD (вердикт L0/L1) рядом;
- на F-020 печатает обе: `friction recipe F-020` (почему/как) + `cohort guard` (куда эскалировать).

FRICTION остаётся источником правды по симптомам и рецептам; CLAUDE Engine — по решению и исполнению. `preflight` — это фасад над обоими, не третий движок.

## 4. Что слить сейчас, что оставить раздельно

- **Слить:** ownership-классификатор (P1-блокер в обеих картах), validate-ERROR probe → F-020 в `friction.py`, единый freshness-probe, перекрёстные ссылки в выводе, лестница автоматизации как общее правило.
- **Раздельно:** логика эскалации L0/L1 (мой движок) ; реестр F-XXX как registry (шире parallel-work — Windows/encoding/sandbox) ; мутирующие механизмы (lock/worktree/stream-adopt — мои, read-only граница Codex священна) ; meta-политика порога автоматизации (governance Codex).

Чистый шов между подсистемами = **граница read/write**: FRICTION наблюдает, CLAUDE мутирует. Это и есть архитектурный инвариант, который надо зафиксировать в D-017/D-018.

## Перекрытие (overlap)

| Аспект | Claude | Codex | Вердикт |
|---|---|---|---|
| Dirty / foreign uncommitted source in shared tree | cohort.py guard parses git status --short, filters M-code within SOURCE_DIRS → trigger `uncommitted-source` (tools/cohort.py:344, 356-357) | friction.py check_git_status splits dirty into nonvolatile/volatile/generated → F-006/F-008/F-015 warns (tools/friction.py:354-394); ledger F-006 (docs/friction-ledger.md:25) | complement — same raw signal (git status), different lens: mine = escalation decision (L0/L1), Codex = symptom classification (which F-id). Both blind to ownership (mine/foreign/unknown). Merge the ownership classifier, keep both consumers. |
| Stale generated indexes | guard runs generate.py --check → trigger `stale-index` (tools/cohort.py:346-347, 360-361) | check_generate rc!=0/STALE → F-007 warn; check_drift → F-011 (tools/friction.py:412-419, 445-449) | duplicate detector, complementary framing. Both shell out to generate.py --check. Codex adds drift_check.py layer. Single freshness probe should feed both. |
| Volatile runtime noise (LIVE.md, logs/*) | policy-level canonical-vs-volatile split (docs/parallel-work-policy.md); guard excludes via HOT_FILES set, not a volatile check | check_volatile_tracking + F-008: detects volatile still git-tracked AND missing from .gitignore (tools/friction.py:397-409) | complement — Codex's mechanical check (tracked? ignored?) is strictly stronger than my policy text. Adopt Codex F-008 check as the enforcement arm of my policy. |
| Gate-poison (whole-tree validate ERROR blocks all commits) | guard runs validate.py, parses ERROR=N → trigger `gate-poison`, prints clean-base worktree advice (tools/cohort.py:350-353, 376-378); incident doc темы/gate-poison-situation-2026-06-22.md:1.1 | named as symptom only — F-006/F-007/F-011/F-015 cover the *cause* (foreign half-done), but friction.py collect_status NEVER runs validate.py, so no ERROR>0 detector (tools/friction.py:530-571) | complement (gap on Codex side). The T-150 incident IS the collision: Codex's own half-done task poisoned my gate. My guard detects it; Codex's ledger explains why it recurs. Wire my validate-ERROR probe into friction.py as the F-020 detector. |
| Commit-lock / index.lock serialization | commit_lock.py O_EXCL TTL~120s, wrapped in cohort ship (model: Level-0) | check_commit_lock parses lock status → F-005 (tools/friction.py:422-428); ledger F-005 (docs/friction-ledger.md:24) | complement — mine owns the mechanism (acquire/release), Codex observes its state read-only. No conflict; Codex is the diagnostic mirror of my lock. |
| Stream lifecycle / adoption | stream.py check (stale>14d, broken FM); variants.py registry | check_stream → F-013; ledger flags 2 legacy broken streams found during T-150 (tools/friction.py:452-456; gap P0) | duplicate tool call (both shell stream.py check), complementary backlog. Same source of truth; merge reporting, keep my stream.py as the engine. |
| Level-0 / Level-1 escalation decision | core engine: guard → recommend L1 worktree; flow.py/worktree.py execute (model: layered coordination) | explicitly out of scope — friction is detector/gate, defers decision to D-022/parallel-work-policy; gap: 'ownership-aware classifier needed for L0/L1 precision' | stay separate — Codex correctly does NOT make the escalation decision. My engine owns it. Codex feeds evidence; I decide. Clean boundary. |
| Automation threshold / when to build a guard | implicit (D-022 triggers A-F); no calibrated repeat-count rule | explicit calibrated ladder: 1 observe / 2-3 playbook / 4+ skill / 6+ detector / 8+ guard (docs/friction-ledger.md:159-167) | stay separate — Codex owns governance/cadence. This is the meta-policy that decides whether my triggers graduate into guards. Adopt as shared rule, Codex remains author. |

## Слить сейчас (merge_now)
- Single ownership-aware dirty classifier (the P1 blocker in both maps): one function file→{mine\|generated\|volatile\|foreign\|unknown} using SOURCE_DIRS + GENERATED_SHARED + VOLATILE + queue/claim→task→file mapping. cohort.py guard (tools/cohort.py:344-345) and friction.py check_git_status (tools/friction.py:354-359) both reimplement git-status parsing and both lack ownership resolution. Extract to a shared module (e.g. tools/ownership.py) consumed by both. This closes my gap 'no per-agent scoping' AND Codex gap 'classifier does not exist yet'.
- Wire the gate-poison/validate-ERROR probe into friction.py as F-020. cohort.py guard already runs validate.py and parses ERROR=N (tools/cohort.py:350-353); friction.py collect_status (tools/friction.py:530-571) runs eight probes but NOT validate.py. Add a check_gate_poison() that shells validate.py, parses ERROR=N, and emits F-020. Both detectors then agree on the single most dangerous shared-tree state (T-150 class).
- Unify the freshness probe: generate.py --check is run independently by cohort guard (tools/cohort.py:346) and friction check_generate (tools/friction.py:548-549). Run once, share the result, so a parallel session does not trigger two redundant 45s generator runs.
- Make `cohort guard` and `friction status` cross-link in output: guard's L1 recommendation should point to `friction recipe F-020`; friction status' F-006/F-020 warns should point to `cohort guard` for the escalation verdict. Today they are two silos hitting the same incident (T-150) with no pointer between them.
- Adopt Codex's automation ladder (docs/friction-ledger.md:159-167) as the shared governance rule for when a D-022 trigger graduates into a blocking guard. My triggers A-F currently have no calibrated promotion criterion; Codex's 8+/data-loss threshold supplies it.

## Оставить раздельно (stay_separate)
- Escalation decision logic (L0/L1/L2 worktree, merge-gate, 3-variant same-file fork). This is my engine's job (cohort/flow/worktree/merge_gate). Codex's own scope statement excludes 'agent decision-making' — friction is a detector, not a dispatcher. Merging would make friction a second orchestrator, which Codex's retrospective explicitly warns against ('маленькие detector/guard слои, не большой диспетчер').
- The F-XXX ledger as a registry (F-001..F-019). It spans far beyond parallel-work (Windows runtime F-001..004, encoding, external-code sandbox F-012, skill drift F-018). Folding it into my coordination engine would dilute both. It stays Codex-owned; my engine just contributes the parallel-work archetypes (F-005..F-008, F-015, F-020).
- Execution mechanisms: commit_lock acquire/release, worktree spawn/remove, stream adopt. These are mutating operations under my ownership (D-021: merge-gate = Stefan/integrator). Codex's read-only-by-default architecture must NOT take on mutation; it observes lock/stream/worktree state, it does not change it. The read/write boundary is the cleanest seam between the two subsystems.
- The automation-threshold meta-policy itself stays Codex-authored governance. I consume it; I do not own the cadence of 'when does a recipe become a guard'.

## Архетип F-020 (предложение в friction-ledger Codex'а)

- **Класс:** shared-gate transient poisoning (whole-tree commit block from one foreign half-done task)
- **Определение:** One agent's incomplete task makes the project-wide validate gate RED, and because the pre-commit hook runs validate.py over the WHOLE tree (tools/githooks/pre-commit:45) with exit 1 on any ERROR (tools/validate.py:427), every agent's commit is blocked — including agents editing unrelated files. Canonical instance: T-150 declared topic: docs/friction-retrospective-2026-06-22.md before the file existed; validate.py:166-168 saw os.path.exists()==False → err() → ERROR>0 → exit 1 → all commits rejected until Codex created the file. Poison classes: missing-topic-file, bad front-matter, dupe-id, stale-index, broken xref. Scope is whole-tree (validate.py has no agent/zone scoping); the block is transient (clears when the foreign half-done state is completed or removed).
- **Детектор:** cohort guard gate-poison + S1 validate quarantine. (1) cohort.py guard already implements the primary probe: run validate.py, regex ERROR=(\d+), if >0 emit trigger gate-poison with up to 3 ERROR lines as evidence (tools/cohort.py:350-353). (2) Port this into friction.py as check_gate_poison() (currently absent — collect_status at tools/friction.py:530-571 runs generate/drift/stream but never validate, so friction is blind to the single most dangerous state). (3) S1 validate quarantine = stage 1 of the gate distinguishes MINE vs FOREIGN ERROR using the shared ownership classifier (merge_now item 1): if the offending source file maps to my own claim → it is my bug, fix it; if it maps to a foreign/unknown claim → quarantine, do NOT wait, escalate to L1 worktree from a CLEAN base.
- **Политика:** parallel-work-policy: validate ERROR→L1 or wait. If validate ERROR is caused by MY uncommitted source → fix-forward (create missing file / repair FM), then ship. If caused by FOREIGN half-done → do NOT wait for the coworker's commit as a strategy (matches my 'no waiting' rule and Codex F-007 recipe 'do not commit a mixed index'): go Level-1 worktree from a clean base (tools/cohort.py:376-378), merge back only after the shared gate clears. Short transient (<5 min) wait is tolerable; structural recurrence triggers the automation ladder.
- **Governance:** Per the Codex automation ladder (docs/friction-ledger.md:159-167), gate-poison qualifies for the guard/gate tier (8+ repeats OR commit/data-loss risk) — it is a whole-tree commit blocker, the highest-severity class. The DETECTOR is approved now (read-only, already live in cohort guard). The STRUCTURAL fix — scoping validate.py per-agent / per-zone so one foreign error does not block all — is NOT a solo edit: it changes the shared gate contract and must go through D-017/D-018 collective acceptance (котёл + technical + humanitarian double-check). F-020 stays a proposed shared archetype until ratified; ownership of validate.py scoping is integrator/Stefan (D-021).

## Открытые вопросы коллективу
- F-020 структурный фикс: scoping validate.py по агенту/зоне (чтобы одна чужая ERROR не блокировала всех) vs per-task pre-commit vs оставить whole-tree + быстрый детектор. Меняет контракт общего gate — нужен явный консенсус и владелец (integrator/Stefan по D-021). Кто пишет, в каком worktree?
- Где живёт общий ownership-классификатор: новый tools/ownership.py, импортируемый и cohort.py и friction.py? Чей это owner — claude (часть engine) или codex (часть детектора)? Нужен ли третий нейтральный модуль, чтобы ни одна подсистема не тянула зависимость на другую?
- Единая точка входа: `top.py preflight` (новая) vs расширить существующую `top.py friction` (codex) vs `cohort guard` (claude)? Кнопка должна звать обе подсистемы — кто её владелец и как избежать двойного запуска validate/generate?
- Лестница автоматизации (1/2-3/4+/6+/8+) принимается как общее governance-правило для ВСЕХ триггеров (включая мои D-022 A-F), или остаётся внутренней нормой FRICTION? Если общая — где канон (docs/friction-ledger.md или новый decision)?
- Repeat-counters: F-017 говорит, что счётчики приблизительные. Нужен ли logs/friction.jsonl как ОБЩИЙ event-log, в который пишут и guard, и friction status, чтобы решение 'detector→guard' опиралось на факты, а не оценки? Формат и владелец?
- Граница read/write как инвариант: фиксируем ли в D-017/D-018 явно, что FRICTION никогда не мутирует (только temp-probe), а все мутации — через CLAUDE Engine под commit_lock/merge_gate? Это снимает риск, что детектор обрастёт auto-fix.
- 2 legacy broken streams, найденные при T-150 (gap P0 Codex): чинить front-matter или закрывать? Это отдельная P0-задача в котёл — кто берёт и под каким T-id?
