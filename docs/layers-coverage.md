# Карта покрытия слоёв L0–L7 (T-032)

> **Канонический источник нумерации слоёв L0–L7.** Этот файл (вместе с `docs/middle-layer-guide.md`) —
> авторитетный источник нумерации `L0–L7`. Другие документы должны ссылаться сюда, а не переопределять
> номера. Иллюстративные/исторические схемы с иной нумерацией (`docs/agent-layer-design.md` §2,
> `docs/status-report-2026-06-20.md`) каноном не являются (ревью T-078, находка J).

Какие слои «среднего слоя пирамиды» (см. `docs/middle-layer-guide.md`) уже покрыты проектом, а где пробелы. Помогает выбрать, что строить дальше по D-010.

Легенда: ✅ покрыто · 🟡 частично · ❌ нет.

| Слой | Что это | В проекте | Статус | Что не хватает / след. шаг |
|---|---|---|---|---|
| **L0 Основание** | ОС, ФС, железо | Windows + file-native репозиторий | ✅ | — |
| **L1 Runtime** | Python / Node / shell / Docker / WSL2 | Python-инструменты и PowerShell работают; стандартный Windows `tempfile` и `asyncio` stdio pipes имеют локальные ограничения; execute preflight описан в `docs/execute-sandbox-preflight.md` | 🟡 | WSL2 + Docker/контейнеры только перед запуском непроверенного кода; продолжать использовать `drivers/test_tmp.py` и `tmp-work/` для тестов |
| **L2 MCP-драйверы** | обёртки ИИ↔возможность (stdio/http) | 9 driver manifest; MCP wrappers для `files`, `data`, `repo-runner`, `codex-local`, `gateway`, `git-log`, `sqlite`; sync `tools/list` и sync `tools/call` acceptance 27/27 работают; manifest-tools validation и gateway in-process regression есть | 🟡 | Оставшийся hardening: официальный async stdio runtime в проблемных Windows-средах и server/sandbox только по спросу |
| **L3 Skills** | пассивные навыки, грузятся по требованию | `skills/driver-acceptance`, `skills/pipeline-operator`, `skills/repo-review` оформлены как переносимые `SKILL.md` + README; usage/packaging guide — `docs/skills-usage.md` | ✅ | позже упаковать как plugin/marketplace, если появится реальная командная установка |
| **L4 Агенты/субагенты** | исполнители с ролью и контекстом | `participants/` (Claude/Codex/Mavis/Novax), `AGENTS.md` | ✅ | — |
| **L5 Plugins/Marketplaces** | упаковка навыков+MCP в пакет | есть кандидаты (`skills/`, `drivers/`), но нет plugin manifest/install lifecycle | ❌ | позже, когда один skill/driver реально понадобится переносить как пакет |
| **L6 Память / RAG** | SQLite, векторная БД, индексы | `workbench` SQLite driver ready; `documents`/`audit_log`, ingest/search tests, CLI acceptance, `gateway.memory_query`; `tools/knowledge.py` имеет FTS5 search, `report --out`, `reports/`, `data/knowledge-corpus/`, regression-тест write-path safety | 🟡 | применить workflow к более крупному безопасному корпусу; vector/RAG оставить позже |
| **L7 Оркестрация** | правила + конвейер + наблюдаемость | `AGENTS.md`, `PROTOCOL.md`, `pipeline.py`, `queue`, `dispatch`, `generate`/`validate`, `next_id` | ✅ | — |
| **Вершина: клиент-хост** | дирижёр (Cowork/Codex/Claude) | агенты в своих сессиях | ✅ | — |

## Вывод

Сильные слои — **L0, L3, L4, L7** (основание, skills, агенты, оркестрация). После T-087..T-120 средний слой уже вышел за пределы «карты»: **L2** имеет рабочие read-only драйверы и переносимую MCP `tools/call` приёмку 27/27, включая `sqlite`; **L6** имеет SQLite workbench/ingest/search, FTS5, `report --out`, `reports/`, безопасный mini-corpus и regression-тест write-path safety. Но это всё ещё read-only прототип, а не execute-платформа: запуск чужого кода требует отдельной песочницы и accepted decision.

**Рекомендуемый порядок (right-size, по D-010):**
1. **L6 — larger safe corpus:** применить knowledge workflow к более крупному безопасному корпусу и сравнивать `reports/` между запусками.
2. **L2 — async/stdout compatibility:** при необходимости проверить официальный async MCP client во внешней среде; локальный sync path уже покрывает регулярную приёмку.
3. **L5 — packaging later:** plugin/marketplace только если конкретный skill/driver нужно переносить как пакет.
4. **L1 — WSL2+Docker** только когда дойдём до запуска непроверенного кода Sven4 или другого внешнего кода (песочница).

Связано: `docs/middle-layer-guide.md`, `docs/agent-layer-design.md`, `docs/bridge-usage.md`, `docs/execute-sandbox-preflight.md`, `docs/skills-usage.md`, `topics/ai-os-bridge.md`, `decisions/D-010.md`.
