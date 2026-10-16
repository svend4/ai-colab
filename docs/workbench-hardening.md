# Workbench DB hardening report

Дата: 2026-06-20
Автор: Codex
Связано: `T-031`, `T-052`, `T-054`, `T-055`, `drivers/workbench.md`

## Контекст

Claude закрыл `T-052`: добавлен `drivers/workbench/workbench.py` и `drivers/workbench/test_workbench.py`; done-marker сообщает, что тесты прошли.

Codex перепроверил код статически. В отличие от `files` и `repo-runner`, `workbench` — не read-only driver: он создаёт и изменяет SQLite DB. Поэтому ему нужна более строгая L1/L2-политика: allowed-root для пути БД, лимиты выборок и ограничение bulk ingest.

## Что изменено

В `drivers/workbench/workbench.py`:

- добавлен `PathAccessError`;
- добавлен `resolve_db_path(db_path, base_dir=None)`;
- добавлены разрешённые suffix: `.db`, `.sqlite`, `.sqlite3`;
- `connect()` и `init()` получили `base_dir`;
- CLI использует `WORKBENCH_BASE` как allowed-root и требует её (fail-closed, см. `docs/files-driver-hardening.md`);
- `query_documents()` и `audit()` ограничивают `limit`;
- `ingest_repo()` получил `max_documents`.

В `drivers/workbench/test_workbench.py`:

- добавлены проверки `resolve_db_path`;
- добавлена проверка выхода за `base_dir`;
- добавлена проверка suffix;
- добавлена проверка `max_documents`;
- добавлена проверка capped query limit.

Добавлен `drivers/workbench.md`:

- `mode: safe-write`;
- `risk: medium`;
- `audit: true`;
- `sandbox: workspace-write-only`.

## Что осталось не проверено

Codex не запускал Python-тесты из-за `T-039`. Нужна runtime-приёмка `T-055`:

```powershell
python drivers\workbench\test_workbench.py
python tools\validate.py
python tools\generate.py --check
```

Дополнительно после восстановления runtime:

- проверить CLI `init/list/audit`;
- проверить `WORKBENCH_BASE`;
- проверить, что `drivers/workbench.md` проходит driver schema validation;
- решить, нужен ли MCP-wrapper для workbench сразу или после FTS/chunks.

## Мнение Codex

`workbench.db` — важный шаг от “папка с Markdown” к рабочей памяти проекта. Но именно потому, что это память, её нельзя оставлять как произвольную запись в любой путь. Текущая версия теперь ближе к безопасному L2: запись ограничивается зоной, выдача ограничивается лимитами, bulk ingest не может бесконечно разрастись за один вызов.

Следующий инженерный шаг после runtime-приёмки — не сразу MCP, а FTS/chunks plan: понять, какие поля индексировать и как связать `documents` с извлечённым текстом.

