# PowerShell UTF-8 output

Дата: 2026-06-20

Статус: заметка по ручной диагностике Windows PowerShell.

## Наблюдение

Пользователь выполнил:

```powershell
Get-Content -LiteralPath ".\PIPELINE.md"
```

PowerShell показал русские символы как mojibake (`Ð...`, `Ñ...`, `â€”`). При этом JSON-файлы читаются нормально, а `PIPELINE.md` в репозитории остаётся корректным UTF-8.

Вывод: это проблема отображения/декодирования в Windows PowerShell, а не повреждение файла.

## Как читать UTF-8 в Windows PowerShell

В текущей сессии PowerShell выполнить:

```powershell
chcp 65001
[Console]::InputEncoding = [System.Text.UTF8Encoding]::new($false)
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
$OutputEncoding = [Console]::OutputEncoding
```

После этого читать Markdown так:

```powershell
Get-Content -Encoding UTF8 -LiteralPath ".\PIPELINE.md"
Get-Content -Encoding UTF8 -LiteralPath ".\TASKS.md"
Get-Content -Encoding UTF8 -LiteralPath ".\LIVE.md"
```

Если консоль всё равно показывает mojibake, лучше использовать машинные проверки:

```powershell
Get-Content -Raw -Encoding UTF8 -LiteralPath ".\logs\pipeline.json" | ConvertFrom-Json | ConvertTo-Json -Depth 8
```

## Почему это важно

Проект активно использует Markdown с русским текстом. Если Windows PowerShell читает UTF-8 как ANSI/legacy codepage, человек видит повреждённый текст, хотя файл на диске нормальный. Это может привести к ложным исправлениям и лишним правкам.

Правило: перед ручной проверкой русскоязычных `.md` файлов в PowerShell нужно явно включать UTF-8 или использовать редактор, который корректно определяет кодировку.

## Confirmation 2026-06-20

Пользователь выполнил предложенную последовательность:

```powershell
chcp 65001
[Console]::InputEncoding = [System.Text.UTF8Encoding]::new($false)
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
$OutputEncoding = [Console]::OutputEncoding
Get-Content -Encoding UTF8 -LiteralPath ".\PIPELINE.md"
Get-Content -Encoding UTF8 -LiteralPath ".\TASKS.md"
```

Результат: `PIPELINE.md` и `TASKS.md` отобразились корректно на русском языке. Это подтверждает, что проблема была в настройке вывода PowerShell, а не в содержимом файлов.
