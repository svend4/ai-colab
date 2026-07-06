<!-- GENERATED folder_index.py — НЕ редактировать руками; навигация-через-метаданные -->
# Индекс папки `drivers/` — 13 файлов, 10 подпапок

> Машино- и человекочитаемое оглавление визиток (вместо шардинга плоской папки).

## Подпапки

- `drivers/codex-local/`
- `drivers/data/`
- `drivers/file-inventory/`
- `drivers/files/`
- `drivers/gateway/`
- `drivers/git-log/`
- `drivers/repo-runner/`
- `drivers/sqlite/`
- `drivers/workbench/`
- `drivers/workbench-db/`

## Файлы (визитки)

| файл | type | status | суть |
|---|---|---|---|
| [CATALOG.md](../drivers/CATALOG.md) | — | — | Генерируется `tools/drivers_catalog.py` из `drivers/*.md` — не править вручную. |
| [SCHEMA.md](../drivers/SCHEMA.md) | schema | draft | Статус: **draft**. Это рабочее предложение по Q-008, а не финально принятое решение. |
| [_template.md](../drivers/_template.md) | driver | draft | Что драйвер делает и какой источник/программу/данные оборачивает. |
| [codex-local.md](../drivers/codex-local.md) | driver | ready | Мост к локальной рабочей среде Codex на Windows. Проверка статуса, запуск безопасных прове |
| [data.md](../drivers/data.md) | driver | ready | Слой для read-only работы с табличными файлами CSV/TSV: обнаружение таблиц, чтение колонок |
| [file-inventory.md](../drivers/file-inventory.md) | driver | draft | Read-only карта файлов проекта или указанной папки: путь, размер, mtime, тип, MIME, risk f |
| [files.md](../drivers/files.md) | driver | ready | Дать агентам стандартный способ описывать работу с файлами: список, чтение, поиск, краткое |
| [gateway.md](../drivers/gateway.md) | driver | ready | Цель — дать агенту одну точку входа в «средний слой» (файлы + репозитории + память), не по |
| [git-log.md](../drivers/git-log.md) | driver | ready | Read-only доступ к **истории git** репозитория — чтобы AI-агент понимал эволюцию проекта: |
| [repo-runner.md](../drivers/repo-runner.md) | driver | ready | Read-only inventory-драйвер для репозиториев (локальных или GitHub). Не запускает код — то |
| [sqlite.md](../drivers/sqlite.md) | driver | ready | Read-only доступ к **произвольным SQLite-БД** приложений (`.db`/`.sqlite`/`.sqlite3`) внут |
| [workbench-schema.md](../drivers/workbench-schema.md) | — | — | Локальная SQLite-база для L3: повторяемый поиск и отчётность по корпусу документов/репозит |
| [workbench.md](../drivers/workbench.md) | driver | ready | Локальная SQLite-память для корпуса: таблица `documents` хранит обработанные файлы/репозит |
