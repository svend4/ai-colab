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
- `agent-onboarding.md` — present-tense чистовик для человека/агента: что система умеет сейчас, роли, карта документации, Q&A, зрелость и идеи развития.
- `top-agent-operating-manual.md` — чистовая инструкция для человека или AI-агента на "вершине пирамиды": metadata, функции, Q&A, проблемы коллективной работы, микро-инструкции и roadmap автоматизации.
- `onboarding-opinions-comparison-2026-06-21.md` — сравнение свежих обзоров/мнений (`agent-onboarding`, `top-agent-operating-manual`, architecture recheck): консенсус, расхождения, очередь T-124..T-128 и вопрос Q-013.
- `l2-candidates.md` — приоритетный список первых L2/MCP-кандидатов: `files` первым после T-029, `repo-runner` как fallback, затем `data` и `codex-local`.
- `layers-coverage.md` — карта покрытия слоёв L0-L7: что уже есть, где пробелы, какие следующие шаги.
- `pipeline-operator-guide.md` — практический порядок работы с pipeline/live-room.
- `agent-roles-matrix.md` — матрица ролей людей, AI-агентов и скриптов: зоны записи, запреты, типовые задачи, эскалация и цикл pool-задачи.
- `commit-stream-policy.md` — политика commit/streams: как не коммитить чужую half-done работу и как вести параллельные варианты перед mainline.
- `workspace-pyramid-levels.md` — модель 4 уровней папок: `core/` как переносимое ядро, `portals/` как чистовые специализированные области, `collab/` как история/полилог, `sandbox/` как входной хаос.
- `driver-safety-policy.md` — правила безопасности для драйверов и больших папок.
- `external-code-sandbox.md` — универсальная схема `sandbox/` для внешнего кода и старых долгов вроде `svend4`: intake, quarantine, read-only inventory, workspaces, reports, execute gate.
- `data-folder-plan.md` — план будущей `data/` структуры для корпуса: inbox/originals/copies/text/chunks/indexes/reports/audit/workbench.db и правила записи.
- `test-corpus-plan.md` — план маленького безопасного fixture-корпуса для проверки `files`, `text-extract`, `search-index`, `report`.
- `runtime-diagnostics.md` — диагностика блокировки внешних процессов/Python runtime, которая держит T-029/T-039 blocked.
- `driver-schema-acceptance-checklist.md` — checklist перед переводом D-013 из `proposed` в `accepted`.
- `agent-layer-design.md` — технический разбор слоя драйверов/Treiber/MCP и вариантов L0-L4.
- `glossary.md` — глоссарий канона проекта.
- `quickstart.md` и `agent-quickstart.md` — быстрый старт для людей и агентов.
