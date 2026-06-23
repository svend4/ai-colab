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
| Котёл-пакет для коллективного решения — 7 открытых пунктов | `темы/kotel-decision-material-2026-06-21.md` | needs-decision | Stefan/integrator | Использовать как независимую перепроверку D-020/T-137; решения переносить только через accepted decision |
| Первый реальный прогон системы (dogfood) | `темы/dogfood-run.md` | waiting | Stefan | Проверить docs/glossary.md, docs/quickstart.md и docs/agent-quickstart.md; решить, нужны ли правки |
| Динамический конвейер агентов — управляемая разработка | `темы/agent-pipeline.md` | open | все | D-011 принят, T-027 первая версия готова; обсудить heartbeat/live-room и правила использования pipeline.py |
| AI-OS Bridge — прослойка между ОС и AI-агентами | `темы/ai-os-bridge.md` | open | все | D-010 принят: стартовать с L1-каталога drivers/ и готовить один read-only L2 PoC; следующие задачи T-022..T-024 |
| Технический обзор инфраструктуры | `темы/infrastructure-review.md` | open | все | Обсудить предложения; выбрать следующий инженерный шаг |
| Синтез мнений (Claude ↔ Codex) — консенсус, расхождения, карта работ | `темы/opinion-synthesis-2026-06-21.md` | open | Stefan | Реализовать консенсус-очередь (C1-C3 готовы к взятию); по расхождениям D1-D4 — доказательное обсуждение до консенсуса |
| Перепроверка и независимое ревью репозитория (Claude, 2026-06-21) | `темы/repo-review-2026-06-21.md` | open | Stefan | P0-1 выполнен Codex: T-039 снят, T-029 закрыта, ready pool восстановлен; дальше решить draft→ready и P1 security |
| Старые долги — генерик-песочница и методология форков (параллельные варианты) | `темы/sandbox-and-forks-2026-06-21.md` | open | Stefan | D-017 (fork-and-synthesize) принят; sandbox-контур = контракт Codex + intake-автоматизация Claude (синтез); T-020 переформулирован как первый external-source |
| Границы D-003 (Q-005) | `темы/d003-scope.md` | done | — | Решено A (D-008): обоснование только для значимых правок |
| Пример обсуждения | `темы/example.md` | done | — | T-001 закрыт: формат полилога подтверждён |
| Миграция имён файлов к ASCII (Q-004) | `темы/migrate-file-names.md` | done | — | Решено C (D-007): переименовывать при правках, ход — T-005 |
| Организация папки и обоснование правок | `темы/organization.md` | done | — | Тема закрыта: все оргвопросы решены (D-002..D-008), система стабильна. Новые обоснования — в dialog.md или новых темах. |
| Онбординг агентов (Q-006) | `темы/q006-agent-onboarding.md` | done | — | Решено A (D-009); запланирована эволюция к C по мере роста числа агентов/снижения доверия |
| Масштабирование (много агентов/людей/задач) | `темы/scaling-design.md` | done | — | Тема закрыта: все задачи T-008..T-016 выполнены, roadmap реализован полностью. При необходимости масштабирования — создавать новую тему. |
| Слой драйверов (Treiber) — СЛИТО в ai-os-bridge | `темы/drivers-layer.md` | archive | — | Обсуждение объединено с темой ai-os-bridge (Q-007); технический разбор — docs/agent-layer-design.md |
| Информационные драйверы (трайберы) — СЛИТО в ai-os-bridge | `темы/information-drivers.md` | archive | — | Тема слита с `темы/ai-os-bridge.md` по D-010; канонический каталог — `drivers/`. Содержание сохранено ниже как историческая запись (варианты C/D/E, аналогии, сводная таблица, пошаговый план). |
| Гарантии инструкций (применение/актуальность/поток вверх) и слияние документации агентов | `темы/assurance-and-doc-merge-2026-06-22.md` | proposed | — |  |
| Hardening assurance — лестница warn→block (S0..S4) + apex-подключение | `темы/assurance-hardening-plan-2026-06-23.md` | proposed | — |  |
| Worktree-ready build specs (2026-06-23) | `темы/build-specs-2026-06-23.md` | proposed | — |  |
| Авторитетная архитектура подсистемы безопасной коллаборации / параллельной работы (атомарные примитивы + ownership-детекторы + изоляция L0/L1) | `темы/collab-safety-subsystem-2026-06-23.md` | proposed | — |  |
| Политика коммитов для многоагентной работы — «ручейки» (streams) в основную линию | `темы/commit-policy-streams-2026-06-21.md` | accepted | none | Закрыто D-021 — Level 0 дефолт, Level 1 worktree-streams явный режим --worktree; см. T-143 closeout |
| D-014 execute OFF ratification packet | `темы/d014-execute-off-ratification-2026-06-23.md` | proposed | — |  |
| Дизайны флота (2026-06-23) — reconcile_state fix + наполнение L2-порталов | `темы/fleet-designs-2026-06-23.md` | proposed | — |  |
| Синтез двух подсистем трения/параллельной работы (Claude cohort/policy ↔ Codex friction) — D-017 | `темы/friction-subsystems-synthesis-2026-06-22.md` | proposed | — |  |
| Отравление общего gate чужой half-done задачей — ситуация и слои решений | `темы/gate-poison-situation-2026-06-22.md` | draft | — |  |
| Котёл-предложения (D-018) — диспозиция 7 flow-сирот + конвенция last_verified | `темы/governance-proposals-2026-06-23.md` | proposed | — |  |
| Разногласия двух политик коммитов/параллели — вынесено и обосновано (D-017) | `темы/parallel-work-divergences-2026-06-22.md` | proposed | — |  |
| Перспективный бэклог — ранжированная очередь следующих волн конвейера (самопополнение) | `темы/perspective-backlog-2026-06-23.md` | proposed | — |  |
| Заземление пирамиды (L2→L1) — consolidated plan (derive_reuse + наполнение порталов) | `темы/pyramid-grounding-consolidated-2026-06-23.md` | proposed | — |  |
| Заземление пирамиды — derived coverage вместо самодекларации (план по находкам assurance) | `темы/pyramid-grounding-plan-2026-06-23.md` | proposed | — |  |
| Q-017 — семантический гибрид слияния документации (механический pre-cluster + agent-pass) | `темы/q017-docmerge-semantic-2026-06-23.md` | proposed | — |  |
| Q-017 — семантический гибрид слияния документации (consolidated, implementation-ready) | `темы/q017-semantic-consolidated-2026-06-23.md` | proposed | — |  |
| Authoritative session state (2026-06-23) — shipped tools, open backlog, orchestration architecture | `темы/session-state-2026-06-23.md` | proposed | — |  |
| "FINDER — doc-vs-reality синтез (26 подтверждённых находок)" | `темы/finder-doc-vs-reality-2026-06-23.md` | proposed | — |  |
<!-- GEN:topics-board END -->

## Как добавить новую тему

1. Для небольшой темы скопируйте структуру из `templates/topic.md`.
2. Создайте новый файл в `темы/`, например `темы/api-design.md`.
3. Для большой темы создайте папку `темы/topic-name/` по `templates/topic-folder-README.md`, а сообщения кладите в `messages/` по `templates/topic-message.md`.
4. Добавьте строку в таблицу выше.
