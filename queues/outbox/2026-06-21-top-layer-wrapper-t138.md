# T-138 — top command panel

Дата: 2026-06-21.
Агент: Codex.
Связано: `tools/top.py`, `tools/test_top.py`, `docs/top-layer-command-groups.md`.

## Что сделано

Добавлен `tools/top.py` — верхняя обёртка команд для людей и агентов.

Основные сценарии:

- `buttons` — показать “кнопки”/группы действий;
- `status` — git status + pipeline + drift;
- `health` — validate + generate --check + capabilities --check + drivers_catalog --check;
- `agent-start` — onboarding агента;
- `take` — взять задачу через pipeline;
- `snapshot` — обновить производные снимки;
- `knowledge` — собрать report по corpus;
- `cycle` — показать безопасный цикл работы агента.

## Почему так

Проблема верхнего слоя была не в отсутствии функций, а в том, что они разложены по разным командам. `top.py` делает их сценариями, которые можно использовать как кнопки. Это удобно человеку и агенту одновременно: человек видит смысл действия, агент получает стабильный CLI-контракт.

## Проверка

```powershell
python tools\test_top.py
python tools\top.py buttons
python tools\top.py health
python tools\validate.py
python tools\generate.py --check
```

## Дальше

Следующий уровень — не переписывать `top.py`, а использовать его JSON-кнопки как вход для GUI/MCP/web-панели или для автоматического “agent console”.