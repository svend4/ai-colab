# workbench.db — схема (дизайн, T-031)

Локальная SQLite-база для L3: повторяемый поиск и отчётность по корпусу документов/репозиториев и аудит работы агентов. Это **дизайн схемы**, без реализации. Заполняется драйверами (inventory → `documents`) и конвейером/инструментами (события → `audit_log`).

## Таблица `documents`

Одна строка — один обработанный артефакт (файл, репозиторий, выгрузка).

| Поле | Тип | Назначение |
|---|---|---|
| `id` | INTEGER PRIMARY KEY | внутренний id |
| `source` | TEXT | источник (`local`, `svend4`, `repo:<name>`) |
| `path` | TEXT | путь/URL артефакта (уникален вместе с `source`) |
| `type` | TEXT | `file` / `repo` / `dataset` / `doc` |
| `lang` | TEXT | язык/языки (для кода и текста) |
| `summary` | TEXT | краткое описание (из драйвера-инвентаризатора) |
| `size_bytes` | INTEGER | размер |
| `risk` | TEXT | `low`/`medium`/`high` (из risk-report драйвера) |
| `source_last_verified` | TEXT (ISO date) | когда последний раз сверяли с источником (детекция дрейфа, как в манифесте драйвера) |
| `created_at` | TEXT (ISO ts) | когда занесён |

Индексы: `UNIQUE(source, path)`; `INDEX(type)`; `INDEX(risk)`.

## Таблица `audit_log`

Append-only журнал действий (кто/что/над чем) — машинный аудит в дополнение к `dialog.md`.

| Поле | Тип | Назначение |
|---|---|---|
| `id` | INTEGER PRIMARY KEY | |
| `ts` | TEXT (ISO ts) | время события |
| `agent` | TEXT | кто (`Claude`/`Codex`/`Mavis`/`Novax`/`pool`) |
| `action` | TEXT | `claim`/`done`/`fail`/`inventory`/`run`/`edit` |
| `target` | TEXT | над чем (`T-030`, `documents:42`, путь) |
| `detail` | TEXT | произвольная заметка/отчёт |

Индексы: `INDEX(ts)`; `INDEX(agent)`; `INDEX(action)`.

## Как ложится на существующее

- **Драйвер-инвентаризатор** (`repo-runner`, будущий `files`) выдаёт JSON → строки `documents` (path/type/lang/summary/risk/size). `repo-runner/inventory.py` уже даёт нужную структуру.
- **Конвейер** (`pipeline.py`) — события `claim/done/fail` ложатся в `audit_log` (агент уже пишет per-task done-маркеры; их можно зеркалить в БД).
- **Детекция дрейфа** — поле `source_last_verified` совпадает с одноимённым полем манифеста драйвера (Q-008/B): один принцип на уровне файла и базы.

## Границы (что НЕ входит)

- Реализация (создание БД, ORM, миграции) — отдельная задача после принятия схемы.
- Векторный поиск/эмбеддинги (L3+, RAG) — отдельный слой; здесь только реляционный каркас.
- Запуск кода из репозиториев — только после песочницы (D-010), не часть схемы.

Источник правды по статусу: задача `T-031`. Связано: `темы/ai-os-bridge.md`, `docs/middle-layer-guide.md` (§ слой 6 — память/знания), `drivers/repo-runner.md`.
