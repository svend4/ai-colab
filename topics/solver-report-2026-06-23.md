---
id: solver-report-2026-06-23
type: solver-report
status: proposed
date: 2026-06-23
author: solver-orchestrator
scope: integration of 4 solver outputs (P4, P8, P5+P6+P9, P7)
verified_against: working tree @ master (HEAD 144bb7b)
---

# SOLVER report — 2026-06-23

Единый отчёт по четырём решённым задачам. Каждая секция — самодостаточная спека для applier'а: премиса (проверена против дерева/git-лога), режим применения, и точные правки. Все premises ниже подтверждены прямым чтением файлов на момент сборки (см. «Verification» в каждой секции).

> **SHIPPED-UPDATE 2026-06-23:** P4 (cohort/flow `--strict`) **зашиплен** коммитом `e3907a4` — `MANDATORY_TRIGGERS@cohort.py:52`, `ship(strict=)@:259`, `turn(strict=)@:208`, `guard(strict=)@:386`. Заголовочный `verified_against: HEAD 144bb7b` (:9) — стейл-но-честный снимок на момент сборки; `e3907a4` лёг ПОСЛЕ него, поэтому @HEAD строка «ничего не применено» по P4 устарела.

Сводка по режимам применения:

| Problem | Тип | Режим | Файлы | Ratify? |
|---|---|---|---|---|
| **P4** | impl-spec | **inline** (additive, opt-in default-off) — **SHIPPED `e3907a4`** | `tools/cohort.py`, `tools/flow.py`, `tools/test_cohort.py` (+опц. `tools/test_flow.py`) | нет |
| **P8** | impl-spec | **worktree** (`doc_consensus.py` co-owned) | `tools/doc_consensus.py`, `tools/test_doc_consensus.py` (+ note в `docs/workflow-orchestration-policy.md`) | нет |
| **P5+P6+P9** | doc-edits | **inline** (unique-match string replace) | 7 файлов (topics/* + docs/*) | нет (документация догоняет уже-зашедший код) |
| **P7** | doc-edits + task-spec | **inline** | `drivers/gateway.md` + новый `tasks/T-174.md` | нет |

---

## P4 — cohort/flow enforcement-half (T-148 reopened)

**Apply: inline** (single dev, additive, opt-in default-off). Зеркало уже-принятого `friction.py --strict` / `pipeline.py done --strict` паттерна + D-022 §1/§4 + D-023. Ratify не нужен.

**Verification (подтверждено):** `tools/cohort.py:42` — `HOT_FILES`; `:199 def turn(agent, do_run=False)`; `:246 def ship(agent, files, message=None, do_run=False)`; `:336 def guard(as_json=False, agent=None)`. Все сигнатуры совпадают с premise. `MANDATORY_TRIGGERS` отсутствует — добавляется.

**Premise / scope (Q-013:124-128, D-022 §1/§4, D-023):** `cohort.py guard/turn/ship` только ПЕЧАТАЮТ «go to worktree» и всегда `return 0`; не блокируют. `flow.py finish --worktree` регенерирует+гейтит ДО merge, но ничего ПОСЛЕ — остаётся merge-back гонка. Построить **opt-in blocking mode** (`--strict`, default-off), где два **mandatory** триггера — **same-file collision** и **foreign-STALE** (единственные доказанные потери, Q-013:124) — делают `guard`/`ship` exit!=0 и заставляют `ship` ОТКАЗАТЬ в коммите в общее дерево. Прочие триггеры (hot-tool, stale-index, gate-poison) остаются recommended (печать, не блок). Плюс закрыть merge-back гонку (`flow.py:196-201`) регенерацией на слитом коммите.

Default-off proof: при `strict=False` `blocked` всегда `False`, все return-пути остаются `0`, новые строки не печатаются — байт-в-байт как сегодня. flow.py-правка behaviour-preserving в no-race случае (no-op amend) и строго безопаснее в race-случае.

### EDIT 1 — cohort.py: mandatory-trigger set + same-file detector

**1a.** После `HOT_FILES` (после строки 43) добавить константу:
```python

# MANDATORY триггеры (Q-013:124 / D-022 §1 A,E §4 Вариант-1): только same-file коллизия и чужой
# STALE-источник (foreign) — единственные ДОКАЗАННЫЕ потери. Остальные триггеры (hot-tool,
# stale-index, gate-poison) — recommended (печать, не блок). В --strict только эти двое возвращают
# nonzero и заставляют ship отказать в коммите в общее дерево.
MANDATORY_TRIGGERS = ("foreign-source", "same-file")
```

**1b.** Перед `def guard(` (строка 336) вставить read-only детектор:
```python
def _foreign_branch_files(self_agent=None):
    """Пути, затронутые незамёрженными ветками ДРУГИХ агентов (agent/<other>/<task>).

    Read-only: для каждой ветки agent/* (кроме своей) берём файлы её коммитов, ещё не влитых
    в HEAD (git diff --name-only HEAD...branch). Это «другой агент уже трогает этот файл в своём
    притоке» — основа same-file детекта (LS-2, D-022 §4 Вариант-1). Никогда не бросает."""
    rc, out = _git("for-each-ref", "--format=%(refname:short)", "refs/heads/agent")
    files = set()
    for br in (out or "").splitlines():
        br = br.strip()
        if not br.startswith("agent/"):
            continue
        parts = br.split("/")
        if self_agent and len(parts) >= 2 and parts[1] == self_agent:
            continue
        rc2, diff = _git("diff", "--name-only", "HEAD...%s" % br)
        if rc2 == 0:
            for ln in diff.splitlines():
                p = ln.strip().replace("\\", "/")
                if p:
                    files.add(p)
    return files
```
`HEAD...<branch>` (три точки) = файлы ветки с merge-base; `_git` уже возвращает `(rc, stdout)` и глотает ошибки; пустой `refs/heads/agent` ⇒ no-op. Новых импортов нет.

### EDIT 2 — cohort.py: guard вычисляет same-file, возвращает nonzero в strict

**2a.** Сигнатура (336): `def guard(as_json=False, agent=None):` → `def guard(as_json=False, agent=None, strict=False):`

**2b.** После `foreign = sorted(...)` (после строки 349) добавить:
```python
    # same-file = мой dirty-путь, который ДРУГОЙ агент уже трогает в своём притоке (LS-2, D-022 §4).
    fb = _foreign_branch_files(self_agent=agent)
    same_file = sorted({p for p in paths if p in fb})
```

**2c.** В список `triggers` после блока `if foreign:` добавить:
```python
    if same_file:
        triggers.append({"trigger": "same-file", "files": same_file, "recipe": "foreign"})
```

**2d.** После `level1 = bool(triggers)` добавить:
```python
    # mandatory = подмножество, которое в --strict БЛОКИРУЕТ (foreign-source, same-file).
    mandatory = [t for t in triggers if t["trigger"] in MANDATORY_TRIGGERS]
    blocked = strict and bool(mandatory)
```

**2e.** JSON payload — заменить блок `if as_json:` на:
```python
    if as_json:
        print(json.dumps({"level1_recommended": level1, "triggers": triggers,
                          "mandatory": [t["trigger"] for t in mandatory],
                          "strict": strict, "blocked": blocked}, ensure_ascii=False, indent=2))
        return 1 if blocked else 0
```

**2f.** Финальный человеко-вывод — перед `print(line)` / `return 0` вставить BLOCK-строку:
```python
    if blocked:
        print("\n  [STRICT BLOCK] обязательные триггеры: %s — коммит в общее дерево ОТКЛОНЁН. "
              "Уйди в worktree (flow.py start --worktree) и вливай через merge_gate." %
              ", ".join(t["trigger"] for t in mandatory))
    print(line)
    return 1 if blocked else 0
```

### EDIT 3 — cohort.py: ship отказывает под strict + mandatory

**3a.** Сигнатура (246): добавить `strict=False`.

**3b.** После empty-files guard (после строки 253) вставить strict-гейт ПЕРЕД `msg =`:
```python
    if strict:  # opt-in blocking (mirrors friction/pipeline --strict): обязательный триггер -> ОТКАЗ
        norm = [f.replace("\\", "/") for f in files]
        foreign = set(own.summary(norm, agent=agent)["by"]["foreign"])
        same_file = {p for p in norm if p in _foreign_branch_files(self_agent=agent)}
        hit = sorted(foreign | same_file)
        if hit:
            kinds = (["foreign-source"] if foreign else []) + (["same-file"] if same_file else [])
            print("ОТКАЗ (--strict): %s — обязательный триггер Уровня-1 (%s). "
                  "Коммит в общее дерево запрещён: уйди в worktree "
                  "(python tools/flow.py start %s <task> --worktree --run) и влей через merge_gate." %
                  (", ".join(hit), ", ".join(kinds), agent))
            return 1
```
Scoped к файлам, переданным в `ship` (selective-add). Возвращает `1` (как friction/pipeline). Default-off: `strict=False` пропускает весь блок.

### EDIT 4 — cohort.py: turn honours strict

**4a.** Сигнатура (199): добавить `strict=False`.

**4b.** Заменить `guard(agent=agent)` (строки 205-206) на:
```python
    grc = guard(agent=agent, strict=strict)
    if strict and grc != 0:
        print("\n--strict: обязательный триггер Уровня-1 активен — смена остановлена. "
              "Уйди в worktree (flow.py start --worktree --run), затем повтори turn.")
        return grc
```

### EDIT 5 — cohort.py: CLI wiring для --strict (main)

**5a.** Рядом с `--json`/`--run`: добавить `strict = _flag(rest, "--strict")`. (`pos` уже фильтрует `--*`, флаг не утечёт в file-list.)

**5b.** Прокинуть `strict=strict` в три arm'а: `turn(pos[0], do_run=do_run, strict=strict)`; `guard(..., strict=strict)`; оба `ship(...)` return'а.

**5c.** Doc-string: добавить `[--strict]` к `ship` usage-строке и расширить trailing-note про opt-in/default-off зеркало friction/pipeline.

### EDIT 6 — flow.py: закрыть merge-back гонку (finish --worktree, 191-201)

Заменить `cmds = [...]` блок: после `git merge` добавить пост-merge регенерацию на слитом коммите + amend в merge-commit + повторный `merge_gate check`:
```python
            cmds = [[sys.executable, "tools/generate.py"],
                    [sys.executable, "tools/merge_gate.py", "check", args[1]],
                    ["git", "merge", "--no-ff", b, "-m", "Merge %s" % b],
                    [sys.executable, "tools/generate.py"],
                    ["git", "add",
                     "TASKS.md", "QUESTIONS.md", "DECISIONS.md", "board.md", "STATUS.md", "index.json"],
                    ["git", "commit", "--amend", "--no-edit"],
                    [sys.executable, "tools/merge_gate.py", "check", args[1]]]
            cmds += wt.remove_cmds(args[1], args[2])
            return run_or_print(cmds, do_run)
```
`run_or_print` аборится на первом nonzero rc — если пост-merge гейт КРАСНЫЙ, teardown (`wt.remove_cmds`) не запускается, приток цел для retry. `git add` — только 6 канонических `GENERATED` индексов (D-023 §2). No-race случай: пост-merge `generate.py` не меняет индексы, `add` ничего не стейджит, `commit --amend --no-edit` — no-op-content amend — net поведение как сегодня + один дешёвый verify.

### EDIT 7 — tests (additive)

- **7a. tools/test_cohort.py:** после `guard --json` блока добавить `guard --strict --json` (проверяет ключи `strict`/`blocked`/`mandatory`, на чистом репо rc 0). После ship-dry блока — `ship --strict` без файлов (подсказка не ломается) и `ship --strict` на чистом пути (план либо явный ОТКАЗ). Существующие assertions нетронуты (доказывает default-off инвариант).
- **7b. tools/test_flow.py:** assert что `finish ... --worktree` (dry) печатает ≥2 `generate.py`, `commit --amend`, и пост-merge `merge_gate.py` после `git merge`. (Если нет worktree-dry helper'а — добавить 3-строчный subprocess по образцу `_run`.)

### Verification checklist (read-only / dry)
1. `python tools/cohort.py guard --json` — ключи неизменны; rc 0.
2. `python tools/cohort.py guard --strict --json` — есть `strict:true`/`blocked`/`mandatory`; rc 1 только при живом mandatory.
3. `python tools/cohort.py ship claude <clean-file> --strict` — нормальный dry-план (rc 0); foreign/same-file ⇒ «ОТКАЗ (--strict)» + rc 1.
4. `python tools/cohort.py ship claude <file>` (без --strict) — байт-в-байт как сегодня.
5. `python tools/cohort.py turn claude --strict` — стоп iff guard nonzero.
6. `python tools/flow.py finish mavis T-020 --worktree` (dry) — список: generate → merge_gate → git merge → generate → git add(6) → commit --amend → merge_gate → worktree remove → branch -D.
7. `python tools/test_cohort.py`, `python tools/test_flow.py` — green.

**Инварианты:** opt-in default-off; symbol-anchored & additive (1 константа, 1 helper, 3 kw-параметра default false, 1 CLI-флаг, 1 расширение flow.py command-list); mandatory-set = ровно `{foreign-source, same-file}`; D-023 ownership (post-merge add только 6 GENERATED); reopens T-148 enforcement-half без трогания detector-half.

---

## P8 — Q-017 `report --semantic` для doc_consensus.py

**Apply: worktree** (`tools/doc_consensus.py` co-owned). Default-путь остаётся pure-stdlib, no-cost, байт-в-байт; всё gated за `--semantic`. Ratify не нужен.

**Verification (подтверждено):** `tools/doc_consensus.py:71 def _append_unit`, `:144 def analyze(paths, root=ROOT, thr=0.4)`, `:168 def render(res)`, `:217 def main()`. Reference-дизайны: `topics/q017-semantic-consolidated-2026-06-23.md`, `topics/q017-docmerge-semantic-2026-06-23.md` (оба присутствуют).

**Инварианты (не ломать):** `analyze(paths, root=ROOT, thr=0.4)` держит сигнатуру/return-shape (тесты зовут позиционно); default `report` (без `--semantic`) идентичен сегодня; rc-контракт `main()` (`0`/`2`) неизменен; новых импортов сверх stdlib нет (`subprocess`/`json`/`os`/`re`/`sys` уже импортированы).

### Change 1 — стабильный id юнита (`_append_unit:77`)
Заменить dict-литерал так, чтобы каждый юнит нёс `"id": where` (где `where` = `file:line`, уже глобально уникален). Additive — `analyze`/`render`/тесты не затронуты.

### Change 2 — residue-extraction (`_residue`, после `analyze` ~:165)
Добавить `SEMANTIC_THR = 0.65`, `_rep(cluster)` (longest-token member, как `render():181`), и `_residue(res)` — split на settled high-conf кластеры (≥2 docs, НЕ шлём агенту) и residue (по одному репрезентату на settled multi-member кластер + все divergent юниты, де-дуп по id).

### Change 3 — agent shell-out + batched semantic pass
Добавить `AGENT_BATCH=50`, `AGENT_ENV="DOC_CONSENSUS_AGENT"`, `_AGENT_PROMPT` (просит ТОЛЬКО JSON {consensus, divergences}), `_run_agent(payload_json)` (subprocess.run, `shell=True`, читает команду из env; `''` если не сконфигурён — degrade-safe seam, который тесты monkeypatch'ят), `_parse_agent(raw)` (толерантный extract outermost `{...}`), `_semantic_pass(residue)` (батчит ~50/call, union групп по shared unit-id). Паттерн идентичен `_topic_files`/`synthesis_helper.py`.

### Change 4 — `_merge` (транзитивный union по unit-id)
Добавить `_merge(settled, groups, all_units)`: семантическая группа, ссылающаяся на репрезентат механического кластера, транзитивно тянет ВЕСЬ кластер; consensus должен span ≥2 docs; settled кластеры, не задетые агентом, остаются как `mechanical` consensus. Возвращает `{consensus:[{members, rationale, mechanical}], divergent_ids:set}`.

### Change 5 — orchestrator + extended render
Добавить `analyze_semantic(paths, root=ROOT, thr=SEMANTIC_THR, agent_label=None)` (high-thr mechanical pre-cluster → residue → semantic_pass → merge; return `{"semantic":True, consensus, divergent, divergence_detail, docs, n_units, agent}`). В `render(res)` добавить guard в начале: `if res.get("semantic"): return _render_semantic(res)` — лексический body неизменен. `_render_semantic`: front-matter `status: proposed` + `source-docs` + `semantic-agent` + «ничего не auto-accepted — материал для котла (D-017/D-018)»; consensus-header переиспользует существующую строку `"## Консенсус ..."` (assertion `"Консенсус" in txt` держится в обоих режимах); per-item: текст репрезентата + «встречается в N док.» + file:line cross-refs всех members + «почему это одна идея:» (rationale или `(механический матч)`); divergence-секция переиспользует `"## Разногласия ..."`, раскрывает D-017 sub-points при наличии `divergence_detail`.

### Change 6 — wire `--semantic` в `main()` (:217-245)
После `len(files) < 2` guard, заменить единичный `analyze(...)` на ветку:
```python
    abs_files = [os.path.join(ROOT, f) if not os.path.isabs(f) else f for f in files]
    if "--semantic" in a:
        sem_thr = float(_arg(a, "--thr", str(SEMANTIC_THR)))
        res = analyze_semantic(abs_files, thr=sem_thr)
    else:
        res = analyze(abs_files, thr=thr)
    text = render(res)
```
`--out` (`:237-244`) неизменён, теперь персистит `status: proposed` semantic-отчёт. Docstring (`:14-17`) — добавить `[--semantic]` opt-in строку + note про `$DOC_CONSENSUS_AGENT` (default no-cost lexical).

### Change 7 — обязательный regression-фикстур (test_doc_consensus.py)
Добавить `import json` к импортам. Внутри `run()` (после q1/q2 блока, ~:64) — binding acceptance-gate «одна идея — разные слова» (q017-consolidated:91-97): (1) lexical mode ПРОВАЛИВАЕТ (0 consensus при любом thr на нулевом token-overlap); (2) stub `dc._run_agent` (no LLM в CI), который концептуально группирует два парафраза по unit-id; (3) `--semantic` ЛОВИТ (1 consensus через оба дока, несёт rationale); (4) semantic render — `status: proposed` + «Консенсус».

### Verify
`python tools/test_doc_consensus.py` (без `DOC_CONSENSUS_AGENT` — stub заменяет `_run_agent`, LLM не зовётся) и `python tools/test_synthesis_helper.py`. Default `python tools/doc_consensus.py report --files a.md b.md` — вывод неизменён. Также свернуть opt-in/scoped note в `docs/workflow-orchestration-policy.md` (build-order шаг 6).

---

## P5+P6+P9 — документация догоняет уже-зашедший код

**Apply: inline.** Все правки — уникальные in-place string-replace, old_string'и verbatim из текущего дерева, Read-before-Edit конфликтов нет. Ratify не нужен (доку приводим в соответствие коду, уже в master).

**Verification (подтверждено git-логом + деревом):**

| Claim | Реальность | Commit |
|---|---|---|
| P5: `reconcile_state.py fix` — заглушка | `cmd_fix(apply=False)` живёт на `tools/reconcile_state.py:259`, диспетчер на `:295`; dry-run/`--apply`, derived-only, PRIMARY-refuse, exit_code — всё по дизайну. **Подтверждено чтением файла.** | **94c3c35** |
| P6: F-020 не в friction REGISTRY | `F-020` — REGISTRY-запись `friction.py:274`; `check_gate_poison()` `:477`; в `collect_status`/`recommendation`. **Подтверждено.** | **67fa8b5** |
| P9a: `stream.py check` «not yet» | `cmd == "check"` на `tools/stream.py:292` (P-11 graveyard detector). **Подтверждено.** | **686a0fb** |
| P9b: pre-commit hook «не реализован» | `tools/githooks/pre-commit` существует, гейтит `validate.py` ERROR + `generate.py --check`. NOTE: хук НЕ детектит `git add -A` сам — правки сохраняют truthful nuance. **Подтверждено.** | **0f74e61** |

### P5 — reconcile_state.py fix stub (4 правки)
Точные old→new для каждого файла:
- `topics/q016-assurance-state-2026-06-23.md` (строка 87, пункт 8 таблицы): пометить `~~SHIPPED 2026-06-23 (commit 94c3c35)~~`, `cmd_fix` на `:259`, режим `~~worktree~~ done`. Дизайн сохранить как историч. спеку.
- `topics/fleet-designs-2026-06-23.md` (строка 17): заменить «`reconcile_state.py:234` — заглушка» на блок `> SHIPPED 2026-06-23 (commit 94c3c35)` + «Дизайн (теперь реализованный):».
- `topics/perspective-backlog-2026-06-23.md` (строка 51, пункт 10): `~~reconcile_state.py fix subcommand~~ — SHIPPED ... cmd_fix at :259`, статус `done`.
- `topics/session-state-2026-06-23.md` (строка 58, пункт 10): `~~fix subcommand~~ — SHIPPED (94c3c35) ... :259`, `done`.
(`docs/engine-subsystems-overview-2026-06-23.md`:96 — нейтральная key-files ссылка, НЕ содержит P5-stub claim, не правится для P5.)

### P6 — F-020 в friction REGISTRY (2 файла)
- `docs/engine-subsystems-overview-2026-06-23.md` (строка 37): `F-001..F-019` → `F-001..F-020`, «F-020 ЕЩЁ НЕ в REGISTRY» → «F-020 ПОДКЛЮЧЁН (SHIPPED 2026-06-23, 67fa8b5): REGISTRY `:274` + `check_gate_poison()` `:477` + `collect_status`/`recommendation`».
- `topics/collab-safety-subsystem-2026-06-23.md` — 3 правки: §2.3 (стр.122) `F-001..F-019` → `F-001..F-020` + добавить F-020 в «LEVEL 1 OR SELECTIVE-ADD»; §2.4 заголовок (стр.124) «Замечание о F-020» → «F-020 (gate-poison) — ПОДКЛЮЧЁН (SHIPPED 2026-06-23, 67fa8b5)»; §2.4 body (стр.126) «F-020 нет в REGISTRY» → «F-020 ЕСТЬ в REGISTRY ... check_gate_poison реализован ... оба детектора согласованы ... drift закрыт».

### P9 — parallel-work-policy.md (4 строки)
- Строка 224 (`stream.py check`): «(not yet implemented)» → «(SHIPPED 2026-06-23, 686a0fb; tools/stream.py:292, P-11 graveyard detector)».
- Строка 229 (pre-commit hook): «(but not yet implemented ... T-143-results)» → «hook ЕСТЬ (SHIPPED 0f74e61; tools/githooks/pre-commit) — блокирует на validate.py ERROR + generate.py --check (:45-57). Оговорка: НЕ детектит `git add -A` напрямую; selective-add остаётся дисциплиной + покрывается gate-poison/F-020».
- Строка 250 (антипаттерн git add -A): «pre-commit hook (не реализован, но нужен)» → «SHIPPED 0f74e61 ... Прим.: ловит отравленный результат стейджа, а не сам флаг -A; явная wide-add-проба ещё не добавлена».
- Строка 254 (антипаттерн stream graveyard): «(not yet implemented)» → «(SHIPPED 686a0fb; tools/stream.py:292). Остаётся: auto-archive старых proposed-streams (детектор есть, авто-архивация — нет)».

**Notes для applier:** `session-state:49`/`perspective-backlog:42` (Q-016 done-gate) и `perspective-backlog:44`/`session-state:51` (Q-017 semantic) — **out of scope**, не трогать. P9 правки 229/250 НЕ overclaim'ят: хук shipped, но truthful caveat (гейтит validate/generate, не literal `git add -A` detector) сохранён. Если applier предпочитает плоский «shipped» — можно убрать «Оговорка/Прим.» предложение, но caveat — точная реконсиляция.

---

## P7 — gateway.md: call_tool acceptance закрыта sync-путём + tracking-task

**Apply: inline.** Два файла: правка `drivers/gateway.md` (status-секция + front-matter) + создание `tasks/T-174.md`. Ratify не нужен.

**Verification (подтверждено):** `drivers/gateway.md:17 source_last_verified: 2026-06-21`; `:57 ## Статус на 2026-06-21`; `:61` несёт `ready-except-mcp-stdio-call-acceptance`. `drivers/mcp_sync_acceptance.py` существует (real `tools/call` по всем 6 tool'ам через `SyncMcpClient`, shipped green pass=6/fail=0). `tasks/T-174.md` отсутствует, T-001..T-173 заняты — T-174 свободен. **Всё подтверждено.**

**Problem:** `drivers/gateway.md` (## Статус, строки 57-63) всё ещё утверждает, что gateway не прошёл полную `call_tool` MCP acceptance, и пинит runtime-статус `ready-except-mcp-stdio-call-acceptance`. Escape-hatch «или не добавлена синхронная `tools/call` приёмка» уже satisfied: `drivers/mcp_sync_acceptance.py` делает real `tools/call` против всех 6 tool'ов (`files_list`, `files_read`, `files_search`, `files_summarize`, `repo_inspect`, `memory_query`) через sync `SyncMcpClient` (subprocess.Popen + JSON-RPC, без `asyncio.create_subprocess_exec`), каждый возвращает не-error результат, suite зелёный. Остаётся только **async** stdio путь на Windows (`WinError 5`, T-087) — environment-dependent.

### Edit 1 — `drivers/gateway.md`: переписать stale status-секцию (строки 57-63)
Заменить весь блок: заголовок `## Статус на 2026-06-21` → `## Статус на 2026-06-23`; claim «не считается прошедшим полную `call_tool` MCP acceptance» → «**`call_tool` MCP acceptance — закрыта** переносимым синхронным путём» (real `tools/call` по 6 tool'ам через `SyncMcpClient`, `SYNC ACCEPTANCE pass=6 fail=0`, `RESULT OK`); async stdio gap переформулировать как **среда-зависимую** оговорку (`PermissionError [WinError 5]`, T-087), отслеживаемую в **T-174**. Короткая формула: `ready` — манифест/tools-list/call_tool(sync) пройдены; async stdio acceptance — environment-dependent, ждёт T-174. T-094 регрессия сохранена.

### Edit 2 — `drivers/gateway.md`: front-matter (строка 17)
`source_last_verified: 2026-06-21` → `source_last_verified: 2026-06-23`. (Опц.: строка 54 тоже несёт `2026-06-21` stamp — может остаться или быть bumped; не load-bearing.)

### Task-spec — создать `tasks/T-174.md`
Новый файл-трекер async-stdio WinError-5 блокера (зависимости T-087/T-088, topic `topics/ai-os-bridge.md`, status open, owner pool). Тело: `call_tool` acceptance закрыта sync-путём; единственная оговорка — async stdio `WinError 5`; задача существует чтобы блокер не стал молча постоянным. Что сделать: периодически перезапускать `python drivers/mcp_acceptance_test.py`, фиксировать воспроизводимость; при решении — применить и закрыть + обновить ## Статус; при подтверждённой невозможности — `wontfix` с обоснованием. Контекст ссылается на `drivers/mcp_acceptance_test.py` (async, падает), `drivers/mcp_sync_acceptance.py` (sync, зелёный), `drivers/gateway.md` (## Статус).

**Note для applier:** если `index.json` или catalog-валидатор трекает задачи — зарегистрировать T-174 там по repo-конвенции создания задач.

---

## Ready-to-apply сводка (для оркестратора)

- **P4** — inline сейчас. 3 файла (+1 опц.). Additive, opt-in default-off, без ratify. Verify: cohort/flow dry + 2 теста.
- **P8** — worktree (co-owned doc_consensus.py). 2 файла + note в workflow-orchestration-policy.md. Default-путь неизменен, agent за `$DOC_CONSENSUS_AGENT`. Verify: 2 теста, default report неизменён.
- **P5+P6+P9** — inline сейчас. 7 файлов, unique-match string-replace, доку догоняет код (94c3c35/67fa8b5/686a0fb/0f74e61). Без ratify.
- **P7** — inline сейчас. gateway.md (2 правки) + новый tasks/T-174.md. Без ratify; опц. регистрация T-174 в index.json.
