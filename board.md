# Доска тем

Это навигация по обсуждениям. Для задач используйте `TASKS.md`, для вопросов - `QUESTIONS.md`, для решений - `DECISIONS.md`.

## Статусы тем

- `open` - обсуждается.
- `needs-decision` - нужно принять решение.
- `waiting` - ждем ответа участника.
- `done` - тема завершена.
- `archive` - тема закрыта и больше не активна.

## Темы

<!-- GEN:topics-board START — генерируется tools/generate.py, не править вручную -->
| Тема | Файл или папка | Статус | Ждем ответ от | Следующий шаг |
|---|---|---|---|---|
| Котёл-пакет для коллективного решения — 7 открытых пунктов | `topics/kotel-decision-material-2026-06-21.md` | needs-decision | Stefan/integrator | Использовать как независимую перепроверку D-020/T-137; решения переносить только через accepted decision |
| Первый реальный прогон системы (dogfood) | `topics/dogfood-run.md` | waiting | Stefan | Проверить docs/glossary.md, docs/quickstart.md и docs/agent-quickstart.md; решить, нужны ли правки |
| Динамический конвейер агентов — управляемая разработка | `topics/agent-pipeline.md` | open | все | D-011 принят, T-027 первая версия готова; обсудить heartbeat/live-room и правила использования pipeline.py |
| AI-OS Bridge — прослойка между ОС и AI-агентами | `topics/ai-os-bridge.md` | open | все | D-010 принят: стартовать с L1-каталога drivers/ и готовить один read-only L2 PoC; следующие задачи T-022..T-024 |
| ИНЦИДЕНТ — массовое урезание 147 outbox-отчётов (8643 строки), предъявление antigravity | `topics/incident-outbox-mass-strip-2026-06-24.md` | open | — |  |
| Технический обзор инфраструктуры | `topics/infrastructure-review.md` | open | все | Обсудить предложения; выбрать следующий инженерный шаг |
| Реестр МЕТА-вопросов — информационный рефакторинг, санация, омоложение репозитория на лету | `topics/meta-sanation-questions-2026-06-24.md` | open | — |  |
| Синтез мнений (Claude ↔ Codex) — консенсус, расхождения, карта работ | `topics/opinion-synthesis-2026-06-21.md` | open | Stefan | Реализовать консенсус-очередь (C1-C3 готовы к взятию); по расхождениям D1-D4 — доказательное обсуждение до консенсуса |
| Параллельная многоагентная работа без блокировки: «ручейки/streams», форк-варианты, worktree и merge-back | `topics/parallel-forks-history-2026-06-22.md` | open | — |  |
| Перепроверка и независимое ревью репозитория (Claude, 2026-06-21) | `topics/repo-review-2026-06-21.md` | open | Stefan | P0-1 выполнен Codex: T-039 снят, T-029 закрыта, ready pool восстановлен; дальше решить draft→ready и P1 security |
| Старые долги — генерик-песочница и методология форков (параллельные варианты) | `topics/sandbox-and-forks-2026-06-21.md` | open | Stefan | D-017 (fork-and-synthesize) принят; sandbox-контур = контракт Codex + intake-автоматизация Claude (синтез); T-020 переформулирован как первый external-source |
| Вопросник — триадный фрактал «золотой середины» (частный·средний·глобальный) как универсальный принцип записи информации | `topics/triadic-golden-mean-questionnaire-2026-06-25.md` | open | — |  |
| Границы D-003 (Q-005) | `topics/d003-scope.md` | done | — | Решено A (D-008): обоснование только для значимых правок |
| Пример обсуждения | `topics/example.md` | done | — | T-001 закрыт: формат полилога подтверждён |
| Миграция имён файлов к ASCII (Q-004) | `topics/migrate-file-names.md` | done | — | Решено C (D-007): переименовывать при правках, ход — T-005 |
| Организация папки и обоснование правок | `topics/organization.md` | done | — | Тема закрыта: все оргвопросы решены (D-002..D-008), система стабильна. Новые обоснования — в dialog.md или новых темах. |
| Онбординг агентов (Q-006) | `topics/q006-agent-onboarding.md` | done | — | Решено A (D-009); запланирована эволюция к C по мере роста числа агентов/снижения доверия |
| Масштабирование (много агентов/людей/задач) | `topics/scaling-design.md` | done | — | Тема закрыта: все задачи T-008..T-016 выполнены, roadmap реализован полностью. При необходимости масштабирования — создавать новую тему. |
| Слой драйверов (Treiber) — СЛИТО в ai-os-bridge | `topics/drivers-layer.md` | archive | — | Обсуждение объединено с темой ai-os-bridge (Q-007); технический разбор — docs/agent-layer-design.md |
| Информационные драйверы (трайберы) — СЛИТО в ai-os-bridge | `topics/information-drivers.md` | archive | — | Тема слита с `topics/ai-os-bridge.md` по D-010; канонический каталог — `drivers/`. Содержание сохранено ниже как историческая запись (варианты C/D/E, аналогии, сводная таблица, пошаговый план). |
| Архитектурные основы — канонический свод | `topics/architecture-fundamentals-2026-06-24.md` | proposed | — |  |
| Adoption Statistics — 2026-06-23 | `topics/adoption-statistics-2026-06-23.md` | proposed | — |  |
| Оповещение: Практика Dogfooding и параллельные задачи | `topics/agent-self-reflection-delegation.md` | active | — |  |
| Алхимический синтез - спираль бабочки | `topics/alchemy_synthesis_20260625_144041.md` | proposed | — |  |
| Alpha-2 -> Alpha-3 roadmap: план развития проекта | `topics/alpha2-to-alpha3-roadmap-2026-06-24.md` | proposed | — |  |
| Гарантии инструкций (применение/актуальность/поток вверх) и слияние документации агентов | `topics/assurance-and-doc-merge-2026-06-22.md` | proposed | — |  |
| Hardening assurance — лестница warn→block (S0..S4) + apex-подключение | `topics/assurance-hardening-plan-2026-06-23.md` | proposed | — |  |
| Worktree-ready build specs (2026-06-23) | `topics/build-specs-2026-06-23.md` | proposed | — |  |
| Авторитетная архитектура подсистемы безопасной коллаборации / параллельной работы (атомарные примитивы + ownership-детекторы + изоляция L0/L1) | `topics/collab-safety-subsystem-2026-06-23.md` | proposed | — |  |
| Политика коммитов для многоагентной работы — «ручейки» (streams) в основную линию | `topics/commit-policy-streams-2026-06-21.md` | accepted | none | Закрыто D-021 — Level 0 дефолт, Level 1 worktree-streams явный режим --worktree; см. T-143 closeout |
| Очередь коммитов с обратной связью и предсохранением → обобщение на технический и СЕМАНТИЧЕСКИЙ синтез | `topics/commit-queue-and-synthesis-2026-06-26.md` | proposed | — |  |
| Context-graph слой для мульти-агентной памяти (статья TDS) — мы это уже построили + бенчмарк | `topics/context-graph-rag-cross-pollination-2026-06-26.md` | proposed | — |  |
| D-014 execute OFF ratification packet | `topics/d014-execute-off-ratification-2026-06-23.md` | proposed | — |  |
| Proposal: Глобальная очистка очередей и ресайклинг технического долга (Вторсырье) | `topics/debt-cleanup-recycling-proposal-2026-06-24.md` | proposed | — |  |
| Систематическая формула решения дефектов многоагентной работы (класс «конкурентного вклада») + аудит истории | `topics/defect-class-formula-2026-06-26.md` | proposed | — |  |
| Drivers / AI-OS Bridge subsystem — authoritative state (2026-06-23) | `topics/drivers-subsystem-state-2026-06-23.md` | proposed | — |  |
| FINDER фронтира — рост-бэклог реально-нерешённого (37 пунктов) | `topics/finder-frontier-2026-06-23.md` | proposed | — |  |
| Дизайны флота (2026-06-23) — reconcile_state fix + наполнение L2-порталов | `topics/fleet-designs-2026-06-23.md` | proposed | — |  |
| Синтез двух подсистем трения/параллельной работы (Claude cohort/policy ↔ Codex friction) — D-017 | `topics/friction-subsystems-synthesis-2026-06-22.md` | proposed | — |  |
| Отравление общего gate чужой half-done задачей — ситуация и слои решений | `topics/gate-poison-situation-2026-06-22.md` | resolved | — |  |
| Котёл-предложения (D-018) — диспозиция 7 flow-сирот + конвенция last_verified | `topics/governance-proposals-2026-06-23.md` | proposed | — |  |
| Кросс-опыление .inf-формат ↔ наш канон — что заимствовать в проект | `topics/inf-format-cross-pollination-2026-06-26.md` | proposed | — |  |
| Расширенный вопросник .inf — рой 20 агентов (новые подвопросы + варианты ответов) | `topics/inf-questionnaire-expanded-2026-06-26.md` | proposed | — |  |
| Независимая ручная оценка svend4/infon (.inf) — что взять сюда, что посоветовать туда | `topics/infon-repo-independent-eval-2026-06-26.md` | proposed | — |  |
| Цикл 1: изучение вопросника, новые вопросы и ответы | `topics/information-refactoring-cycle-1-2026-06-25.md` | proposed | — |  |
| Information Refactoring Cycle 2 - ответы, новые вопросы и методы большой группы | `topics/information-refactoring-cycle-2-2026-06-25.md` | proposed | — |  |
| Information Refactoring Cycle 3 - action-plan, status-backfill и новые вопросы | `topics/information-refactoring-cycle-3-2026-06-25.md` | proposed | — |  |
| Информационный рефакторинг репозитория: дерево вопросов | `topics/information-refactoring-question-tree-2026-06-25.md` | proposed | — |  |
| Котёл: Системная Критика, Технический Долг и Ответственность | `topics/kotel-system-critique-2026-06-24.md` | proposed | — |  |
| Котёл: пошаговый план после системной критики | `topics/kotel-system-critique-2026-06-24-action-plan.md` | proposed | — |  |
| MMORPG reverse engineering into 2D text workbench for humans and agents | `topics/mmorpg-2d-text-workbench-2026-06-26.md` | proposed | — |  |
| Навигация-через-метаданные вместо шардинга — резолюция divergence (техническая реальность) | `topics/navigation-vs-sharding-2026-06-24.md` | proposed | — |  |
| Three newly-surfaced producer-workflow problems + designs (2026-06-23) | `topics/new-problems-2026-06-23.md` | resolved | — |  |
| Offline/headless Zed-like workbench — реалистичный MVP (план, подтверждён Goodall) | `topics/offline-headless-workbench-mvp-2026-06-26.md` | proposed | — |  |
| Разногласия двух политик коммитов/параллели — вынесено и обосновано (D-017) | `topics/parallel-work-divergences-2026-06-22.md` | proposed | — |  |
| Перспективный бэклог — ранжированная очередь следующих волн конвейера (самопополнение) | `topics/perspective-backlog-2026-06-23.md` | proposed | — |  |
| Заземление пирамиды (L2→L1) — consolidated plan (derive_reuse + наполнение порталов) | `topics/pyramid-grounding-consolidated-2026-06-23.md` | proposed | — |  |
| Заземление пирамиды — derived coverage вместо самодекларации (план по находкам assurance) | `topics/pyramid-grounding-plan-2026-06-23.md` | proposed | — |  |
| Q-016 assurance — состояние «построено vs осталось» (2026-06-23) | `topics/q016-assurance-state-2026-06-23.md` | proposed | — |  |
| Q-017 — семантический гибрид слияния документации (механический pre-cluster + agent-pass) | `topics/q017-docmerge-semantic-2026-06-23.md` | proposed | — |  |
| Q-017 — семантический гибрид слияния документации (consolidated, implementation-ready) | `topics/q017-semantic-consolidated-2026-06-23.md` | proposed | — |  |
| Разбор полётов — КОНСЕНСУС (общие пункты C-01..C-18 из мульти-документного синтеза) | `topics/razbor-consensus-2026-06-24.md` | proposed | — |  |
| Разбор полётов — РАЗНОГЛАСИЯ (21 DIV: конфликты + standalone из мульти-документного синтеза) | `topics/razbor-divergence-2026-06-24.md` | proposed | — |  |
| Lane B — статус 21 разногласия после churn-reconcile (что разрешено / открыто / в котёл) | `topics/razbor-divergence-status-2026-06-24.md` | proposed | — |  |
| Наш репо как collaborative-dev-service — субстрат + governance (позиционирование) | `topics/repo-as-collaborative-dev-service-2026-06-26.md` | proposed | — |  |
| Механизм safe-auto-apply — детекторы чинят тривиальное (D-018 proposal) | `topics/safe-auto-apply-design-2026-06-23.md` | proposed | — |  |
| Backlog доделывания — заявленные пункты сессии (simple→complex, кто владелец) | `topics/session-backlog-2026-06-26.md` | proposed | — |  |
| Authoritative session state (2026-06-23) — shipped tools, open backlog, orchestration architecture | `topics/session-state-2026-06-23.md` | proposed | — |  |
| Промежуточный статус-доклад проекта (фундамент для дальнейшего развития, не финал) | `topics/session-status-2026-06-24.md` | proposed | — |  |
| SOLVER report — 2026-06-23 | `topics/solver-report-2026-06-23.md` | proposed | — |  |
| svend4/infon assessment for multi-agent repo work | `topics/svend4-infon-assessment-2026-06-26.md` | proposed | — |  |
| Text diffusion canvas from svend4/infon for multi-agent work | `topics/text-diffusion-canvas-from-infon-2026-06-26.md` | proposed | — |  |
| Котёл: доказательная база по зависимостям text-extract (вход к T-137) | `topics/text-extract-deps-evidence-2026-06-21.md` | proposed | — |  |
| Единый спек 2D-текст-workbench — консолидация 3 независимо сошедшихся дизайнов | `topics/textscene-unified-spec-2026-06-26.md` | proposed | — |  |
| Ось ВРЕМЕНИ (decay/температура) — третья ось проекта, реализация DIV-06 | `topics/time-axis-decay-2026-06-24.md` | proposed | — |  |
| "FINDER — doc-vs-reality синтез (26 подтверждённых находок)" | `topics/finder-doc-vs-reality-2026-06-23.md` | proposed | — |  |
| Живой svend4/infon = TVCP (не .inf) — независимая оценка по фактическому репо, для мульти-агентной работы | `topics/tvcp-live-repo-eval-2026-06-26.md` | proposed | — |  |
| Патч-совет svend4/infon (TVCP) — конкретные правки по прочитанному коду + текст-канва как новый режим | `topics/tvcp-patch-advice-2026-06-26.md` | proposed | — |  |
| "textscene — 2D полу-диффузионная многоагентная текстовая модель (мощь TVCP-видеосвязи → текст)" | `topics/tvcp-text-diffusion-hybrid-2026-06-26.md` | proposed | — |  |
| Типизированный граф связей — вторая ось (дерево ⟂ граф), реализация DIV-07/08 | `topics/typed-link-graph-2026-06-24.md` | proposed | — |  |
| Zed multiplayer agents analysis and repo synthesis | `topics/zed-multiplayer-agents-analysis-2026-06-26.md` | proposed | — |  |
<!-- GEN:topics-board END -->

## Как добавить новую тему

1. Для небольшой темы скопируйте структуру из `templates/topic.md`.
2. Создайте новый файл в `topics/`, например `topics/api-design.md`.
3. Для большой темы создайте папку `topics/topic-name/` по `templates/topic-folder-README.md`, а сообщения кладите в `messages/` по `templates/topic-message.md`.
4. Добавьте строку в таблицу выше.
