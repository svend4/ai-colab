# T-133 text-extract — отчёт Codex

Дата: 2026-06-21.
Агент: Codex.
Связано: `T-133`, `D-016`, `tools/text_extract.py`, `tools/knowledge.py`, `topics/opinion-synthesis-2026-06-21.md`.

## Что сделано

- Добавлен `tools/text_extract.py`: read-only извлечение текста для `.md`, `.markdown`, `.txt`, `.text`, `.html`, `.htm`.
- Подключено к `tools/knowledge.py`: `build/report/search` теперь индексируют содержимое документа через `text_extract`, а не только первую непустую строку.
- Добавлен `tools/test_text_extract.py`.
- Расширен `tools/test_knowledge.py`: проверяется поиск термина из тела Markdown-документа (`PortalNeedle`) через FTS.

## Почему так

Это закрывает практический пробел D1 из синтеза мнений. `text-extract` не должен быть доменной функцией юридического портала или svend4: это универсальная способность ядра. Любой тематический портал получает одинаковый путь:

`файл -> redacted text -> SQLite/FTS -> report/search`.

Я сознательно начал со stdlib-форматов `.md/.txt/.html`, потому что они безопасны, воспроизводимы и не требуют внешних зависимостей. PDF/DOCX оставлены следующим шагом: там нужен отдельный выбор парсера, тестовый corpus и решение о зависимости.

## Проверка

```powershell
python tools\test_text_extract.py
python tools\test_knowledge.py
python tools\test_portal.py
python tools\validate.py
```

Результат: все проверки прошли.

## Что дальше

- Для T-137: согласовать DOCX/PDF стратегию. DOCX можно попробовать через stdlib `zipfile`; PDF лучше не делать самодельно без решения о зависимости.
- Для C4: взять безопасный corpus 50-200 файлов и сравнить отчёты до/после.
- Для D3: не строить ещё один крупный слой, пока не появится реальный corpus и повторяемый спрос.