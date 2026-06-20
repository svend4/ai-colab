# data/fixtures/

Минимальный безопасный тестовый корпус для драйверов `files`, будущего `text-extract`, `search-index` и `report`.

Все файлы здесь synthetic/test data. Не добавлять реальные персональные, медицинские, юридические или секретные документы.

## Состав

- `sample-doc.md` — Markdown-документ с заголовками.
- `sample-notes.txt` — простой текст.
- `sample-data.json` — структурированный JSON.
- `sample-table.csv` — маленькая таблица.
- `nested/topic-summary.md` — вложенный Markdown.
- `nested/case-outline.txt` — вложенный текстовый план.
- `.hidden-note.txt` — hidden-file для проверки `include_hidden`.

## Ожидаемые проверки

- `files` видит обычные файлы и вложенные папки.
- `files` по умолчанию пропускает `.hidden-note.txt`.
- `files --include-hidden` включает `.hidden-note.txt`.
- `--hash` создаёт SHA-256 для маленьких файлов.
- будущий `text-extract` извлекает текст из `.md`, `.txt`, `.json`, `.csv`.
- будущий `report` может собрать краткий отчёт по типам файлов.

