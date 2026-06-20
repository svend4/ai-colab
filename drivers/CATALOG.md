# Каталог драйверов (Treiber)

Генерируется `tools/drivers_catalog.py` из `drivers/*.md` — не править вручную.

| ID | Драйвер | Уровень | Режим | Риск | Статус |
|---|---|---|---|---|---|
| codex-local | Codex local driver — мост к локальной рабочей среде | L1 | manual | medium | draft |
| data | Data driver — таблицы, JSON, SQLite и индексы | L1 | read-only | medium | draft |
| files | Files driver — безопасное чтение и инвентаризация файлов | L1 | read-only | low | draft |
| repo-runner | Repo runner — inventory репозиториев и будущий запуск в песочнице | L1 | read-only | medium | ready |
