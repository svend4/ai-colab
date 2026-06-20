# Статус проекта

Этот файл читается первым. Здесь коротко фиксируется, что сейчас происходит, что важно, и куда смотреть дальше.

## Текущий фокус

- **AI-OS Bridge перешёл от обсуждения к первому практическому слою.** Q-007 закрыт через D-010: выбран поэтапный вариант B -> E / L1 -> ранний L2.
- **Создан L1-каталог `drivers/`.** Есть README, шаблон и первые манифесты: `files`, `data`, `repo-runner`, `codex-local`.
- **Система заморожена для продуктовой работы.** Текущий набор инструментов — sufficient; новые инструменты — только по явной потребности проекта.
- **Следующий шаг:** T-023 — добавить машинный индекс драйверов; T-024 — спроектировать read-only repo inventory driver для Sven4/local repos.

## Что изменилось недавно

| Дата | Кто | Изменение | Ссылка |
|---|---|---|---|
| 2026-06-20 | Codex | Импортирован внешний архитектурный документ `ai_middle_layer_architecture_ru.md` и подключён к работе AI-OS Bridge как roadmap для MVP; backlog драйверов добавлен в `drivers/README.md`, создана T-025. | `docs/ai_middle_layer_architecture_ru.md`, `темы/information-drivers.md`, `tasks/T-025.md` |
| 2026-06-20 | Codex | **AI-OS Bridge: старт L1-драйверов.** Q-007 закрыт через D-010; создан каталог `drivers/` с шаблоном и первыми манифестами; заведены T-022..T-024. | `темы/information-drivers.md`, `decisions/D-010.md`, `drivers/README.md` |
| 2026-06-20 | Novax | **Новый проект: AI-OS Bridge.** Создана тема `ai-os-bridge.md`, задача T-020, вопрос Q-007 с разбором 3 вариантов архитектуры (A/B/C). Концепция: прослойка между ОС и AI-агентами для подключения локальных программ (Codex) и внешних репозиториев (svend4). | `темы/ai-os-bridge.md`, `tasks/T-020.md`, `questions/Q-007.md` |
| 2026-06-19 | Novax | **Заморозка мета-развития:** стабилизационный этап завершён (19 задач, 9 решений, 6 вопросов, 0 ERROR). Система готова к продуктовой работе; новые инструменты — только по явной потребности. | `STATUS.md`, `tasks/T-005.md`, `dialog.md` |
| 2026-06-19 | Novax | **Meta-улучшения:** починен pre-commit hook (fallback-поиск Python по Windows-путям); флипнуты статусы тем `scaling-design` и `organization` в `done` (все задачи и оргвопросы закрыты). | `tools/githooks/pre-commit`, `темы/scaling-design.md`, `темы/organization.md` |
| 2026-06-19 | Mavis | Зарегистрирован третий AI-агент по запросу Stefan: карточка `participants/mavis.md`, строки в `AGENTS.md` и `participants.md`, обоснование в `dialog.md`. | `participants/mavis.md`, `AGENTS.md`, `participants.md`, `dialog.md` |
| 2026-06-19 | Novax | Зарегистрирован 4-й AI-агент Novax по запросу Stefan: карточка `participants/novax.md`, строки в `AGENTS.md` и `participants.md`, права в `tools/permissions.json`, обоснование в `dialog.md`. | `participants/novax.md`, `AGENTS.md`, `participants.md`, `tools/permissions.json` |
| 2026-06-19 | Stefan (через Novax) | Первый dogfood-прогон: задачи T-017 (glossary, Mavis) и T-018 (quickstart, Novax); Novax выполнил quickstart через `queue.py` claim→complete. | `темы/dogfood-run.md`, `docs/quickstart.md`, `tasks/T-017.md`, `tasks/T-018.md` |
| 2026-06-20 | Codex | Перепроверен dogfood-прогон: T-017/T-018 переведены в done, тема ждёт review Stefan; исправлен `permissions.py` для кириллических путей и worker generated-файлов. | `темы/dogfood-run.md`, `tasks/T-017.md`, `tasks/T-018.md`, `tools/permissions.py`, `tools/permissions.json` |
| 2026-06-19 | Claude/Stefan | Q-006 закрыт: D-009 принимает само-регистрацию агентов сейчас и эволюцию к гибридному онбордингу позже. | `questions/Q-006.md`, `decisions/D-009.md`, `темы/q006-agent-onboarding.md` |
| 2026-06-19 | Codex | Добавлен протокол масштабной работы для многих людей, AI-агентов и скриптов. | `PROTOCOL.md` |
| 2026-06-19 | Codex | Уточнен режим больших тем и добавлено состояние `queues/claimed/` для параллельных агентов. | `PROTOCOL.md`, `queues/claimed/README.md` |
| 2026-06-19 | Codex | Уточнены права AI-агентов: решения можно предлагать, а утверждать только при явной роли сборщика. | `AGENTS.md` |
| 2026-06-19 | Codex | Принято правило D-003: значимые правки служебных файлов должны сопровождаться объяснением в теме или общей ленте. | `DECISIONS.md`, `темы/organization.md` |
| 2026-06-19 | Codex | Принято D-002: для больших тем используется папка темы и отдельный файл на каждое сообщение. | `DECISIONS.md`, `PROTOCOL.md` |
| 2026-06-19 | Codex | Перепроверены замечания Claude: добавлено правило часового пояса, обновлена тестовая тема, уточнены Q-002/Q-003. | `README.md`, `PROTOCOL.md`, `QUESTIONS.md`, `темы/example.md` |
| 2026-06-19 | Codex | Добавлен каркас для задач, вопросов, решений, документов и шаблонов. | `STATUS.md` |
| 2026-06-19 | Claude | Исправлены нестыковки: единый формат подписи, Claude добавлен в реестр, D-002 помечен как предложенный, из списков тем убраны служебные файлы. | `AGENTS.md`, `DECISIONS.md` |
| 2026-06-19 | Claude | Заведена тема обоснования правок (форум-стайл), предложение D-003; повторно убрана строка `PROTOCOL.md` из «Активных тем» (причина — в теме). | `темы/organization.md`, `DECISIONS.md` |
| 2026-06-19 | Claude | Закрыты Q-001 (ASCII-имена) и Q-003 (гибридный сборщик) по голосу Stefan; добавлены D-004/D-005/D-006 и шаблон `templates/decision-options.md`. | `DECISIONS.md`, `QUESTIONS.md`, `README.md` |
| 2026-06-19 | Codex | Перепроверены D-004/D-005/D-006: выровнены правила утверждения решений, закрыта T-002 и добавлено правило D-004 в `QUESTIONS.md`. | `PROTOCOL.md`, `AGENTS.md`, `TASKS.md`, `QUESTIONS.md` |
| 2026-06-19 | Claude | Открыт Q-004 (миграция русских имён к ASCII) первым разбором по D-004; имя файла в ASCII по D-005. | `темы/migrate-file-names.md`, `QUESTIONS.md`, `board.md` |
| 2026-06-19 | Claude | Q-004 закрыт голосом Stefan: вариант C (постепенная миграция) → D-007; добавлена ongoing-задача T-005. | `DECISIONS.md`, `QUESTIONS.md`, `TASKS.md` |
| 2026-06-19 | Codex | Перепроверен D-007: уточнено, что он дополняет D-005 по существующим русским именам. | `DECISIONS.md`, `QUESTIONS.md`, `README.md`, `темы/migrate-file-names.md` |
| 2026-06-19 | Claude | Открыт Q-005 (границы D-003: что считать значимой правкой) разбором по D-004. | `темы/d003-scope.md`, `QUESTIONS.md`, `board.md` |
| 2026-06-19 | Claude | Q-005 закрыт голосом Stefan: вариант A (обоснование только для значимых правок) → D-008. Оргнастройка папки завершена. | `DECISIONS.md`, `QUESTIONS.md` |
| 2026-06-19 | Codex | Добавлен технический обзор инфраструктуры: плюсы, минусы, риски и roadmap продолжения. | `темы/infrastructure-review.md`, `TASKS.md` |
| 2026-06-19 | Claude | Добавлена инженерная оценка (ответ к обзору Codex): денормализация→генерация, front-matter, git-as-concurrency, AI-стоимость, right-size, адвокат дьявола; в `board.md` добавлена тема обзора. | `темы/infrastructure-review.md`, `board.md` |
| 2026-06-19 | Claude | Начат `tools/`: реализован валидатор канона `tools/validate.py` (+README), логика самопроверена на фикстурах; T-006 → review. Авторитетный запуск — на Windows (монтирование песочницы отдаёт файлы устаревшими/обрезанными). | `tools/validate.py`, `tools/README.md`, `TASKS.md` |
| 2026-06-19 | Claude | Валидатор прогнан на Windows: 0 ERROR (канон консистентен), commit 572ffa3; T-006 done. Добавлен pre-commit hook `tools/githooks/pre-commit` (блокирует коммит при ERROR). | `tools/githooks/pre-commit`, `tools/README.md`, `TASKS.md` |
| 2026-06-19 | Claude | Смоук-тест очередей (T-003/T-004): прогон inbox→claimed→outbox→done. Happy-path ок; найдено — перенос требует delete/move, claimed/ без TTL, нет проверки claim↔inbox. Очередь оставлена «спящей» (right-size). | `queues/outbox/2026-06-19-2044-smoke-test-result.md`, `TASKS.md` |
| 2026-06-19 | Claude | T-001 закрыт: формат полилога подтверждён реальной нагрузкой сессии (тестовое сообщение в `темы/example.md`). Стабилизационный этап завершён (T-001…T-006; T-005 — ongoing). | `темы/example.md`, `TASKS.md` |
| 2026-06-19 | Claude | Добавлен генератор навигации `tools/generate.py` (T-007): таблицы тем в STATUS/Доска собираются из front-matter тем; маркеры GEN; hook теперь проверяет навигацию (`--check`). Самопроверен на фикстуре. | `tools/generate.py`, `STATUS.md`, `board.md`, `темы/*` |
| 2026-06-19 | Codex | Добавлена развернутая оценка масштабирования для сценария «много агентов, людей и задач»: стадии зрелости, минусы, целевая архитектура и backlog T-008…T-013 как предложения. | `темы/scaling-design.md` |
| 2026-06-19 | Claude | T-008 (старт): реестр задач шардирован — задачи в `tasks/T-XXX.md` с front-matter, `TASKS.md` стал генерируемым индексом (маркеры GEN:tasks); генератор расширен и самопроверен. Цель: 4 агента, 2 человека, 2–3 задачи. | `tasks/*`, `tools/generate.py`, `TASKS.md` |
| 2026-06-19 | Claude | T-009: Очередь 2.0 — `tools/queue.py` (атомарный claim O_EXCL + TTL-lease + fencing-token + согласованные переходы). Закрывает дефекты T-004; самопроверено (гонка/fencing/перехват). | `tools/queue.py`, `tasks/T-009.md` |
| 2026-06-19 | Claude | T-008 завершён: шардированы и вопросы (`questions/Q-XXX.md`), и решения (`decisions/D-XXX.md`); `QUESTIONS.md`/`DECISIONS.md` стали генерируемыми индексами; генератор и валидатор расширены. | `questions/*`, `decisions/*`, `tools/*`, `QUESTIONS.md`, `DECISIONS.md` |
| 2026-06-19 | Claude | T-010: валидатор v2 — `check_sources` проверяет файлы-источники tasks/questions/decisions (front-matter, уникальность id, имя=id, статусы, целостность `depends_on`); аддитивно, существующие проверки не тронуты. Самопроверено. | `tools/validate.py`, `tasks/T-010.md` |
| 2026-06-19 | Codex | Перепроверен новый машинный индекс: `index.json` сгенерирован из front-matter, `generate.py --check` теперь проверяет его актуальность; назначение описано в `tools/README.md`. | `index.json`, `tools/generate.py`, `tools/README.md`, `темы/scaling-design.md` |
| 2026-06-19 | Claude | T-012 роли (`tools/permissions.py` + `permissions.json`: проверка зоны записи агента) и T-013 git-flow (`tools/flow.py`: ветка-на-агента + merge-гейт). Совещательные guard'ы, самопроверено. Закрывает пункты 5–6 роадмапа. | `tools/permissions.py`, `tools/permissions.json`, `tools/flow.py`, `tasks/T-012.md`, `tasks/T-013.md` |
| 2026-06-19 | Claude | T-014 диспетчер+DAG (`dispatch.py`: готовые/заблокированные по depends_on), T-015 риск-гейтинг (`risk_gate.py`: low→AUTO/medium→REVIEW/high→HUMAN), T-016 метрики (`metrics.py`). Самопроверено. Роадмап `scaling-design` закрыт полностью. | `tools/dispatch.py`, `tools/risk_gate.py`, `tools/metrics.py`, `tasks/T-014.md`, `tasks/T-015.md`, `tasks/T-016.md` |
| 2026-06-19 | Codex | Перепроверены инструменты масштабного слоя: документация `tools/README.md` дополнена, `metrics.py` считает активную очередь по Queue 2.0, `flow.py` исправлен для UTF-8 вывода в Windows-консоли. | `tools/README.md`, `tools/metrics.py`, `tools/flow.py`, `темы/scaling-design.md` |

## Активные темы

<!-- GEN:topics-status START — генерируется tools/generate.py, не править вручную -->
| Тема | Где | Статус | Следующее действие |
|---|---|---|---|
| Первый реальный прогон системы (dogfood) | `темы/dogfood-run.md` | waiting | Проверить docs/glossary.md, docs/quickstart.md и docs/agent-quickstart.md; решить, нужны ли правки |
| AI-OS Bridge — прослойка между ОС и AI-агентами | `темы/ai-os-bridge.md` | open | D-010 принят: стартовать с L1-каталога drivers/ и готовить один read-only L2 PoC; следующие задачи T-022..T-024 |
| Технический обзор инфраструктуры | `темы/infrastructure-review.md` | open | Обсудить предложения; выбрать следующий инженерный шаг |
| Границы D-003 (Q-005) | `темы/d003-scope.md` | done | Решено A (D-008): обоснование только для значимых правок |
| Пример обсуждения | `темы/example.md` | done | T-001 закрыт: формат полилога подтверждён |
| Миграция имён файлов к ASCII (Q-004) | `темы/migrate-file-names.md` | done | Решено C (D-007): переименовывать при правках, ход — T-005 |
| Организация папки и обоснование правок | `темы/organization.md` | done | Тема закрыта: все оргвопросы решены (D-002..D-008), система стабильна. Новые обоснования — в dialog.md или новых темах. |
| Онбординг агентов (Q-006) | `темы/q006-agent-onboarding.md` | done | Решено A (D-009); запланирована эволюция к C по мере роста числа агентов/снижения доверия |
| Масштабирование (много агентов/людей/задач) | `темы/scaling-design.md` | done | Тема закрыта: все задачи T-008..T-016 выполнены, roadmap реализован полностью. При необходимости масштабирования — создавать новую тему. |
| Слой драйверов (Treiber) — СЛИТО в ai-os-bridge | `темы/drivers-layer.md` | archive | Обсуждение объединено с темой ai-os-bridge (Q-007); технический разбор — docs/agent-layer-design.md |
| Информационные драйверы (трайберы) — СЛИТО в ai-os-bridge | `темы/information-drivers.md` | archive | Тема слита с `темы/ai-os-bridge.md` по D-010; канонический каталог — `drivers/`. Содержание сохранено ниже как историческая запись (варианты C/D/E, аналогии, сводная таблица, пошаговый план). |
<!-- GEN:topics-status END -->

## Как просить ИИ отреагировать

Пишите в любом Markdown-файле (укажите агента, например @Claude или @Codex):

```md
@Claude
Нужно прочитать этот файл, ответить на вопросы и предложить следующий шаг.
```

Если нужно прочитать всю папку, напишите в чате: "прочитай рабочую папку и отреагируй на новые изменения".
