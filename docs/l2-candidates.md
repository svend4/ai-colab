# L2 Candidates: First MCP / Tool Drivers

Дата: 2026-06-20
Связано: `drivers/`, `drivers/SCHEMA.md`, `docs/mvp-roadmap.md`, `tasks/T-033.md`

## Цель

Выбрать первый практический L2-кандидат: драйвер, который можно превратить из L1 Markdown-манифеста в настоящий локальный read-only tool или MCP-инструмент.

Критерии:

- read-only по умолчанию;
- низкий риск испортить данные;
- высокая польза для агентов;
- понятный JSON-выход;
- не требует секретов;
- можно тестировать на маленьких fixture-папках;
- не требует сервера на первом шаге.

## Приоритетный список

| Приоритет | Драйвер | Режим | Риск | Почему полезен | Главный риск | Условие старта |
|---|---|---|---|---|---|---|
| 1 | `files` | read-only | low | Базовая карта больших папок: пути, типы, размеры, hash, summary; L2-draft engine и MCP-wrapper уже есть (`T-043`, `T-046`, `T-047`) | Python runtime сейчас нестабилен, runtime acceptance заблокирован | Закрыть `T-039`, затем выполнить `T-048` |
| 2 | `repo-runner` | read-only | medium | Уже есть inventory для репозиториев; полезно для Sven4/local repos | Нельзя переходить к `run/test` без sandbox | Оставить только inspect/summarize/risk-report |
| 3 | `data` | read-only | medium | Нужен для SQLite/CSV/JSON и будущего `workbench.db` | SQL/write/migrations должны быть запрещены | Сначала создать schema `documents` + `audit_log` |
| 4 | `codex-local` | manual/read-only | medium | Может дать статус рабочей папки, checks, summary изменений | Риск слишком широкого доступа к окружению Codex | Ограничить списком разрешённых команд |

## Рекомендация

Первый L2 PoC остаётся **`files`**. Кодовая часть уже продвинулась дальше первичного плана: есть engine, MCP-wrapper и hardening. Но статус не должен становиться `ready`, пока не удаётся стабилизировать Python runtime и выполнить `T-048`. Это самый безопасный и универсальный слой: без карты файлов нельзя уверенно строить text extraction, search index, reports и SQLite memory.

Если Python runtime остаётся заблокированным, временный первый L2 PoC можно делать на **`repo-runner`**, потому что у него уже есть рабочий read-only contract и тесты от Novax. Но важно не расширять его до запуска кода.

## Минимальный контракт `files` L2

```text
inventory(path, max_files=1000, include_hidden=false, hash=false)
```

Выход:

```json
{
  "path": "...",
  "mode": "read-only",
  "summary": {
    "total_files": 0,
    "total_dirs": 0,
    "total_size_bytes": 0,
    "extensions": {},
    "kinds": {}
  },
  "files": []
}
```

Запрещено:

- delete;
- rename;
- move;
- write into scanned folder;
- upload/send to internet;
- execute files;
- read secrets intentionally.

## Минимальный контракт `repo-runner` L2

```text
inspect(repo_path)
detect_tests(repo_path)
summarize(repo_path)
risk_report(repo_path)
```

Запрещено:

- `install`;
- `run`;
- `test`;
- shell execution;
- network access;
- Docker/container start.

## Решение для следующего шага

Практичный порядок:

1. Разблокировать `T-039`.
2. Выполнить `T-048`: `test_files.py`, `test_inventory.py`, MCP handshake/tools-list/call, `validate.py`, `generate.py --check`.
3. Если всё проходит, закрыть `T-029` и обсудить перевод `drivers/files.md` из `draft`.
4. Только после этого расширять MCP metadata и подключение к внешним клиентам как стабильный драйвер.
