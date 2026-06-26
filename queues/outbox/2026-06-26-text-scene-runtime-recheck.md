# Text scene runtime recheck

Дата: 2026-06-26
Автор: codex
Статус: proposed / runtime-blocked

## Контекст

В проекте появился кандидат на следующий слой 2D-текстового workbench:

- `tools/text_scene.py`
- `tools/test_text_scene.py`

Идея инструмента соответствует ранее обсужденной линии: не копировать TVCP/Zed как GUI, а сделать headless/offline слой, где информация показывается не только линейным чатом, но и 2D-сценой из карточек, уровней, связей и прогрессивного раскрытия.

## Что проверялось

План проверки был такой:

1. Проверить текущий `git status`.
2. Найти связанные документы через `rg`.
3. Запустить `python tools\test_text_scene.py`.
4. При успешном результате проверить `tools\validate.py`.
5. После этого принять решение о staged/commit отдельным узким коммитом.

## Что произошло

Короткие команды оболочки снова зависли:

- `git status --short`
- `rg ... text_scene ...`
- точечная попытка остановить зависшие проверки через процессный список
- даже `taskkill` не вернул управление в ожидаемое короткое окно

Это подтверждает старый архетип проблемы: нижний runtime/Windows shell иногда блокирует даже простые операции. В такой ситуации нельзя честно утверждать, что интеграция протестирована, пока не получен вывод тестов.

## Предварительная оценка text_scene

По уже прочитанному содержимому файлов:

- инструмент выглядит read-only;
- не запускает внешние процессы;
- не пишет файлы;
- строит 2D-карточки из канона `view.load_canon()`;
- поддерживает ANSI/HTML-рендер;
- тесты выглядят in-process и не должны требовать сети, git или subprocess.

То есть концептуально это хороший кандидат на отдельный небольшой commit, но только после фактического запуска теста.

## Статическая проверка без PowerShell

Так как PowerShell/git/rg зависли, была выполнена дополнительная проверка через `node_repl` и прямое чтение файлов:

- `tools/text_scene.py`: 227 строк, опасные маркеры `subprocess`, `os.system`, `Popen`, `socket`, `requests`, `urllib`, `open(`, `write(`, `remove(`, `unlink(`, `rmtree(`, `shutil` не найдены.
- `tools/test_text_scene.py`: 103 строки, опасные маркеры не найдены.
- CLI-флаги инструмента: `--depth`, `--cols`, `--level`, `--steps`, `--html`.
- Основные функции: `bfs_levels`, `build_cells`, `render_card`, `render_ansi`, `diffuse`, `render_html`, `main`.

Вывод: по статике инструмент соответствует роли read-only renderer. Блокировка остаётся только в отсутствии подтверждённого запуска `python tools\test_text_scene.py` в текущей shell-среде.

## Что должен сделать следующий агент

Если shell восстановлен:

```powershell
$env:PYTHONIOENCODING = "utf-8"
python tools\test_text_scene.py
python tools\validate.py
```

Если обе команды проходят:

```powershell
python tools\commit_lock.py acquire codex --ttl 180 --wait 60
git add -- tools\text_scene.py tools\test_text_scene.py
git commit -m "feat: add text scene renderer"
python tools\commit_lock.py release codex
```

Если `git status` или `rg` снова зависают, не расширять число команд, а сначала фиксировать runtime-problem в friction ledger и перейти к ручному read-only review.

## Рекомендация

`tools/text_scene.py` надо рассматривать как первый перенос идеи "текстовой диффузионной сцены" из концепции в инструмент. Он не должен сразу становиться главным интерфейсом. Правильный следующий шаг:

1. Принять его как экспериментальный read-only renderer.
2. Не давать ему полномочий писать в repo.
3. Затем добавить `text_mux` или `workspace-map`, который будет собирать несколько thread/portal/queue источников в единую 2D-сцену.
4. Только после этого обсуждать интерактивный terminal UI.

## Повторная проверка после runtime-fix

После восстановления shell и обхода зависших процессов выполнены проверки:

- `python tools\test_text_scene.py` → OK.
- `python tools\test_text_mux.py` → сначала упал на старом архетипе `TemporaryDirectory`/Windows permissions; тест исправлен на явный каталог `tmp-work/text_mux_test/run_*`; после исправления → OK.
- `python tools\validate.py` → OK=12 WARN=0 ERROR=0.

Технический вывод: `text_scene` можно считать проверенным read-only renderer. `text_mux` можно считать проверенным экспериментальным cell-store/lanes renderer, но он выше по риску, потому что содержит файловый провод `events.jsonl`; его надо принимать как отдельный слой с явными границами записи.
