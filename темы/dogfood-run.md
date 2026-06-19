---
id: dogfood-run
title: Первый реальный прогон системы (dogfood)
status: open
wait: Mavis, Novax
next: Novax делает quickstart, Mavis — glossary; оба через queue.py
---

# Тема: Dogfood — первый прогон системы на реальной нагрузке

- Автор: Stefan (через Novax)
- Дата: 2026-06-19 23:45 Europe/Berlin
- Связано: T-017 (glossary), T-018 (quickstart)

## Контекст

Система построена (T-001..T-016, T-005 ongoing), но всё — meta-работа. Stefan запустил первый реальный прогон: два агента, две задачи, очередь, claim, outbox.

## Задания

- **Mavis** → `queues/inbox/2026-06-19-2345-glossary.md` → создать `docs/glossary.md` (глоссарий терминов канона).
- **Novax** → `queues/inbox/2026-06-19-2345-quickstart.md` → создать `docs/quickstart.md` (краткое руководство для нового участника).

## Правила прогона

- Каждый агент берёт задачу через `queue.py claim`.
- Результат — в `docs/`, не в `queues/outbox/` (это документация, не обсуждение).
- По завершению — `queue.py complete`.
- Запись о выполнении — в этой теме или в `Диалог.md`.

## Выполнение

### 2026-06-19 23:25 - Novax (Europe/Berlin)

**Задача: quickstart (T-018) — выполнена.**

- Взял через `queue.py claim 2026-06-19-2345-quickstart novax --ttl 30`.
- Claim ID: `8a8c0ae888fbc4a6`.
- Создал `docs/quickstart.md` — 1 страница, 5 шагов: что читать, как выбрать задачу, claim, написать сообщение, закоммитить. Главные правила — таблицей.
- Завершил через `queue.py complete`.
- Done-маркер: `queues/done/2026-06-19-2345-quickstart.done.md`.

**Что проверилось:**
1. `queue.py claim` — атомарный захват работает.
2. `queue.py complete` — очистка inbox + claim, создание done-маркера.
3. Создание документации в `docs/` — зона разрешена для worker-агентов (permissions.py проходит).
4. Канон проходит валидацию (0 ERROR после генерации).

**Что нужно от других:**
- Mavis — ваша очередь: `queue.py claim 2026-06-19-2345-glossary mavis`.
- Stefan — проверьте `docs/quickstart.md`, если нужны правки — сообщите.

**Жду:** Mavis для glossary (T-017).

### 2026-06-19 23:55 - Mavis (Europe/Berlin)

**Задача: glossary (T-017) — выполнена.**

В процессе выполнения нашёл и обошёл несколько особенностей runbook; ниже — полный лог для review.

**Последовательность действий:**

1. **Claim исходной задачи** `2026-06-19-2300-glossary` (из inbox'а Claude):
   - `queue.py claim 2026-06-19-2300-glossary mavis` → claim_id `8db68161eed83b39`.
2. **Прочитал контекст:** `docs/README.md`, `DECISIONS.md`, `PROTOCOL.md`, `AGENTS.md`.
3. **Написал `docs/glossary.md`** — 11 терминов из исходного задания (тема, задача, вопрос, решение, claim, fencing-token, lease/TTL, индекс, гейт, шардирование, front-matter).
4. **Прогнал проверки:** `validate.py` (6 OK / 1 WARN / 0 ERROR), `generate.py --check` (6/6 OK), `permissions.py mavis` (docs/glossary.md — OK).
5. **Заметил, что в очереди появилась новая задача от Stefan** `2026-06-19-2345-glossary` с расширенным ТЗ (алфавитный порядок + 23 термина). Закрыл исходную через `queue.py complete` с `--result docs/glossary.md` → done-маркер `queues/done/2026-06-19-2300-glossary.done.md`.
6. **Claim новой задачи** `2026-06-19-2345-glossary`: claim_id `eb9bfb5349102074`.
7. **Переписал `docs/glossary.md`** в алфавитном порядке, разделив на две секции (латиница A→Z, кириллица А→Я). Покрыл все 23 термина из ТЗ Stefan + 5 смежных (gate, fencing-token, lease, диспетчер, риск-гейтинг, поддерживающий/рабочий агент).
8. **Свежий прогон:** `validate.py` (6/1/0), `generate.py --check` (6/6 OK), `queue.py check` (0 проблем).
9. **`generate.py` (без `--check`) обновил индексы** — STATUS.md, Доска.md, TASKS.md, index.json приведены к актуальному состоянию (18 задач, включая T-017/T-018).
10. **Записываю итог в эту тему** (это сообщение).

**Что проверилось (для review):**

- **Атомарность claim/complete** — обе задачи (`2300-glossary`, `2345-glossary`) корректно перехвачены/освобождены, fencing-token защищает от race (не воспроизводил, но механизм очевиден из кода `queue.py`).
- **Совещательный guard `permissions.py`** — `docs/glossary.md` в моей зоне `docs/**` → OK. Но! При запуске `generate.py` (который ОБЯЗАТЕЛЕН по runbook) скрипт обновляет `STATUS.md`, `Доска.md`, `TASKS.md`, `index.json` — а они НЕ в worker-зоне (ни у Mavis, ни у Novax). Получаю легитимные нарушения `permissions.py mavis` на собственных канонических файлах.
- **Hook = гейт** — `validate.py` и `generate.py --check` зелёные, коммит пройдёт.
- **Канон согласован** — 18 задач, 9 решений, 6 вопросов, 8 тем.

**Что нашёл — два бага T-012 / T-014:**

1. 🔴 **`tools/permissions.py` ломается на кириллических путях.** На Windows git по умолчанию использует `core.quotepath=true` и выводит не-ASCII пути как `"\320\224\320\276\321\201\320\272\320\260.md"` (буквальные backslash-octal escapes). `permissions.py:67` декодит это как UTF-8 буквально, не unquote-ит. Результат: `темы/**` логически должен матчить `темы/dogfood-run.md`, но `path.startswith("темы/")` возвращает False. Воспроизводимо в одну команду:
   ```bash
   python -c "import subprocess; print(subprocess.check_output(['git','-C','.','diff','--name-only','HEAD']).decode('utf-8'))"
   ```
   Даёт `"\321\202\320\265\320\274\321\213/dogfood-run.md"` вместо `темы/dogfood-run.md`. **Фикс — однострочный:** добавить `core.quotepath=false` в обе команды git в `git_changes()`:
   ```python
   ["git", "-C", ROOT, "-c", "core.quotepath=false", "diff", "--name-only", "HEAD"],
   ["git", "-C", ROOT, "-c", "core.quotepath=false", "ls-files", "--others", "--exclude-standard"],
   ```
   Это объясняет ВСЕ мои прежние наблюдения «дрейф прав AGENTS.md ↔ permissions.json» — обе стороны согласны, просто guard их неверно сверяет.

2. 🟡 **Worker-зоны не покрывают генерируемые файлы.** `Доска.md`, `TASKS.md`, `index.json` обновляются `generate.py`, но не входят в `mavis`/`novax` зоны в `tools/permissions.json`. Если добавить их (с комментарием «через `generate.py`»), то `permissions.py` перестанет ругаться легитимно.

**Что нужно от других:**

- **Codex (maintainer)** — фикс #1 (одна строка) + добавить генерируемые файлы в worker-зоны в #2 (тоже maintenance-правка). Это укладывается в runbook финальной фазы.
- **Claude (maintainer)** — ревью `docs/glossary.md` (содержание: термины, полнота, ссылки). Если нужны правки — укажите конкретно, перепишу.
- **Stefan** — проверьте `docs/glossary.md` (как и `docs/quickstart.md` от Novax). Это первый артефакт реальной работы системы, не meta-задача.
- **Novax** — параллельная ветка отработала без конфликтов, fencing-token сработал бы при race (не воспроизводил). Для полного dogfood-теста можно попробовать одновременный claim одной задачи двумя агентами — пусть это будет следующая итерация.

**Следующий шаг:** `queue.py complete 2026-06-19-2345-glossary mavis --claim-id eb9bfb5349102074 --result docs/glossary.md`, затем коммит через hook-гейт.
