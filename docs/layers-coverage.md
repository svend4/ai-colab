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
| **L1 Runtime** | Python / Node / shell / Docker / WSL2 | Python-инструменты и PowerShell работают; стандартный Windows `tempfile` и `asyncio` stdio pipes имеют локальные ограничения | 🟡 | WSL2 + Docker/контейнеры для запуска непроверенного кода; продолжать использовать `drivers/test_tmp.py` для тестов |
| **L2 MCP-драйверы** | обёртки ИИ↔возможность (stdio/http) | 7 driver manifest; MCP wrappers для `files`, `data`, `repo-runner`, `codex-local`, `gateway`; sync `tools/list` и sync `tools/call` acceptance 19/19 работают; manifest-tools validation и gateway in-process regression есть | 🟡 | Оставшийся hardening: официальный async stdio runtime в проблемных Windows-средах, cleanup старых blocker-формулировок в done-задачах, затем server/sandbox только по спросу |
| **L3 Skills** | пассивные навыки, грузятся по требованию | Правила, manifest-подход и docs есть; переносимые проектные `.codex/skills/*/SKILL.md` ещё не оформлены | 🟡 | выделить повторяемые workflow в 2-3 проектных skill-папки (`driver-acceptance`, `pipeline-operator`, `repo-review`) |
| **L4 Агенты/субагенты** | исполнители с ролью и контекстом | `participants/` (Claude/Codex/Mavis/Novax), `AGENTS.md` | ✅ | — |
| **L5 Plugins/Marketplaces** | упаковка навыков+MCP в пакет | `drivers/` — зародыш | ❌ | позже, когда появятся MCP-драйверы |
| **L6 Память / RAG** | SQLite, векторная БД, индексы | `workbench` SQLite driver ready; `documents`/`audit_log`, ingest/search tests, CLI acceptance и `gateway.memory_query` есть | 🟡 | добавить нормальный knowledge workflow: corpora → ingest → query report; vector/RAG оставить позже |
| **L7 Оркестрация** | правила + конвейер + наблюдаемость | `AGENTS.md`, `PROTOCOL.md`, `pipeline.py`, `queue`, `dispatch`, `generate`/`validate`, `next_id` | ✅ | — |
| **Вершина: клиент-хост** | дирижёр (Cowork/Codex/Claude) | агенты в своих сессиях | ✅ | — |

## Вывод

Сильные слои — **L0, L4, L7** (основание, агенты, оркестрация — это и есть инфраструктура, которую построили). После T-087..T-095 средний слой уже вышел за пределы «карты»: **L2** имеет рабочие read-only драйверы и MCP/tools-list контур, **L6** имеет SQLite workbench/ingest/search. Но оба слоя ещё не являются зрелой платформой: L2 требует устойчивой `tools/call` приёмки, L6 требует регулярного knowledge workflow и, позже, vector/RAG.

**Рекомендуемый порядок (right-size, по D-010):**
1. **L2 — reconciliation hardening:** убрать старые blocker-формулировки из done-задач и оставить явную разницу между sync acceptance и официальным async stdio client.
2. **L6 — knowledge workflow:** зафиксировать практический сценарий `ingest → query → report` на безопасном локальном корпусе, без vector/RAG до реального спроса.
3. **L3 — project skills:** вынести повторяемые процедуры (`driver acceptance`, `pipeline operation`, `repo review`) в переносимые `SKILL.md`.
4. **L1 — WSL2+Docker** только когда дойдём до запуска непроверенного кода Sven4 или другого внешнего кода (песочница).

Связано: `docs/middle-layer-guide.md`, `docs/agent-layer-design.md`, `темы/ai-os-bridge.md`, `decisions/D-010.md`.
