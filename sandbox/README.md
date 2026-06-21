# Sandbox workspace

`sandbox/` — уровень L4: входной хаотичный материал, внешние источники и quarantine.

`sandbox/` — локальная рабочая зона для внешнего кода, внешних репозиториев и экспериментальных источников.

Она универсальна: не привязана к `svend4`, одной персоне или одному домену. Любой внешний источник сначала проходит здесь intake и read-only inventory. Запуск кода запрещён до отдельного accepted decision и preflight.

## Структура

| Папка | Назначение | В Git |
|---|---|---|
| `inbox/` | manifests и первичная регистрация источников | только README |
| `sources/` | сырые внешние архивы/клоны/копии | нет |
| `workspaces/` | disposable рабочие копии для анализа/экспериментов | нет |
| `runs/` | raw runtime logs будущих запусков | нет |
| `reports/` | очищенные sandbox summaries | только README; важные отчёты можно переносить в общий `reports/` |
| `templates/` | шаблоны source manifest и run plan | да |

## Правило по умолчанию

```text
external source -> manifest -> quarantine -> read-only inventory -> report -> decision
```

Не запускать install/test/build scripts из внешнего кода, пока не закрыт `docs/execute-sandbox-preflight.md`.

## Где читать подробнее

- `docs/external-code-sandbox.md` — концепция и процесс.
- `docs/execute-sandbox-preflight.md` — gate перед любым execute.
- `sandbox/templates/external-source-manifest.template.json` — как описать источник.
- `sandbox/templates/sandbox-run-plan.template.json` — как описать будущий разрешённый запуск.
