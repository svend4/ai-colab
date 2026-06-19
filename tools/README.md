# tools/ — инструментарий инфраструктуры

Скрипты, которые делают правила папки технически проверяемыми, а не только договорными.

## Состав

- `validate.py` — валидатор канона. Проверяет инварианты между `DECISIONS.md`, `QUESTIONS.md`, `TASKS.md`, `Доска.md`, `STATUS.md` и темами. Заменяет ручную «перепроварку».
- `generate.py` — генератор навигации и машинного индекса: таблицы тем/задач/вопросов/решений собираются из front-matter, `index.json` собирается из того же канона. Режим `--check` для hook/CI.
- `queue.py` — Queue 2.0: атомарный claim, TTL lease и fencing-token для заданий в `queues/`.
- `race_test.py` — стресс-проверка атомарности `queue.py claim`: несколько параллельных агентов пытаются взять одну задачу, победить должен ровно один.
- `dispatch.py` — read-only диспетчер задач: показывает готовые и заблокированные задачи по `depends_on`.
- `risk_gate.py` — советчик по уровню автономии: `low -> AUTO`, `medium -> REVIEW`, `high -> HUMAN`.
- `permissions.py` — кооперативная проверка прав агента на измененные файлы по `tools/permissions.json`.
- `flow.py` — безопасная подсказка git-flow команд: ветка-на-агента, gate, merge.
- `metrics.py` — сводка по канону и очереди; есть машинный режим `--json`.
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
3. **generator**: `STATUS.md`/`Доска.md` генерируются из канона, чтобы убрать класс дрейфа структурно.

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

Таблицы тем в `STATUS.md` («Активные темы») и `Доска.md` («Темы») больше не редактируются руками — они **генерируются** из front-matter каждого файла `темы/*.md`. Один источник на тему ⇒ две таблицы не могут разойтись (класс дрейфа устранён структурно).

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

Между маркерами `<!-- GEN:topics-status START ... -->` … `END` и `<!-- GEN:topics-board START ... -->` … `END` править вручную не нужно — перезапишется. Остальной текст `STATUS.md`/`Доска.md` (включая журнал «Что изменилось») не трогается.

Рабочий цикл: меняешь `status`/`next` в front-matter темы → `python tools/generate.py` → `git add -A && git commit` (hook проверит, что навигация актуальна).

## Машинный индекс (`index.json`)

`generate.py` также строит корневой `index.json`: детерминированный машинный снимок канона для агентов и скриптов. Он содержит массивы `topics`, `tasks`, `questions`, `decisions`, собранные из front-matter и сгенерированных источников.

Зачем: агенту не нужно перечитывать все Markdown-файлы для первичной ориентации. Он может сначала прочитать `index.json`, выбрать релевантные сущности, а уже потом открыть конкретные темы/задачи/решения.

Проверка:

```bash
python tools/generate.py --check
```

Если `index.json` устарел, команда сообщает `STALE: index.json`; нужно запустить `python tools/generate.py` и добавить обновленный `index.json` в коммит вместе с изменениями канона.

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
topic: темы/scaling-design.md
depends_on: [T-008]     # зависимости (для будущего DAG)
next: следующий шаг
---

# T-009 — Краткое название

Человеческое описание / заметки.
```

Зачем: агенты создают/правят **свои** файлы задач, а не общую таблицу — нет конфликтов записи на `TASKS.md`. Поля `priority`/`risk`/`depends_on` пока хранятся для будущего (DAG, риск-гейтинг), в индексной таблице не показываются.

Цикл: создал/изменил `tasks/T-XXX.md` → `python tools/generate.py` → коммит (hook проверит `--check`). Поля `priority`/`risk`/`depends_on` — задел под Этапы D–E из `темы/scaling-design.md`.

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

`<task>` — имя файла из `queues/inbox/<task>.md` (без `.md`). Гарантии:

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
python tools/permissions.py mavis tasks/T-020.md темы/scaling-design.md
```

Worker-агентам разрешены сгенерированные индексы (`TASKS.md`, `QUESTIONS.md`, `DECISIONS.md`, `Доска.md`, `index.json`) как выход `generate.py`; вручную править содержимое между `GEN`-маркерами не нужно.

`flow.py` печатает безопасные git-команды для модели "ветка-на-агента"; с `--run` выполняет их.

```bash
python tools/flow.py start mavis T-020
python tools/flow.py gate mavis
python tools/flow.py finish mavis T-020
```

## Метрики (`metrics.py`, T-016)

Сводка для быстрой ориентации:

```bash
python tools/metrics.py
python tools/metrics.py --json
```

Очередь считается по текущему формату Queue 2.0: `claimed` = `*.claim.md`, `done` = `*.done.md`, `failed` = `*.failed.md`. Старые legacy-файлы в этих папках остаются историей, но не считаются активным состоянием очереди.
