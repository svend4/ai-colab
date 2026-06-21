# Pipeline operator guide (T-034)

Короткая инструкция, как работать с конвейером `tools/pipeline.py` — для людей и агентов. Конвейер = «общий котёл»: берёшь следующую готовую задачу, делаешь, отчитываешься, берёшь следующую.

## Цикл одного агента

```
status            # посмотреть котёл
next <Имя>        # атомарно занять следующую готовую задачу
# ...делаешь задачу...
done <Имя> <T-id> --report "что сделал"
next <Имя>        # и снова — пока не «КОТЁЛ ПУСТ»
```

Полные команды:

```bash
python tools/pipeline.py status                       # лента: в работе / готовы / заблокированы
python tools/pipeline.py next   <Имя>                  # занять следующую готовую
python tools/pipeline.py mine   <Имя>                  # мои текущие задачи
python tools/pipeline.py done   <Имя> <T-id> --report "..."
python tools/pipeline.py fail   <Имя> <T-id> --reason "..."
python tools/pipeline.py snapshot                      # обновить PIPELINE.md + logs/pipeline.json
python tools/pipeline.py heartbeat <Имя> <T-id> --progress 50 --note "..." --eta "..."
```

## Правила

1. **Одна открытая задача за раз.** Не бери вторую, пока текущая не `done`/`fail`. Проверяй `mine <Имя>` перед `next`.
2. **`owner: pool` — общая, бери смело.** Задача с конкретным именем владельца (например `owner: Codex`) — закреплённая, не вытягивай её; работай со своими и с `pool`.
3. **Готовая = `todo` + зависимости done + не занята.** Заблокированные зависимостями `next` не выдаёт — это нормально.
4. **Заверши явно.** `done --report "..."` (успех) или `fail --reason "..."` (не вышло → задача в `blocked`). Не оставляй «висящий» claim — TTL 30 мин его потом отпустит, но лучше закрывать самому.
5. **Длинную задачу — с heartbeat** (по желанию): `heartbeat <Имя> <T-id> --progress N` показывает остальным, что ты жив и на каком проценте. Пишется в `logs/heartbeat/<Имя>.json`, не в общий файл.
6. **Отчёт — короткий и по делу:** что сделал, какой файл/результат. Он попадает в `queues/done/<T-id>.done.md`.
7. **После задачи — синхронизируй канон:** `python tools/generate.py`, затем коммит (pre-commit-гейт проверит `validate.py` + `generate.py --check`).
8. **Новую задачу заводи через `next_id.py`** (`task`/`question`/`decision`), не выбирай номер вручную — иначе коллизии id.
9. **Коммит — только своих файлов.** Если в workspace есть чужие half-done изменения, не делай `git add -A`; используй явный список файлов или оставь вариант в `streams/`.
10. **Спорный вариант — сначала stream.** Если задача архитектурная или есть конкурирующие подходы, оформи `streams/<topic>/<stream-id>/STREAM.md`, а mainline меняй после review/adoption.

## Где смотреть состояние

- **Люди:** `PIPELINE.md` (Kanban) и `LIVE.md` (heartbeat-лента) — генерируются `snapshot`.
- **Агенты/скрипты:** `logs/pipeline.json` и `logs/heartbeat.json`.
- Источник правды по статусу задачи — всегда `tasks/<T-id>.md`.

Связано: `tools/README.md` (раздел «Конвейер»), `темы/agent-pipeline.md`, `decisions/D-011` (конвейер), `D-012` (heartbeat).

См. также: `docs/commit-stream-policy.md`.
