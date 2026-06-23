---
id: gate-poison-situation-2026-06-22
type: topic
title: Отравление общего gate чужой half-done задачей — ситуация и слои решений
status: resolved
resolved_by: F-020 (tools/friction.py check_gate_poison), tools/test_friction_f020.py, cohort.py guard; план S1/B2/S3 — реализованная база
date: 2026-06-22
related: [D-017, D-022, Q-015, F-006, F-007, F-011, F-015, T-150]
---

# Отравление общего gate (gate-poison) чужой незавершённой задачей

> Сводка одного инцидента, диагностированного за сессию 2026-06-22: одна битая
> ссылка в чужой half-done задаче (Codex T-150 → `docs/friction-retrospective-2026-06-22.md`,
> файла ещё не было) делала `validate.py` КРАСНЫМ и через pre-commit hook блокировала
> коммиты ВСЕМ агентам, пока файл не появился. Цель документа — описать механизм
> детально и дать РАЗНЫЕ варианты решения на РАЗНОЙ глубине (быстрый фикс / тактический /
> структурный / governance), чтобы агент или человек видел картину «что за ситуация и как
> её решать на разных уровнях».

---

## 1. Описание ситуации

### 1.1 Механизм отравления (SHARED-GATE TRANSIENT POISONING)

Pre-commit hook (`tools/githooks/pre-commit`) прогоняет ДВА последовательных gate по
ВСЕМУ дереву и блокирует коммит при любом ERROR:

- `tools/githooks/pre-commit:45` — `"$PY" tools/validate.py || { ... exit 1 }`
- `tools/githooks/pre-commit:52` — `"$PY" tools/generate.py --check || { ... exit 1 }`

Ядро механизма — проверка тем-ссылок в `validate.py`:

- `tools/validate.py:166-168` (в `check_tasks`):
  ```python
  for p in md_paths(topic):
      if not os.path.exists(os.path.join(ROOT, p)):
          err(f"TASKS: {tid} «Тема» → нет файла {p}")
  ```
- `tools/validate.py:38-39` — `err(m)` просто добавляет сообщение в глобальный список `ERRORS`.
- `tools/validate.py:427` — `sys.exit(1 if ERRORS else 0)`: ЛЮБОЙ один ERROR → exit 1.
- `tools/validate.py:426` печатает итог `OK=.. WARN=.. ERROR=..` (его парсит cohort.py).

**Цепочка отравления (на примере T-150):**
1. Создаётся `tasks/T-150.md` с front-matter `topic: docs/friction-retrospective-2026-06-22.md`.
2. `generate.py` рендерит строку в `TASKS.md` с backtick-путём в колонке «Тема».
3. Файл темы ещё НЕ создан → `validate.py:167` видит `os.path.exists()==False` → `err(...)`.
4. `ERRORS` непуст → `validate.py:427` → exit 1.
5. `pre-commit:45` получает ненулевой код → `exit 1` → коммит отклонён.
6. Поскольку `validate.py` сканирует ВСЁ дерево, отклоняются коммиты ВСЕХ агентов —
   и автора T-150, и тех, кто правит совершенно несвязанные файлы.

Зафиксировано в `docs/friction-retrospective-2026-06-22.md:152`: «validate.py сначала был
красным, потому T-150.topic указывал на ещё не созданный retrospective doc. Решение:
создать этот документ до финального validate». Отравление очистилось транзиентно, когда
Codex создал файл.

### 1.2 Чем это сильнее, чем stale-index (P-3)

Stale-index (F-007) ломает только `generate.py --check` (навигация устарела — лечится
`generate.py` + `git add`). Gate-poison ломает `validate.py` — более ранний и более жёсткий
gate: его НЕЛЬЗЯ вылечить регенерацией, только созданием недостающего файла или правкой
TASKS.md/источника. Поэтому это «отравление общего gate чужой half-done», а не просто drift.

### 1.3 Классы отравления (все ведут к одному exit 1)

| # | Класс | Где детектится | Почему блокирует всех |
|---|-------|----------------|------------------------|
| 1 | Missing topic/source-файл по ссылке | `validate.py:166-168` (`check_tasks`); аналог в `check_nav:184-187` для `темы/` в board.md/STATUS.md | `err()` → `ERRORS` непуст → `validate.py:427` exit 1 |
| 2 | Битый/неполный front-matter в источнике | `validate.py:235` (нет id), `:244-245` (нет title), `:247-248` (нет status) | Schema-нарушение = hard error; один файл = глобальный ERROR |
| 3 | Дубль id в реестре источников | `validate.py:239-240` (`if fid in seen: err(...дубликат...)`) | Любой дубль id = ERROR на всё дерево |
| 4 | Stale generated index | `generate.py:310-313` (STALE), `:341-343` exit 1 | `pre-commit:52` получает exit 1 → коммит отклонён |
| 5 | Битая cross-ссылка (depends_on / Q→D и т.п.) | `validate.py:255-258` (`depends_on` → несуществующая задача) | Cross-ref несуществующей сущности = ERROR на всё дерево |

### 1.4 Область (scope)

WHOLE-TREE. `validate.py:195` делает `os.walk(ROOT)` и собирает ВСЕ ошибки в глобальный
`ERRORS`. Нет скоупинга по агенту/подкоманде/зоне. Единственное нарушение в любом из
`{tasks/, questions/, decisions/, drivers/, TASKS.md, QUESTIONS.md, DECISIONS.md, STATUS.md,
board.md, index.json}` → глобальный exit 1 → блок всех коммитов.

### 1.5 Текущий статус

CURRENTLY CLEAN (exit 0): все задачи имеют валидные topic-ссылки либо без темы, front-matter
валиден, индексы свежие. НО механизм жив и срабатывал 3+ раза за сессию — каждый раз, когда
задача создавалась раньше своего topic-файла. Это повторяющийся архетип (P-3).

### 1.6 Связанные frictions (`docs/friction-ledger.md`)

- **F-006** (`ledger:25`) — чужая half-done в общем дереве. Прямая первопричина: незавершённая
  задача отравляет общий gate.
- **F-007** (`ledger:26`) — stale generated indexes. Родственный (класс 4), второй gate hook.
- **F-011** (`ledger:30`) — docs drift: «агент принимает решение по старой информации»; ровно
  про `generate.py --check`/`validate.py`.
- **F-015** (`ledger:35`) — сторонние правки между проверкой и commit (check→commit race);
  то же окно гонки, что и merge-back wall.
- **merge-back wall** — «Уже за сессию трижды всплывала граница merge-back в контендящееся/
  отравленное master» — это и есть симптом данного отравления.
- **same-file contention** — несколько агентов правят TASKS.md, один создаёт T-ID с битым
  topic, остальные не могут коммитить.

---

## 2. Варианты решения — матрица по глубине

Сводная таблица (детали ниже). Effort/Risk: low/medium/high.

| Глубина | Вариант | Effort | Risk | Где менять |
|---------|---------|--------|------|------------|
| Быстрый | B1. Заполнить файл-заглушку темы | low | medium | `docs/<тема>.md` |
| Быстрый | B2. L0-правило «коммить ссылку + файл вместе» + проверка | low | low | `validate.py:166-168`, `friction-playbook.md` |
| Быстрый | B3. Scope-валидация (только staged-файлы) | low | medium | `pre-commit:45`, `validate.py` (`--staged`) |
| Тактич. | T1. Вернуть T-150 в blocked / убрать строку TASKS.md | low | medium | `TASKS.md`, `tasks/T-150.md`, `generate.py` |
| Тактич. | T2. L1 worktree от чистой базы | medium | low | `flow.py`, `parallel-work-policy.md`, `worktree.py` |
| Тактич. | T3. Попросить автора закрыть/исправить | low | low | автор T-150, `TASKS.md` |
| Тактич. | T4. Delta-валидация (не добавлять новых ERROR) | medium | medium | `validate.py` (`--check-delta`), `merge_gate.py`, hook |
| Тактич. | T5. `--no-verify` (почти всегда НЕЛЬЗЯ) | low | high | hook bypass, `parallel-work-policy.md` |
| Структ. | S1. Карантин half-done (status→WARN, done→ERROR) | low | low | `validate.py` (`parse_tasks/questions/decisions`) |
| Структ. | S2. Разделённое здоровье: health(advisory) vs gate(scoped) | high | medium | `validate.py` split, `merge_gate.py`, `permissions.py`, hook, `cohort.py` |
| Структ. | S3. Guard-триггер gate-poison + L1-алерт | low | low | `cohort.py:348-363` (готово!), `metrics.py`, `friction.py` |
| Структ. | S4. Авто-восстановление (auto_heal stub) | high | high | новый `auto_heal.py`, `merge_gate.py`, `validate.py` |
| Govern. | G1. L1-by-default при validate ERROR | high | medium | `pre-commit`, `flow.py`, `friction-playbook.md` |
| Govern. | G2. Роль gate-integrator для отравленных окон | high | medium | `parallel-work-policy.md`, `merge_gate.py`, TASKS.md |
| Govern. | G3. D-023: done ↔ все зависимости готовы | high | medium | `decisions/D-023.md`, `validate.py`, `DECISIONS.md` |

### 2.1 Быстрый фикс (минуты)

**B1. Заполнить файл-заглушку темы.** Создать недостающий `docs/<тема>.md` с заголовком +
placeholder. Немедленно делает ERROR=0, hook проходит для всех.
- Pros: разблокирует за <1 мин; файл всё равно нужен; минимальный риск.
- Cons: создаёшь чужой контент (нарушает ownership); placeholder становится первым коммитом
  в файле; конфликт, если автор пишет тот же файл; не масштабируется (плодить заглушки на
  каждый half-done?).
- Где: `docs/friction-retrospective-2026-06-22.md` (как placeholder), `TASKS.md` (строка T-150),
  `validate.py:166-168` (падающая проверка).

**B2. L0-правило «ссылка + файл в одном коммите» + жёсткая проверка.** В `friction-playbook.md`:
«не коммить task/question/decision со ссылкой на несуществующий файл; topic создаётся в том же
коммите». Кодифицировать в `validate.py:166-168` уже фактически есть — усилить сообщение и
добавить в playbook раздел «Перед новой задачей».
- Pros: бьёт по корню за ~30 сек кода; без новой подсистемы; ловит ДО упаковки half-done.
- Cons: правка validate.py требует ревью; может отвергнуть легитимную 2-stage работу; не лечит
  уже отравленный mainline.
- Где: `validate.py:166-168`, `docs/friction-playbook.md`.

**B3. Scope-валидация (только изменённые/staged файлы).** Hook проверяет лишь staged этого
коммита, не всё дерево.
- Pros: самый быстрый фикс (~час); агент видит только СВОИ ошибки; простой откат.
- Cons: пропускает ошибки, бывшие в дереве ДО коммита (false negatives); финальное дерево может
  остаться грязным; два агента закоммитят ошибки в разные части, в сумме gate RED.
- Где: `pre-commit:45-50`, `validate.py` (режим `--staged/--diff`).

### 2.2 Тактические (этот инцидент, обратимо)

**T1. Вернуть T-150 в draft/blocked или временно убрать строку из TASKS.md.** Тогда нет ссылки
на несуществующий файл → validate проходит.
- Pros: разблокирует немедленно; обратимо; не создаёшь чужой контент; «не готово → не done».
- Cons: правка TASKS.md = правка governance-таблицы; автор может испугаться «пропала задача»;
  после возврата нужен `generate.py` (возможен конфликт); лечит симптом.
- Где: `TASKS.md` (строка T-150), `generate.py`, `tasks/T-150.md`.

**T2. L1 worktree от чистой базы.** `git worktree add` от стабильного коммита, работать и
коммитить там (hook проходит), merge ждёт очистки master. Документированный паттерн.
- Pros: твой коммит не зависит от чужой half-done; Level-1 изоляция (отдельный validate/generate
  контекст по D-022); параллельная работа; merge автоматизируем после очистки.
- Cons: нужен синтаксис git worktree; disk overhead; возможны merge-конфликты; не лечит сам gate
  (работаешь вокруг); если твоя задача зависит от заблокированного коммита — всё равно stuck.
- Где: `git config core.hooksPath`, `docs/parallel-work-policy.md` (раздел L1), `tools/flow.py`,
  `tools/worktree.py`.

**T3. Попросить автора закрыть/исправить.** Синхронно автору (Codex): T-150 done, но topic-файла
нет → gate poison. Пусть выберет (a) создать файл, (b) blocked, (c) убрать из TASKS.md.
- Pros: прямое общение; автор знает причину (WIP/feedback); документирует инцидент.
- Cons: зависит от доступности автора (timezone/busy); синхронно; не решает, если автор занят.
- Где: автор T-150, `TASKS.md`, `docs/friction-retrospective-2026-06-22.md`.

**T4. Delta-валидация (монотонность ERROR).** Коммит проходит, если он НЕ добавляет новых ERROR:
сравнить ERROR(staged) vs ERROR(HEAD); пускать если `ERROR(staged) <= ERROR(HEAD)`.
- Pros: агент не блокируется чужой half-done — чинит своё; гарантирует «не хуже»; эволюционно.
- Cons: сложнее в отладке (откуда дельта?); нужен baseline; на уже заражённом дереве первый
  коммит усугубляет; дерево остаётся грязнее.
- Где: `validate.py` (`--check-delta` с base-ref), `merge_gate.py`, hook.

**T5. `git commit --no-verify` — почему почти всегда НЕЛЬЗЯ.** Обход hook.
- Pros: быстро; твой коммит проходит; для emergency, если уверен в своих файлах.
- Cons: НЕ лечит poison — следующий коммит соседа всё равно заблокирован; убивает доверие к hook;
  `parallel-work-policy.md` запрещает без явного решения уровня D-021/D-022; маскирует реальные
  ошибки; в shared-tree особенно опасно (merge может быть corrupted). Анти-паттерн F-006/F-015.
- Где: `pre-commit:8` (документация bypass), `parallel-work-policy.md`.

### 2.3 Структурные (правка инструментов)

**S1. Карантин half-done (рекомендуемая база).** В `validate.py` сделать ссылку условной от
статуса: `status ∈ {todo, doing, blocked}` + битая topic-ссылка → **WARN**, а не ERROR; **ERROR**
только при `status=done` (и аналогично answered/accepted для Q/D).
- Pros: очень простая механика; архитектурно корректно (незавершённое ≠ готовое); автоматически
  разрешает параллель (Codex ставит T-150 doing, ссылка «в процессе» ок); НЕ трогает hook/gate/
  cohort; снимает основную боль.
- Cons: не ловит ERROR в done-задачах, если кто-то сломает их файл; требует дисциплины (done
  только после готовности); если чужая задача в done с битой ссылкой — всё равно блок; «бит-в-
  процессе» скрывается до позднего surprise.
- Где: `validate.py` (`parse_tasks`/`parse_questions`/`parse_decisions` — условие по статусу;
  опционально front-matter `required_topic: true/false`).

**S2. Разделённое здоровье дерева.** Две проверки: HEALTH (advisory, всё дерево, печатает в
`cohort.guard()`) и GATE (блокирует только ошибки, добавленные ЭТОЙ задачей/зоной из
`permissions.json`).
- Pros: чёткое разделение видимость vs блокировка; масштабируется на параллель; отвечает на
  D-022 (загрязнил не-свою зону → WARN); снимает LS-5 (видимость).
- Cons: рефакторинг validate.py + merge_gate.py (2-3 ч); нужно определить границы зон (сложно при
  параллели); пересечение зон — кто отвечает?; правило zone обходимо (коммит в чужую зону).
- Где: `validate.py` (split `check_health` + `check_gate`), `merge_gate.py`, `permissions.py`,
  `pre-commit`, `cohort.py` guard.

**S3. Guard-триггер gate-poison + L1-алерт (почти готово в коде!).** `cohort.py` guard УЖЕ
детектирует poison — `tools/cohort.py:348-363`: запускает `validate.py`, ищет `ERROR=(\d+)`,
собирает первые ERROR-строки, выставляет `trigger: gate-poison`. Останется: добавить метрику
`poison_count` в `metrics.py` и трекинг события в `friction.py`.
- Pros: почти ничего не менять — guard уже печатает gate-poison; выбор за агентом (подождать или
  worktree); friction-тренд во времени; отвечает на первопричину (D-022); лёгкий откат.
- Cons: НЕ блокирует автоматически (нужна дисциплина); если агент игнорирует — упрётся в hook;
  нужна культура уважения worktree-рекомендации; метрика без действия = шум.
- Где: `tools/cohort.py:348-363` (готово), `tools/metrics.py`, `tools/friction.py`.

**S4. Авто-восстановление (auto_heal).** Гибрид T4+S1: основная валидация delta, плюс
`auto_heal.py` при ERROR>0 пытается (a) создать stub-файл, (b) пометить unknown в TASKS.md,
(c) regenerate.
- Pros: самовосстановление gate; агент получает помощь, а не блок; история poison-событий;
  меньше ручного вмешательства.
- Cons: сложнейший (2-3 дня); риск, что auto-heal stub случайно закоммитят и распространят;
  нужны консервативные правила (что создавать можно); маскирует реальную незавершённость; высокая
  операционная сложность отладки.
- Где: новый `tools/auto_heal.py`, `merge_gate.py`, `validate.py`.

### 2.4 Governance (процесс/политика)

**G1. L1-by-default при validate ERROR.** Если hook видит `validate.py` ERROR (не WARN) — shared-
tree коммиты заблокированы, агенту предписано `flow.py start <agent> <task> --worktree`. Изолирует
отравление от mainline (синергия с Q-015 B / D-022 trigger C).
- Pros: отравленные коммиты не попадают в mainline до фикса; явный сигнал «используй worktree»;
  рекурсивно (merge_gate в worktree тоже ловит ERROR).
- Cons: правка `flow.py`/hook (нетривиально); жёстко для мелких doc-правок; нужен хороший UX
  объяснения ERROR.
- Где: `pre-commit` (после validate rc!=0), `flow.py`, `friction-playbook.md`.

**G2. Роль gate-integrator для отравленных окон.** Назначить single point (Stefan/дежурный) для
разрешения validate ERROR: ACCEPT только если (1) error временный (файл будет создан next turn),
(2) письменное обоснование в `queues/outbox/`, (3) не блокирует других (индексы свежие). Коммит
приземляется со статусом `gated` в PIPELINE.md.
- Pros: нет монолит-затора (один пакет ≠ все блокированы); документирует исключения; интегратор
  может post-hoc cherry-pick фикс; согласуется с D-022 (merge-gate как final validation).
- Cons: governance overhead роли; bottleneck при медленном интеграторе (нужен SLA <2 ч); разные
  интеграторы → разные критерии (нужен playbook).
- Где: `parallel-work-policy.md` (раздел роли), `TASKS.md` (роль), `merge_gate.py` (статус
  `gated-approval`).

**G3. D-023: status=done ↔ все зависимости готовы.** Decision: задача/вопрос может быть `done`
только если все файлы-ссылки (topic, depends_on) существуют и зависимые задачи тоже `done`.
Проверяется `validate.py`.
- Pros: предотвращает poison по конструкции; «done → deliverables ready»; обучает команду.
- Cons: нужен buy-in/обсуждение; иногда «done» = «моя часть готова, ждём генерации»; надо отличать
  авторские файлы (docs/...) от генерируемых (TASKS.md); без автоэнфорса обойдут.
- Где: `decisions/D-023.md`, `parallel-work-policy.md`, `validate.py` (done-deps check), `DECISIONS.md`.

---

## 3. Подсистема Codex (friction.py/ledger/playbook): дубль или комплемент?

**Вывод: это КОМПЛЕМЕНТ, не дубль.** Две подсистемы решают разные задачи:

- **Моя ветка (parallel-work-policy / cohort.guard / cohort)** — `docs/parallel-work-policy.md`
  (D-022/Q-015 B) + `tools/cohort.py` guard: КОГДА уходить в Level-1 worktree, как не сцеплять
  агентов через генерируемые индексы, триггеры (uncommitted-source / hot-file / stale-index /
  **gate-poison**). Это «как один агент не отравляет общий gate и как изолироваться».

- **Ветка Codex (friction.py / friction-ledger / friction-playbook)** — `tools/friction.py`
  (T-150, status/recipe/list), `docs/friction-ledger.md` (F-001..F-019), `docs/friction-playbook.md`:
  read-mostly детектор, мапит видимые симптомы на F-XXX и печатает стабильный рецепт. Это «реестр
  повторяющихся болей + рецепты».

- **D-017 (`decisions/D-017.md`)** решает ТРЕТЬЕ — fork-and-synthesize: как двум агентам работать
  над одной СОДЕРЖАТЕЛЬНОЙ темой через параллельные форки + обязательный синтез. Gate-poison —
  это НЕ про варианты содержания, а про gate-гигиену half-done. Значит D-017 и gate-poison —
  разные оси: их нельзя путать.

**Предложение синтеза (в духе D-017, без дублирования):**
1. Добавить в `docs/friction-ledger.md` новый архетип **F-020 «Gate-poisoning from half-done task
   dependencies»** со ссылкой на D-022 (триггер gate-poison уже есть в `cohort.py:348-363`) и на
   данный документ. Правило: задача с ссылкой на несуществующий topic → либо blocked до создания
   файла (B2/S1), либо в Level-1 worktree (T2/G1).
2. Связать слои: детектор (`cohort.guard` gate-poison + `friction.py` рецепт F-020) → политика
   (parallel-work-policy: «validate ERROR → L1 или ждать») → governance (опционально D-023).
   Так подсистемы Codex и моя сходятся: friction.py указывает на проблему, cohort/policy дают
   действие. Это синтез по образцу D-017 (сравнить → консенсус), а не выбор «или-или».
3. Явно задокументировать различие D-017 vs F-020, иначе агенты перепутают сценарии (вариант
   содержания ≠ битая зависимость).

---

## 4. Рекомендуемый слоёный план

### Сейчас (разблокировать и закрыть инцидент)
- Если gate КРАСНЫЙ из-за чужого half-done: **T3** (попросить автора) ИЛИ **T2** (L1 worktree),
  при острой нужде — **B1** (заглушка). НЕ использовать `--no-verify` (T5).
- Перед стартом любой работы запускать `tools/cohort.py guard` — он уже печатает gate-poison
  (`cohort.py:348-363`), это бесплатная ранняя видимость (**S3** уже на 90% в коде).

### Дальше (структурно, низкий риск, высокий эффект)
- **S1 (карантин half-done)** как первичная правка `validate.py`: status doing/todo/blocked +
  битая topic-ссылка → WARN; done → ERROR. Это снимает корень gate-poison без трогания hook.
- **B2** в `friction-playbook.md`: «ссылка + файл в одном коммите».
- **S3 добиение**: метрика `poison_count` в `metrics.py` + `friction.py note F-020` для тренда.

### Governance (когда стабилизируется)
- **F-020** в ledger + раздел в `parallel-work-policy.md`: «validate ERROR → L1 или ждать»
  (мягкий **G1**).
- Рассмотреть **D-023** (done ↔ зависимости готовы) как автоэнфорс S1 на уровне политики.
- **G2** (gate-integrator) — только если параллель вырастет и затор станет частым; иначе overhead.

### Что НЕ делать
- S4 (auto_heal) и S2 (зоны) — отложить: высокий effort/risk, не оправданы текущей частотой.
- T5 (`--no-verify`) — запрещено без явного решения D-021/D-022.

---

## Связанные файлы (абсолютные пути)
- `C:/Users/stefan/Documents/New project ai colab/tools/validate.py` (:166-168, :235-258, :427)
- `C:/Users/stefan/Documents/New project ai colab/tools/githooks/pre-commit` (:45, :52)
- `C:/Users/stefan/Documents/New project ai colab/tools/generate.py` (:300-343)
- `C:/Users/stefan/Documents/New project ai colab/tools/cohort.py` (:348-363 — gate-poison guard)
- `C:/Users/stefan/Documents/New project ai colab/tools/friction.py` (T-150, подсистема Codex)
- `C:/Users/stefan/Documents/New project ai colab/docs/friction-ledger.md` (F-006/F-007/F-011/F-015)
- `C:/Users/stefan/Documents/New project ai colab/docs/parallel-work-policy.md` (D-022/Q-015 B триггеры)
- `C:/Users/stefan/Documents/New project ai colab/decisions/D-017.md` (fork-and-synthesize — комплемент)
- `C:/Users/stefan/Documents/New project ai colab/docs/friction-retrospective-2026-06-22.md` (:152 — инцидент)
