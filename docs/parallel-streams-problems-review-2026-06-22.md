# Parallel streams/problems review — 2026-06-22

Task: `T-146`
Related: `D-017`, `D-019`, `D-021`, `T-135`, `T-136`, `T-143`, `T-144`, `Q-015`, `streams/commit-policy/20260622-0555-codex/STREAM.md`

## Короткий вывод

Проблема ожидания чужого commit уже была не раз описана и доказана практикой. Текущее состояние такое:

- `D-017` разрешил содержательные дубли как форки: второй агент не должен отказываться только потому, что тема уже начата.
- `D-019` сформулировал Level 0/Level 1/stream-модель: selective-add + `commit_lock` сейчас, `streams/` как полу-формат, worktree + merge-gate как следующий уровень.
- `D-021` принял Level 1 worktree-streams: отдельный `git worktree` на агента/задачу, merge через gate, Level 0 остаётся дефолтом.
- `T-144` добавил `top.py work-mode`, который уже умеет подсказать, когда нужна изоляция.

Моё мнение: система концептуально правильно эволюционировала, но граница применения Level 1 всё ещё слишком мягкая. Если агент видит чужую незавершённую работу, stale generated index или hot files, ожидание чужого commit нельзя считать нормальным рабочим циклом. В таких случаях надо переходить в worktree-приток или оформлять stream/variant, иначе система снова превращается в очередь ожидания.

## Что уже было сделано

### 1. Fork-and-synthesize

`D-017` зафиксировал главное изменение мышления: дубликат содержательного мнения не является мусором. Если одна карточка уже есть, второй агент должен дать свой вариант, а не снимать вопрос. Это решает проблему, когда один ранний вариант блокирует появление лучшего решения.

Рабочая формула:

```text
несколько вариантов -> сравнение -> консенсусные пункты в реализацию -> спорные пункты в Q/D/stream
```

### 2. Streams как полу-формат

`docs/commit-stream-policy.md` и `streams/README.md` описывают `streams/` как слой между свободным текстом и Git. Это не замена Git и не второй VCS. Это пакет доказательств/варианта:

```text
streams/<topic>/<stream-id>/STREAM.md
streams/<topic>/<stream-id>/notes.md
streams/<topic>/<stream-id>/patch.diff
streams/<topic>/<stream-id>/evidence/
```

Смысл: вариант уже достаточно структурирован, чтобы его можно было читать, сравнивать и принимать, но он ещё не загрязняет mainline.

### 3. Level 0: общий workspace с дисциплиной

Level 0 уже полезен:

- `tools/commit_lock.py` сериализует момент commit/generate/add;
- selective-add запрещает случайный `git add -A` в грязном дереве;
- `tools/cohort.py ship` и `top.py` дают более удобную обвязку.

Но Level 0 не убирает общий generated-state: `TASKS.md`, `QUESTIONS.md`, `index.json`, `PIPELINE.md`, `LIVE.md`, heartbeat/log snapshots.

### 4. Level 1: worktree-притоки

`D-021` принял Level 1. Инструменты уже есть:

- `tools/worktree.py` печатает/создаёт отдельный worktree;
- `tools/flow.py --worktree` даёт start/finish обвязку;
- `tools/merge_gate.py` проверяет validate/generate/permissions перед вливанием;
- `tools/top.py work-mode` подсказывает режим.

Проверка в T-146:

```powershell
python tools\top.py work-mode codex T-146 --parallel --hot-files
```

Результат: рекомендация `Level 1 worktree`, причины `parallel work, hot generated/shared files`.

Сухой запуск:

```powershell
python tools\flow.py start codex T-146 --worktree
```

Результат: печатает `git worktree add -b agent/codex/T-146 ...`, без выполнения до `--run`.

## Реальные проблемы, которые уже проявлялись

### P1. Ожидание чужого commit теряет время

Пример из T-133/T-136: агент готов коммитить свои файлы, но `generate --check` видит stale `TASKS.md/index.json`, потому другой агент создал или изменил task. Если агент регенерирует и закоммитит индекс, он может включить чужое half-done состояние. Если не регенерирует, pre-commit/gate краснеет. Итог: он ждёт чужой commit.

Вывод: Level 0 защищает от грубой ошибки, но не даёт параллельной скорости.

### P2. Generated indexes являются shared hot files

`TASKS.md`, `QUESTIONS.md`, `DECISIONS.md`, `index.json`, `PIPELINE.md` полезны как навигация, но создают связность между задачами. Даже если кодовые файлы разные, обновление одного task меняет общий индекс.

Нужно считать generated indexes горячей зоной. Если два агента одновременно меняют источники для индекса, Level 1 должен быть предпочтительным или обязательным.

### P3. `commit_lock` сериализует commit, но не изолирует работу

`commit_lock.py` решает гонку за `index.lock`, но не делает workspace независимым. Пока один агент думает, другой видит его незакоммиченные файлы. Это лучше, чем хаос, но хуже, чем параллельные притоки.

### P4. Широкий `git add -A` опасен

Это уже закрыто политикой, но риск остаётся человеческим: в грязном shared tree одна команда может забрать чужие файлы. Поэтому selective-add должен оставаться жёстким правилом Level 0.

### P5. Streams могут стать кладбищем вариантов

Если stream создан, но не имеет статуса, adoption-условий и ссылки на task/decision, он превращается в архивный шум. Поэтому каждый stream должен иметь:

- `status`;
- related task/question/decision;
- критерии adoption;
- итог: `adopted`, `superseded`, `rejected` или `archived`.

### P6. Worktree повышает сложность запуска

Level 1 технически чище, но требует дисциплины:

- агент должен знать новый путь worktree;
- нужно понимать, где выполнять команды;
- merge-owner должен быть определён;
- нельзя плодить забытые worktree/branches.

Поэтому Level 1 не должен быть всегда включён для каждой мелкой правки. Нужны триггеры.

### P7. Merge-gate может стать новым узким местом

Если только один человек может вливать все притоки, скорость снова упадёт. Нужна роль интегратора или правило: low-risk docs/tools с зелёным gate может вливать назначенный агент, high-risk только Stefan/интегратор.

### P8. Shell/Windows замедления и зависания искажают ощущение прогресса

В этой среде простые PowerShell-команды иногда стартуют дольше 10 секунд. Были отдельные проблемы с `%TEMP%`, permissions и encoding. Это не только UX-дефект: долгие команды увеличивают вероятность, что другой агент успеет изменить generated-state между check и commit.

Метод: короткие команды, timeout wrappers, workspace-safe temp, UTF-8 setup, избегать длинных конвейеров.

## Где моё мнение отличается от более мягкой политики

Текущая формулировка `D-021`: Level 0 дефолт, Level 1 явный режим при реальной параллельной нагрузке.

Я предлагаю уточнить: есть случаи, где Level 1 должен быть не просто рекомендацией, а обязательным режимом:

1. В `git status` есть чужие незакоммиченные task/question/decision/source-файлы.
2. `generate.py --check` краснеет из-за чужой активной задачи или placeholder/state drift.
3. Задача трогает hot files: generated indexes, `tools/top.py`, `tools/portal.py`, `_canon`, генераторы, registry/catalog.
4. Пользователь явно просит параллельную работу нескольких агентов над одной темой.
5. Агент не может отличить свои изменения от чужих без риска.

Это оформлено как `Q-015` и stream `20260622-0555-codex`.

## Предлагаемая рабочая карта

### Этап 1. Уточнить Level 1 trigger policy

Принять по `Q-015` вариант B: Level 1 обязателен при трёх практических триггерах: чужие незавершённые файлы, stale generated index, hot files.

Результат: маленькое decision/update к `D-021` или новый `D-022`.

### Этап 2. Добавить preflight detector

Нужна команда:

```powershell
python tools\top.py preflight codex T-146
```

Она должна показать:

- dirty files grouped by owner/unknown;
- generated indexes stale/fresh;
- hot files touched by task;
- active claims;
- recommended mode: Level 0 или Level 1;
- exact commands.

`work-mode` уже делает часть этого, но пока требует ручных флагов `--parallel`, `--dirty-mainline`, `--hot-files`.

### Этап 3. Сделать worktree-start удобнее

Добавить сухую команду “одна кнопка”:

```powershell
python tools\top.py worktree-start codex T-146
```

По умолчанию печатать план. С `--run` создавать worktree. После создания печатать:

- новый путь;
- команды health/check;
- как завершить через merge-gate;
- как удалить worktree после merge.

### Этап 4. Улучшить stream lifecycle

Добавить автоматическую проверку stream-пакетов:

```powershell
python tools\stream.py check
```

Проверять:

- `status` допустим;
- есть `related` или ссылка в теле;
- есть adoption conditions;
- stale proposed stream старше N дней помечается в отчёте.

### Этап 5. Развести generated snapshots и canonical indexes

`TASKS.md`, `QUESTIONS.md`, `DECISIONS.md`, `index.json` нужны для канона. `PIPELINE.md`, `LIVE.md`, heartbeat/log snapshots больше похожи на runtime-видимость. Их надо аккуратно разделять в commit policy: canonical indexes коммитить при изменении sources; volatile snapshots не включать в обычный commit без причины.

### Этап 6. Определить merge-owner tiers

Предложение:

- low-risk docs/tests/tools wrappers: назначенный агент может merge при green gate и clean scope;
- medium-risk governance/core tools: второй агент review или Stefan;
- high-risk execute/network/external code/secrets: только Stefan/явный интегратор.

## Вопросы для людей и агентов

1. Согласны ли участники, что вариант B из `Q-015` должен стать обязательным правилом?
2. Кто может быть назначенным интегратором для Level 1 притоков, кроме Stefan?
3. Должен ли `top.py work-mode` автоматически анализировать `git status`, или это отдельная команда `preflight`?
4. Нужно ли запрещать commit при stale generated index, если stale вызван чужой активной задачей?
5. Какой максимальный срок жизни `status: proposed` stream без adoption/rejection?
6. Должны ли generated runtime snapshots (`LIVE.md`, heartbeat/pipeline logs) вообще попадать в обычные commits?
7. Нужен ли отдельный `streams/<topic>/<id>/evidence/commands.md`, куда агенты складывают точный вывод проверок?

## Моё техническое заключение

Текущая инфраструктура уже прошла важную стадию: она не просто хранит обсуждения, а имеет task pipeline, claims, validation, generated indexes, streams, worktree plan, merge gate, top facade и commit policy. Это уже “середина пирамиды”, но пока она частично требует ручной дисциплины.

Следующий уровень должен быть не в большом автономном оркестраторе, а в маленьком preflight/decision layer: агент перед задачей получает точный ответ “Level 0 или Level 1”, почему, какие файлы опасны, какие команды выполнить. Это принесёт динамику без потери управляемости.