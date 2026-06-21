---
name: pipeline-operator
description: Работать с конвейером задач AI-OS Bridge как агент — атомарно взять задачу, отчитаться, поддерживать heartbeat, не ломая канон. Использовать при выполнении задач из общего пула tasks/.
---

# Skill: оператор конвейера (pipeline-operator)

Повторяемая дисциплина работы агента с `tools/pipeline.py` и каноном.

## Цикл работы

1. **Взять задачу (атомарно):** `python tools/pipeline.py next <agent>` — выдаёт `T-id` и
   `claim_id`, ставит `status: doing`. Не брать вторую задачу, пока есть незакрытая своя.

2. **Heartbeat (по желанию, при длинной задаче):**
   `python tools/pipeline.py heartbeat <agent> <T-id> --progress N --note "..." --eta "..."`.

3. **Сделать работу**, затем **закрыть с fencing:**
   `python tools/pipeline.py done <agent> <T-id> --claim <claim_id> --report "..."`
   (или `fail ... --reason "..."`). `--claim` обязателен для защиты от перехвата (T-082).

4. **Пересобрать канон:** `python tools/generate.py` (TASKS/index/STATUS/board из front-matter),
   затем `python tools/validate.py` → `ERROR=0`, `python tools/pipeline.py snapshot`.

## Правила

- Источник правды по статусу — `tasks/T-XXX.md` front-matter; `TASKS.md`/`index.json` **генерируемые**
  (не править руками). Перед коммитом гнать `generate` → `validate` (pre-commit хук это проверяет).
- Не выполнять чужую свежую задачу (проверяйте claim); не менять чужие финальные решения без
  записи в `DECISIONS.md`.
- При гонке коммитов с другим агентом: `generate && git add -A && git commit` одной цепочкой
  (хук падает на устаревшей навигации — перегенерируйте и повторите).
- Новый id — только через `python tools/next_id.py task` (атомарно, без коллизий).

## Готово, если

Задача `done` с done-маркером `queues/done/<id>.done.md`, `validate ERROR=0`, snapshot обновлён.

Связано: `docs/pipeline-operator-guide.md`, `AGENTS.md`, `PROTOCOL.md`.
