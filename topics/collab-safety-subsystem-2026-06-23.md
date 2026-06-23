---
id: collab-safety-subsystem-2026-06-23
type: topic
title: Авторитетная архитектура подсистемы безопасной коллаборации / параллельной работы (атомарные примитивы + ownership-детекторы + изоляция L0/L1)
status: proposed
date: 2026-06-23
related: [D-021, D-022, D-023, parallel-work-policy, parallel-work-consensus-2026-06-22]
---

# Подсистема безопасной коллаборации: авторитетная архитектура

> **proposed** — единый канон-документ по подсистеме collaboration-safety / parallel-work. Сводит три producer-секции (атомарные примитивы конкурентности, ownership-классификация/детекторы трения, модель изоляции L0/L1 + слияние) в одну авторитетную картину. Governance-основа ратифицирована в `D-021` (Уровень-1 принят), `D-022` (триггеры/политика) и `D-023` (ownership-ответственность за индексы); детальная матрица «ситуация → механизм» — в `docs/parallel-work-policy.md`.

Эта подсистема отвечает на один вопрос: **как N агентов работают над одним репозиторием параллельно, не теряя чужую работу, не блокируя друг друга и не вливая «грязное» состояние в общую историю.** Ответ распадается на три слоя, описанных ниже:

1. **Атомарные примитивы конкурентности** — как сериализуются коммиты и фехтуются claim-ы задач без потоков, замков ОС и БД (только атомарные операции ФС + TTL-лизы + fencing-токены).
2. **Ownership-классификация и детекторы трения** — как один классификатор отличает «моё» от «чужого», и как детектор (`friction.py`) и исполнитель (`cohort.py guard`) на этом строят вердикт.
3. **Изоляция и слияние** — бинарная модель Level-0 (общее дерево + `commit_lock`) против Level-1 (worktree-на-агента + `merge_gate`), её триггеры эскалации и правило ответственности за индексы.

Все три слоя разделяют одну идею: **лиза, которая истекает по времени** (без liveness-пинга), реклеймится «winner-take-all»-атомарным созданием, а **fencing-токен** не даёт зомби-холдеру закоммитить устаревший результат.

---

## Слой 1. Атомарные примитивы конкурентности: сериализация коммитов и фехтование claim-ов

Конкурентные агенты в этом репозитории **никогда** не используют потоки-замки ОС или базу данных; они координируются целиком через **атомарные операции файловой системы** — `os.open(..., O_CREAT|O_EXCL)` для «выигрывает ровно один создатель» и `os.replace` для атомарного свопа — плюс дисциплину **TTL-лиза + fencing-токен**, чтобы работу упавшего агента можно было безопасно реклеймить, не давая двум агентам «выиграть» одновременно. Есть два уровня: короткоживущий commit-lock, сериализующий git-коммиты, и per-task claim, фехтующий работу конвейера.

### 1.1. Commit-lock — сериализация `git commit` (`tools/commit_lock.py`)

Замок — единственный файл `queues/commit.lock` (`commit_lock.py:30`). Цель явно в docstring: агенты не должны драться за гитовый `index.lock`, поэтому перед `generate + git add + git commit` агент берёт замок и освобождает после; коммиты сериализуются, «no rebounds and fails on a parallel index.lock» (`commit_lock.py:6-8`). Docstring аккуратно подчёркивает, что это **сериализация, а не изоляция** — он не защищает от коммита чужой half-done работы; это задача отдельного правила *selective-add* (коммить только свои файлы, никогда `git add -A`), с полной изоляцией, отложенной до worktree (`commit_lock.py:10-12`).

- **Атомарный acquire через O_EXCL.** `_write_excl` открывает замок через `os.open(LOCK, os.O_CREAT | os.O_EXCL | os.O_WRONLY)` (`commit_lock.py:67`). `O_EXCL` делает создание падающим с `FileExistsError`, если файл уже существует, так что ровно один из N гонящихся агентов создаёт его. Тело — три строки: `agent`, `epoch` (now) и `lease_epoch` (now + ttl) (`commit_lock.py:66`).
- **TTL-лиза / устаревание.** Свежесть чисто временная: `_fresh` возвращает `int(d["lease_epoch"]) > int(time.time())` (`commit_lock.py:58-62`). Дефолтный TTL — 120с (`commit_lock.py:72`).
- **Stale-takeover с race-safety.** В `acquire` при `FileExistsError` холдер читается; если он **не** свеж (`not _fresh(d)`), замок `os.remove`-ится и цикл повторяется (`commit_lock.py:80-88`). Комментарий отмечает: гонка здесь разрешается `O_EXCL` на retry — даже если два агента оба удалят и повторят, только один пересоздаст файл. Если холдер ещё свеж, агент ждёт до `--wait` секунд, опрашивая каждые 0.5с, затем возвращает `1` (BUSY) по дедлайну (`commit_lock.py:89-93`).
- **Release с проверкой владения.** `release` отказывается удалять замок, удерживаемый другим агентом: если `d.get("agent") != agent`, печатает ошибку и возвращает `1`, не удаляя (`commit_lock.py:101-103`). Это не даёт одному агенту сбросить замок другого.

Контракт кодов возврата: `acquire` возвращает `0`=взял / `1`=не взял (`commit_lock.py:79, 92`), так что шелловый `if` может гейтить коммит (`commit_lock.py:20-23`).

### 1.2. Атомарная выдача id (`tools/next_id.py`)

Тот же примитив `O_CREAT|O_EXCL` не даёт двум агентам выпустить одинаковый `T-/Q-/D-` id. `existing_max` сканирует директорию на `max+1` (`next_id.py:87-94, 116`), затем в цикле пытается создать `<id>.md` через `os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)`; при `FileExistsError` (другой агент схватил это число) инкрементирует `n` и повторяет, до 1000 попыток (`next_id.py:117-124, 130`). Созданный файл — валидный-но-зарезервированный stub, чтобы `validate.py` прошёл до того, как агент его заполнит (`next_id.py:41-84`). Это паттерн docstring-а «as claim in queue.py» (`next_id.py:11-12`).

### 1.3. Pipeline-claim — фехтование работы задач (`tools/pipeline.py`)

Claim — файл `queues/claimed/<T-id>.claim.md` (`pipeline.py:91-92`), чей front-matter несёт `task`, `agent`, `claim_id` и `lease_epoch` (`pipeline.py:135-136`). `claim_id` — случайный `uuid4().hex[:12]` (`pipeline.py:133`) и действует как **fencing-токен**. Дефолтная лиза — 30 мин (`pipeline.py:56, 134`). Свежесть, как и у commit-lock, — `lease_epoch > now` (`claim_is_fresh`, `pipeline.py:95-105`).

Цель дизайна — **gap-free pull**: `try_claim` сливает DAG-готовность и атомарный захват в один `pull-next`, так что «между „увидел задачу“ и „взял её“ нет окна для перехвата» (`pipeline.py:9, 24-26`).

**`try_claim` — атомарный claim, включая stale-takeover (`pipeline.py:121-191`):**
- **Happy path:** `os.open(p, O_CREAT|O_EXCL|O_WRONLY)` — первый создатель выигрывает, пишет тело, возвращает `cid` (`pipeline.py:138, 189-191`).
- **Занято живым агентом:** при `FileExistsError` читаем холдера; если `lease_epoch > now`, возвращаем `None` (`pipeline.py:141-146`).
- **Stale-takeover, гейтированный вторым эксклюзивным замком.** Это тонкая часть (T-082 / review T-078 finding I, `pipeline.py:122-130, 147-188`). Два агента, видящие *один и тот же* истёкший claim, не должны оба его перезаписать. Поэтому takeover гейтируется lock-файлом, чьё имя **производно от `claim_id` устаревшего claim-а**: `"%s.take.%s" % (p, old["claim_id"])` (`pipeline.py:148`). Оба агента вычисляют одно имя замка; `O_CREAT|O_EXCL` на нём даёт ровно одного победителя (`pipeline.py:149-152`).
- **Re-check под замком (double-take guard).** После взятия замка холдер перечитывается; если claim уже не тот же устаревший — пропал, другой `claim_id`, или теперь свеж — агент отступает с `None` (`pipeline.py:161-165`). Комментарий объясняет: это закрывает гонку (T-084 re-check), где другой агент уже сделал takeover и *освободил* замок между чтением `old` и взятием замка; без этого опоздавший агент затёр бы свежий claim (double capture).
- **Атомарный своп.** Новый claim пишется во временный файл `"%s.tmp.%s" % (p, cid)`, затем `os.replace(tmp, p)` свопает его атомарно (`pipeline.py:166-176`). Замок всегда снимается в `finally` (`pipeline.py:184-188`).
- **Windows-харднинг.** `os.replace` ретраится до 5×0.02с на транзиентный `PermissionError`, затем сдаётся, возвращая `None`, а не пробрасывая исключение; `PermissionError` на начальном `os.open` тоже возвращает `None` (`pipeline.py:139-140, 169-183`). `claim_holder` так же глотает `OSError` и возвращает `None` (транзиентный «нет холдера»-вид) вместо краша (`pipeline.py:107-118`).

**Фехтование на завершении — `_check_holder` в `done`/`fail` (`pipeline.py:308-322`):** Оба `cmd_done` и `cmd_fail` зовут `_check_holder(tid, agent, claim_id)` и прерываются по ошибке (`pipeline.py:361-363, 389-391`). Он применяет два правила:
1. **Проверка имени агента (всегда):** если `agent` текущего холдера — кто-то другой, reject (`pipeline.py:317-318`).
2. **Проверка fencing-токена (только когда передан `claim_id`):** переданный `claim_id` должен равняться `claim_id` текущего холдера, иначе «intercepted/expired» — так что агент, чей claim был перехвачен или истёк, не может закрыть устаревшую работу (`pipeline.py:319-321`). Когда `claim_id` не дан, вызов обратно-совместим (только по имени). Только после прохождения `cmd_done` ставит статус `done`, пишет per-task done-маркер и `_release`-ит claim (`pipeline.py:377-379`).

Per-task done/fail-маркеры (`queues/done/<id>.done.md`, `queues/failed/...`) — conflict-free источник истины для отчётов (`pipeline.py:24-26, 378, 289-305`), избегающий контеншена на общем логе. `heartbeat` тоже использует temp-file-then-`os.replace` для атомарных апдейтов (`pipeline.py:632-636`).

### 1.4. Как тесты доказывают, что работа не теряется

**`tools/test_commit_lock.py`** прогоняет замок через весь контракт на изолированном `COLLAB_ROOT` (`test_commit_lock.py:32-35`): первый acquire успешен, acquire второго агента отвергается (`==1`), чужой `release` отвергается (`==1`), а у владельца — успешен, и — ключевой кейс durability — рукописный замок с `lease_epoch: 1` (давно истёкший) корректно перехватывается новым агентом (`test_commit_lock.py:41-54`). Это ровно гарантия «TTL удаляет замок упавшего агента».

**`tools/test_pipeline_fencing.py`** (T-082, findings H/I) доказывает фехтование claim под реальной конкурентностью:
- **done-fencing:** неверный `claim_id` (`deadbeef00`) отвергается, чужой агент отвергается, и только корректный `cid` доходит до `done` — с уликой `applied`, попадающей в done-маркер (`test_pipeline_fencing.py:57-71`). Done без `claim_id` остаётся обратно-совместимым (`test_pipeline_fencing.py:74-81`).
- **Сама гонка:** заглавный тест сеет истёкший claim и запускает **8 потоков**, зовущих `try_claim` одновременно, повторённых **16 раундов** (одиночные прогоны прятали баг, `test_pipeline_fencing.py:136-140`). Каждый раунд проверяет, что ни один воркер не упал, **ровно один победитель** (`len(winners) == 1`), и claim в итоге свеж (`test_pipeline_fencing.py:155-175`). Это конкретное доказательство: `.take.<claim_id>`-замок + re-check + `os.replace` позволяют ровно одному агенту реклеймить брошенную работу — никогда ноль, никогда два.
- **Targeted-claim состояния:** ready→success, busy→reject (чужой claim нетронут, статус не изменён), unmet-dependency→reject, placeholder→reject, done/missing→reject — подтверждая, что claim никогда не создаётся там, где не должен (`test_pipeline_fencing.py:177-203`).

### 1.5. Сводка модели сериализации/фехтования

| Забота | Примитив | Где |
|---|---|---|
| Сериализовать git-коммиты | `O_CREAT\|O_EXCL` lock-файл + TTL-лиза + release с проверкой владельца | `commit_lock.py:67, 58-62, 101-103` |
| Уникальная выдача id | `O_CREAT\|O_EXCL` create-or-bump-and-retry | `next_id.py:117-124` |
| Атомарно заклеймить задачу | `O_CREAT\|O_EXCL` claim-файл; у `pull-next` нет окна | `pipeline.py:138, 9` |
| Безопасно реклеймить задачу упавшего агента | второй `O_EXCL`-замок по `claim_id` устаревшего + re-check + `os.replace` | `pipeline.py:148-176` |
| Не дать устаревшему/перехваченному агенту завершить работу | fencing-токен `claim_id`, проверяемый в done/fail | `pipeline.py:308-322` |
| Crash-recovery без потери работы | временной `lease_epoch` TTL делает claim-ы/замки реклеймимыми | `commit_lock.py:58`, `pipeline.py:95-105` |

Два пути crash-recovery делят одну идею: лиза, которая *истекает* (без liveness-пинга), реклеймится winner-take-all атомарным созданием, с fencing-токеном (`claim_id` / `agent`), гарантирующим, что исходный, теперь-зомби-холдер никогда не закоммитит устаревший результат.

---

## Слой 2. Ownership-классификация и детекторы трения

Репозиторий отличает *мою* работу от *чужой* через один общий классификатор (`tools/ownership.py`, T-153), который импортируют обе подсистемы: Codex-сторонний детектор (`tools/friction.py status`) и Claude-сторонний исполнитель (`tools/cohort.py guard`). До T-153 каждый грубо считал «чужие незакоммиченные файлы» сам, так что `guard` ложно срабатывал на *собственных* правках агента; `ownership.py` теперь единственный источник истины (`tools/ownership.py:4-18`).

### 2.1. Классификатор: mine | generated | volatile | foreign | unknown

`classify(path, agent, task_files, claim_map, root)` возвращает ровно одну метку, проверяемую в приоритетном порядке (`tools/ownership.py:62-89`):

1. **mine** — путь (или basename) в явном списке `task_files` (`:67-70`), либо entity-id пути (`T-/Q-/D-NNN`, через `_ID_RE` `:30`) мапится в claim-карте на холдера, равного `agent` (`:78-82`).
2. **volatile** — рантайм-снимки: точные члены `VOLATILE` (`LIVE.md`, `PIPELINE.md`, `logs/heartbeat.json`, `logs/pipeline.json`), любой `logs/`-префикс, или basename-ы `heartbeat.json`/`pipeline.json` (`:26-28`, `:71-72`). Не стейджатся в обычных коммитах.
3. **generated** — канонические производные индексы, чей basename в `GENERATED` (`TASKS.md`, `QUESTIONS.md`, `DECISIONS.md`, `board.md`, `STATUS.md`, `index.json`) (`:25`, `:73-74`). Регенерируются, поэтому не связывают агентов.
4. **foreign** — source-файл с entity-id, чей claim-холдер — *другой* агент (`:78-83`), либо `outbox/`/`streams/`-файл, чей суффикс имени называет другого агента через `_AGENT_RE` (claude|codex|mavis|novax) (`:31`, `:84-88`).
5. **unknown** — source-файл без явного владения (tools/docs/themes без claim-а); намеренно *не* трактуется как foreign (`:15`, `:89`).

Поиск холдера приходит из `claims()`, который парсит `queues/claimed/*.claim.md` на строку `agent:`, чтобы построить `task_id -> holder` (`:38-54`). Ключевое правило дизайна (`:17`): **только `foreign` обязан эскалировать до Level-1 (D-022)**; generated/volatile/unknown/mine — нет. `summary(paths, ...)` сворачивает per-path классификацию в бакеты и флаг `has_foreign`, сигналящий, требуется ли Level-1 (`:98-104`).

### 2.2. cohort.py guard: триггеры и рецепт ship

`guard()` читает `git status --short`, нормализует пути и вычисляет Level-1-триггеры (`tools/cohort.py:336-394`). Он «ownership-aware»: foreign приходит прямо из `own.summary(paths, agent)["by"]["foreign"]` (`:349`), так что срабатывает только на чужих заклейменных файлах, никогда на моих/generated/volatile. Четыре триггера, каждый несёт кросс-линк `recipe`-алиас в friction.py (`:362-370`):

- **foreign-source** — присутствуют чужие source-файлы → рецепт `foreign` (`:363-364`).
- **hot-tool** — грязный путь в `tools/`-scoped-подмножестве `HOT_FILES` (`top.py`, `portal.py`, `capabilities.py`, `generate.py`); заметьте, генерируемые индексы здесь исключены, т.к. регенерируются (`:42-43`, `:350-351`, `:365-366`).
- **stale-index** — `generate.py --check` вернул не-ноль или вывод содержит `STALE`/`устарел` → рецепт `stale-index` (`:353-354`, `:367-368`).
- **gate-poison** — `validate.py` сообщает `ERROR=N>0`, т.е. общий validate-гейт красный (часто от half-done соседа) и pre-commit-хук заблокировал бы коммиты *всем* → рецепт `gate-poison` (`:355-359`, `:369-370`, `:386-388`).

Любой триггер ставит `level1_recommended`, и вердикт указывает на `flow.py start <agent> <task> --worktree --run`; иначе Level-0 в порядке через `cohort ship` (`:371`, `:389-392`).

Путь **ship** (`ship()`, `:246-281`) — Level-0 safe-commit-цикл, на который ссылается selective-add + regenerate: `commit_lock acquire` (сериализация) → `git add <явные файлы>` только, никогда `git add -A` (`:252`, `:273`) → `generate.py` для обновления производных индексов, чтобы хук не упал на устаревании соседа (`:258`, `:274`) → `git commit` → `commit_lock release` (`:268-280`). Регенерированные индексы намеренно оставляются не-staged для владельца изменённого source (`:248-250`).

### 2.3. friction.py: F-XXX детекторы, read-only/advisory

`tools/friction.py` — read-mostly детектор (T-150): он мапит симптомы на F-XXX ledger-записи и печатает рецепты, но не авто-чинит; единственная запись по умолчанию — tmp-work-проба, которая создаётся и удаляется (`tools/friction.py:3-13`). `collect_status()` прогоняет ~13 проб и эмитит `make_check`-записи со статусом `ok|warn|fail|info` плюс улика и хинт-рецепт (`:323-333`, `:542-587`).

Ownership-интеграция — в `check_git_status()` (`:357-406`): зовёт `ownership.summary()` на грязных путях и ветвится по `foreign` (`:363-366`). Если foreign-source есть → **F-006 warn** «shared tree has FOREIGN uncommitted source» с Level-1 worktree-рецептом; иначе если есть не-volatile грязное → **F-006 warn**, но в рамке «yours/unknown, not foreign» с selective-add/Level-0-рецептом; иначе **F-006 ok** (`:368-381`). Отдельные проверки флагуют volatile-снимки (**F-008**, `:383-390`) и грязные generated/shared-файлы, требующие re-check перед стейджем (**F-015**, `:392-405`). Идентичность агента течёт из CLI-флагов `--agent`/`--task`/`--files`, где task-карта `tasks/<T-ID>.md` трактуется как моя (`:550-554`, `:691-693`).

Полный реестр держит **F-001..F-020** (`:47-285`; F-020 добавлен 2026-06-23, commit `67fa8b5`, запись `:273-284`). `recommendation()` превращает худшие статусы в один вердикт, напр. STOP на F-003/F-004 fail, WAIT на F-005, «LEVEL 1 OR SELECTIVE-ADD» на F-006/F-007/F-011/F-013/F-015/F-020 warn (`:635`). Рецепты адресуемы по id или алиасу через `ALIASES`.

### 2.4. F-020 (gate-poison) — ПОДКЛЮЧЁН (SHIPPED 2026-06-23, commit `67fa8b5`)

Под-вопрос говорит «F-001..F-020», и теперь **F-020 ЕСТЬ в REGISTRY friction.py** (`tools/friction.py:273-284`, добавлен commit `67fa8b5`). Рекомендованный `check_gate_poison()` реализован (`friction.py:477`): `collect_status` прогоняет `validate.py` и эмитит F-020 warn при `ERROR=N>0` (`:608`), а `recommendation` учитывает F-020 в «LEVEL 1 OR SELECTIVE-ADD» (`:635`). Теперь оба детектора (friction.py + cohort.py guard `tools/cohort.py:355-359`) согласованно флагуют самое опасное состояние общего дерева — drift, отмеченный в `topics/friction-subsystems-synthesis-2026-06-22.md:94,101,105-111`, закрыт. gate-poison больше не только cohort-сторонний guard-триггер: это подключённый friction.py-детектор.

### 2.5. Как две стороны сходятся

`friction.py` — read-only источник истины о *симптомах и рецептах*; `cohort.py guard` — *решающее/исполнительное* плечо, мапящее то же грязно-древесное состояние в вердикт Level-0-vs-Level-1. Они делят `ownership.py`, так что «моё vs чужое» судится одинаково, а триггеры guard кросс-ссылаются на friction-рецепты по алиасу (`tools/cohort.py:384-385`). Обе сегодня независимо шеллят в `generate.py --check` и (на cohort-стороне) `validate.py` — синтез-док флагует это дублирование (`topics/friction-subsystems-synthesis-2026-06-22.md:95`) и предлагает единую общую freshness-пробу.

---

## Слой 3. Изоляция + слияние: Level-0 (общее дерево + commit_lock) против Level-1 (worktree + merge_gate)

Кодовая база коллаборации определяет **бинарную двухуровневую модель** для мульти-агентной параллельной работы, ратифицированную в `decisions/D-021.md` и детализированную в `decisions/D-022.md` + `docs/parallel-work-policy.md`. Level-0 — дешёвый дефолт (общее дерево, сериализованные коммиты); Level-1 — обязательная-по-триггеру изоляция (per-agent git worktree + merge-gate). `decisions/D-023.md` добавляет ownership-правило, кто коммитит регенерированные индексы.

### 3.1. Level-0 — общее дерево + commit_lock (дефолт)

Level-0 — «selective-add + `commit_lock` в общем дереве» и «остаётся дешёвым дефолтом для изолированной работы» (`docs/parallel-work-policy.md:30`; `decisions/D-021.md:23-24`: «**Уровень-0** (selective-add + `commit_lock`) остаётся дефолтом»). Все агенты делят одно рабочее дерево; git-операции сериализуются через advisory `commit_lock`, а коммиты используют **явный selective-add** (`git add file1 file2`, никогда `git add -A` в грязном дереве — `docs/parallel-work-policy.md:67`, анти-паттерн 1 на :182).

`tools/stream.py` — **stream-packet (fork)-слой** и показывает, как переиспользуется Level-0-сериализация: он импортирует `commit_lock as cl` с комментарием «сериализация записи под общий commit-lock (Уровень 0)» (`tools/stream.py:34`). При адопте stream-варианта переписывание front-matter оборачивается в `cl.acquire(agent)` / `cl.release(agent)`, чтобы агенты «не дерёмся за общий канон» (`tools/stream.py:231-238`). Stream-пакет — `streams/<topic>/<id>/STREAM.md` с front-matter (id/topic/agent/status/created, опц. `adopted_commit`), описанный как «fork-пакет варианта», чей адопт в mainline — governance-решение, отложенное до D-018 (`tools/stream.py:6-10`, :76-94). В формулировке проекта streams держат mainline узкой («маленький ручеёк / a narrow trickle») — т.е. варианты развиваются в half-committed-пакетах, пока явно не `adopt`-нуты под замком.

### 3.2. Level-1 — изоляция worktree + merge_gate (обязательна по триггеру)

Level-1 даёт каждому агенту **собственный git worktree** на ветке `agent/<agent>/<task>`, так что `git add -A` видит только работу этого агента, а `index.lock` никогда не коллизит (`tools/worktree.py:4-9`). `tools/worktree.py` — «Уровень-1 политики коммитов, T-136» и завершает Level-1-набор рядом со `stream.py` (fork-пакеты) и `merge_gate.py` (гейт) (`tools/worktree.py:4-9`). Его CLI — `spawn` / `list` / `remove`, safe-by-default (команды только печатаются, пока не передан `--run` — `tools/worktree.py:11-15`, :61-66). Директория worktree создаётся как **сиблинг репозитория** (`<parent>/<repo>-wt-<agent>-<task>`), т.к. git worktree не может быть вложен в тот же репозиторий (`tools/worktree.py:41-44`). `spawn` запускает `git worktree add -b agent/<agent>/<task> <path>`; `remove` запускает `git worktree remove` + `git branch -D` (`tools/worktree.py:47-54`). Слияние притока в mainline идёт «через `tools/merge_gate.py` (зелёный гейт), затем `git merge`» (`tools/worktree.py:17-18`, :86).

`tools/merge_gate.py` отвечает «безопасно ли влить эту работу в mainline?» как green(0)/red(1) (`tools/merge_gate.py:4`). Он прогоняет **те же read-only-стадии**, что и `tools/flow.py` start/gate/finish: (1) `validate.py`, (2) `generate.py --check`, (3) `permissions.py <agent>` (только когда агент передан) (`tools/merge_gate.py:8-11`, :50-65). С `--with-tests` дополнительно globs `tools/test_*.py` и прогоняет каждый; **тесты ВЫКЛ по умолчанию**, чтобы in-flight падающий тест соседа (напр. `test_top.py`) ложно не покраснил гейт (`tools/merge_gate.py:11-14`, :61-64). Стадия зелёная только если `rc==0` и вывод не имеет `STALE`-маркера (`tools/merge_gate.py:68-74`); любая красная стадия → общий exit 1, «RED — НЕ вливать» (`tools/merge_gate.py:124-128`).

### 3.3. Триггеры эскалации (Level-0 → Level-1)

`decisions/D-022.md:23-27` делает Level-1 «ОБЯЗАТЕЛЕН ПО ТРИГГЕРАМ» (Q-015 вариант B), детектируется `python tools/cohort.py guard`. Пять триггеров:
- **A** — чужие незакоммиченные source-файлы в `git status` (tasks/, decisions/, questions/, tools/, drivers/, docs/, topics/, `streams/*/STREAM.md`) (`docs/parallel-work-policy.md:11`, :34; `D-022.md:23-24`).
- **B** — `generate.py --check` STALE, и устаревший source — **не** собственная staged-работа агента (`docs/parallel-work-policy.md:12`, :35; `D-022.md:24-25`).
- **C** — планируемая правка HOT-файла (TASKS.md, QUESTIONS.md, DECISIONS.md, index.json, PIPELINE.md, `tools/top.py`, `tools/portal.py`, генераторы, `_canon/*`) (`docs/parallel-work-policy.md:13`, :47; `D-022.md:25-26`).
- **D** — Stefan/владелец явно запрашивает параллельную мульти-агентную / fork-and-synthesize-работу над одной темой (`docs/parallel-work-policy.md:14`; `D-022.md:26`).
- **E** — предсказанная same-file-коллизия (`docs/parallel-work-policy.md:15`, :38; `D-022.md:26`).

Дополнительные gate-poison / load-триггеры: КРАСНЫЙ общий `validate`-гейт от half-done соседа форсит Level-1 worktree с чистой базы (триггер F, `docs/parallel-work-policy.md:16`); и эскалировать немедленно, если `commit_lock` BUSY >2 раз / >120с или `generate.py` пришлось перезапустить >5 раз из-за устаревшего состояния соседа (`docs/parallel-work-policy.md:26`, :54, :64). Нет триггеров → остаёмся Level-0 (`D-022.md:27`).

**Same-file-варианты** (`D-022.md:41-49`; `docs/parallel-work-policy.md:21-23`): Вариант 1 (worktree + 3-way `git merge` через merge_gate) для КРУПНЫХ/содержательных правок (≈500+ строк, code, архитектура) — кейс LS-2 `text_extract.py`, который должен был быть Вариантом 1, а не «кто последний перезаписал»; Вариант 2 (один-файл-один-claim, форк рядом как `docs/<file>-<agent>-review.md`, owner интегрирует) для ревью/мелких правок; Вариант 3 (принять перезапись + обязательный синтез после) только для маленькой заранее-одобренной draft-последовательности или экстренного hot-fix-а с post-hoc синтезом.

### 3.4. Ownership-aware ответственность за индексы (D-023)

`decisions/D-023.md` разрешает единственное расхождение, найденное слиянием двух commit-политик (Claude «commit-your-own» vs Codex «условно / интегратором», Q-017): это «не жёсткий conflict, а emphasis с граничным условием» — унификация, сохраняющая обе позиции, уже реализованная в `cohort ship` + `tools/ownership.py` (`D-023.md:14-18`). Объединённое правило: кто менял **source** (`tasks/`/`questions/`/`decisions/`), тот отвечает за свежесть его **генерируемого индекса** (`TASKS.md`/`QUESTIONS.md`/`DECISIONS.md`/`index.json`/`board.md`/`STATUS.md`), различая владение через `tools/ownership.py` (`D-023.md:22-24`):
1. **Чистый случай (mine):** мои source-правки → регенерирую через `generate.py` и коммичу индекс **в том же changeset** со своей работой («commit-your-own», дефолт) (`D-023.md:26-28`).
2. **Загрязнённый случай (foreign):** регенерированный индекс захватил бы **чужой незакоммиченный** source → индекс **НЕ коммитить** (оставить не-staged); его закоммитит владелец источника или интегратор. При триггерах → Level-1 worktree по D-022 (`D-023.md:29-31`).
3. **Различение автоматическое:** `cohort guard` / `ownership.py` классифицируют грязный индекс как `generated`, а источники как `mine|foreign`; `cohort ship` уже регенерирует и коммитит **только своё**, оставляя foreign-задетые индексы их владельцу (`D-023.md:32-33`).

Чистый эффект (`D-023.md:35`): позиции Claude и Codex — «дефолт vs граничное условие» одного правила, а не противоречие — агент ни блокируется, ни тащит чужое half-done в общую историю.

---

## Сводка подсистемы

Три слоя — один контур безопасной коллаборации:

- **Атомарные примитивы** (`commit_lock.py`, `next_id.py`, `pipeline.py`) гарантируют, что конкуренция за коммиты, id и задачи разрешается winner-take-all без потери работы упавших агентов — лиза истекает, fencing-токен не даёт зомби закоммитить.
- **Ownership-классификация** (`ownership.py`, общая для `friction.py` и `cohort.py guard`) даёт единое суждение «моё vs чужое», которое детектор превращает в рецепт, а исполнитель — в вердикт L0/L1.
- **Изоляция/слияние** (`stream.py`, `worktree.py`, `merge_gate.py` под D-021/D-022/D-023) даёт бинарную модель: дешёвый L0 по умолчанию, обязательный-по-триггеру L1 с зелёным гейтом, и ownership-правило, кто коммитит регенерированные индексы.

**Связанные файлы (все абсолютные):**
- `C:/Users/stefan/Documents/New project ai colab/tools/commit_lock.py`
- `C:/Users/stefan/Documents/New project ai colab/tools/next_id.py`
- `C:/Users/stefan/Documents/New project ai colab/tools/pipeline.py`
- `C:/Users/stefan/Documents/New project ai colab/tools/ownership.py`
- `C:/Users/stefan/Documents/New project ai colab/tools/cohort.py`
- `C:/Users/stefan/Documents/New project ai colab/tools/friction.py`
- `C:/Users/stefan/Documents/New project ai colab/tools/stream.py`
- `C:/Users/stefan/Documents/New project ai colab/tools/worktree.py`
- `C:/Users/stefan/Documents/New project ai colab/tools/merge_gate.py`
- `C:/Users/stefan/Documents/New project ai colab/tools/test_commit_lock.py`
- `C:/Users/stefan/Documents/New project ai colab/tools/test_pipeline_fencing.py`
- `C:/Users/stefan/Documents/New project ai colab/decisions/D-021.md`
- `C:/Users/stefan/Documents/New project ai colab/decisions/D-022.md`
- `C:/Users/stefan/Documents/New project ai colab/decisions/D-023.md`
- `C:/Users/stefan/Documents/New project ai colab/docs/parallel-work-policy.md`
- `C:/Users/stefan/Documents/New project ai colab/topics/friction-subsystems-synthesis-2026-06-22.md`
</doc_content>
</invoke>
