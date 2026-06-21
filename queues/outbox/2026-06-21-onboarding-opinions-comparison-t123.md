# T-123 — comparison of onboarding/manual opinions

Сравнил свежие варианты обзора системы:

- `docs/agent-onboarding.md`;
- `docs/top-agent-operating-manual.md`;
- `docs/architecture-docs-recheck-2026-06-21.md`;
- `docs/bridge-usage.md`;
- `docs/layers-coverage.md`;
- задачи `T-120`, `T-121`, `T-122`.

Создан чистовой документ:

- `docs/onboarding-opinions-comparison-2026-06-21.md`.

После первичного сравнения обнаружен параллельный синтез Claude:

- `темы/opinion-synthesis-2026-06-21.md`;
- `T-129` — capability manifest уже реализован;
- `T-130` — drift detector;
- `T-131` — onboard-команда;
- `Q-014` — домен юридического workbench vs generic-инструмент.

Главный вывод: документы не противоречат в основе. Они смотрят на один объект с разных уровней:

- `agent-onboarding.md` — удобный вход для человека/нового агента;
- `top-agent-operating-manual.md` — операционная карта и micro-skills для агента;
- `architecture-docs-recheck-2026-06-21.md` — оценка стадии относительно ранней концепции.

Консенсусные пункты заведены в очередь:

- `T-124` — quickstart pipeline cleanup;
- `T-129` — system capabilities manifest, уже done;
- `T-130` — docs drift detector;
- `T-127` — larger safe corpus;
- `T-131` — `tools/onboard.py`.

Дубли `T-125`, `T-126`, `T-128` закрыты как merged/duplicate, чтобы не засорять pipeline.

Спорные пункты вынесены в `Q-013`:

- один чистовой документ или два связанных;
- worktree/ветка на агента сейчас или позже;
- баланс автоматизации середины и реальных данных;
- L5 plugin packaging сейчас или позже;
- что делать с `T-020` / svend4.
- отдельный вопрос `Q-014`: цель проекта — юридический workbench или generic-инструмент.

Моё мнение: ближайшее развитие должно быть не новым большим философским документом, а малой автоматизацией входа и проверкой на реальном read-only corpus. Execute/svend4 нельзя ускорять без sandbox decision.
