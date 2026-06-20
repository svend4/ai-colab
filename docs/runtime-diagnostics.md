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

