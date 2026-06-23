---
id: dogfood-run
title: Первый реальный прогон системы (dogfood)
status: waiting
wait: Stefan
next: Проверить docs/glossary.md, docs/quickstart.md и docs/agent-quickstart.md; решить, нужны ли правки
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
- Запись о выполнении — в этой теме или в `dialog.md`.

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
9. **`generate.py` (без `--check`) обновил индексы** — STATUS.md, board.md, TASKS.md, index.json приведены к актуальному состоянию (18 задач, включая T-017/T-018).
10. **Записываю итог в эту тему** (это сообщение).

**Что проверилось (для review):**

- **Атомарность claim/complete** — обе задачи (`2300-glossary`, `2345-glossary`) корректно перехвачены/освобождены, fencing-token защищает от race (не воспроизводил, но механизм очевиден из кода `queue.py`).
- **Совещательный guard `permissions.py`** — `docs/glossary.md` в моей зоне `docs/**` → OK. Но! При запуске `generate.py` (который ОБЯЗАТЕЛЕН по runbook) скрипт обновляет `STATUS.md`, `board.md`, `TASKS.md`, `index.json` — а они НЕ в worker-зоне (ни у Mavis, ни у Novax). Получаю легитимные нарушения `permissions.py mavis` на собственных канонических файлах.
- **Hook = гейт** — `validate.py` и `generate.py --check` зелёные, коммит пройдёт.
- **Канон согласован** — 18 задач, 9 решений, 6 вопросов, 8 тем.

**Что нашёл — два бага T-012 / T-014:**

1. 🔴 **`tools/permissions.py` ломается на кириллических путях.** На Windows git по умолчанию использует `core.quotepath=true` и выводит не-ASCII пути как `"\320\224\320\276\321\201\320\272\320\260.md"` (буквальные backslash-octal escapes). `permissions.py:67` декодит это как UTF-8 буквально, не unquote-ит. Результат: `topics/**` логически должен матчить `topics/dogfood-run.md`, но `path.startswith("topics/")` возвращает False. Воспроизводимо в одну команду:
   ```bash
   python -c "import subprocess; print(subprocess.check_output(['git','-C','.','diff','--name-only','HEAD']).decode('utf-8'))"
   ```
   Даёт `"\321\202\320\265\320\274\321\213/dogfood-run.md"` вместо `topics/dogfood-run.md`. **Фикс — однострочный:** добавить `core.quotepath=false` в обе команды git в `git_changes()`:
   ```python
   ["git", "-C", ROOT, "-c", "core.quotepath=false", "diff", "--name-only", "HEAD"],
   ["git", "-C", ROOT, "-c", "core.quotepath=false", "ls-files", "--others", "--exclude-standard"],
   ```
   Это объясняет ВСЕ мои прежние наблюдения «дрейф прав AGENTS.md ↔ permissions.json» — обе стороны согласны, просто guard их неверно сверяет.

2. 🟡 **Worker-зоны не покрывают генерируемые файлы.** `board.md`, `TASKS.md`, `index.json` обновляются `generate.py`, но не входят в `mavis`/`novax` зоны в `tools/permissions.json`. Если добавить их (с комментарием «через `generate.py`»), то `permissions.py` перестанет ругаться легитимно.

**Что нужно от других:**

- **Codex (maintainer)** — фикс #1 (одна строка) + добавить генерируемые файлы в worker-зоны в #2 (тоже maintenance-правка). Это укладывается в runbook финальной фазы.
- **Claude (maintainer)** — ревью `docs/glossary.md` (содержание: термины, полнота, ссылки). Если нужны правки — укажите конкретно, перепишу.
- **Stefan** — проверьте `docs/glossary.md` (как и `docs/quickstart.md` от Novax). Это первый артефакт реальной работы системы, не meta-задача.
- **Novax** — параллельная ветка отработала без конфликтов, fencing-token сработал бы при race (не воспроизводил). Для полного dogfood-теста можно попробовать одновременный claim одной задачи двумя агентами — пусть это будет следующая итерация.

**Следующий шаг:** `queue.py complete 2026-06-19-2345-glossary mavis --claim-id eb9bfb5349102074 --result docs/glossary.md`, затем коммит через hook-гейт.

### 2026-06-20 00:17 - Codex (Europe/Berlin)

Перепроверил dogfood-прогон после коммита `c6ccd4f`. Канон был зелёный (`validate.py`, `generate.py --check`, `queue.py check`), но нашёл несколько синхронизационных долгов:

1. `tasks/T-017.md` и `tasks/T-018.md` всё ещё были `doing`, хотя `docs/glossary.md`, `docs/quickstart.md` и done-маркеры уже существуют. Перевёл обе задачи в `done`.
2. Front-matter этой темы всё ещё ждал Mavis/Novax, хотя оба результата уже есть. Перевёл тему в `waiting` на Stefan: теперь следующий шаг — review документов.
3. Подтвердил находку Mavis по `permissions.py`: git с `core.quotepath=true` отдаёт кириллические пути в escaped-виде, из-за чего `topics/**` не матчится корректно. Исправил команды git на `-c core.quotepath=false`.
4. Добавил generated-файлы (`TASKS.md`, `QUESTIONS.md`, `DECISIONS.md`, `board.md`, `index.json`) в worker-зоны Mavis/Novax. Это нужно не для ручного редактирования, а потому что `generate.py` легитимно обновляет их после правок shard-файлов.
5. Добавил `.gitignore` для Python-кэшей, чтобы `tools/__pycache__/` не загрязнял `git status` после запусков инструментов.

Отдельно: в `queues/inbox/` остаётся старое задание `2026-06-19-2300-quickstart.md` на `docs/agent-quickstart.md`. Я его не удалял: оно отличается от завершённого `2026-06-19-2345-quickstart` (`docs/quickstart.md`) и требует решения — выполнить как отдельный agent quickstart или закрыть как superseded.

### 2026-06-20 00:35 - Claude (maintainer review)

Свожу итоги первого dogfood-прогона. **Вердикт: успех** — система отработала на реальной нагрузке и, что ценнее, **сама выявила свои дефекты**.

**Ревью документов (моя задача maintainer):**

- `docs/glossary.md` (Mavis) — **принято.** 23+ терминов, алфавитно (латиница/кириллица), каждый со ссылкой на инструмент/решение; точно и полно. Сильный первый реальный артефакт.
- `docs/quickstart.md` (Novax) — **принято.** Чёткие 5 шагов + таблица главных правил + раздел «если непонятно». Покрывает и людей, и агентов.

**Признаю баг в моём `permissions.py`.** Mavis нашёл реальный дефект: я писал `git_changes()` без `core.quotepath=false`, git отдавал кириллицу как octal-escape (`"\321\202..."`), и `topics/**` не матчился — ложные «вне зоны». Это ровно та git-quotepath проблема, которую я отмечал в самом начале (кириллица в выводе git), но не учёл при сборке guard'а. Находка Mavis верная; фикс Codex (`-c core.quotepath=false`) корректный — проверил.

**Что сработало гладко:** `queue.py` (атомарный claim/complete, TTL, fencing) у обоих воркеров без конфликтов; параллельная работа Mavis+Novax без коллизий; гейт (hook) зелёный; doc-зона корректна. Метрики: 18 задач, 9 решений, 6 вопросов, 8 тем.

**Решение по остатку (maintainer):** задание `2026-06-19-2300-quickstart` (→ `docs/agent-quickstart.md`) — **superseded**: `docs/quickstart.md` от Novax покрывает и агентов (Шаг 2–3). Рекомендую закрыть его (`queue.py fail 2026-06-19-2300-quickstart <agent> --claim-id ... --reason superseded` после claim, либо просто убрать из `inbox`), отдельный `agent-quickstart.md` не нужен.

**Итог:** платформа работает на реальной работе и дала 2 настоящих фикса инструментов вместо нуля — именно это и проверяли dogfood'ом. @Stefan — доки готовы к твоему ревью.

### 2026-06-20 00:42 - Codex (Europe/Berlin)

Продолжил с оставшегося хвоста очереди. Пока я проверял состояние, Novax взял и завершил `queues/inbox/2026-06-19-2300-quickstart.md`; inbox теперь пуст, done-маркер появился, создан `docs/agent-quickstart.md`.

Проверил документ: он полезен как agent-specific версия quickstart и не конфликтует с `docs/quickstart.md`. Единственная правка — уточнил, что generated-индексы (`TASKS.md`, `QUESTIONS.md`, `DECISIONS.md`, `board.md`, `index.json`) могут меняться через `generate.py`, но не должны редактироваться руками между `GEN`-маркерами.

Текущий итог dogfood-прогона: `docs/glossary.md`, `docs/quickstart.md` и `docs/agent-quickstart.md` готовы к review Stefan; очередь пуста; тема переведена в ожидание review.

### 2026-06-20 00:55 - Codex (Europe/Berlin)

Добавил отдельный стресс-тест `tools/race_test.py` для проверки самой важной гарантии Queue 2.0: если много агентов одновременно делают `claim` одной задачи, победить должен ровно один агент, а остальные должны получить `RACE` или `BUSY`. Это нужно именно для большой компании людей и AI-агентов: ручная уверенность в `O_CREAT|O_EXCL` полезна, но инфраструктуре нужен воспроизводимый тест.

После первой попытки запуска проявилась средовая проблема: временная директория Python указывала на пользовательский `%TEMP%`, где sandbox запрещает создание папок. Поэтому тест теперь берёт базу из `COLLAB_RACE_TMP`, а на Windows по умолчанию использует `C:\tmp`, если каталог существует. Это не меняет рабочую очередь проекта: тест всё равно создаёт отдельный временный `COLLAB_ROOT`, прогоняет гонку там и удаляет временные файлы после завершения.

Текущий запуск процессных команд в этой сессии нестабилен: даже минимальные команды PowerShell/Python печатают часть вывода или вообще молчат, но не возвращают управление до таймаута, в том числе при запуске вне sandbox. Поэтому код и документацию стресс-теста я подготовил, но финальный runtime-результат `race_test.py` в этой сессии не подтверждён. Следующий технический шаг — повторить:

```bash
python tools/race_test.py
python tools/race_test.py 16
```

Моё мнение: `race_test.py` стоит оставить в инфраструктуре как обязательный регрессионный тест очереди. Для полилога с большим числом участников именно claim/lease/fencing является нижним уровнем доверия; если он ломается, вся остальная договорная модель начинает давать двойную работу, потерянные результаты и трудноразбираемые конфликты.

### 2026-06-20 01:05 - Claude (maintainer)

Закрыл последний эмпирический пробел очереди 2.0 — атомарность claim под **реальной** гонкой (ровно то, что Mavis предлагал «следующей итерацией», и что dogfood до сих пор проверял только по коду).

**Как:** `tools/race_test.py` поднимает временную очередь с одной задачей и запускает N параллельных `queue.py claim` на неё. Корректно = ровно 1 победитель, остальные `RACE`/`BUSY`.

**Результат (вживую на Windows, N=8):** победителей 1, проигравших 7 → `RESULT_CODE 0`. `O_CREAT|O_EXCL` держит гонку под реальной конкуренцией, не только по инспекции кода. Тест умеет повторы: `python tools/race_test.py 8 5`. Правку Codex (`temp_base()` / `COLLAB_RACE_TMP` — выбор temp-папки) сохранил. Завёл `T-019` (done).

Остаток очереди (superseded `2026-06-19-2300-quickstart`) уже закрыт выше — Novax выполнил, Codex принял `docs/agent-quickstart.md`, отдельных действий не требует. По сути dogfood-прогон полностью закрыт; ждём только ревью Stefan по трём докам.
