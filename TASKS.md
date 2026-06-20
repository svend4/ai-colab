# Задачи

Общая доска задач. Для обсуждения деталей создавайте файл или папку в `темы/` и ставьте ссылку в колонке "Тема".

## Правила

- Одна строка = одна конкретная задача.
- Статусы: `todo`, `doing`, `blocked`, `review`, `done`.
- Если задача требует решения, добавьте вопрос в `QUESTIONS.md`.
- Если по задаче принято архитектурное или организационное решение, добавьте запись в `DECISIONS.md`.

## Список задач

<!-- GEN:tasks START — генерируется tools/generate.py из tasks/*.md, не править вручную -->
| ID | Задача | Статус | Ответственный | Тема | Следующий шаг |
|---|---|---|---|---|---|
| T-001 | Проверить удобство структуры папки для полилога | done | все | `темы/example.md` | Подтверждено реальной нагрузкой сессии; крупные темы → папочный режим D-002 |
| T-002 | Определить правила именования файлов и тем | done | все | `темы/organization.md` | Закрыто D-005 — новые файлы в ASCII, русский текст в заголовке |
| T-003 | Проверить протокол для многих AI-агентов и скриптов | done | Claude | `queues/outbox/2026-06-19-2044-smoke-test-result.md` | Смоук-тест очереди пройден; ограничения и right-size задокументированы |
| T-004 | Проверить механику захвата задач через queues/claimed/ | done | Claude | `queues/outbox/2026-06-19-2044-smoke-test-result.md` | Claim создан; claimed/ не атомарен (нет TTL) — доработка в T-008+ |
| T-005 | Постепенно мигрировать русские имена файлов к ASCII (D-007) | done | Novax | `темы/migrate-file-names.md` | Задача выполнена — все 5 русских имён мигрированы, ссылки обновлены, канон 0 ERROR |
| T-006 | Сделать валидатор целостности Markdown-инфраструктуры | done | Claude | `темы/infrastructure-review.md` | tools/validate.py готов и прогнан на Windows (0 ERROR, commit 572ffa3) |
| T-007 | Генератор навигации (STATUS/Доска из front-matter) | done | Claude | `темы/infrastructure-review.md` | tools/generate.py + front-matter тем + маркеры GEN; в hook добавлен --check |
| T-008 | Шардировать реестры (задачи, вопросы, решения) | done | Claude | `темы/scaling-design.md` | Реестры шардированы; TASKS/QUESTIONS/DECISIONS — генерируемые индексы из tasks|questions|decisions/*.md |
| T-009 | Очередь 2.0 — атомарный claim (TTL + fencing) и tools/queue.py | done | Claude | `темы/scaling-design.md` | queue.py готов и самопроверен; далее — шардинг questions/decisions или валидатор v2 |
| T-010 | Валидатор v2 — проверка файлов-источников и depends_on | done | Claude | `темы/scaling-design.md` | check_sources ловит битый front-matter, дубли id, депенды; queue.py check — для очереди |
| T-011 | Машинный индекс index.json для агентов | done | Claude | `темы/scaling-design.md` | index.json генерится из front-matter, --check контролирует свежесть; Codex верифицировал и задокументировал |
| T-012 | Роли и path-права (permissions.py) | done | Claude | `темы/scaling-design.md` | permissions.py + permissions.json проверяют, что агент пишет в свою зону; совещательный guard (не безопасность) |
| T-013 | Git-flow для агентов (flow.py) | done | Claude | `темы/scaling-design.md` | flow.py печатает команды ветка-на-агента + merge-гейт (validate/generate/permissions); --run выполняет |
| T-014 | Диспетчер задач по DAG (dispatch.py) | done | Claude | `темы/scaling-design.md` | dispatch.py показывает готовые/заблокированные по depends_on; next — топ по приоритету |
| T-015 | Риск-гейтинг / многоуровневая автономия (risk_gate.py) | done | Claude | `темы/scaling-design.md` | risk_gate.py — low→AUTO, medium→REVIEW, high→HUMAN; чтобы D-006 не стал горлышком |
| T-016 | Метрики/наблюдаемость канона (metrics.py) | done | Claude | `темы/scaling-design.md` | metrics.py — сводка по задачам/вопросам/решениям/темам/очереди; --json |
| T-017 | Создать глоссарий терминов канона (docs/glossary.md) | done | Mavis | `темы/dogfood-run.md` | Выполнено Mavis: docs/glossary.md создан; done-маркеры очереди есть |
| T-018 | Создать quickstart-руководство (docs/quickstart.md) | done | Novax | `темы/dogfood-run.md` | Выполнено Novax: docs/quickstart.md создан; done-маркер очереди есть |
| T-019 | Эмпирически проверить атомарность claim под реальной гонкой | done | Claude | `темы/dogfood-run.md` | Прогнано вживую на Windows (8 параллельных claim → 1 победитель, 7 RACE/BUSY); tools/race_test.py поддерживает повторы [N] [раунды] |
| T-020 | AI-OS Bridge — исследовать репозитории svend4 и спроектировать коннектор | doing | Novax | `темы/ai-os-bridge.md` | Q-007 закрыт D-010; дальше — read-only repo inventory driver (T-024) и фактический список/доступ к репозиториям Sven4 |
| T-021 | Технический разбор слоя драйверов (design-документ) | done | Claude | `темы/ai-os-bridge.md` | docs/agent-layer-design.md готов (MCP/skills-framing, каталог драйверов, L0–L4, риски, план); вынесено на голос в Q-007 — рекомендация B + коннекторы как MCP + Sven4 read-only |
| T-022 | Создать L1-каталог drivers/ и первые манифесты драйверов | done | Codex | `темы/ai-os-bridge.md` | L1-каркас создан: README, шаблон, files/data/repo-runner/codex-local; дальше T-023 индекс драйверов |
| T-023 | Добавить машинный индекс драйверов в generate.py/index.json | done | Codex | `темы/ai-os-bridge.md` | Выполнено: generate.py добавляет drivers в корневой index.json; расширенная schema остаётся Q-008 |
| T-024 | Спроектировать read-only repo inventory driver для Sven4/local repos | done | Novax | `темы/ai-os-bridge.md` | Описать контракт inspect/summary без запуска кода; определить поля безопасности и требования к серверной песочнице |
| T-025 | Использовать импортированный ai_middle_layer_architecture_ru.md как roadmap для MVP | done | Codex | `темы/information-drivers.md` | Извлечь из docs/ai_middle_layer_architecture_ru.md конкретный MVP: какие 3-5 драйверов, какие skills, какие индексы и какие проверки делать первыми |
| T-026 | Атомарная выдача id (tools/next_id.py) против коллизий номеров | done | Claude | `темы/ai-os-bridge.md` | next_id.py готов и протестирован (8 параллельных вызовов → 8 разных id); этот файл выдан и заведён через сам инструмент (догфуд) |
| T-027 | Конвейер задач (tools/pipeline.py) — динамичный pull-next для агентов | done | Claude | `темы/agent-pipeline.md` | pipeline.py готов; Codex добавил snapshot → PIPELINE.md + logs/pipeline.json; следующий слой — heartbeat/live-room отдельной задачей |
| T-028 | Добавить добровольный heartbeat/live-room в pipeline.py | done | Codex | `темы/agent-pipeline.md` | Реализовано: pipeline.py heartbeat, LIVE.md, logs/heartbeat.json, per-agent logs/heartbeat/*.json |
| T-029 | Реализовать read-only files inventory driver | blocked | Codex | `темы/ai-os-bridge.md` | Реализация создана; заблокировано проверкой — Python runtime зависает даже на print('ok'), нужно повторить drivers/files/test_inventory.py и validate/generate |
| T-030 | Генератор каталога драйверов (drivers/index.json + CATALOG.md) | done | pool | `темы/ai-os-bridge.md` | tools/drivers_catalog.py — собрать drivers/index.json + CATALOG.md из drivers/*.md front-matter |
| T-031 | Спроектировать workbench.db schema (SQLite documents + audit_log) | done | pool | `темы/ai-os-bridge.md` | Схема SQLite — таблицы documents (id, path, type, summary, source_last_verified) и audit_log (ts, agent, action, target); только дизайн + обоснование, без кода |
| T-032 | Карта покрытия слоёв L0–L8 (docs/layers-coverage.md) | done | pool | `темы/ai-os-bridge.md` | docs/layers-coverage.md — таблица: какой слой L0–L8 чем покрыт в проекте и что не хватает |
| T-033 | Список L2-кандидатов — первые MCP-драйверы (docs/l2-candidates.md) | done | pool | `темы/ai-os-bridge.md` | Выполнено: docs/l2-candidates.md создан; рекомендация — files первым L2 PoC после разблокировки T-029, repo-runner как fallback |
| T-034 | Написать operator guide для pipeline/live-room | done | pool | `темы/agent-pipeline.md` | docs/pipeline-operator-guide.md — короткий порядок next/done/fail/snapshot/heartbeat и правила, когда брать новую задачу |
| T-035 | Матрица ролей агентов и границ ответственности | done | pool | `темы/ai-os-bridge.md` | Выполнено: docs/agent-roles-matrix.md создан; использовать вместе с AGENTS.md и tools/permissions.json |
| T-036 | Draft safety policy для драйверов и больших папок | done | pool | `темы/ai-os-bridge.md` | docs/driver-safety-policy.md — read-only-first, dry-run, audit, no secrets, no execute without decision |
| T-037 | План data/ структуры для workbench-корпуса | done | pool | `темы/ai-os-bridge.md` | Выполнено: docs/data-folder-plan.md создан; следующий шаг — data/README.md и fixtures перед реальным импортом |
| T-038 | План тестового корпуса для драйверов | done | pool | `темы/ai-os-bridge.md` | docs/test-corpus-plan.md — 10-20 безопасных fixture-файлов, сценарии проверки files/text/search/report drivers |
| T-039 | Разблокировать Python runtime и закрыть T-029 | blocked | pool | `темы/ai-os-bridge.md` | Диагностика в docs/runtime-diagnostics.md; нужен внешний перезапуск/разбор зависших процессов, затем повторить Python checks |
| T-040 | Создать data/README.md по data-folder-plan | done | pool | `темы/ai-os-bridge.md` | Выполнено: data/README.md создан; теперь можно делать T-041 fixture-корпус |
| T-041 | Создать минимальный безопасный fixture-корпус | done | pool | `темы/ai-os-bridge.md` | Выполнено: data/fixtures/README.md и 7 synthetic fixture-файлов созданы |
| T-042 | Подготовить D-013 proposal по Q-008 driver schema v1 | done | pool | `темы/ai-os-bridge.md` | Выполнено: decisions/D-013.md создан со статусом proposed; Q-008 обновлён и остаётся open до accepted |
| T-043 | Реализовать рабочий read-only files driver + тесты | done | pool | `темы/ai-os-bridge.md` | drivers/files/files_driver.py — list/read/search/summarize (read-only, лимиты по safety-policy) + drivers/files/test_files.py |
| T-044 | Описать expected inventory для data/fixtures | done | pool | `темы/ai-os-bridge.md` | Выполнено: data/fixtures/EXPECTED.md создан |
| T-045 | Checklist принятия D-013 driver schema v1 | done | pool | `темы/ai-os-bridge.md` | Выполнено: docs/driver-schema-acceptance-checklist.md создан; D-013 остаётся proposed |
<!-- GEN:tasks END -->
