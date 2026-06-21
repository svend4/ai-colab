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
| T-029 | Реализовать read-only files inventory driver | done | Codex | `темы/ai-os-bridge.md` | Выполнено: files inventory driver проверен Batch B; L2 MCP-приёмка продолжается отдельно в T-048 |
| T-030 | Генератор каталога драйверов (drivers/index.json + CATALOG.md) | done | pool | `темы/ai-os-bridge.md` | tools/drivers_catalog.py — собрать drivers/index.json + CATALOG.md из drivers/*.md front-matter |
| T-031 | Спроектировать workbench.db schema (SQLite documents + audit_log) | done | pool | `темы/ai-os-bridge.md` | Схема SQLite — таблицы documents (id, path, type, summary, source_last_verified) и audit_log (ts, agent, action, target); только дизайн + обоснование, без кода |
| T-032 | Карта покрытия слоёв L0–L8 (docs/layers-coverage.md) | done | pool | `темы/ai-os-bridge.md` | docs/layers-coverage.md — таблица: какой слой L0–L8 чем покрыт в проекте и что не хватает |
| T-033 | Список L2-кандидатов — первые MCP-драйверы (docs/l2-candidates.md) | done | pool | `темы/ai-os-bridge.md` | Выполнено: docs/l2-candidates.md создан; рекомендация — files первым L2 PoC после разблокировки T-029, repo-runner как fallback |
| T-034 | Написать operator guide для pipeline/live-room | done | pool | `темы/agent-pipeline.md` | docs/pipeline-operator-guide.md — короткий порядок next/done/fail/snapshot/heartbeat и правила, когда брать новую задачу |
| T-035 | Матрица ролей агентов и границ ответственности | done | pool | `темы/ai-os-bridge.md` | Выполнено: docs/agent-roles-matrix.md создан; использовать вместе с AGENTS.md и tools/permissions.json |
| T-036 | Draft safety policy для драйверов и больших папок | done | pool | `темы/ai-os-bridge.md` | docs/driver-safety-policy.md — read-only-first, dry-run, audit, no secrets, no execute without decision |
| T-037 | План data/ структуры для workbench-корпуса | done | pool | `темы/ai-os-bridge.md` | Выполнено: docs/data-folder-plan.md создан; следующий шаг — data/README.md и fixtures перед реальным импортом |
| T-038 | План тестового корпуса для драйверов | done | pool | `темы/ai-os-bridge.md` | docs/test-corpus-plan.md — 10-20 безопасных fixture-файлов, сценарии проверки files/text/search/report drivers |
| T-039 | Разблокировать Python runtime и закрыть T-029 | done | pool | `темы/ai-os-bridge.md` | Выполнено: runtime-блокер снят; T-029 закрыта; acceptance-задачи T-048/T-051/T-055/T-057/T-059 возвращены в пул |
| T-040 | Создать data/README.md по data-folder-plan | done | pool | `темы/ai-os-bridge.md` | Выполнено: data/README.md создан; теперь можно делать T-041 fixture-корпус |
| T-041 | Создать минимальный безопасный fixture-корпус | done | pool | `темы/ai-os-bridge.md` | Выполнено: data/fixtures/README.md и 7 synthetic fixture-файлов созданы |
| T-042 | Подготовить D-013 proposal по Q-008 driver schema v1 | done | pool | `темы/ai-os-bridge.md` | Выполнено: decisions/D-013.md создан со статусом proposed; Q-008 обновлён и остаётся open до accepted |
| T-043 | Реализовать рабочий read-only files driver + тесты | done | pool | `темы/ai-os-bridge.md` | drivers/files/files_driver.py — list/read/search/summarize (read-only, лимиты по safety-policy) + drivers/files/test_files.py |
| T-044 | Описать expected inventory для data/fixtures | done | pool | `темы/ai-os-bridge.md` | Выполнено: data/fixtures/EXPECTED.md создан |
| T-045 | Checklist принятия D-013 driver schema v1 | done | pool | `темы/ai-os-bridge.md` | Выполнено: docs/driver-schema-acceptance-checklist.md создан; D-013 остаётся proposed |
| T-046 | Обернуть files driver в настоящий MCP-сервер (stdio) | done | pool | `темы/ai-os-bridge.md` | drivers/files/mcp_server.py на FastMCP — инструменты list/read/search/summarize поверх files_driver.py; тест handshake + tools/list |
| T-047 | Усилить безопасность files MCP driver перед дальнейшим использованием | done | Codex | `темы/ai-os-bridge.md` | Выполнено: allowed-root, max_files/max_hits, skip dirs, read redaction; runtime-приёмка вынесена в T-048 |
| T-048 | Runtime-приёмка files driver и MCP wrapper после восстановления Python | blocked | pool | `темы/ai-os-bridge.md` | Blocked by runtime: files unit/inventory tests pass, but MCP stdio depends on asyncio subprocess pipe, which fails with PermissionError WinError 5 in this environment |
| T-049 | Обернуть repo-runner в MCP-сервер (read-only inventory) | done | pool | `темы/ai-os-bridge.md` | drivers/repo-runner/mcp_server.py на FastMCP — инструменты inspect/summary/risks поверх inventory.scan_repo (read-only, без запуска кода); тест handshake |
| T-050 | Усилить безопасность repo-runner MCP wrapper | done | Codex | `темы/ai-os-bridge.md` | Выполнено: REPO_RUNNER_BASE, max_files/truncated, allowed-root checks, тестовые проверки; runtime-приёмка вынесена в T-051 |
| T-051 | Runtime-приёмка repo-runner MCP wrapper после hardening | blocked | pool | `темы/ai-os-bridge.md` | Blocked by runtime: repo-runner unit test passed, but MCP stdio acceptance depends on asyncio subprocess pipe; see docs/mcp-stdio-windows-pipe-diagnostics-2026-06-21.md |
| T-052 | Реализовать workbench.db (SQLite) по схеме T-031 + тесты | done | pool | `темы/ai-os-bridge.md` | drivers/workbench/workbench.py — init/add_document/query_documents/log/audit по схеме documents+audit_log; тесты на чистой stdlib (sqlite3) |
| T-053 | Сквозной поток драйвер→workbench→поиск (ingest pipeline) | done | pool | `темы/ai-os-bridge.md` | drivers/workbench/ingest.py — scan (files/repo-runner) → workbench.add_document/ingest_repo → query; тест end-to-end на фикстуре |
| T-054 | Усилить безопасность workbench.db driver и добавить манифест | done | Codex | `темы/ai-os-bridge.md` | Выполнено: allowed-root для DB, suffix check, query/ingest limits, drivers/workbench.md; runtime-приёмка вынесена в T-055 |
| T-055 | Runtime-приёмка workbench.db driver после hardening | todo | pool | `темы/ai-os-bridge.md` | Готово к взятию: workbench/workbench-db tests прошли в Batch B; осталось CLI init/list/audit с WORKBENCH_BASE и generate.py --check при необходимости |
| T-056 | Усилить безопасность ingest pipeline после T-053 | done | Codex | `темы/ai-os-bridge.md` | Выполнено: WORKBENCH_BASE, INGEST_SOURCE_BASE, INGEST_MAX_FILES, db_base/source_base propagation; runtime-приёмка вынесена в T-057 |
| T-057 | Runtime-приёмка ingest pipeline после hardening | todo | pool | `темы/ai-os-bridge.md` | Готово к взятию: test_ingest/test_workbench/test_search прошли в Batch B; осталось CLI repo/dir с WORKBENCH_BASE/INGEST_SOURCE_BASE и generate.py --check при необходимости |
| T-058 | Driver schema v1 — валидатор и генератор каталога драйверов | done | pool | `темы/ai-os-bridge.md` | Создать валидатор drivers/ и генератор CATALOG.md + index.json |
| T-059 | File inventory driver — no-deps Python, карта файлов проекта | todo | pool | `темы/ai-os-bridge.md` | Готово к взятию: file-inventory tests прошли в Batch B; осталось demo scan/fixture-report и final generator/check pass |
| T-060 | Workbench.db schema — SQLite для документов и audit_log | done | pool | `темы/ai-os-bridge.md` | Спроектировать схему, создать init-скрипт, тесты, манифест |
| T-061 | (зарезервировано — заполните) | done | Claude | — | зарезервировано через tools/next_id.py — заполните |
| T-062 | (зарезервировано — заполните) | todo | Claude | — | зарезервировано через tools/next_id.py — заполните |
| T-063 | (зарезервировано — заполните) | todo | Claude | — | зарезервировано через tools/next_id.py — заполните |
| T-064 | (зарезервировано — заполните) | todo | Claude | — | зарезервировано через tools/next_id.py — заполните |
| T-065 | Подготовить runtime recovery playbook для снятия T-039 | done | Codex | `темы/ai-os-bridge.md` | Выполнено: docs/runtime-recovery-playbook.md создан; после внешнего восстановления выполнить проверки по порядку |
| T-066 | State reconciliation layer — спецификация контроля дрейфа индексов | done | Codex | `темы/ai-os-bridge.md` | Выполнено: docs/state-reconciliation-layer.md создан; после восстановления T-039 можно реализовать tools/reconcile_state.py |
| T-067 | Pipeline placeholder gating — не выдавать резервные задачи агентам | done | Codex | `темы/ai-os-bridge.md` | Выполнено: Batch C подтвердил ready_sorted() == []; placeholder-задачи не выдаются агентам |
| T-068 | Pipeline orphan doing detection — показывать doing без claim как проблему | done | Codex | `темы/ai-os-bridge.md` | Выполнено: Batch C подтвердил T-020 как doing without active claim |
| T-069 | Зафиксировать отчёт о текущей концептуальной и технической стадии | done | Codex | `темы/ai-os-bridge.md` | Выполнено: docs/implementation-stage-report-2026-06-20.md и queues/outbox/2026-06-20-implementation-stage-report.md созданы для оценки людьми и агентами |
| T-070 | Зафиксировать внешний PowerShell runtime check для T-039 | done | Codex | `темы/ai-os-bridge.md` | Выполнено: docs/runtime-powershell-check-2026-06-20.md создан; T-039 уточнён, но остаётся blocked до project validation/test batch |
| T-071 | Зафиксировать PowerShell UTF-8 display issue | done | Codex | `темы/ai-os-bridge.md` | Выполнено: docs/powershell-utf8-output.md создан; читать Markdown через Get-Content -Encoding UTF8 после chcp 65001 |
| T-072 | Зафиксировать успешный core runtime validation batch | done | Codex | `темы/ai-os-bridge.md` | Выполнено: docs/runtime-validation-batch-2026-06-20.md создан; следующий шаг — driver acceptance batch через python |
| T-073 | Подтвердить исправление UTF-8 вывода в PowerShell | done | Codex | `темы/ai-os-bridge.md` | Выполнено: пользователь подтвердил, что chcp 65001 + Get-Content -Encoding UTF8 корректно показывают PIPELINE.md и TASKS.md |
| T-074 | Подготовить driver acceptance batch для снятия T-039-зависимостей | done | Codex | `темы/ai-os-bridge.md` | Выполнено: docs/driver-acceptance-batch-2026-06-21.md создан; нужно запустить batch и вернуть вывод |
| T-075 | Зафиксировать MCP handshake RESULT OK от 2026-06-21 | done | Codex | `темы/ai-os-bridge.md` | Выполнено: docs/mcp-handshake-result-2026-06-21.md создан; Batch D пройден, нужны Batch B/C driver tests и pipeline guards |
| T-076 | Зафиксировать успешный Batch B driver tests от 2026-06-21 | done | Codex | `темы/ai-os-bridge.md` | Выполнено: docs/driver-tests-result-2026-06-21.md создан; Batch B пройден, Batch C pipeline guards ещё нужен |
| T-077 | Зафиксировать успешный Batch C pipeline guards от 2026-06-21 | done | Codex | `темы/ai-os-bridge.md` | Выполнено: docs/pipeline-guards-result-2026-06-21.md создан; T-067 и T-068 закрыты |
| T-078 | Перепроверка репозитория и независимое ревью (Claude) — плюсы/минусы/рекомендации | done | claude | `темы/repo-review-2026-06-21.md` | Прогнаны валидаторы и runtime-тесты драйверов; найден дрейф index.json и фантомный блокер T-039; отчёт — queues/outbox/2026-06-21-claude-repo-review.md и темы/repo-review-2026-06-21.md |
| T-079 | Снять фантомный runtime-блокер T-039 и вернуть acceptance-задачи в пул | done | Codex | `темы/repo-review-2026-06-21.md` | Выполнено: T-029/T-039 закрыты, T-059 разблокирована, pipeline снова содержит ready-задачи |
| T-080 | data-драйвер — redaction секретов и байтовый лимит вывода (P1 security, находка F) | done | claude | `темы/repo-review-2026-06-21.md` | Реализовано: drivers/redaction.py (канонический хелпер) + redaction значений ячеек и max_output_bytes в data_driver.head; test_data расширен (AWS-ключ и token-значение маскируются); тест зелёный |
| T-081 | Разблокировать MCP stdio subprocess на Windows для driver acceptance | done | pool | `темы/ai-os-bridge.md` | Диагностика выполнена: plain subprocess works, asyncio subprocess pipe fails with PermissionError WinError 5; MCP acceptance needs external runtime or sync subprocess workaround |
| T-082 | pipeline.py — fencing в done/fail и атомарный перехват claim (P1, находки H/I) | done | claude | `темы/repo-review-2026-06-21.md` | Реализовано backward-compatible: опц. --claim ID + сверка claim_id в done/fail, проверка держателя в fail, атомарный takeover протухшего claim через эксклюзивный lock; тест tools/test_pipeline_fencing.py зелёный, race_test регрессия ок |
| T-083 | Аудит-логирование вызовов в MCP-драйверах risk>=medium (P1 security, находка E) | done | claude | `темы/repo-review-2026-06-21.md` | Re-home из T-081 (коллизия id с задачей Codex про MCP-stdio). Реализовано: drivers/audit.py + обвязка data/repo-runner/codex-local MCP; тест drivers/test_audit.py + e2e зелёные |
| T-084 | Валидатор tools↔@mcp.tool() — машинная сверка манифеста с сервером (P1, находка K) | done | claude | `темы/repo-review-2026-06-21.md` | Реализовано: опц. поле manifest `tools` + check_driver_tools() в validate.py (ERROR при расхождении); поля проставлены для data/repo-runner/codex-local; SCHEMA.md дополнен; validate OK=9/0/0 |
| T-085 | Единый tools/_canon.py — убрать 8 копий парсера front-matter (P1, находка L) | todo | pool | `темы/repo-review-2026-06-21.md` | Отложено сознательно (высокий blast radius): вынести parse_front_matter в tools/_canon.py и заменить 8 копий (validate/generate/queue/pipeline/dispatch/metrics/risk_gate/drivers_catalog) одним импортом; сделать в выделенном PR с прогоном всех инструментов |
<!-- GEN:tasks END -->
