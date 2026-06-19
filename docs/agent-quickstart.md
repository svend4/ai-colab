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

# Или: какие задачи готовы к взятию
python tools/dispatch.py
```

`dispatch.py` покажет задачи со статусом `todo` и выполненными зависимостями (`depends_on`). Если список пуст — смотрите `queues/inbox/` или `TASKS.md`.

## Шаг 3. Взять задачу через `queue.py claim`

```bash
# Посмотреть свободные задачи
python tools/queue.py list

# Взять задачу (task — имя файла без .md)
python tools/queue.py claim <task> <agent> --ttl 30

# Сохранить claim_id — он нужен для complete
```

Пример: `python tools/queue.py claim dogfood-glossary mavis --ttl 30`

## Шаг 4. Работать в своей зоне

```bash
# Проверить, что вы пишете туда, куда разрешено
python tools/permissions.py <agent>

# Или с явными файлами:
python tools/permissions.py <agent> file1.md file2.md
```

Worker-зона (`novax`, `mavis`): `tasks/`, `questions/`, `decisions/`, `темы/`, `queues/`, `docs/`, `code/`, `STATUS.md`, `Диалог.md`.  
Generated-индексы (`TASKS.md`, `QUESTIONS.md`, `DECISIONS.md`, `Доска.md`, `index.json`) могут измениться после `python tools/generate.py`; не редактируйте их вручную между `GEN`-маркерами.
Не пишите в `PROTOCOL.md`, `AGENTS.md`, `tools/` без явного запроса.

## Шаг 5. Пройти гейт и закоммитить

```bash
# 1. Проверить канон
python tools/validate.py

# 2. Обновить навигацию (если меняли темы/задачи/вопросы/решения)
python tools/generate.py

# 3. Проверить, что навигация актуальна
python tools/generate.py --check

# 4. Проверить права
python tools/permissions.py <agent>

# 5. Git commit
python tools/generate.py --check && git add -A && git commit -m "описание"
```

Pre-commit hook (`tools/githooks/pre-commit`) автоматически запускает `validate.py` и `generate.py --check`. Если ERROR — коммит блокируется.

## Главные правила — одним списком

| № | Правило | Что делать |
|---|---|---|
| 1 | **Не переписывать чужие сообщения** | Пишите новые записи в конец файла или новый файл в `messages/` |
| 2 | **Агент предлагает, человек утверждает** | Ваши решения — `proposed`; `accepted` только человек или сборщик (D-006) |
| 3 | **Значимые правки — с обоснованием** | Короткое объяснение в `Диалог.md` или профильной теме (D-003, D-008) |
| 4 | **Claim перед работой** | `queue.py claim` — атомарный захват, не двигайте файлы руками |
| 5 | **Проверяйте права** | `permissions.py <agent>` перед записью; не пишите в чужую зону |
| 6 | **Валидатор зелёный** | `validate.py` → `generate.py` → commit; ERROR блокирует |

## Если что-то непонятно

- Задайте вопрос в `Диалог.md` или `questions/`.
- Позовите агента: `@Claude`, `@Codex`, `@Mavis`, `@Novax`.
- Прочтите `PROTOCOL.md` — полные правила масштабной работы.
- Прочтите `tools/README.md` — описание всех инструментов.
