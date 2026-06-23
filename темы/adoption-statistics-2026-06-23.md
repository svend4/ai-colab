# Adoption Statistics — 2026-06-23

status: proposed
point-in-time base: 623a193 / @623a193
as-of: 2026-06-23
input: 8 slice_stats (223 измеренных актива) + 10 подтверждённых dormant
method: usage_count везде = реальный счёт из grep/git/subprocess/sqlite, НЕ оценка

---

## 0. TL;DR — прямой ответ Stefan

- **Общий коэффициент применения накопленного ≈ 78%** (взвешенно по «wired/active/enforced» внутри каждого класса) — **≈ 90%**, если считать «применением» любую цитату/inbound-ссылку (мягкая метрика для доков).
- **Что НЕ применяется (полка-пыль):** 9 dormant-инструментов, 4 orphan-дока, 18 из 23 решений живут только как декларация (не впаяны в код), 5 friction-рецептов — registry-only без детектора, 1 портал-стор queried-vs-stored недоказуем.
- **Режим: СМЕШАННЫЙ.** Производство параллельно (**56%** воркфлоу в параллельных окнах, до **4** нод одновременно, бригада до **17** агентов на ноду), но **интеграция серийна** — один git-author (Max), один commit-band-оркестратор = bottleneck.
- **Runtime-температура:** реально «горячий» **1** из 5 подсистем (conveyor, sub-hour). Ядро knowledge — **COLD** (corpus DB заморожен 06-21).

---

## 1. Статистика применения по классам активов

| Класс | Всего | Active | Referenced-only | Dormant/Dead | % применения |
|---|---|---|---|---|---|
| tool (wiring) | 41 | 32 | 0 | 9 dormant | **78%** |
| skill | 5 | 4 | 1 | 0 | **80%** |
| doc+theme | 141 | 137 cited | — | 4 orphan/dead | **97%** |
| friction-recipe (F) | 20 | 15 wired-detector | 5 registry-only | 0 | **75%** |
| decision (D) | 23 | 5 enforced-by-code | 18 declarative/orch-only | (3 proposed) | **22%** |
| driver/data-store | 9 | 8 populated (1 query-proven) | 7 build-only | 1 dormant | **89% pop / 11% query-proven** |
| runtime-subsystem | 5 | 5 с трейсами | — | 0 | **100% (с трейсом)** |
| **ИТОГ (твёрдые классы)** | **244 строк-метрик / 223 уник. актива** | — | — | **24 не-применяются** | **~78% / ~90%** |

Примечание по двойному счёту: tools проходят двумя срезами (WIRING n=41 и GIT-ACTIVITY n=78). GIT-срез измеряет другую ось — свежесть коммитов, не wiring. По коду применяется 78% (32/41); по git-свежести 93.6% инструментов трогали за последние ~3 дня (73/78 recent-active, медиана 2 коммита, максимум 14 у top.py).

### 1a. Детализация tools (WIRING, 41)
- active=32: вызван хуком (validate/generate), ИЛИ импортируется ≥1 продакшн-тулом, ИЛИ subprocess в конвейере (pipeline/cohort/flow/conveyor/top).
- dormant=9 (22%): есть main(), но 0 импортёров И 0 subprocess-вызывателей — чистый CLI без вызывателя, упомянут только в доках/тасках.

### 1b. Decisions — самый низкий реальный коэффициент
- 23 всего: 20 accepted, 3 proposed.
- **Только 5 (22%) впаяны в код** (validator-правило / commit-gate / исполняемый триггер).
- 18 — декларация или orchestration-only: цитируются в десятках *.md как принцип, но без runtime-проводки. Цитата в docstring/help/test_ НЕ считается enforcement.

### 1c. Friction — 75% wired
- 15/20 имеют make_check(F-id) call-site в детекторе collect_status.
- 5 — registry-only (определение есть, детектор не вызывает).

### 1d. Docs — высокий cited%, но с поправкой
- cited 137/141 (97%), orphan 4 (3%). Распределение inbound: 0→4, 1-3→31, 4-9→56, 10-19→34, 20-49→14, 100+→2 (темы/ai-os-bridge.md=135, docs/README.md=108).
- ПОПРАВКА: часть inbound у крупных доков — это 4 авто-инвентарных JSON (repo-inventory/corpus/fixture-report), механически перечисляющих все файлы. Даже после вычитания авто-инвентаря: cited=137/141 (97%), те же 4 orphan — вывод устойчив.

---

## 2. Топ подтверждённых DORMANT-активов (полка-пыль) — 10

| # | Актив | Класс | Статус | Почему пыль (0 потребителей) |
|---|---|---|---|---|
| 1 | tools/metrics.py | tool | dormant | 0 import / 0 subprocess; все 22 упоминания = doc/task/inventory; сам импортирует _canon (потребитель, не цель). main() только под __main__. |
| 2 | tools/next_id.py | tool | dormant | 0 import / 0 subprocess; все ссылки — ручной CLI-шаг в доках + output-stub в index.json/TASKS. Запускается человеком руками. |
| 3 | tools/risk_gate.py | tool | dormant | 0 import (git -S за всю историю пусто); ни один из 25 subprocess-тулов не зовёт; нет githooks/yml/Makefile. Реализует D-006, но без вызывателя. |
| 4 | tools/race_test.py | tool | dormant | Лист: сам зовёт queue.py, но никто не зовёт его. Ручной стресс-тест; не в CI (нет test_-префикса). |
| 5 | tools/sandbox_intake_demo.py | tool | dormant | (синтетический id metrics_placeholder_synthesis_gate). 0 import/subprocess; только CLI-кнопка `sandbox-demo` в _BUTTONS. Тест зелёный, но usage_count=0. |
| 6 | docs/finder-solver-pipeline-methodology.md | doc | DEAD | 0 inbound во всём дереве; слаг появлялся ровно в 1 коммите (создание). Упоминания «FINDER» — про другой концепт. Write-once-never-cited. |
| 7 | docs/core-export-acceptance-result-2026-06-21.md | doc | DEAD | 0 inbound; sibling-таски цитируют свои acceptance-доки, а T-140 — нет. Pickaxe: ссылку никогда не добавляли. |
| 8 | docs/kotel-decision-material-intake-2026-06-21.md | doc | DEAD | 0 редакторских inbound; единственные совпадения — .git/index и авто-инвентарь repo-knowledge.db. |
| 9 | docs/portal-example-l2-result-2026-06-21.md | doc | DEAD | 0 inbound; pyramid-candidate-map ссылается на сам пример портала, не на result-док. Runtime-следа нет. |
| 10 | D-006 «Сборщик итогов — гибрид (high-risk утверждает человек)» | decision | dormant | Единственная реализация = risk_gate.py (сам dormant). 0 import; новый skill top-layer-orchestrator не ссылается. Accepted, цитируется как принцип, но в коде не применяется. |

Связка: dormant #3 (risk_gate.py) и dormant #10 (D-006) — одна и та же мёртвая ветка (решение + его единственная нереализованная обвязка).

---

## 3. Runtime-температура (что прогонялось и когда)

base 623a193 / 2026-06-23. 5 подсистем, у всех 5 есть runtime-трейсы (.pyc mtime как proxy «реально исполнялось»).

| Подсистема | Температура | Последний прогон / след |
|---|---|---|
| conveyor | **HOT** (live, sub-hour) | conveyor.pyc compiled 16:36 / conveyor.json heartbeat 16:15 |
| friction | **WARM** | прогон сегодня ~13:00 |
| assurance | **WARM** | прогон сегодня ~13:00 |
| reconcile | **COOLING** | прогон 11:20, но backlog T-181 READY/unrun |
| knowledge | **COLD-core** | knowledge.py last ran 06-21T18:49; knowledge.db заморожен 06-21T14:07; сегодня обновлён только repo-knowledge.db (через repo-runner, НЕ knowledge.py) |

Подтверждающие артефакты: queues/done=145, conveyor workflows tracked=36, driver_audit_lines=214, reports=10 (3 датированы сегодня), logs=7.

Вывод: «горячее» применение накопленного = 1/5 подсистем (conveyor). Knowledge-корпус — главный остывший актив: хранилище наполнено, но query доказан committed-артефактом только для knowledge-corpus (FTS5 «bridge»→7 hits); порталы и repo-knowledge.db — build-only evidence, query из логов недоказуем (0 query-строк в любом audit_log).

---

## 4. DATA / хранилища знаний

| Метрика | Значение |
|---|---|
| stores всего | 9 |
| populated | 8 |
| dormant | 1 |
| empty | 0 |
| query-proven (committed-артефакт) | **1** (knowledge-corpus) |
| build-only evidence | 7 |
| порталов (всего / built / с query-артефактом) | 3 / 3 / **0** |
| .db files | 5, audit-actions distinct = только `knowledge_build`, query-строк в audit = 0 |

Все .db gitignored (build-артефакты, регенерируются). Реальное «применение» (чтение/запрос) доказано лишь для 1 из 9 хранилищ; остальные доказаны только на запись (наполнены, но queried-vs-stored недоказуемо).

---

## 5. Вердикт PROCESS-MODE (parallel / sequential)

**СМЕШАННЫЙ: производство параллельно, интеграция серийна.**

| Метрика | Значение |
|---|---|
| conveyor workflows | 36 (shipped 31 / dismissed 4 / inflight 1) |
| воркфлоу в параллельных окнах | 20 из 36 = **56%** |
| parallel-bursts (≥2 within 30s) | 7 |
| max одновременных нод в одном burst | **4** |
| max агентов на одну ноду (wide brigade) | **17** |
| бригадных воркфлоу (4wf × 4 ноды × 4 агента) | 8 нод |
| commit median gap | 7.3 мин |
| rapid-fire gaps <3 мин | 10 |
| git-авторов distinct | **1** (все 200 коммитов = Max) |
| agent-branch merges (last 200) | agent/claude=4, agent/codex=1 |
| subject agent-mentions (last 40) | FINDER=7, SOLVER=6, Mavis=1 |

Идентичность агента живёт НЕ в git %an (он один), а в merge-namespace (agent/codex, agent/claude) и сабджектах (FINDER/SOLVER/Mavis/Codex).

**Serial bottleneck:** запись в одну git-историю / commit-band одного оркестратора (canon: workflow-conveyor-policy.md:26,63; orchestration-architecture:174). Параллелизм есть на производстве (до 4 нод, бригады 17), но горлышко — единый интегратор.

Доля: **~56% parallel / ~44% serial** на уровне воркфлоу; на уровне интеграции в master — **100% serial**.

---

## 6. ИТОГ — общий коэффициент применения

**Твёрдая метрика (active/wired/enforced):**
- Сумма «применяемых»: tools 32 + skills 4 + friction 15 + decisions(code) 5 + data populated 8 + runtime 5 + docs cited 137 = **206**.
- Сумма «не-применяемых»: tools-dormant 9 + skills-ref-only 1 + friction registry-only 5 + decisions declarative 18 + data dormant 1 + docs orphan 4 = **38**.
- **Общий коэффициент ≈ 206 / (206+38) ≈ 84%** по строкам-метрикам.
- По уникальным активам (223): применяется ≈ **199**, dormant/dead ≈ **24** → **≈ 90%** мягко (docs cited зачтены), **≈ 78%** жёстко (если decisions считать по коду, а docs по genuine-цитированию).

**Что конкретно полка-пыль (не применяется):**
1. **Решения** — слабейшее звено: 78% (18/23) живут декларацией, не кодом (enforced-pct=22%).
2. **9 dormant-инструментов** (metrics, next_id, risk_gate, race_test, sandbox_intake_demo +4) — CLI без вызывателя.
3. **4 orphan/dead-дока** — write-once-never-cited.
4. **5 friction-рецептов** registry-only (нет детектора).
5. **Knowledge-ядро остыло** (corpus заморожен 06-21); query доказан лишь для 1/9 хранилищ, 0/3 порталов имеют query-артефакт.

**Что реально работает горячо:** conveyor (HOT, sub-hour) + friction/assurance (WARM, today) + 32 wired-инструмента + 137 cited-доков. Производственный параллелизм здоров (4 ноды, бригады 17); ограничитель — единый серийный интегратор (1 git-author / commit-band).