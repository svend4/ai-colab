# Pipeline operator guide (T-034)

Короткая инструкция, как работать с конвейером `tools/pipeline.py` — для людей и агентов. Конвейер = «общий котёл»: берёшь следующую готовую задачу, делаешь, отчитываешься, берёшь следующую.

## Цикл одного агента

```
status            # посмотреть котёл
next <Имя>        # атомарно занять следующую готовую задачу
claim <Имя> <T-id> # атомарно занять конкретную готовую задачу
# ...делаешь задачу...
done <Имя> <T-id> --claim <claim_id> --report "что сделал" --applied "AGENTS.md, PROTOCOL.md, Checks"
next <Имя>        # и снова — пока не «КОТЁЛ ПУСТ»
```

Полные команды:

```bash
python tools/pipeline.py status                       # лента: в работе / готовы / заблокированы
python tools/pipeline.py next   <Имя>                  # занять следующую готовую
python tools/pipeline.py claim  <Имя> <T-id>           # занять конкретную ready-задачу
python tools/pipeline.py mine   <Имя>                  # мои текущие задачи
python tools/pipeline.py done   <Имя> <T-id> --claim <claim_id> --report "..." --applied "AGENTS.md, PROTOCOL.md, Checks"
python tools/pipeline.py fail   <Имя> <T-id> --reason "..."
python tools/pipeline.py snapshot                      # обновить PIPELINE.md + logs/pipeline.json
python tools/pipeline.py heartbeat <Имя> <T-id> --progress 50 --note "..." --eta "..."
```

## Правила

1. **Одна открытая задача за раз.** Не бери вторую, пока текущая не `done`/`fail`. Проверяй `mine <Имя>` перед `next`.
   Если нужна именно конкретная задача, используй `claim <Имя> <T-id>`, а не `next`: команда не возьмёт другую задачу и вернёт ошибку, если T-id не ready.
2. **`owner: pool` — общая, бери смело.** Задача с конкретным именем владельца (например `owner: Codex`) — закреплённая, не вытягивай её; работай со своими и с `pool`.
3. **Готовая = `todo` + зависимости done + не занята.** Заблокированные зависимостями `next` не выдаёт — это нормально.
4. **Заверши явно.** `done --report "..."` (успех) или `fail --reason "..."` (не вышло → задача в `blocked`). Не оставляй «висящий» claim — TTL 30 мин его потом отпустит, но лучше закрывать самому.
5. **Длинную задачу — с heartbeat** (по желанию): `heartbeat <Имя> <T-id> --progress N` показывает остальным, что ты жив и на каком проценте. Пишется в `logs/heartbeat/<Имя>.json`, не в общий файл.
6. **Отчёт — короткий и по делу:** что сделал, какой файл/результат. Для служебных задач добавляй `--applied "AGENTS.md, PROTOCOL.md, Checks"`; это попадёт в `queues/done/<T-id>.done.md` как машинное поле `applied` и как читаемая строка. Старый `done --report` оставлен для совместимости, но для service/governance-задач без `--applied` pipeline печатает `WARN`, чтобы агент не забывал evidence.
7. **После задачи — синхронизируй канон:** `python tools/generate.py`, затем selective-add и коммит под `commit_lock.py` (pre-commit-гейт проверит `validate.py` + `generate.py --check`).
8. **Новую задачу заводи через `next_id.py`** (`task`/`question`/`decision`), не выбирай номер вручную — иначе коллизии id.
9. **Коммит — только своих файлов.** Если в workspace есть чужие half-done изменения, не делай `git add -A`; используй явный список файлов или оставь вариант в `streams/`.
10. **Спорный вариант — сначала stream.** Если задача архитектурная или есть конкурирующие подходы, оформи `streams/<topic>/<stream-id>/STREAM.md`, а mainline меняй после review/adoption.

## Где смотреть состояние

- **Люди:** `PIPELINE.md` (Kanban) и `LIVE.md` (heartbeat-лента) — генерируются `snapshot` и являются runtime-снимками, не commit-scope.
- **Агенты/скрипты:** `logs/pipeline.json` и `logs/heartbeat.json` — runtime-снимки, игнорируются Git после T-148.
- Источник правды по статусу задачи — всегда `tasks/<T-id>.md`.

Связано: `tools/README.md` (раздел «Конвейер»), `topics/agent-pipeline.md`, `decisions/D-011` (конвейер), `D-012` (heartbeat).

См. также: `docs/commit-stream-policy.md`.

## Volatile snapshots (T-148)

`PIPELINE.md`, `LIVE.md`, `logs/pipeline.json`, `logs/heartbeat.json` остаются рабочими файлами на диске, но больше не отслеживаются Git. Они могут обновляться командами `snapshot`/`heartbeat` в любой момент и не должны попадать в обычный commit. Источник правды остаётся в `tasks/`, `questions/`, `decisions/`, `queues/claimed`, `queues/done` и generated canonical indexes (`TASKS.md`, `QUESTIONS.md`, `DECISIONS.md`, `index.json`).
