# indexes/ — слой навигации (вместо шардинга)

> GENERATED `tools/folder_index.py` — НЕ редактировать руками.

Машино- и человекочитаемые **папка-индексы**: одно оглавление визиток (id/type/status/суть) на крупную
папку, чтобы не листать сотни файлов и **не резать плоскую структуру** (решение
`topics/navigation-vs-sharding-2026-06-24.md`: шардинг не нужен — машине плоско всё равно, навигацию
решают метаданные).

- `tasks.md`, `decisions.md`, `questions.md`, `docs.md`, `topics.md`, `drivers.md` — индексы папок.
- Пересборка: `python tools/folder_index.py write-all`. Проверка актуальности: `… check-all`
  (входит в блок `structure`).
- Дополняет: визитка файла (`header.py`), индекс команд (`command_index.py`), канон-индекс (`index.json`).
