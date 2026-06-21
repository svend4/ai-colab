# Каталог драйверов (Treiber)

Генерируется `tools/drivers_catalog.py` из `drivers/*.md` — не править вручную.

| ID | Драйвер | Уровень | Режим | Риск | Статус |
|---|---|---|---|---|---|
| codex-local | Codex local driver — мост к локальной рабочей среде | L1 | manual | medium | ready |
| data | Data driver — таблицы, JSON, SQLite и индексы | L1 | read-only | medium | ready |
| file-inventory | File inventory driver — project file map with metadata and risk flags | L2 | read-only | low | draft |
| files | Files driver — безопасное чтение и инвентаризация файлов | L1 | read-only | low | ready |
| gateway | Gateway — единый MCP над files/repo/workbench (композиция) | L2 | read-only | medium | ready |
| git-log | Git-log driver — read-only история git (коммиты, авторы, история файла) | L2 | read-only | medium | ready |
| repo-runner | Repo runner — inventory репозиториев и будущий запуск в песочнице | L1 | read-only | medium | ready |
| workbench | Workbench DB driver — SQLite-память корпуса и audit log | L2 | safe-write | medium | ready |
