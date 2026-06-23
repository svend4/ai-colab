# Проверка истории ручейков, worktree и merge-back

Дата: 2026-06-23
Агент: codex
Тип: outbox-review

## Что проверено

Проверены текущие источники политики и кода:

- `docs/commit-stream-policy.md`
- `docs/parallel-work-policy.md`
- `docs/workflow-conveyor-policy.md`
- `docs/workflow-orchestration-policy.md`
- `streams/README.md`
- `topics/parallel-forks-history-2026-06-22.md`
- `topics/parallel-work-divergences-2026-06-22.md`
- `tools/worktree.py`
- `tools/flow.py`
- `tools/top.py`
- `tools/cohort.py`
- `tools/stream.py`
- `tools/merge_gate.py`
- реальные stream-пакеты Codex и Claude в `streams/`
- свежий `git log`

## Вывод

Идея "свой ручеек / свое дерево / своя ветка / потом влить в master/main" уже реализована в проекте тремя слоями.

1. `streams/` - полу-коммит для вариантов: уже структурированный пакет, но еще не mainline. Он нужен для спорных идей, альтернатив и fork-and-synthesize.
2. Level 0 - общее дерево с `commit_lock` и selective-add. Это дешево, но не изолирует shared generated state.
3. Level 1 - настоящий `git worktree` на агента и задачу, ветка `agent/<agent>/<task>`, слияние через `merge_gate`.

Текущий верхний слой сам рекомендует Level 1 для параллельной работы, грязной mainline и hot/generated файлов:

```powershell
python tools\top.py work-mode codex T-188 --parallel --dirty-mainline --hot-files
```

Результат проверки: recommendation = `Level 1 worktree`.

Dry-run команды:

```powershell
python tools\flow.py start codex T-188 --worktree
python tools\flow.py finish codex T-188 --worktree
```

`worktree.py` печатает конкретный приток:

```powershell
git worktree add -b agent/codex/T-188 "C:\Users\stefan\Documents\New project ai colab-wt-codex-T-188"
```

Без `--run` это только план, не изменение репозитория.

## Примеры других агентов

Claude оставил stream `streams/portal-location/20260621-1931-claude/STREAM.md`. Это пример содержательного варианта: Claude не стал сразу менять горячий `portal.py`, а оформил вариант, риски, recommendation и условие adoption.

Codex оставил stream `streams/commit-policy/20260622-0555-codex/STREAM.md`. Там прямо сказано, что Level 0 недостаточен, если generated indexes устаревают из-за чужой работы, и что Level 1 должен быть обязательным по триггерам.

`git log` показывает более крупный исторический стиль: FINDER/SOLVER, бригады, дирижеры, интеграторы, batch-commit. Это похоже на организационную надстройку над тем же принципом: много параллельного анализа, но серийная точка интеграции в одну историю.

## Сравнение с моей текущей практикой

В этой сессии я часто работал в Level 0: claims, outbox, selective edits, проверки, без коммита. Это допустимо для небольших изолированных правок и анализа, но хуже соответствует D-022, когда:

- дерево уже грязное;
- другие агенты имеют активные claims;
- меняются hot files или generated indexes;
- есть вероятность same-file конфликта;
- пользователь явно просит параллельную работу.

Так как я не делал commit, риск захвата чужой half-done работы был ниже. Но сама работа в общем дереве все равно создавала типичную проблему: shared generated state и необходимость повторных перепроверок. Для следующей крупной build-задачи правильнее начинать с `top.py work-mode` и при красном триггере уходить в Level 1 worktree.

## Практическое правило

Если задача только аналитическая или это короткий doc/outbox без hot files, можно Level 0.

Если задача пишет код, меняет `tools/`, генераторы, `TASKS.md`, `index.json`, `PIPELINE.md`, или идет параллельно с чужой активной работой, нужно:

```powershell
python tools\top.py work-mode <agent> <T-id> --parallel --dirty-mainline --hot-files
python tools\flow.py start <agent> <T-id> --worktree
```

После review и готового worker-commit:

```powershell
python tools\flow.py finish <agent> <T-id> --worktree
```

`--run` добавлять только после просмотра dry-run плана и текущего `git status`.

## Открытый организационный риск

Техническая часть построена. Основной риск теперь не в отсутствии кода, а в дисциплине применения:

- агенты продолжают по привычке работать в общем дереве;
- merge-owner/интегратор остается узким местом;
- stream-пакеты могут зависать без adoption;
- worktree есть, но не всегда включается по триггеру.

Рекомендация: для следующей крупной задачи не просто обсуждать Level 1, а реально провести один полный цикл: `start --worktree --run` -> работа в соседнем каталоге -> worker commit -> `finish --worktree` -> merge-gate -> outbox-retro.
