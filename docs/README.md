# Документация

В этой папке хранится документация проекта: требования, архитектура, API, инструкции, заметки по установке.

Рекомендуемая структура:

```text
docs/
  requirements.md
  architecture.md
  api.md
  setup.md
```

Правило: обсуждение ведем в `темы/`, а в `docs/` переносим уже очищенный и согласованный материал.

## Текущие важные документы

- `ai_middle_layer_architecture_ru.md` — импортированный архитектурный документ о промежуточном слое между Codex, Windows, GitHub/сервером и большой базой информации. Используется как опорный источник для AI-OS Bridge, `drivers/` и следующих задач T-023..T-025.
- `mvp-roadmap.md` — практический MVP-roadmap из импортированного документа: стадия проекта, плюсы/минусы, первые драйверы, SQLite-память, проверки и следующий слой работ.
- `l2-candidates.md` — приоритетный список первых L2/MCP-кандидатов: `files` первым после T-029, `repo-runner` как fallback, затем `data` и `codex-local`.
- `layers-coverage.md` — карта покрытия слоёв L0-L8: что уже есть, где пробелы, какие следующие шаги.
- `pipeline-operator-guide.md` — практический порядок работы с pipeline/live-room.
- `agent-roles-matrix.md` — матрица ролей людей, AI-агентов и скриптов: зоны записи, запреты, типовые задачи, эскалация и цикл pool-задачи.
- `driver-safety-policy.md` — правила безопасности для драйверов и больших папок.
- `data-folder-plan.md` — план будущей `data/` структуры для корпуса: inbox/originals/copies/text/chunks/indexes/reports/audit/workbench.db и правила записи.
- `test-corpus-plan.md` — план маленького безопасного fixture-корпуса для проверки `files`, `text-extract`, `search-index`, `report`.
- `runtime-diagnostics.md` — диагностика блокировки внешних процессов/Python runtime, которая держит T-029/T-039 blocked.
- `agent-layer-design.md` — технический разбор слоя драйверов/Treiber/MCP и вариантов L0-L4.
- `glossary.md` — глоссарий канона проекта.
- `quickstart.md` и `agent-quickstart.md` — быстрый старт для людей и агентов.
