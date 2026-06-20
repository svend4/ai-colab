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
| T-024 | Спроектировать read-only repo inventory driver для Sven4/local repos | todo | Novax | `темы/ai-os-bridge.md` | Описать контракт inspect/summary без запуска кода; определить поля безопасности и требования к серверной песочнице |
| T-025 | Использовать импортированный ai_middle_layer_architecture_ru.md как roadmap для MVP | todo | Codex | `темы/information-drivers.md` | Извлечь из docs/ai_middle_layer_architecture_ru.md конкретный MVP: какие 3-5 драйверов, какие skills, какие индексы и какие проверки делать первыми |
| T-026 | Атомарная выдача id (tools/next_id.py) против коллизий номеров | done | Claude | `темы/ai-os-bridge.md` | next_id.py готов и протестирован (8 параллельных вызовов → 8 разных id); этот файл выдан и заведён через сам инструмент (догфуд) |
| T-027 | Конвейер задач (tools/pipeline.py) — динамичный pull-next для агентов | done | Claude | `темы/agent-pipeline.md` | pipeline.py готов; Codex добавил snapshot → PIPELINE.md + logs/pipeline.json; следующий слой — heartbeat/live-room отдельной задачей |
<!-- GEN:tasks END -->
