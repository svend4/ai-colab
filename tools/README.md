# tools/ — инструментарий инфраструктуры

Скрипты, которые делают правила папки технически проверяемыми, а не только договорными.

## Состав

- `validate.py` — валидатор канона. Проверяет инварианты между `DECISIONS.md`, `QUESTIONS.md`, `TASKS.md`, `board.md`, `STATUS.md`, темами и draft schema драйверов из `drivers/SCHEMA.md`. Заменяет ручную «перепроверку».
- `generate.py` — генератор навигации и машинного индекса: таблицы тем/задач/вопросов/решений собираются из front-matter, `index.json` собирается из того же канона. Режим `--check` для hook/CI.
- `queue.py` — Queue 2.0: атомарный claim, TTL lease и fencing-token для заданий в `queues/`.
- `race_test.py` — стресс-проверка атомарности `queue.py claim`: несколько параллельных агентов пытаются взять одну задачу, победить должен ровно один.
- `next_id.py` — атомарная выдача id (`T-`/`Q-`/`D-`): берёт `max+1` и резервирует номер через `O_CREAT|O_EXCL`, чтобы два агента не заняли один id.
- `dispatch.py` — read-only диспетчер задач: показывает готовые и заблокированные задачи по `depends_on`.
- `pipeline.py` — конвейер: агент атомарно берёт следующую готовую задачу из «общего котла» (`next`) или конкретную ready-задачу (`claim <agent> <T-id>`), делает, отчитывается, берёт следующую. Объединяет dispatch (готовность) и queue (захват) в один pull/claim.
- `risk_gate.py` — советчик по уровню автономии: `low -> AUTO`, `medium -> REVIEW`, `high -> HUMAN`.
- `permissions.py` — кооперативная проверка прав агента на измененные файлы по `tools/permissions.json`.
- `flow.py` — безопасная подсказка git-flow команд: ветка-на-агента, gate, merge.
- `metrics.py` — сводка по канону и очереди; есть машинный режим `--json`.
- `top.py` — верхняя панель сценариев/“кнопок”: status, health, friction, advice, agent-start, subagent-handoff, conveyor, take, snapshot, knowledge, report-diff, cycle, work-mode.
- `friction.py` — read-mostly диагностика повторяющихся проблем: dirty/stale/volatile/lock/pipeline/drift/streams/temp/sandbox/skill-links + рецепты F-001..F-019.
- `draft_code.py` — no-execute manager для agent draft-code packets: `create/check/review/list` в `sandbox/drafts/` или `tmp-work`, где код является evidence, а не implementation.
- `info_draft.py` — no-canon manager для document/information draft packets: `create/check/review/list` в `sandbox/info-drafts/` или `tmp-work`, где текст является evidence, а не accepted canon.
- `independent_first.py` — guard перед repo-search/comparison: проверяет, что stream уже содержит собственные секции 01-03, алгоритм и псевдокод.
- `report_diff.py` — механическое сравнение двух `knowledge.py report` Markdown-отчётов: документы, типы, hit-count.
- `text_extract.py` — универсальное read-only извлечение текста для knowledge/portals: `.md`, `.txt`, `.html`, `.docx` на stdlib, с redaction через `files`/canonical redaction. PDF оставлен отдельным dependency decision.
- `githooks/pre-commit` — перед коммитом запускает `validate.py` и `generate.py --check`.

## Как запускать

Из корня проекта:

```bash
python tools/validate.py
```

Коды выхода: `0` — ошибок нет; `1` — есть ERROR. WARN не валит сборку.

## План (по консенсусу infrastructure-review)

Порядок: **front-matter → validator → generator**.

1. **validator** (этот шаг): проверяет текущий формат канона.
2. **front-matter**: машиночитаемый слой (YAML) для D/Q/T/тем — следующий контролируемый шаг.
3. **generator**: `STATUS.md`/`board.md` генерируются из канона, чтобы убрать класс дрейфа структурно.

### Почему валидатор раньше front-matter

Сознательное отклонение от буквального порядка «front-matter сначала»:

- регистры `DECISIONS/QUESTIONS/TASKS` — многозаписные (front-matter — пофайловый, не на запись);
- добавление front-matter в русскоязычные темы-файлы по D-007 запускает миграцию имён с обновлением ссылок.

Поэтому сначала — рабочий валидатор на текущей прозе-грамматике (она уже достаточно структурирована: таблицы Q/T, заголовки `## D-XXX` + поле `Статус`). Машиночитаемый слой добавим отдельным контролируемым изменением.

## Pre-commit hook

`githooks/pre-commit` запускает `validate.py` перед каждым коммитом и **блокирует** коммит при `ERROR` (`WARN`, например кириллические имена по D-007, не блокирует).

Активация один раз (из корня репозитория):

```bash
git config core.hooksPath tools/githooks
```

Разовый пропуск: `git commit --no-verify`. На Unix может понадобиться `chmod +x tools/githooks/pre-commit` (на Windows с Git for Windows не требуется).

## Генератор навигации (`generate.py`)

Таблицы тем в `STATUS.md` («Активные темы») и `board.md` («Темы») больше не редактируются руками — они **генерируются** из front-matter каждого файла `topics/*.md`. Один источник на тему ⇒ две таблицы не могут разойтись (класс дрейфа устранён структурно).

Front-matter темы (вверху файла, парсер простой: `ключ: значение`):

```md
---
id: organization
title: Организация папки и обоснование правок
status: open
wait: все
next: краткий следующий шаг
---

# Тема: ...
```

Поля: `id` (для сортировки), `title`, `status` (`open`/`needs-decision`/`waiting`/`done`/`archive`), `wait` (колонка «Ждём ответ от» в Доске), `next` (следующий шаг). Тема без `title` в навигацию не попадает.

Запуск:

```bash
python tools/generate.py          # переписать таблицы между маркерами GEN:
python tools/generate.py --check  # ничего не писать; exit 1, если навигация устарела (используется в hook)
```

Между маркерами `<!-- GEN:topics-status START ... -->` … `END` и `<!-- GEN:topics-board START ... -->` … `END` править вручную не нужно — перезапишется. Остальной текст `STATUS.md`/`board.md` (включая журнал «Что изменилось») не трогается.

Рабочий цикл: меняешь `status`/`next` в front-matter темы → `python tools/generate.py` → `git add -A && git commit` (hook проверит, что навигация актуальна).

## Машинный индекс (`index.json`)

`generate.py` также строит корневой `index.json`: детерминированный машинный снимок канона для агентов и скриптов. Он содержит массивы `topics`, `tasks`, `questions`, `decisions`, `drivers`, собранные из front-matter и сгенерированных источников.

Зачем: агенту не нужно перечитывать все Markdown-файлы для первичной ориентации. Он может сначала прочитать `index.json`, выбрать релевантные сущности, а уже потом открыть конкретные topics/задачи/решения.

Проверка:

```bash
python tools/generate.py --check
```

Если `index.json` устарел, команда сообщает `STALE: index.json`; нужно запустить `python tools/generate.py` и добавить обновленный `index.json` в коммит вместе с изменениями канона.

### Драйверы в `index.json` (T-023)

L1-каталог `drivers/` теперь тоже виден агентам через `index.json`. Генератор читает `drivers/*.md` с `type: driver`, пропускает `_template.md` и добавляет массив `drivers` с полями `id`, `title`, `file`, `status`, `level`, `mode`, `owner`, `risk`, `activation`, `interfaces`, `inputs`, `outputs`, `sandbox`, `secrets`, `related`.

Это машинная навигация, не валидация схемы. Обязательные поля и расширенная manifest schema обсуждаются отдельно в Q-008.

## Шардирование реестра задач (T-008)

Чтобы убрать «горячий файл» при многих агентах, **каждая задача — отдельный файл** `tasks/T-XXX.md` с front-matter, а `TASKS.md` — генерируемый индекс (между маркерами `<!-- GEN:tasks … -->`).

Front-matter задачи:

```md
---
id: T-009
type: task
title: Краткое название
status: todo            # todo | doing | blocked | review | done
owner: Claude           # кто отвечает
priority: normal        # low | normal | high
risk: low               # low | medium | high
topic: topics/scaling-design.md
depends_on: [T-008]     # зависимости (для будущего DAG)
next: следующий шаг
---

# T-009 — Краткое название

Человеческое описание / заметки.
```

Зачем: агенты создают/правят **свои** файлы задач, а не общую таблицу — нет конфликтов записи на `TASKS.md`. Поля `priority`/`risk`/`depends_on` пока хранятся для будущего (DAG, риск-гейтинг), в индексной таблице не показываются.

Цикл: создал/изменил `tasks/T-XXX.md` → `python tools/generate.py` → коммит (hook проверит `--check`). Поля `priority`/`risk`/`depends_on` — задел под Этапы D–E из `topics/scaling-design.md`.

Так же шардированы **вопросы** (`questions/Q-XXX.md` → индекс `QUESTIONS.md`) и **решения** (`decisions/D-XXX.md` → индекс `DECISIONS.md`). Полный текст решения — в его файле; `DECISIONS.md` — навигационный индекс (`ID | Решение | Статус | Дата | Файл`). Валидатор читает индекс решений как таблицу, поэтому источник правды по решениям — `decisions/*.md`.

## Очередь 2.0 (`queue.py`, T-009)

Атомарный рабочий цикл задач для многих агентов. Агент **не двигает файлы руками** — вызывает инструмент, инструмент меняет `queues/*` консистентно.

```bash
python tools/queue.py list                                  # что в inbox и кем занято
python tools/queue.py claim    <task> <agent> [--ttl 30]    # атомарно взять задачу → печатает claim_id
python tools/queue.py complete <task> <agent> --claim-id ID [--result PATH]
python tools/queue.py fail     <task> <agent> --claim-id ID [--reason TEXT]
python tools/queue.py release  <task> <agent> --claim-id ID
python tools/queue.py check                                 # claim без задания/без done
```

`<task>` — имя файла из `queues/inbox/<task>.md` (без `.md`). Для pipeline-claim `check`
также признаёт `tasks/<task>.md`, потому что `tools/pipeline.py next` занимает задачи из
канонического каталога задач, а не из `queues/inbox/`. Гарантии:

- **Атомарность:** claim создаётся через `O_CREAT|O_EXCL` — два агента не возьмут задачу одновременно (второй получит `BUSY`).
- **TTL:** claim «свежий», пока lease в будущем; протухший (упавший агент) можно перехватить.
- **Fencing:** уникальный `claim_id`; `complete`/`fail` требуют его — агент, чей claim перехватили, не завершит чужую задачу.

Это рабочая замена ручному перемещению файлов между `inbox/claimed/outbox/done/failed` (дефект из смоук-теста T-004).

### Стресс-проверка claim (`race_test.py`)

`race_test.py` проверяет ключевую гарантию очереди: при одновременном `claim` одной задачи победить должен ровно один агент, остальные получают `RACE` или `BUSY`.

```bash
python tools/race_test.py       # 8 параллельных claim
python tools/race_test.py 16    # 16 параллельных claim
```

Скрипт работает во временном `COLLAB_ROOT` и не трогает рабочую очередь проекта. На Windows временная директория по умолчанию берётся из `C:\tmp`, если она существует; это обходит окружения, где запись в пользовательский `%TEMP%` запрещена sandbox'ом. При необходимости можно явно задать базу:

```bash
set COLLAB_RACE_TMP=C:\tmp
python tools/race_test.py 16
```

## Выдача id (`next_id.py`, T-026)

Чтобы агенты не занимали один номер дважды при параллельной работе (за сессию были коллизии `Q-008 ×2`, `Q-009 ×2`), id выдаются атомарно — той же техникой, что claim в `queue.py`.

```bash
python tools/next_id.py question --agent Claude   # → Q-0NN + файл-заглушка
python tools/next_id.py task     --agent Codex     # → T-0NN
python tools/next_id.py decision --agent Mavis      # → D-0NN
```

Инструмент сканирует каталог, берёт `max+1` и создаёт `questions|tasks|decisions/<id>.md` через `O_CREAT|O_EXCL`. Если номер перехватил другой агент — берёт следующий свободный. Заглушка валидна для `validate.py`, помечена «(зарезервировано)» и содержит `reserved_by`, `reserved_epoch`, `reservation_token`.

Параллельный безопасный путь после T-223/T-226 collision:

```bash
python tools/next_id.py task --agent Codex
python tools/next_id.py check T-228 --agent Codex --token <reservation_token>
python tools/next_id.py fill T-228 --agent Codex --token <reservation_token> --from tmp-work/T-228.fill.md
```

`fill` проверяет, что reservation принадлежит этому агенту, что токен совпадает, и что `id` в подготовленном файле совпадает с резервом. Потом файл заменяется атомарно. Если обнаружена collision-ситуация, не переписывайте чужой файл: оставьте outbox-отчёт и берите свежий id.

Договорённость: перед созданием нового `Q`/`T`/`D` — сначала `next_id.py`, не выбирать номер вручную. Перед заполнением в параллельном режиме — `check` или `fill`, а не голая ручная перезапись placeholder.

## Валидатор v2 — проверка источников (T-010)

Кроме сверки индексов, `validate.py` теперь проверяет **файлы-источники** напрямую (`check_sources`):

- у каждого `tasks/*.md`, `questions/*.md`, `decisions/*.md` есть front-matter с `id`, `title`, `status`;
- `id` уникальны внутри реестра и совпадают с именем файла;
- статусы из допустимого набора;
- `depends_on` в задачах ссылается на существующие задачи.

Зачем: генератор молча пропускает файл с битым/отсутствующим front-matter — валидатор v2 это ловит. Целостность самой очереди проверяет `python tools/queue.py check`.

## Диспетчер задач (`dispatch.py`, T-014)

Показывает, какие задачи можно брать прямо сейчас: `status=todo` и все `depends_on` уже `done`.

```bash
python tools/dispatch.py       # списки готовых и заблокированных задач
python tools/dispatch.py next  # один id задачи с наивысшим приоритетом
```

Инструмент ничего не меняет. Захват задачи делается отдельно через `queue.py`.

## Конвейер задач (`pipeline.py`, T-027)

«Общий котёл»: агент сам тянет следующую готовую задачу, делает, отчитывается, берёт следующую — несколько агентов параллельно через одну форму. Делает работу динамичной (цикл вместо ручной раздачи).

```bash
python tools/pipeline.py next   Claude                  # атомарно занять след. готовую задачу
python tools/pipeline.py claim  Claude T-152            # атомарно занять конкретную ready-задачу
python tools/pipeline.py done   Claude T-027 --report "сделал X" --applied "AGENTS.md, PROTOCOL.md, Checks"
python tools/pipeline.py fail   Claude T-031 --reason "нужен доступ"
python tools/pipeline.py status                          # лента: в работе / готовы / заблокированы
python tools/pipeline.py snapshot                        # записать PIPELINE.md + logs/pipeline.json
python tools/pipeline.py heartbeat Claude T-027 --progress 40 --note "пишу тест" --eta "10m"
python tools/pipeline.py mine   Claude                   # мои активные задачи
```

Цикл агента:

```
next → (делаю задачу) → done --report --applied → next → … → "КОТЁЛ ПУСТ"
```

- **Pull-next атомарен.** `next` объединяет dispatch (готовность по DAG) и queue (захват через `O_CREAT|O_EXCL`) в одну операцию — между «увидел» и «занял» нет окна для перехвата. Проверено: 5 параллельных `next` → 5 разных задач, ноль задвоений.
- **Готовая задача** = `status:todo` + все `depends_on` done + не занята свежим claim'ом. Заблокированные зависимостями в `next` не попадают.
- **Targeted claim.** Если агенту нужна конкретная задача, используйте `pipeline.py claim <agent> <T-id>` или `top.py take <agent> <T-id>`. Команда применяет те же ready/placeholder/claim проверки, что `next`, но не берёт другую задачу при ошибке.
- **Отчёт — без «горячего файла».** `done` пишет per-task маркер `queues/done/<id>.done.md` (источник правды, без конфликтов слияния) и переводит задачу в `done`. Для служебных задач добавляй `--applied "AGENTS.md, PROTOCOL.md, Checks"`: это сохраняет короткое evidence в front matter и в теле done-маркера. Если service/governance-задача закрыта без `--applied`, pipeline печатает `WARN`, но не блокирует старый сценарий. Единый вид ленты — `pipeline.py status` (генерируется на лету, как индексы), а не общий файл с параллельными дописываниями (это был бы тот самый конфликт записи из D-002).
- **Snapshot для людей и агентов.** `snapshot` пишет `PIPELINE.md` как человекочитаемую доску и `logs/pipeline.json` как машинный срез для быстрых агентных циклов. После T-148 это volatile runtime-файлы: они остаются на диске, но игнорируются Git.
- **Добровольный heartbeat.** `heartbeat` пишет `logs/heartbeat/<agent>.json`, обновляет `logs/heartbeat.json` и `LIVE.md`. Это live-слой по D-012: полезен для долгих задач и параллельной работы, но не обязателен для каждого действия. Агрегированные heartbeat/LIVE snapshots после T-148 не входят в обычный commit.
- Источник правды по статусу задачи — `tasks/*.md`; после прогона запусти `generate.py`, чтобы обновить индексы.

## Риск-гейтинг (`risk_gate.py`, T-015)

Советчик для многоуровневой автономии:

```bash
python tools/risk_gate.py policy
python tools/risk_gate.py T-016
```

Политика: `low -> AUTO`, `medium -> REVIEW`, `high -> HUMAN`. Это не отменяет D-006: высокорисковые решения по-прежнему утверждает человек.

## Права и git-flow (`permissions.py`, `flow.py`)

`permissions.py` проверяет, не выходит ли агент за разрешенные пути из `tools/permissions.json`.

```bash
python tools/permissions.py mavis
python tools/permissions.py mavis tasks/T-020.md topics/scaling-design.md
```

Worker-агентам разрешены сгенерированные индексы (`TASKS.md`, `QUESTIONS.md`, `DECISIONS.md`, `board.md`, `index.json`) как выход `generate.py`; вручную править содержимое между `GEN`-маркерами не нужно.

`flow.py` печатает безопасные git-команды для модели "ветка-на-агента"; с `--worktree` печатает Level 1 worktree-приток; с `--run` выполняет их. `launch-plan` дополнительно печатает handoff-пакет для внешнего sub-agent launcher: repo lane, worker prompt и finish-команду; с `--json` отдаёт тот же контракт как `subagent_launch_plan.v1`.

```bash
python tools/flow.py start mavis T-020
python tools/flow.py gate mavis
python tools/flow.py finish mavis T-020
python tools/flow.py start mavis T-020 --worktree
python tools/flow.py launch-plan mavis T-161 agent launch workflow --worktree
python tools/flow.py launch-plan mavis T-161 agent launch workflow --worktree --json
```

## Метрики (`metrics.py`, T-016)

Сводка для быстрой ориентации:

```bash
python tools/metrics.py
python tools/metrics.py --json
```

Очередь считается по текущему формату Queue 2.0: `claimed` = `*.claim.md`, `done` = `*.done.md`, `failed` = `*.failed.md`. Старые legacy-файлы в этих папках остаются историей, но не считаются активным состоянием очереди.

## Извлечение текста (`text_extract.py`, T-133)

`text_extract.py` — маленькая универсальная способность ядра для L6 knowledge workflow и тематических порталов. Она не привязана к домену: любой портал с документами получает один и тот же безопасный путь `file -> redacted text -> FTS/search/report`.

```bash
python tools/text_extract.py extract data/knowledge-corpus/README.md
python tools/text_extract.py summary data/knowledge-corpus/README.md
```

Сейчас поддерживаются `.md`, `.markdown`, `.txt`, `.text`, `.html`, `.htm`, `.docx` без внешних зависимостей (`.docx` через stdlib Open XML: `zipfile` + `ElementTree`). `tools/knowledge.py` использует этот слой при `build/report`, поэтому FTS индексирует содержимое документа, а не только первую строку. PDF намеренно оставлен отдельным dependency decision.

## Верхняя панель (`top.py`, T-138)

`top.py` группирует существующие инструменты в сценарии, удобные как людям, так и агентам. Если тема уже известна, `agent-start --task T-id --context "..."` запускает onboarding/status, assurance/advice и быстрый поиск по канону.

```bash
python tools/top.py buttons
python tools/top.py status codex
python tools/top.py health
python tools/top.py assurance all --json
python tools/top.py agent-start codex --task T-188 --context "parallel work policy"
python tools/top.py subagent-handoff mavis T-161 "agent launch workflow" --worktree
python tools/top.py subagent-handoff mavis T-161 "agent launch workflow" --worktree --json
python tools/top.py take codex             # next
python tools/top.py take codex T-152       # targeted claim
python tools/top.py snapshot
python tools/top.py knowledge data/knowledge-corpus --query bridge --out reports/bridge.md
python tools/top.py repo-search "parallel work policy" --limit 5
python tools/top.py report-diff reports/a.md reports/b.md --out reports/diff.md
python tools/top.py variant-start codex "parallel work policy" --task T-254
python tools/independent_first.py check streams/<topic>/<stream-id>/STREAM.md --json
python tools/top.py variant-batch "parallel work policy" --agents codex,mavis --task T-259
python tools/top.py draft-code create demo-draft --owner codex --purpose "prototype safely" --task T-260
python tools/top.py info-draft create doc-draft --owner codex --purpose "structure documentation safely" --task T-261
python tools/draft_code.py create demo-draft --owner codex --purpose "prototype safely" --task T-260
python tools/draft_code.py review sandbox/drafts/demo-draft --json
python tools/top.py conveyor --json
python tools/top.py synthesize-docs doc-synthesis-stream-corpus --json
python tools/top.py synthesize-docs doc-synthesis-stream-corpus --ready-only --json
python tools/top.py butterfly --seed codex-preview --json
python tools/conveyor.py land w123 --output queues/outbox/w123-output.md
python tools/top.py work-mode codex T-144 --parallel
```

Это не новый источник правды. Это тонкая обёртка над `pipeline.py`, `validate.py`, `generate.py`, `capabilities.py`, `drivers_catalog.py`, `knowledge.py`, `repo_search.py`, `drift_check.py`, `assurance.py`, `flow.py` и `merge_gate.py`. `variant-start` создаёт independent-first stream-пакет по D-028/T-258, откладывает repo-search по умолчанию и показывает preflight/next commands; `variant-batch` создаёт `_batches/<batch-id>.json` manifest для пачки агентов и phase barrier перед synthesis; `synthesize-docs <custom-topic>` может читать `streams/<topic>/*/STREAM.md` как corpus без ручного списка файлов. `work-mode` помогает выбрать D-021 режим: Level 0 shared tree по умолчанию или Level 1 worktree при параллельной/конфликтной работе. `subagent-handoff` превращает `flow.py launch-plan` в верхнюю “кнопку” для запуска внешнего worker-agent; с `--json` он проксирует чистый машинный launch-пакет без служебных заголовков. `butterfly` поднимает смысловой граф котла и генератор synthesis-task в верхнюю панель: dry-run по умолчанию, `--apply-graph` обновляет индекс, `--apply-topic` пишет задачу. `conveyor` поднимает runtime-надзирателя workflow-конвейера (`REFILL`/`PROCESS`/`IDLE`) в ту же верхнюю панель; `conveyor.py land --output` привязывает приземлившийся workflow к durable результату для последующей обработки. `assurance` показывает applied/currency/coverage/flow как advisory apex-снимок; `advice` связывает текущие friction/assurance-сигналы с уже существующими рецептами, а `agent-start` вызывает его автоматически. Строгий режим включается только явным `--strict`. `repo-search` пишет только ignored runtime-БД `logs/repo-knowledge.db`.

## Friction diagnostics (`friction.py`, T-150)

`friction.py` превращает повторяющиеся ручные обходы из `docs/friction-ledger.md` и `docs/friction-playbook.md` в одну read-mostly диагностику. Он не исправляет репозиторий автоматически: показывает симптом, evidence, F-ID и рецепт.

```bash
python tools/friction.py status
python tools/friction.py status --json
python tools/friction.py recipe F-007
python tools/friction.py list
python tools/top.py friction
```

Проверки сейчас покрывают:

- dirty shared tree и generated/shared files;
- volatile snapshots (`LIVE.md`, `PIPELINE.md`, `logs/heartbeat.json`, `logs/pipeline.json`);
- `generate.py --check`, `commit_lock.py status`, `pipeline.py status`, `drift_check.py`, `stream.py check` (`stale`/`broken`/`incomplete_ready`);
- project-safe temp probe под `tmp-work/`;
- наличие sandbox-контракта для external code;
- связь skill `repo-friction-playbook` с каноническими docs/tool.

Если `friction.py` предупреждает про dirty/foreign/stale состояние, это не всегда ошибка: во время активной задачи дерево ожидаемо грязное. Смысл предупреждения — не использовать `git add -A`, не смешивать чужие stream/source изменения и перед commit снова проверить явный список файлов.
## Semantic hybrid (`doc_consensus.py`, opt-in)

`tools/doc_consensus.py report` остаётся по умолчанию чистым stdlib/лексическим режимом: unit extraction + token-Jaccard, без LLM/agent вызовов.

Опциональный режим:

```bash
python tools/doc_consensus.py report --semantic --semantic-budget 3 --files a.md b.md --out reports/doc-consensus-semantic.md
```

Что делает `--semantic`:

- запускает high-threshold механический pre-cluster;
- отправляет только residuum в subprocess-agent из `$DOC_CONSENSUS_AGENT`;
- ожидает JSON с `consensus` groups и `divergences`;
- рендерит результат как `status: proposed`, то есть материал для котла D-017/D-018, не auto-accepted решение.

`--semantic-budget N` ограничивает число agent-batches на один прогон и падает до вызова агента, если residuum требует больше вызовов. Без `$DOC_CONSENSUS_AGENT` semantic режим деградирует безопасно: агентный pass пустой, механические consensus сохраняются. Runtime-рецепт, безопасный stub-agent и auto-accept policy: `docs/doc-consensus-agent-runtime.md`.
## Result intake classifier (`result_intake.py`)

`tools/result_intake.py` — read-only preflight для верхнего слоя перед verify/synthesis. Он классифицирует один landed/outbox/report-файл и печатает, какой режим обработки нужен дальше.

```powershell
python tools/result_intake.py classify queues/outbox/2026-06-23-perspective-backlog-refresh-t177.md
python tools/result_intake.py classify queues/outbox/2026-06-23-perspective-backlog-refresh-t177.md --json
```

Классы:

| Class | Когда применять |
|---|---|
| `read-only-report` | аудит, обзор, статус без изменения канона |
| `variant` | fork/stream/альтернативное мнение, которое надо синтезировать, а не схлопывать как дубль |
| `docs-change` | документация, темы, методология, README |
| `build-change` | код, инструменты, драйверы, тесты, CLI |
| `governance` | решения, accepted/proposed policy, human approval |
| `external-code` | sandbox/source intake/execute/svend4/внешний код |

Инструмент не принимает решения и не запускает проверки сам. Он возвращает class, confidence, evidence flags, signals и recommended next checks. Это вход для будущих шагов `conveyor regulate` и усиленного `top.py process-landed`.
## Conveyor regulate (`conveyor.py`)

`tools/conveyor.py regulate` — read-only advisory для выбора target workflow-conveyor. Он не меняет `logs/conveyor.json`, не запускает агентов и не делает `conveyor.py target`; он только объясняет, что делать с размером флота.

```powershell
python tools/conveyor.py regulate
python tools/conveyor.py regulate --json
python tools/conveyor.py regulate --json --no-assurance
```

Рекомендации:

| Recommendation | Meaning |
|---|---|
| `increase` | conveyor полный, landed backlog пуст, assurance чистый; target можно поднять на 1 |
| `hold` | target менять не надо; чаще всего сначала нужно refill до текущей цели или закрыть advisory |
| `decrease` | оркестратор stale/idle; лучше снизить давление или сначала tick/land/ship |
| `process-first` | есть landed/missing-output; сначала обработать результат, потом масштабировать |

Когда есть landed outputs с путями, команда best-effort использует `result_intake.py`, чтобы показать классы результатов. По умолчанию она также читает `assurance.py all --json`; `--no-assurance` нужен для быстрых smoke/tests.

### Ready-only stream synthesis (T-256)

`--ready-only` у `synthesize-docs` и `doc_synthesis.py scan` фильтрует автоматический stream corpus до вариантов со статусом `ready-for-synthesis` или `synthesis_ready: true`.

```bash
python tools/doc_synthesis.py scan <topic> --ready-only --json
python tools/top.py synthesize-docs <topic> --ready-only --json
```

Явно переданные файлы не фильтруются: explicit corpus остаётся ответственностью вызывающего агента.