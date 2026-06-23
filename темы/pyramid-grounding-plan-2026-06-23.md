---
id: pyramid-grounding-plan-2026-06-23
type: topic
title: Заземление пирамиды — derived coverage вместо самодекларации (план по находкам assurance)
status: proposed
date: 2026-06-23
related: [Q-016, D-018, promotion-rules, pyramid-candidate-map, assurance-and-doc-merge-2026-06-22]
---

# Заземление пирамиды (L2→L1) — план

## Как заземлить пирамиду честно (а не подделкой поля)

Обе карты сходятся: сегодня «grounding» проходит по двум слабым каналам — over-broad манифест с одной стороны и freeform-проза (`core:`) с другой, — а структурного ребра L2->L1 нет. Чинить нужно так, чтобы покрытие проходило по реальным ссылкам, проверяемым на существование.

**1. Сузить манифест до доказанного.** `core/engine-manifest.md:7` сейчас перечисляет 10 файлов (включая 2 теста), на которые НЕ ссылается ни один портал — отсюда все 12 orphan-L1 (`assurance.py:245-253`). Разделить на `files:` (8-инструментный переносимый engine, который и грейдится на reuse) и `candidates:` (knowledge.py + text_extract.py — второй export). orphan-L1 итерируется только по `files:` и теперь честно значит «обещано-переносимым-но-неиспользуемым». status остаётся `proposed` (Q2, D-018).

**2. Структурный l1_basis вместо прозы.** В `portals/example/portal.md` добавить однострочный bracket-list `l1_basis: [tools/knowledge.py, tools/text_extract.py]` — оба файла существуют (проверено) и именно их называет `current-state.md:13`. `_list_field` уже парсит такие списки.

**3. Derived coverage, не самодекларация.** Ключевой риск: `reused_in` НИГДЕ не пишется (нет ни одного writer-а — проверено), только читается в `promote.py:140`, `assurance.py:267`, документируется в `promotion-rules.md:52`. Значит критерий reuse_across_portals сегодня непроходим, а будь у него writer — его можно было бы подделать правкой поля. Решение: `derive_reuse(root)` сканирует, КТО ссылается на каждый L1-артефакт (basename-substring, тот же механизм, что в shipping orphan-L1), инвертирует в token->portals. Им питаются и assurance (grounded только если l1_basis резолвится в инвентарь; нерезолвящаяся запись => high-находка), и гейт `_gate_L2_L1` (>=2 разных портала). Вычисленный `reused_in` штампуется через `_stamp_fm` как provenance, не как авторская заявка. Правка поля больше не проходит гейт.

**4. Честная нерешённость.** Пока второго портала нет, reuse_across_portals намеренно непроходим, и L1 остаётся `proposed` — это документируется, а не маскируется. D-018 (collective ratification) сохраняется как decision-ref override: derived по умолчанию, ратифицированный явный список тоже валиден.

## Конкретные правки

### `core/engine-manifest.md`

**Правка:** Split the front-matter into two lists so the auditor's L1 inventory reflects demonstrated vs aspirational. Keep `files:` as the EXPORTABLE portable engine only (8 tools, no test files mixed in the reuse-graded set): `files: [tools/_canon.py, tools/validate.py, tools/generate.py, tools/next_id.py, tools/commit_lock.py, tools/pipeline.py, tools/dispatch.py, tools/merge_gate.py]`. Add a separate key `candidates: [tools/knowledge.py, tools/text_extract.py]` for the second-export tier (MCP/SQLite-coupled). Leave test_commit_lock.py / test_merge_gate.py out of `files:` (they ship with the export via promote.export's path handling but should not be reuse-graded as core tokens). Note in body that knowledge.py/text_extract.py are the genuinely L2-reused artifacts, hence candidates, not yet `files:`.

**Зачем:** Today `files:` lists 10 tools (incl. 2 test files) that NO portal references, generating all 12 orphan-L1 findings (assurance.py:245-253), while the one tool L2 actually reuses (knowledge.py, referenced in portal.md:7,19, current-state.md:13, workflows.md:13) is absent. Narrowing `files:` to the 8-tool demonstrated engine and moving knowledge/text_extract to `candidates:` makes orphan-L1 mean 'promised-portable-but-unused' honestly. promote.py:339 reads `files:` for export, so keeping it a clean exportable set avoids breaking core-export.

### `portals/example/portal.md`

**Правка:** Add a structured, single-line bracket-list grounding key parseable by _list_field: `l1_basis: [tools/knowledge.py, tools/text_extract.py]`. Keep the freeform `core:` sentence as human prose but make `l1_basis` the machine-checkable channel. These two files exist on disk (verified) and are exactly what current-state.md:13 names as the engine + extractor.

**Зачем:** Currently grounding is asserted only as the freeform `core:` string (portal.md:7), which assurance.py:267 accepts as non-empty without checking the referenced files exist or are L1. parse_front_matter is flat-line (portal.py:47-51 _list_field already parses bracket lists), so a single-line `l1_basis: [...]` is the canonical machine-readable form. This turns prose grounding into a verifiable edge to real L1 artifacts.

### `tools/assurance.py`

**Правка:** In section_coverage (242-253) iterate orphan-L1 over manifest `files:` ONLY (not `candidates:`), so candidate tools stop producing noise. In the ungrounded-L2 check (260-269) replace `grounded = any((fm.get(k)...) for k in (l1_basis,reused_in,core))` with a derived check: build the L1 inventory (basenames of `files:` + core/*.md), parse the portal's `l1_basis` via pr._list_field, and mark grounded only if at least one l1_basis basename resolves to an inventory item OR appears (basename substring) in the portal directory's markdown bodies. Additionally, for each declared l1_basis entry whose basename does NOT resolve to any inventory item, emit a `high` finding ('stale/typo L1 basis: <entry> not in core inventory').

**Зачем:** Replaces self-declared-any-non-empty grounding with existence-checked, L1-resolved grounding (Map 2 STEP 2). A portal is grounded only when it points at a real L1 token, and a typo'd or stale basis is flagged instead of silently passing. Reuses the exact basename-substring mechanic already shipping at 248-253, no new parser/index.

### `tools/promote.py`

**Правка:** Add `derive_reuse(root)` near _list_field: build L1 inventory from engine-manifest `files:` + core/*.md (token=basename), and for each portals/*/portal.md gather its `l1_basis` list plus the portal directory markdown bodies, marking a token reused-by-portal when its basename appears (same concat/substring as assurance._portal_text); return token->set(portal-ids). In _gate_L2_L1 (139-149) replace `reused = _list_field(fm.get('reused_in')); len(reused)>=2` with: count distinct portals referencing the artifact basename via derive_reuse, pass when >=2; keep a decision-ref override (D-018 ratified explicit list still passes). In move()/_stamp_fm path, stamp the COMPUTED reused_in into front-matter as scan provenance, not an author claim.

**Зачем:** reused_in has ZERO writers anywhere in the repo (verified: only read at promote.py:140, assurance.py:267, doc'd at promotion-rules.md:52), so reuse_across_portals can never pass today and editing a field could fake it. Deriving the count from who-actually-references-which-artifact makes the L2->L1 gate measure real reuse. Both assurance.py (which imports promote as pr) and promote.py share one implementation. _stamp_fm (201-217) already writes computed fields, so stamping derived reused_in is provenance not a claim.

### `docs/promotion-rules.md`

**Правка:** Update line 52 reuse_across_portals to state the criterion is now DERIVED: 'доказано повторное применение в >=2 порталах — измеряется сканом ссылок на артефакт (derive_reuse), а не самодекларацией поля reused_in; ratified explicit list в decision-ref остаётся валидным override (D-018)'. Add a one-line note that until a SECOND portal lands, reuse_across_portals is intentionally un-meetable and L1 promotion legitimately stays `proposed`.

**Зачем:** Documents the honest semantics: derived-by-default, ratified-override-allowed. Currently the doc describes reused_in as an author-supplied list, which the no-writers reality and the new derived gate contradict. The 'un-meetable until 2nd portal' note prevents anyone gaming the gate by adding a fake reused_in and explains why engine-manifest status stays proposed.

### `tools/test_assurance.py`

**Правка:** Extend _build_pyramid (62-68): make manifest `files: [tools/aa.py, tools/bb.py]` and add `candidates: [tools/cc.py]`; give p1 `l1_basis: [tools/aa.py]` with NO prose mention of aa, add p3 with `l1_basis: [tools/zz.py]` (zz not in inventory). Add assertions: p1 is grounded purely via l1_basis (no prose), p3 yields a `high` stale-basis finding for zz.py, candidate cc.py does NOT appear in orphan-L1, and a derive_reuse/promote-gate test where 1-vs-2 portals referencing aa flips _gate_L2_L1.

**Зачем:** The temp pyramid (test_assurance.py:62-93) already exercises orphan-L1 and ungrounded-L2; extending it locks in the new contracts: structured grounding without prose, stale-basis detection, candidate exclusion, and the derived 2-portal gate flip. Keeps everything stdlib and root-hermetic.

## Решение по манифесту

Yes — narrow core/engine-manifest.md. Split the single over-broad `files:` (10 entries incl. 2 test files) into two keys: `files:` = the 8-tool portable coordination engine actually graded for reuse (_canon, validate, generate, next_id, commit_lock, pipeline, dispatch, merge_gate), and `candidates:` = the second-export tier (knowledge.py, text_extract.py). Test files stay out of the reuse-graded `files:` set. This is the honest scoping the candidate map already implies (pyramid-candidate-map.md:24-40 separates the engine minimum from second-export candidates) and the manifest body already calls drivers+knowledge a 'second export'. status stays `proposed` (Q2 open, D-018 collective ratification). orphan-L1 then iterates `files:` only and means 'promised-portable-but-unused', not incidental word-absence. knowledge.py is NOT promoted into `files:` because it is the genuinely L2-reused artifact and belongs to the second-export tier; it grounds L2 via the portal's structured l1_basis + derive_reuse, not by being declared core.

## Buildable

**derive_reuse: derived portal->L1 coverage shared by assurance + promote gate** (effort M)

Add derive_reuse(root) in promote.py that builds the L1 inventory from engine-manifest files: + core/*.md (token=basename) and, for each portals/*/portal.md, gathers its l1_basis list plus portal-directory markdown bodies, marking a token reused-by-portal on basename substring (same mechanic as assurance._portal_text/orphan-L1) and returning token->portals. Wire assurance.section_coverage to (a) iterate orphan-L1 over files: only, (b) replace any-non-empty grounding with l1_basis-resolved-against-inventory grounding + high finding for unresolved basis. Wire _gate_L2_L1 to count distinct referencing portals via derive_reuse (pass >=2) with a D-018 decision-ref override, and stamp the computed reused_in via _stamp_fm as provenance. Narrow engine-manifest files:/candidates:, add structured l1_basis to the example portal, update promotion-rules.md:52, and extend test_assurance.py. All stdlib, root-hermetic, reuses _list_field/parse_front_matter/_portal_text/_stamp_fm.

- Файлы: `tools/promote.py`, `tools/assurance.py`, `core/engine-manifest.md`, `portals/example/portal.md`, `docs/promotion-rules.md`, `tools/test_assurance.py`

