---
id: 20260622-0555-codex
topic: commit-policy
agent: codex
status: proposed
created: 2026-06-22
related: [T-146, Q-015, D-017, D-019, D-021, T-135, T-136, T-144]
adoption: none
---

# Stream: Level 1 trigger policy after waiting/generated-index conflicts

## Причина форка

Этот stream создан по T-146 как структурированный “ручеёк” для продолжения темы, которая уже обсуждалась в `D-017`, `D-019`, `D-021`, `T-135`, `T-136` и `T-144`: как не ждать чужой commit, не коммитить чужую half-done работу и не превращать mainline в смесь полуготовых изменений.

## Наблюдение

Level 0 (`commit_lock` + selective-add) достаточен для малых одиночных правок, но не достаточен при параллельной работе над shared generated state. Если `TASKS.md`, `QUESTIONS.md`, `index.json` или другие generated files устаревают из-за чужой активной задачи, агент оказывается перед плохим выбором:

- ждать, пока другой агент закоммитит;
- регенерировать и рискнуть включить чужую half-done структуру;
- пытаться коммитить без generated files и получить красный gate/pre-commit;
- уходить в worktree.

Последний вариант технически правильный, но пока не закреплён как обязательный при конкретных триггерах.

## Вариант

Принять правило: Level 1 worktree обязателен, если есть хотя бы один триггер:

1. В `git status` есть чужие незакоммиченные canonical/source files.
2. `generate.py --check` краснеет из-за чужой активной задачи или общего generated index.
3. Задача затрагивает hot files: generated indexes, `tools/top.py`, `tools/portal.py`, `_canon`, генераторы, registry/catalog.
4. Пользователь явно просит параллельную работу нескольких агентов.
5. Агент не может безопасно отделить свои изменения от чужих.

## Почему это может быть лучше

Это превращает “ждать чужой commit” из нормального режима в исключение. Агент продолжает работу в своём притоке, а mainline получает только проверенный результат через merge-gate.

## Риски

- Больше worktree/branch объектов, которые надо чистить.
- Merge-gate может стать узким местом.
- Новым агентам нужен короткий onboarding по работе из соседнего каталога.

## Проверка

В T-146 dry-run уже показывает, что текущий фасад понимает проблему:

```powershell
python tools\top.py work-mode codex T-146 --parallel --hot-files
```

Рекомендация: `Level 1 worktree`.

```powershell
python tools\flow.py start codex T-146 --worktree
```

Печатает worktree-команду без выполнения до `--run`.

## Что нужно для adoption

1. Ответить на `Q-015`.
2. Если выбран вариант B, оформить короткое decision/update к `D-021`.
3. Добавить `top.py preflight` или расширить `work-mode`, чтобы триггеры определялись автоматически.
4. Добавить `stream.py check`, чтобы proposed streams не зависали без adoption/rejection.