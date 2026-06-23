---
id: assurance-hardening-plan-2026-06-23
type: topic
title: Hardening assurance — лестница warn→block (S0..S4) + apex-подключение
status: proposed
date: 2026-06-23
related: [Q-016, D-018, D-021, instruction-assurance, assurance-and-doc-merge-2026-06-22]
---

# Hardening assurance — план (Q-016, эскалация)

Карты согласованы и проверены по живому репозиторию: assurance.py — это законченный read-only apex-дашборд (Q-016), который не подключён НИ К ЧЕМУ (drift_check.py:90 запускает validate, не assurance; top.py cmd_health на :281-289 — только validate/generate/capabilities/catalog), pipeline.py cmd_done WARN советует, но не блокирует (:342-343), а validate.py проверяет лишь ФОРМАТ source_last_verified (:334-337), не возраст. Лестница warn->block, которую сам Q-016 называет (:49), естественно ложится на пять стадий.

Принцип: НЕ строить второй движок свежести. section_currency в assurance.py уже умеет всё — нудж accepted-без-last_verified (:203), возраст по last_verified|date (:206-208), ссылки на superseded (:210-213). Конвенция last_verified+supersedes — это просто front-matter, который этот код уже читает через line-based _canon.parse_front_matter (правок парсера ноль).

Стадии:
- S0: один governance-коммит — штамп last_verified=2026-06-23 на 19 accepted + 4 политики, 4 proposed не трогаем, без back-date (сбрасывает SLA-часы в 0).
- S1 (строить первым): подключить готовый assurance.py в warning-layer — drift_check.py:90 и apex-SPEC в top.py (кнопка, subparser, cmd_assurance с fail_ok=not strict, строка в cmd_health после :290, строка в cmd_agent_start после :296). Аддитивно, конфликт-лайт, exit-0 по умолчанию — health/CI остаются зелёными. top.py владеет Codex параллельно -> через subagent-handoff/worktree (D-021), якорь по именам символов.
- S2: реализовать задокументированное правило «>30 дней предупреждает» ТОЛЬКО для драйверов в validate.py:334 (WARN, не валит билд).
- S3: opt-in strict — флаг в pipeline.py cmd_done и доступный `assurance --strict` для CI/ревью, без обязательности.
- S4: после квартала данных — добавить `assurance currency --strict` в merge_gate.gate_stages (:55), туда же, где уже гейтят validate/generate.

Ключевое разделение: validate.py получает 30-дневный driver-WARN; решения/политики идут через assurance.py (advisory сейчас, strict-гейт потом), НЕ через ужесточение driver-WARN до ERROR — у них разный SLA (90 vs 30) и разный радиус поражения.

## Стадии

| Стадия | Posture | Что | Файлы |
|---|---|---|---|
| **S0 - Migration prep (governance commit, no code)** | advisory | Stamp last_verified = 2026-06-23 on the 19 accepted decisions (D-001..D-013, D-015..D-018, D-021..D-023) and the 4 currency-target policies (parallel-work-policy, promotion-rules, workflow-orchestration-policy, instruction-assurance). Do NOT back-date; do NOT touch the 4 proposed (D-014/D-019/D-020). This resets every SLA clock to 0 so the freshness signal starts clean instead of firing ~23 times on day one. Declare ONE SLA number: 90d for decisions/policies, 30d for drivers. | `decisions/D-001.md`, `decisions/D-018.md`, `docs/parallel-work-policy.md`, `docs/promotion-rules.md`, `docs/workflow-orchestration-policy.md`, `docs/instruction-assurance.md` |
| **S1 - Advisory wiring (surface, never block)** | advisory | Wire the already-built assurance.py into the warning layer everywhere it is currently absent: (a) add an assurance (no --strict) line in drift_check.run() after the validate block (drift_check.py:90); (b) add the apex surface in top.py via the four additive, conflict-light changes from the Apex SPEC (button, assurance subparser, cmd_assurance handler with fail_ok=not args.strict, warning-layer line in cmd_health after :290, fail_ok line in cmd_agent_start after :296). top.py is owned by Codex in parallel -> apply via subagent-handoff/Level-1 worktree (D-021), anchored on named symbols not line numbers. assurance.py is exit-0 by default so health/merge_gate/CI stay green. | `tools/drift_check.py`, `tools/top.py`, `tools/assurance.py`, `docs/top-layer-command-groups.md`, `docs/agent-onboarding.md` |
| **S2 - Driver freshness WARN (closes documented gap)** | advisory | Implement the documented-but-unimplemented '>30 days warns' rule for DRIVERS ONLY in validate.py check_drivers, right at the existing source_last_verified format check (validate.py:334-337). validate WARN does not fail the build, so this is advisory-by-construction. Keep 30d for drivers; this is the only validate.py freshness change. Do NOT add decision/policy freshness to validate.py - assurance.py section_currency already owns that (assurance.py:206-208). | `tools/validate.py`, `docs/driver-safety-policy.md`, `drivers/SCHEMA.md` |
| **S3 - Opt-in gate (strict available to callers, not yet mandatory)** | opt-in-gate | Expose strict assurance as an opt-in gate without making it part of the default merge gate. cmd_assurance already propagates exit 1 under --strict (fail_ok=not args.strict). Add an opt-in strict path to cmd_done in pipeline.py mirroring the existing advisory WARN at pipeline.py:342-343 (a --strict flag that escalates the advisory applied-evidence WARN to a hard fail). CI/reviewers can run `top.py assurance currency --strict` voluntarily. Collect a quarter of last_verified data before escalating further. | `tools/pipeline.py`, `tools/assurance.py`, `tools/top.py` |
| **S4 - Blocking gate (after a quarter of clean data)** | blocking | Promote currency to a hard merge stage by adding ('assurance currency --strict', 'assurance.py', ('currency','--strict')) to merge_gate.gate_stages (merge_gate.py:55) - the same list where validate/generate already gate. This is the warn->block ladder Q-016:49 names. Gate decisions/policies via assurance only; do NOT harden the validate.py driver WARN to ERROR - drivers and governance docs have different SLAs and blast radius. Precondition: all last_verified gaps closed and 90d convention has run one full quarter. | `tools/merge_gate.py`, `tools/assurance.py`, `questions/Q-016.md` |

## Строить первым

S1 apex+drift wiring of the existing assurance.py (warning layer). Highest value/effort ratio: assurance.py is a finished, verified read-only dashboard wired into NOTHING (drift_check runs validate not assurance at drift_check.py:90; top.py cmd_health runs validate/generate/capabilities/catalog but no assurance at top.py:281-289). The changes are purely additive and conflict-light (one drift_check line, one button, one subparser, one handler, two fail_ok=True lines), carry zero blocking risk because assurance.py is exit-0 by default (assurance.py:382), and they immediately make the currency/applied/coverage/flow verdict visible to every agent and health caller. Everything downstream (S3 opt-in, S4 blocking) depends on this surface existing first, and it honors the read/observe boundary assurance.py was designed around.

## Риски

- top.py is concurrently owned by agent Codex (D-018/D-021): editing it directly will conflict. Mitigation: apply via `top.py subagent-handoff codex ... --worktree` and anchor on named symbols (_BUTTONS 'health' dict, build_parser 'health' subparser, cmd_health, cmd_agent_start), not absolute line numbers which will drift under parallel edits.
- Folding assurance into cmd_health's hard-gated loop (top.py:281-289) would turn `health` red today (live verdict is ATTENTION with high/medium findings) and break every merge_gate/CI caller of health. Mitigation: keep it strictly as a fail_ok=True warning-layer line after :290, mirroring the existing drift_check precedent.
- SLA conflict: assurance.py defaults --max-age to 180 (assurance.py:361) while the convention recommends 90 for decisions/policies and driver-safety-policy.md:14 says 30 for drivers. Three numbers in play. Mitigation: declare ONE number per corpus (90 governance / 30 drivers) and align the assurance default + the convention doc so tool and prose never disagree.
- Back-dating last_verified during migration would either lie about verification or instantly fire the freshness signal ~23 times, training everyone to ignore it. Mitigation: stamp today (2026-06-23) on the 19 accepted + 4 policies only, leaving the 4 proposed decisions untouched (last_verified is an accepted/policy property; assurance.py:203 already gates on status==accepted).
- Premature blocking (S4 before a quarter of data) would gate merges on a brand-new convention with thin signal. Mitigation: S4 is explicitly gated on all last_verified gaps closed AND one full 90d quarter elapsed, per the Q-016:49 ladder.
- Driver WARN->ERROR temptation: hardening validate.py's driver freshness to ERROR to 'also cover' decisions conflates two SLAs and blast radii. Mitigation: governance currency gates ONLY through assurance.py/merge_gate; the validate.py driver check stays a 30d WARN.

