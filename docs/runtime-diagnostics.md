# Runtime Diagnostics

Дата: 2026-06-20
Связано: `tasks/T-039.md`, `tasks/T-029.md`

## Наблюдение

Проблема T-029 не похожа на ошибку `drivers/files/inventory.py`. В текущей сессии зависает запуск внешних программ из shell.

Проверенные команды:

```powershell
where.exe python
Get-Command python -All
& 'C:\Windows\System32\cmd.exe' /c echo ok
```

Результат: все команды ушли в timeout.

Ранее также зависали:

```powershell
python -c "print('ok')"
& '<bundled-python>\python.exe' -c "print('ok')"
python tools\pipeline.py snapshot
```

## Вывод

Блокер находится на уровне запуска внешних процессов в текущей Windows/Codex shell-сессии, а не в конкретном Python-скрипте.

## Что не сделано

Я не останавливал процессы вслепую, потому что это может затронуть чужие Python/CLI-задачи вне проекта.

## Рекомендованные действия

1. Проверить зависшие `python.exe`, `cmd.exe`, `powershell.exe` через Task Manager или отдельную административную консоль.
2. Закрыть только явно зависшие процессы, связанные с этой рабочей папкой.
3. Перезапустить Codex shell/session, если внешние exe не стартуют вообще.
4. После восстановления запуска команд выполнить:

```powershell
python drivers\files\test_inventory.py
python tools\validate.py
python tools\generate.py --check
```

5. Если проверки проходят, закрыть T-029 и перевести `drivers/files.md` в `ready`.

## Update 2026-06-20 - external PowerShell check

Пользователь выполнил проверку в отдельном Windows PowerShell.

Уточнённый результат:

- `python --version` отвечает: `Python 3.11.15`;
- `python -c "import sys, json, sqlite3; ..."` отвечает;
- активный `python` указывает на `C:\Users\stefan\AppData\Local\hermes\hermes-agent\venv\Scripts\python.exe`;
- `sqlite3` доступен (`3.53.1`);
- `py --version` уходит в timeout;
- в системе есть долгоживущие Python-процессы с большим CPU time;
- `Stop-Job -Force` не поддерживается текущим Windows PowerShell, нужна форма `Stop-Job $job`.

Вывод: блокер `T-039` уточнён. Команда `python` уже пригодна для следующего пакета проверок, но `py` launcher и долгоживущие процессы требуют осторожной диагностики. `T-039` остаётся `blocked` до прохождения project validation/test batch.

Подробности: `docs/runtime-powershell-check-2026-06-20.md`.

## Update 2026-06-20 - core runtime validation batch

Пользователь выполнил core runtime validation через `python`:

- `python tools\pipeline.py status` — выполнено;
- `python tools\validate.py` — `OK=8 WARN=0 ERROR=0`;
- `python tools\drivers_catalog.py` — каталог актуален, 7 драйверов;
- `python drivers\mcp_handshake_test.py` — `RESULT OK`.

Вывод: проектный runtime частично восстановлен. Дальше нужно прогнать driver acceptance batch. Подробности: `docs/runtime-validation-batch-2026-06-20.md`.
