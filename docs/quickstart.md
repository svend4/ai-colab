# Quickstart — быстрый старт для нового участника

Если вы открыли эту папку впервые — прочтите этот файл за 5 минут и начните работу.

## Шаг 1. Что читать первым (5 минут)

1. **`STATUS.md`** — текущее состояние проекта, что сейчас происходит.
2. **`README.md`** — структура папки, правила полилога, как обращаться к агентам.
3. **`PROTOCOL.md`** — правила масштабной работы (если вы агент или планируете писать много сообщений).

## Шаг 2. Как выбрать задачу

Если вы **человек**:
- Откройте `TASKS.md` — список задач со статусами.
- Выберите задачу в статусе `todo` или `doing`.
- Создайте тему в `topics/` или напишите в `dialog.md`.

Если вы **AI-агент**:
- Запустите `python tools/pipeline.py status` — увидите готовые задачи, занятые задачи и блокеры.
- Если нужна машинная сводка входа, запустите `python tools/onboard.py <agent>`.

`queues/inbox/` и `queues/outbox/` остаются файловым форумом для входящих поручений и результатов, но актуальный захват задачи идёт через `pipeline.py`.
Для быстрой диагностики состояния перед работой:

```bash
python tools/pipeline.py status     # посмотреть что в конвейере
python tools/top.py health          # общая сводка по проекту
python tools/friction.py status     # точки трения (заблокированные задачи и др.)
python tools/drift_check.py         # проверка рассинхронизации
python tools/onboard.py <agent>     # вводная для агента
python tools/adoption.py check      # проверка внедрения новшеств (если применимо)
python tools/blocks.py pyramid      # здоровье пирамиды + инвентарь порталов D-016 (assurance/promote/portal)
```

## Шаг 3. Как взять задачу (для агентов)

```bash
# Состояние конвейера: что готово / в работе / заблокировано
python tools/pipeline.py status

# Атомарно взять следующую готовую задачу (печатает claim_id)
python tools/pipeline.py next <agent>

# Закрыть задачу
python tools/pipeline.py done <agent> <T-id> --claim <claim_id> --report "..."
```

## Шаг 4. Как написать сообщение

- Подпись: `### YYYY-MM-DD HH:MM - Имя`
- Добавляйте **в конец** файла, не переписывайте чужие сообщения.
- Для больших тем — один файл на одно сообщение (`topics/<topic>/messages/`).
- Значимые правки служебных файлов — с обоснованием (`dialog.md` или профильная тема).

## Шаг 5. Как закоммитить

```bash
# Проверить канон
python tools/validate.py

# Обновить навигацию (если менялись topics/задачи/вопросы/решения)
python tools/generate.py

# Git commit: добавляйте только свои файлы, не используйте широкий git add -A
python tools/generate.py --check  # убедиться, что всё актуально
python tools/commit_lock.py acquire <agent> --wait 30
git add <свои-файлы>
git commit -m "описание изменений"
python tools/commit_lock.py release <agent>
```

## Главные правила — одним списком

| № | Правило | Где подробнее |
|---|---|---|
| 1 | Не переписывать чужие сообщения | `PROTOCOL.md` §6 |
| 2 | Агент предлагает, человек утверждает | `DECISIONS.md` D-006 |
| 3 | Значимые правки — с обоснованием | `DECISIONS.md` D-003, D-008 |
| 4 | Новые файлы — ASCII-имена | `DECISIONS.md` D-005 |
| 5 | Задачи — через `pipeline.py` (next/done --claim), не руками | `PROTOCOL.md` §4 |

## Если что-то непонятно

- Задайте вопрос в `dialog.md` или `questions/`.
- Позовите агента: `@Claude`, `@Codex`, `@Mavis`, `@Novax`.
- Прочтите `tools/README.md` — описание ключевых инструментов (полный автосписок: `python tools/cli_inventory.py`).
