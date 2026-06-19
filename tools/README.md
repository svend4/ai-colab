# tools/ — инструментарий инфраструктуры

Скрипты, которые делают правила папки технически проверяемыми, а не только договорными.

## Состав

- `validate.py` — валидатор канона. Проверяет инварианты между `DECISIONS.md`, `QUESTIONS.md`, `TASKS.md`, `Доска.md`, `STATUS.md` и темами. Заменяет ручную «перепроварку».
- `generate.py` — генератор навигации: таблицы тем в `STATUS.md` и `Доска.md` собираются из front-matter тем. Режим `--check` для hook/CI.
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
