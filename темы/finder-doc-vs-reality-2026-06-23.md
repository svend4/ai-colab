---
title: "FINDER — doc-vs-reality синтез (26 подтверждённых находок)"
date: 2026-06-23
status: proposed
verified_against_head: 0bc8b3b
kind: finder-synthesis
audience: router/orchestrator
---

# FINDER: doc-vs-reality 2026-06-23

26 подтверждённых находок (все real: true, верифицированы против живого кода @ HEAD 0bc8b3b). Высоких нет: 9 med, 17 low. Доминирующий паттерн — doc-underclaims-undone (синтез-отчёты темы/*.md и доки docs/*.md держат уже зашипленную работу как «proposed / Осталось / build-кандидат»). Вторичный кластер — dangling-ref / integrity-gap (line-anchor drift, переименованные deliverable'ы, decision-cross-link разрывы) и 3 machine-red детектора на реальном generated-index лаге.

Ранг: severity (med > low), затем масштаб/blast-radius (сколько доков/читателей вводится в заблуждение, канон vs working-tree), затем критичность пути (искажает ли critical-path/gate).

---

## A. fix-inline — стейл-доки, чинятся правкой текста (основной выход роутера)

Самый массовый кластер: документы под-/пере-заявляют статус относительно кода. Нужно отметить SHIPPED / снять status: proposed / обновить line-якоря. Кода трогать НЕ надо.

P1 — perspective-backlog: 7 пунктов (#1-#6,#8) помечены build/cauldron, хотя зашиплены · med · fix-inline
темы/perspective-backlog-2026-06-23.md:42-49 (committed d2d7a03); reality: #1 pipeline.py _evidence_gaps/check_report_text, #2 friction.py:479, #3 doc_consensus.py:299 --semantic, #4 порталов=3, #5 instructions.py:526, #6 20×last_verified, #8 parallel-work-policy.md уже «SHIPPED». Самый широкий масштаб — 7 шипов в ОДНОЙ ранж-таблице, кормит conveyor.py next (риск повторного запуска закрытой работы). Нюанс: working-tree (uncommitted) уже переписан в «Shipped/closed» — роутеру проверить коммит; если закоммичено — already-ok. direction: doc-underclaims-undone.

P2 — q016 item #9 / fleet-designs §2: «построить 2 L2-портала, порталов=1» — порталов=3 · med · fix-inline
темы/q016-assurance-state-2026-06-23.md:88 + темы/fleet-designs-2026-06-23.md:39-41 (status: proposed :5); reality: portals/bridge-knowledge/ + portals/repo-inventory/ существуют, assurance coverage → «порталов: 3, orphan-L1: 0» (144bb7b+a47e8c9). Бьёт по ДВУМ докам. Коммит d2d7a03 правил ту же таблицу, пометил #8 SHIPPED, но #9 пропустил. direction: doc-underclaims-undone.

P3 — new-problems (status: proposed): все 3 проблемы поданы нерешёнными — все 3 зашиплены · med · fix-inline
темы/new-problems-2026-06-23.md:4 + :11; reality: F-020 friction.py:479+REGISTRY:276 (67fa8b5); base↛apex surfaces-ключ + instructions.py:243 trace (53e6d61) + assurance.py:291 (83ac920); gateway drivers/gateway.md:57-73 переписан (T-174). direction: doc-underclaims-undone.

P4 — q016 item #1 (S0 last_verified migration) держится открытым ratify — зашиплен на 20 решениях · med · fix-inline
темы/q016-assurance-state-2026-06-23.md:65; reality: grep -rl last_verified decisions/ = 20 (9ffb509). Док правился d2d7a03 ПОСЛЕ миграции, пометил #8 SHIPPED, но #1 оставил стейл → искажает critical-path (#1 будто блокирует #2/S4). direction: doc-underclaims-undone.

P5 — q016 item #3 (report_reference_findings) открыт build-spec «её НЕТ» — функция существует · med · fix-inline
темы/q016-assurance-state-2026-06-23.md:72; reality: def report_reference_findings@tools/instructions.py:526, вызов :580 (763691b). Якорь :404-417 устарел — cmd_check_report теперь :571. direction: doc-underclaims-undone.

P6 — q016 item #5 (derive_reuse в promote.py) открыт worktree-build — зашиплен · med · fix-inline
темы/q016-assurance-state-2026-06-23.md:79; reality: def derive_reuse@tools/promote.py:106, гейт :184/:192 (6ede574). Якорь _gate_L2_L1:139-143 устарел → реально :181-198. direction: doc-underclaims-undone.

P7 — solver-report P4 «proposed, ничего не применено» — cohort/flow --strict зашиплен · med · fix-inline
темы/solver-report-2026-06-23.md:13 + таблица :19; reality: MANDATORY_TRIGGERS@cohort.py:52, ship(strict=)@:259, turn(strict=)@:208, guard(strict=)@:386 (e3907a4, ПОСЛЕ self-pinned 144bb7b). Нюанс: self-pin к 144bb7b — стейл-но-честный снимок, но @HEAD вводит в заблуждение. direction: doc-underclaims-undone.

P8 — engine-subsystems-overview: reconcile_state.py fix в «Осталось» как заглушка — зашиплен · med · fix-inline
docs/engine-subsystems-overview-2026-06-23.md:91; reality: cmd_fix()@:259 (dry-run+--apply, DERIVED_CODES@:237, PRIMARY-drift refused :284-288), 94c3c35. Коммит d2d7a03 пометил fix SHIPPED в 4 ДРУГИХ доках, но строку 91 пропустил. direction: doc-underclaims-undone.

P9 — session-state: top.py assurance-wiring в remaining buildables — 5 правок зашиплены · low · fix-inline
темы/session-state-2026-06-23.md:76-77; reality: cmd_assurance@top.py:302, _BUTTONS id:assurance@:82, subparser@:679, warning-layer@:325, advisory@:332 (91cd162 — TOP цитируемого докном окна). direction: doc-overclaims-done.

P10 — backlog/session-state: «Populate L2 portals» как ready-to-build — порталы зашиплены · low · fix-inline
темы/perspective-backlog-2026-06-23.md:32+:45 + темы/session-state-2026-06-23.md:52; reality: 144bb7b+a47e8c9, 3 портала. Caveat: backlog в working-tree правлен, но session-state:52 НЕ тронут → расхождение держится в каноне. Оставлен отдельно от P1/P2 из-за session-state.md. direction: doc-overclaims-done.

P11 — Q-016 (open) перечисляет optional escalations как remaining — построены в коде · med · fix-inline
questions/Q-016.md:48; reality: pipeline.py:356-374 done --strict (коммент «S3 лестницы Q-016»), top.py:679 assurance-кнопка, top.py:332/325. НЕ построена ТОЛЬКО human last_verified front-matter convention (assurance детектит на :202-226). index.json:2291 status open. direction: doc-underclaims-undone. Правка: сузить остаток до one convention.

P12 — Q-008 front-matter answered, хвост говорит «остаётся open, D-013 не accepted» · low · fix-inline
questions/Q-008.md:104; reality: D-013 accepted (DECISIONS.md:22, D-013.md:5), Q-008 status: answered (:5). Обе посылки хвоста ложны. Front-matter (что читают тулы) корректен → impact косметический. direction: doc-overclaims-done.

P13 — gateway.md: рассинхрон даты source_last_verified (FM 2026-06-23 vs проза 2026-06-21) · low · fix-inline
drivers/gateway.md:17 vs :54; reality: проза :54 устарела (фактич. 2026-06-23 — раздел :57-75 + reports/mcp-async-stdio-monitor-forced-2026-06-23.md; контракт проходит mcp_sync_acceptance pass=6 fail=0). direction: integrity-gap.

---

## B. ratify — accepted-решения опираются на непринятое / proposed-записи устарели (governance-действие)

P14 — Accepted D-021 цитирует proposed D-014 как binding («execute = OFF (D-014)») · med · ratify
decisions/D-021.md:44; reality: D-014.md:6 status: proposed (пустой плейсхолдер до 2026-06-23, e324e79); T-175.md:48 «D-014 НЕ accepted ... blocked до Stefan»; DECISIONS.md:23 D-014=proposed. direction: integrity-gap. Disposition ratify: разрыв закрывается ратификацией D-014 (blocked на Stefan). До неё — пометить цитату «pending D-014».

P15 — D-019 (proposed) устарел: Level-1 «remains proposed», но ратифицирован D-021/D-022 — нет superseded-note · med · ratify
decisions/D-019.md:32; reality: D-019 proposed, :32 «pending Stefan», :59-65 «remains proposed»; но D-021.md:21 «Уровень-1 — ПРИНЯТ» + D-022.md:24 «ОБЯЗАТЕЛЕН ПО ТРИГГЕРАМ» (accepted). Конвенция cross-link есть: sibling D-020 ПОЛУЧИЛ «Postscript — D-021» (D-020.md:19-21), D-019 — нет. direction: doc-overclaims-done. Disposition: добавить superseded-in-part note по образцу D-020.

---

## C. build — работа реально НЕ сделана, доки честно держат открытой (распределить в worktree)

P16 — q016 item #6 (section_coverage existence-checked grounding) реально НЕ сделан · low · build
темы/q016-assurance-state-2026-06-23.md:80; reality: assurance.py:267 всё ещё grounded = any((fm.get(k) or '').strip() for k in (...)) — исходный any-non-empty; l1_basis-резолв НЕ внедрён (grep: l1_basis только :267/:269). Док честно держит open. direction: genuinely-undone.

P17 — q016 item #7 частично: engine-manifest split сделан, portal.md без структурного l1_basis · low · build
темы/q016-assurance-state-2026-06-23.md:81; reality: split СДЕЛАН (core/engine-manifest.md:7 files:[8] + :8 candidates); portals/example/portal.md:7 freeform core:, Grep l1_basis = 0. Спека pyramid-grounding-plan:18,34-36. Частично открыт. direction: genuinely-undone.

---

## D. machine-red — детекторы на реальном generated-index лаге (regen + selective-add, НЕ git add -A)

Один корень: source-карта T-176 (doing/Mavis→done/codex) разошлась с TASKS.md/index.json, T-177/T-178 отсутствуют в навигации. python tools/generate.py закрывает все три. Реальный docs↔fact лаг, не шум. git status уже несёт M TASKS.md, M index.json.

P18 — friction status: F-007 generated indexes stale (TASKS.md навигация устарела) · med · fix-inline
tools/friction.py status; reality: generate.py --check → «STALE: TASKS.md / index.json», exit=1; regen переписывает. recommendation: LEVEL 1 OR SELECTIVE-ADD; do not use git add -A. direction: integrity-gap.

P19 — drift_check: навигация/index устарела (STALE, EXIT=1) · med · fix-inline
tools/drift_check.py; reality: «ДРЕЙФ обнаружен (1): STALE: навигация/index», воспроизведено; после regen exit=0. Тот же корень, что P18. direction: integrity-gap.

P20 — reconcile_state check: status=warning, 45 предупреждений (EXIT=1) · med · build
tools/reconcile_state.py; reality: 38 done-missing-marker (T-001..,T-168..T-173 — нет queues/done/T-NNN.done.md), 5 orphan-done-marker (marker есть, tasks/*.md нет), 1 pipeline-snapshot-drift (волатилен). Воспроизведено: error=0 warning=45. direction: integrity-gap. Disposition: часть — reconcile_state fix --apply (derived); orphan/missing markers — ручная сверка → build/close-question.

---

## E. dangling-ref — done-задачи ссылаются на переименованные deliverable'ы (integrity, не функционал)

Функционал везде существует — low. Чинятся правкой ссылки в задаче.

P21 — T-058 (done) называет tools/validate_drivers.py — нет (в validate.py check_drivers) · low · fix-inline
tasks/T-058.md:20; reality: validate_drivers.py отсутствует (filesystem+git log); валидация в validate.py check_drivers@296 / check_driver_tools@409. direction: integrity-gap.

P22 — T-058 (done) называет tools/generate_driver_catalog.py — отгружен как tools/drivers_catalog.py · low · fix-inline
tasks/T-058.md:21; reality: generate_driver_catalog отсутствует (grep матчит только эту строку); drivers_catalog.py пишет CATALOG.md+index.json; done-record T-058.done.md:7 кредитует drivers_catalog.py. direction: integrity-gap.

P23 — T-060 (done) ссылается на drivers/workbench-db.md — манифест = drivers/workbench.md · low · fix-inline
tasks/T-060.md:27; reality: workbench-db.md отсутствует; drivers/workbench-db/ держит init/query/schema/test_db (без .md); манифест = drivers/workbench.md (id: workbench:2). direction: integrity-gap.

P24 — Q-013 цитирует flow.py:141 для merge-back гонки — строка не совпадает · low · fix-inline
questions/Q-013.md:127 (claim сказал :128); reality: flow.py:141 теперь template-print под ## Boundary; acknowledgement переехало на :195-202 (коммент :198 «Остаточная гонка (БЫЛА flow.py:141)»). Low reader-impact. direction: integrity-gap.

P25 — F-020 check_gate_poison line-якоря в overview дрейфанули (claim верен) · low · fix-inline
docs/engine-subsystems-overview-2026-06-23.md:37; reality: цитирует :477/:608, факт def@:479, call@:634, REGISTRY F-020@:276, recommendation@:650 — сдвиг 2-26, :608 на несвязанной строке. F-020 реально подключён (67fa8b5) → claim держится. direction: integrity-gap.

---

## F. close-question / already-ok — открыто по дизайну, расхождения нет

P26 — Q-010 (rename темы/ → topics/) genuinely open — косметический B сделан, структурный A отложен · low · already-ok/close-question
questions/Q-010.md:5 (status: open); reality: B в силе (core.quotepath=false); A НЕ сделан (темы/ есть, topics/ нет, git mv не запускался); 140 frontmatter-refs + hardcode темы в ~15 модулях (generate.py:55). D-007 accepted ратифицирует только принцип, не завершение A; A ждёт no-parallel-work окна (D-008). Silent-resolution НЕТ → док корректен. direction: genuinely-undone-by-design.

---

## Сводные действия для роутера

- fix-inline (доминирует): P1-P13, P18-P19, P21-P25 — одна doc-reconcile волна (по образцу d2d7a03, который частично делал это и пропустил эти строки). Пометить SHIPPED + снять status: proposed + подтянуть line-якоря. Перед правкой проверить working-tree: P1/P10 могут быть уже переписаны (uncommitted).
- ratify: P14 (blocked на Stefan — D-014), P15 (superseded-in-part note по образцу D-020).
- build: P16, P17 (честно открытые), часть P20.
- already-ok/close-question: P26.
- machine-red regen: P18/P19 (+часть P20) — python tools/generate.py + SELECTIVE-ADD, НЕ git add -A; восстановить дерево если проверка тестовая.

---

## completeness-note (непокрытые срезы/области)

1. Покрыто: claim-check темы/*.md (solver-report, new-problems, q016, fleet-designs, perspective-backlog); docs/*.md overviews; open-questions (Q-008/010/013/016); decisions-integrity (D-014/019/021); tasks-vs-reality (T-058/060, session-state); dangling-refs; machine-findings (drift_check/reconcile_state/friction).
2. НЕ покрыто claim-check'ом: в slice названы collab-safety-subsystem-2026-06-23.md и friction-subsystems-synthesis-2026-06-22.md — но НИ ОДНОЙ находки по ним нет (чисты либо не проверены). Статус неизвестен — не презюмировать «ok».
3. Прочие темы/*.md вне набора: assurance-hardening-plan, build-specs, governance-proposals, drivers-subsystem-state, d014-execute-off-ratification, kotel-decision-material, agent-pipeline, ai-os-bridge и др. (~30+ файлов) — claim-check не прогонялся.
4. Skills/recipes: skills/top-layer-orchestrator/ (untracked), skills/README.md (M) — не верифицировались.
5. Queues/outbox: 2026-06-23-agent-capacity-methodology.md, 2026-06-23-top-layer-throughput-methodology.md + docs/top-layer-throughput-methodology.md (untracked) — не claim-чекались.
6. Новые задачи: T-168/169/170 (untracked), T-176/177/178 (в machine-red) — карточки сами по себе не аудировались, только как индекс-дрейф.
7. Severity-потолок: high-находок НЕТ. Если ожидался поиск критических (safety/gate-bypass/data-loss) расхождений — он либо отрицателен, либо не проводился; набор — med/low integrity+staleness.
8. Working-tree vs canon: P1/P7/P10 помечают возможные uncommitted-правки; полный diff working-tree против HEAD по всем 26 не сверялся — роутеру проверить перед fix-inline.
9. Drivers за пределами gateway/workbench: остальные drivers/*.md манифесты на acceptance-gap не проверялись.