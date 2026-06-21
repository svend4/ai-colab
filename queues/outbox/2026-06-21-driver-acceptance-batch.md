# Outbox: driver acceptance batch prepared

Адресаты: люди, AI-агенты, reviewer, summarizer.

Связанный документ: `docs/driver-acceptance-batch-2026-06-21.md`.

## Кратко

Подготовлен воспроизводимый PowerShell checklist для следующего этапа после core runtime validation.

Пакет включает:

- core sanity repeat: `validate.py`, `drivers_catalog.py`;
- driver tests: `files`, `repo-runner`, `workbench`, `workbench-db`, `file-inventory`;
- pipeline guards: `ready_sorted == []`, `T-020` как `doing without active claim`;
- MCP smoke: `drivers/mcp_handshake_test.py`.

## Что нужно сделать

Запустить команды из `docs/driver-acceptance-batch-2026-06-21.md` в Windows PowerShell и вернуть вывод.

После успешного batch можно закрывать зависимые runtime-задачи.

