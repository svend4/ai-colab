# Quickstart для нового агента

Если вы — AI-агент, который только что открыл эту папку, пройдите 5 шагов за 10 минут и начните работу.

## Шаг 1. Прочитать `STATUS.md`

```bash
cat STATUS.md
```

Узнайте текущий фокус, активные темы и что изменилось недавно. Это снимок состояния — читайте первым.

## Шаг 2. Посмотреть индекс и готовые задачи

```bash
# Машинный индекс — все сущности одним файлом
cat index.json

# Какие задачи готовы к взятию / заняты / заблокированы
python tools/pipeline.py status

# Один briefing для нового агента
python tools/onboard.py <agent>
```

`pipeline.py status` показывает актуальный конвейер. `queues/inbox/` и `queues/outbox/` остаются файловым форумом для входящих поручений и результатов, но claim задачи делается через `pipeline.py next`.

## Шаг 3. Взять задачу через `pipeline.py next`

```bash
# Состояние конвейера: что готово / в работе / заблокировано
python tools/pipeline.py status

# Атомарно взять следующую готовую задачу (печатает claim_id)
python tools/pipeline.py next <agent>

# Сохранить claim_id — он нужен для done --claim
```

Пример: `python tools/pipeline.py next mavis`, затем закрыть:
`python tools/pipeline.py done mavis <T-id> --claim <claim_id> --report "..."`.

## Шаг 4. Работать в своей зоне

```bash
# Проверить, что вы пишете туда, куда разрешено
python tools/permissions.py <agent>

# Или с явными файлами:
python tools/permissions.py <agent> file1.md file2.md
```

Worker-зона (`novax`, `mavis`): `tasks/`, `questions/`, `decisions/`, `topics/`, `queues/`, `docs/`, `code/`, `STATUS.md`, `dialog.md`.  
Generated-индексы (`TASKS.md`, `QUESTIONS.md`, `DECISIONS.md`, `board.md`, `index.json`) могут измениться после `python tools/generate.py`; не редактируйте их вручную между `GEN`-маркерами.
Не пишите в `PROTOCOL.md`, `AGENTS.md`, `tools/` без явного запроса.

## Шаг 5. Пройти гейт и закоммитить

```bash
# 1. Проверить канон
python tools/validate.py

# 2. Обновить навигацию (если меняли topics/задачи/вопросы/решения)
python tools/generate.py

# 3. Проверить, что навигация актуальна
python tools/generate.py --check

# 4. Проверить права
python tools/permissions.py <agent>

# 5. Git commit
python tools/commit_lock.py acquire <agent> --wait 30
python tools/generate.py --check
git add <свои-файлы>
git commit -m "описание"
python tools/commit_lock.py release <agent>
```

Pre-commit hook (`tools/githooks/pre-commit`) автоматически запускает `validate.py` и `generate.py --check`. Если ERROR — коммит блокируется.

## Главные правила — одним списком

| № | Правило | Что делать |
|---|---|---|
| 1 | **Не переписывать чужие сообщения** | Пишите новые записи в конец файла или новый файл в `messages/` |
| 2 | **Агент предлагает, человек утверждает** | Ваши решения — `proposed`; `accepted` только человек или сборщик (D-006) |
| 3 | **Значимые правки — с обоснованием** | Короткое объяснение в `dialog.md` или профильной теме (D-003, D-008) |
| 4 | **Claim перед работой** | `pipeline.py next` — атомарный захват+статус; закрытие `done --claim`; не двигайте файлы руками |
| 5 | **Проверяйте права** | `permissions.py <agent>` перед записью; не пишите в чужую зону |
| 6 | **Валидатор зелёный** | `validate.py` → `generate.py` → commit-lock → selective-add → commit; ERROR блокирует |

## Если что-то непонятно

- Задайте вопрос в `dialog.md` или `questions/`.
- Позовите агента: `@Claude`, `@Codex`, `@Mavis`, `@Novax`.
- Прочтите `PROTOCOL.md` — полные правила масштабной работы.
- Прочтите `tools/README.md` — описание всех инструментов.

## Быстрая диагностика инструментов

Перед большой правкой или коммитом агент может быстро проверить верхний слой и типовые проблемы:

```bash
python tools/pipeline.py status
python tools/top.py health
python tools/friction.py status
python tools/drift_check.py
python tools/onboard.py <agent>
python tools/commit_lock.py status
python tools/adoption.py check
python tools/blocks.py scan
```

Назначение:

| Инструмент | Что показывает |
|---|---|
| `pipeline.py status` | состояние конвейера: готовые к взятию, в работе, заблокированные задачи |
| `top.py health` | validate/generate/capabilities/driver catalog как общий health-check |
| `friction.py status` | грязное дерево, stale indexes, gate-poison, lock, temp-проблемы и рецепты |
| `drift_check.py` | дрейф между документацией/индексом и текущими фактами |
| `onboard.py <agent>` | краткий вход агента: стадия, драйверы, execute policy, конвейер, активные задачи |
| `commit_lock.py status` | свободна ли серийная точка git commit |
| `adoption.py check` | проверка внедрения обязательных практик и инструментов |
| `blocks.py scan` | поиск сиротских или нелегальных блочных артефактов (D-016) |
