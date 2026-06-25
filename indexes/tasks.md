<!-- GENERATED folder_index.py — НЕ редактировать руками; навигация-через-метаданные -->
# Индекс папки `tasks/` — 259 файлов

> Машино- и человекочитаемое оглавление визиток (вместо шардинга плоской папки).

## Файлы (визитки)

| файл | type | status | суть |
|---|---|---|---|
| [T-001.md](../tasks/T-001.md) | task | done | Подтверждено реальной нагрузкой сессии (2 ИИ + человек, 8 решений, 5 вопросов). Крупные те |
| [T-002.md](../tasks/T-002.md) | task | done | Закрыто решением D-005: новые технические/тематические файлы в ASCII, кириллица — в заголо |
| [T-003.md](../tasks/T-003.md) | task | done | Прогнан смоук-тест очереди (inbox→claimed→outbox→done). Happy-path работает; ограничения з |
| [T-004.md](../tasks/T-004.md) | task | done | Claim-файл создаётся и фиксирует исполнителя. Найдено: `claimed/` без TTL/fencing — не нас |
| [T-005.md](../tasks/T-005.md) | task | done | Выполнена 2026-06-19. Переименовано 5 файлов: |
| [T-006.md](../tasks/T-006.md) | task | done | — |
| [T-007.md](../tasks/T-007.md) | task | done | — |
| [T-008.md](../tasks/T-008.md) | task | done | Убран write-hotspot: каждая сущность — отдельный файл (`tasks/T-XXX.md`, `questions/Q-XXX. |
| [T-009.md](../tasks/T-009.md) | task | done | Закрывает дефекты смоук-теста T-004: `claimed/` теперь атомарен и с TTL. Самопроверено на  |
| [T-010.md](../tasks/T-010.md) | task | done | Самопроверено на фикстурах: good → 0 ERROR; bad → ловит нет-id, дубли, битый `depends_on`. |
| [T-011.md](../tasks/T-011.md) | task | done | Реализовано Claude, независимо верифицировано и задокументировано Codex (журнал `STATUS.md |
| [T-012.md](../tasks/T-012.md) | task | done | Политика-демо: `claude`/`codex` — `**` (maintainer); `mavis` — work-зоны (`tasks/queues/to |
| [T-013.md](../tasks/T-013.md) | task | done | Зачем: при 4 агентах ветки снижают конфликты на «горячих» файлах; гейт не пускает в master |
| [T-014.md](../tasks/T-014.md) | task | done | Самопроверено на DAG-фикстуре: готовые отсортированы по приоритету, заблокированные показы |
| [T-015.md](../tasks/T-015.md) | task | done | Политика-советчик; финальное действие за человеком/сборщиком. Самопроверено (high→HUMAN, m |
| [T-016.md](../tasks/T-016.md) | task | done | Самопроверено: корректные счётчики и ready/blocked на фикстуре. |
| [T-017.md](../tasks/T-017.md) | task | done | Создать файл `docs/glossary.md` с расшифровкой всех терминов, используемых в репозитории:  |
| [T-018.md](../tasks/T-018.md) | task | done | Создать файл `docs/quickstart.md` — пошаговое руководство для человека или агента, который |
| [T-019.md](../tasks/T-019.md) | task | done | Единственное свойство очереди, которое dogfood-прогон проверил только по коду, а не |
| [T-020.md](../tasks/T-020.md) | task | done | Создать подробный план прослойки AI-OS Bridge. |
| [T-021.md](../tasks/T-021.md) | task | done | Параллельно с T-020 (Novax: исследование svend4 + варианты A/B/C) подготовлен глубокий тех |
| [T-022.md](../tasks/T-022.md) | task | done | Создать первый практический слой AI-OS Bridge: папку `drivers/`, где каждая способность оп |
| [T-023.md](../tasks/T-023.md) | task | done | Сейчас `drivers/` читается человеком и агентом как markdown-каталог. Следующий шаг — сдела |
| [T-024.md](../tasks/T-024.md) | task | done | Спроектировать первый безопасный драйвер для сценария Sven4/local repos. На первом этапе о |
| [T-025.md](../tasks/T-025.md) | task | done | Документ `docs/ai_middle_layer_architecture_ru.md` скопирован из внешней папки в проект и  |
| [T-026.md](../tasks/T-026.md) | task | done | За сессию повторялись коллизии номеров при параллельном создании (Q-008 ×2, Q-009 ×2, назр |
| [T-027.md](../tasks/T-027.md) | task | done | Чтобы общение и работа агентов были **динамичнее**, нужен конвейер: агент сам тянет |
| [T-028.md](../tasks/T-028.md) | task | done | Задача по Q-012/D-012: добавить live-слой без превращения его в обязательную дисциплину дл |
| [T-029.md](../tasks/T-029.md) | task | done | Цель: начать MVP-драйвер `files` из `docs/mvp-roadmap.md`. |
| [T-030.md](../tasks/T-030.md) | task | done | Общая задача — `owner: pool`, берётся через конвейер (`pipeline.py next`). |
| [T-031.md](../tasks/T-031.md) | task | done | Для L3 (повторяемый поиск и отчётность по корпусу) нужна локальная SQLite-база. Эта задача |
| [T-032.md](../tasks/T-032.md) | task | done | Из `docs/ai_middle_layer_architecture_ru.md` и анализа Novax: проект уже покрывает L0/L1/L |
| [T-033.md](../tasks/T-033.md) | task | done | Когда L1-каталог готов, нужен короткий приоритизированный список: какие драйверы оборачива |
| [T-034.md](../tasks/T-034.md) | task | done | Нужен короткий практический документ для людей и агентов: как пользоваться `tools/pipeline |
| [T-035.md](../tasks/T-035.md) | task | done | Нужно сделать компактную матрицу ролей для людей, AI-агентов и скриптов: кто что делает, к |
| [T-036.md](../tasks/T-036.md) | task | done | Нужен один документ с правилами безопасности для драйверов: read-only-first, dry-run для з |
| [T-037.md](../tasks/T-037.md) | task | done | Нужно описать будущую структуру `data/` для большого корпуса: входящие файлы, копии, извле |
| [T-038.md](../tasks/T-038.md) | task | done | Для проверки драйверов нужен маленький безопасный тестовый корпус. Задача — описать состав |
| [T-039.md](../tasks/T-039.md) | task | done | T-029 заблокирована не логикой драйвера, а средой: системный `python` и bundled Python зав |
| [T-040.md](../tasks/T-040.md) | task | done | По `docs/data-folder-plan.md` нужно создать практический `data/README.md`: что хранится в  |
| [T-041.md](../tasks/T-041.md) | task | done | После `docs/test-corpus-plan.md` нужен маленький безопасный corpus в `data/fixtures/`. |
| [T-042.md](../tasks/T-042.md) | task | done | Q-008 остаётся открытым. Нужно подготовить проект решения: |
| [T-043.md](../tasks/T-043.md) | task | done | Первый L2-кандидат по `docs/l2-candidates.md` — `files`. Манифест `drivers/files.md` есть, |
| [T-044.md](../tasks/T-044.md) | task | done | После создания `data/fixtures/` нужен человекочитаемый expected-result: какие файлы должен |
| [T-045.md](../tasks/T-045.md) | task | done | D-013 предложен, но не принят. Нужен checklist для человека/сборщика: какие проверки выпол |
| [T-046.md](../tasks/T-046.md) | task | done | Состав: `drivers/files/mcp_server.py` — FastMCP с инструментами `list_files`/`read_file`/` |
| [T-047.md](../tasks/T-047.md) | task | done | Задача возникла после статической перепроверки `T-046`. |
| [T-048.md](../tasks/T-048.md) | task | done | Цель: после разблокировки `T-039` честно проверить, что `T-043`, `T-046` и `T-047` работаю |
| [T-049.md](../tasks/T-049.md) | task | done | Движок `drivers/repo-runner/inventory.py` (`scan_repo`) уже есть и протестирован (Novax).  |
| [T-050.md](../tasks/T-050.md) | task | done | Цель: после закрытия `T-049` усилить безопасность второго L2-драйвера перед дальнейшим исп |
| [T-051.md](../tasks/T-051.md) | task | done | Цель: после восстановления runtime проверить, что `T-049` и `T-050` работают вместе. |
| [T-052.md](../tasks/T-052.md) | task | done | Схема спроектирована (T-031, `drivers/workbench-schema.md`). Эта задача — рабочий код на ч |
| [T-053.md](../tasks/T-053.md) | task | done | Слои есть по отдельности: драйверы `files`/`repo-runner` (L2) и память `workbench.db` (L6) |
| [T-054.md](../tasks/T-054.md) | task | done | Цель: после реализации `T-052` привести `workbench.db` к политике драйверов. |
| [T-055.md](../tasks/T-055.md) | task | done | Цель: после восстановления runtime проверить `T-052` и `T-054`. |
| [T-056.md](../tasks/T-056.md) | task | done | Цель: после закрытия `T-053` убедиться, что сквозной поток `scan -> workbench -> query` не |
| [T-057.md](../tasks/T-057.md) | task | done | Цель: после восстановления runtime проверить `T-053` и `T-056`. |
| [T-058.md](../tasks/T-058.md) | task | done | **Цель:** формализовать и проверять манифесты драйверов. |
| [T-059.md](../tasks/T-059.md) | task | done | **Цель:** безопасная карта всех файлов в проектной папке (или указанной). |
| [T-060.md](../tasks/T-060.md) | task | done | **Цель:** локальная SQLite БД для хранения метаданных проекта, поиска и аудита. |
| [T-061.md](../tasks/T-061.md) | task | done | — |
| [T-062.md](../tasks/T-062.md) | task | done | Этот id был резервом без реальной задачи. По T-091 закрыт как `done`, чтобы placeholder не |
| [T-063.md](../tasks/T-063.md) | task | done | Этот id был резервом без реальной задачи. По T-091 закрыт как `done`, чтобы placeholder не |
| [T-064.md](../tasks/T-064.md) | task | done | Этот id был резервом без реальной задачи. По T-091 закрыт как `done`, чтобы placeholder не |
| [T-065.md](../tasks/T-065.md) | task | done | Цель: собрать в одном месте порядок восстановления runtime и пакетной приёмки заблокирован |
| [T-066.md](../tasks/T-066.md) | task | done | Цель: зафиксировать техническую спецификацию слоя, который сравнивает `tasks/*.md`, очеред |
| [T-067.md](../tasks/T-067.md) | task | done | Цель: не позволять `tools/pipeline.py next <agent>` автоматически выдавать резервные place |
| [T-068.md](../tasks/T-068.md) | task | done | Цель: сделать видимым состояние, когда задача имеет `status: doing`, но не имеет активного |
| [T-069.md](../tasks/T-069.md) | task | done | Цель: перенести в репозиторий текущую оценку концептуальной и технической стадии проекта,  |
| [T-070.md](../tasks/T-070.md) | task | done | Цель: зафиксировать результат ручной проверки runtime, присланный пользователем из Windows |
| [T-071.md](../tasks/T-071.md) | task | done | Цель: зафиксировать, что mojibake при `Get-Content .\PIPELINE.md` является проблемой отобр |
| [T-072.md](../tasks/T-072.md) | task | done | Цель: зафиксировать результаты ручного запуска core runtime validation через Windows Power |
| [T-073.md](../tasks/T-073.md) | task | done | Цель: зафиксировать, что предложенная процедура для Windows PowerShell решила проблему moj |
| [T-074.md](../tasks/T-074.md) | task | done | Цель: подготовить точный PowerShell checklist для следующего этапа после core runtime vali |
| [T-075.md](../tasks/T-075.md) | task | done | Цель: зафиксировать результат ручного запуска MCP smoke-handshake в рамках driver acceptan |
| [T-076.md](../tasks/T-076.md) | task | done | Цель: зафиксировать результаты driver tests из `queues/inbox/2026-06-21-driver-acceptance- |
| [T-077.md](../tasks/T-077.md) | task | done | Цель: зафиксировать результаты Batch C из `queues/inbox/documentoutput.md`. |
| [T-078.md](../tasks/T-078.md) | task | done | Запрос Stefan: перепроверить репозиторий, зарегистрироваться агентом, начать работать |
| [T-079.md](../tasks/T-079.md) | task | done | Цель: отреагировать на P0-рекомендацию Claude из `T-078` и убрать фантомный runtime-блокер |
| [T-080.md](../tasks/T-080.md) | task | done | Закрывает находку F ревью T-078: `data`-драйвер декларировал `risk: medium`/`audit: true`, |
| [T-081.md](../tasks/T-081.md) | task | done | Цель: разблокировать MCP acceptance-задачи, которые требуют запуска MCP server по stdio. |
| [T-082.md](../tasks/T-082.md) | task | done | Закрывает находки H и I ревью T-078. |
| [T-083.md](../tasks/T-083.md) | task | done | Закрывает находку E ревью T-078: policy (`docs/driver-safety-policy.md:11`) требует, чтобы |
| [T-084.md](../tasks/T-084.md) | task | done | Закрывает находку K ревью T-078: манифестное `interfaces` декларирует одно, а сервер |
| [T-085.md](../tasks/T-085.md) | task | done | Закрывает находку L ревью T-078: парсер front-matter был скопирован 8 раз |
| [T-086.md](../tasks/T-086.md) | task | done | Цель: после закрытия runtime/driver acceptance этапа сформировать следующий пул задач, не  |
| [T-087.md](../tasks/T-087.md) | task | done | Цель: получить локальный MCP acceptance путь, который не использует `asyncio.create_subpro |
| [T-088.md](../tasks/T-088.md) | task | done | Цель: привести `gateway` в честное состояние после ревью. |
| [T-089.md](../tasks/T-089.md) | task | done | Цель: убрать историческую копию redaction-паттернов в `files_driver.py` и подключить `file |
| [T-090.md](../tasks/T-090.md) | task | done | Цель: закрыть governance-риск из `T-078`: драйверы не должны иметь статус `ready` без поня |
| [T-091.md](../tasks/T-091.md) | task | done | Цель: сделать pipeline чище без касания `svend4`. |
| [T-092.md](../tasks/T-092.md) | task | done | Закрывает программно-применимую часть находки G ревью T-078: policy требует реальной |
| [T-093.md](../tasks/T-093.md) | task | done | Этот id был создан как пустой резерв после cleanup T-091. По `docs/stale-work-cleanup-poli |
| [T-094.md](../tasks/T-094.md) | task | done | Закрывает пробел покрытия (находка M ревью T-078) для `gateway` (owner Claude): у драйвера |
| [T-095.md](../tasks/T-095.md) | task | done | Закрывает находку J ревью T-078: нумерация L0-L8 расходилась между документами |
| [T-096.md](../tasks/T-096.md) | task | done | Цель: после закрытия T-087..T-095 привести каноническую карту слоёв в соответствие с факти |
| [T-097.md](../tasks/T-097.md) | task | done | Продуктовая демонстрация (не правка ревью): один запуск показывает, что AI-агент получает |
| [T-098.md](../tasks/T-098.md) | task | done | Шаг 1 из плана «все направления по порядку». Операционный гайд, как реально пользоваться |
| [T-099.md](../tasks/T-099.md) | task | done | Цель: после T-098 проверить `docs/bridge-usage.md` со стороны Codex и довести до состояния |
| [T-100.md](../tasks/T-100.md) | task | done | Цель: закрыть следующий шаг L2 acceptance hardening после `drivers/mcp_sync_probe.py`: не  |
| [T-101.md](../tasks/T-101.md) | task | done | Закрывает «L2 acceptance hardening» (roadmap layers-coverage): официальный async MCP stdio |
| [T-102.md](../tasks/T-102.md) | task | done | Новая способность среднего слоя: AI-агент понимает ЭВОЛЮЦИЮ репозитория (дополняет |
| [T-103.md](../tasks/T-103.md) | task | done | Цель: выполнить требование из T-102 — второй агент сверяет новый `git-log` driver и добавл |
| [T-104.md](../tasks/T-104.md) | task | done | Завершает план «все направления по порядку»: 1) usage-гайд (T-098), 2) sync-приёмка 19/19  |
| [T-105.md](../tasks/T-105.md) | task | done | Follow-up из консолидации (T-104): git-log MCP `tools/call` виснул, хотя in-process и hand |
| [T-106.md](../tasks/T-106.md) | task | done | Follow-up: `logs/driver-audit.jsonl` (пишется `drivers/audit.py` при реальных вызовах без |
| [T-107.md](../tasks/T-107.md) | task | done | Цель: закрыть следующий шаг из `docs/layers-coverage.md`: практический сценарий `ingest →  |
| [T-108.md](../tasks/T-108.md) | task | done | Следующий пункт roadmap `layers-coverage.md` после L2-acceptance: практический сценарий |
| [T-109.md](../tasks/T-109.md) | task | done | Последний actionable пункт roadmap `layers-coverage.md` (L1/WSL2 исключён — для svend4/пес |
| [T-110.md](../tasks/T-110.md) | task | done | Цель: после T-100/T-103/T-107/T-109 синхронизировать roadmap-документы и старые задачи с т |
| [T-111.md](../tasks/T-111.md) | task | done | Цель: сделать следующий L6-шаг после `tools/knowledge.py`: не только печатать отчёт в stdo |
| [T-112.md](../tasks/T-112.md) | task | done | Цель: проверить L6 workflow не только на `data/fixtures`, а на отдельном безопасном mini-c |
| [T-113.md](../tasks/T-113.md) | task | done | Цель: после создания `skills/*/SKILL.md` объяснить, как ими пользоваться и переносить в др |
| [T-114.md](../tasks/T-114.md) | task | done | Цель: подготовить следующий безопасный шаг для `T-020`: что должно быть проверено до любог |
| [T-115.md](../tasks/T-115.md) | task | done | Углубление L6 (направление 3 по запросу Stefan): поверх knowledge workflow добавлен |
| [T-116.md](../tasks/T-116.md) | task | done | Направление 2 по запросу Stefan (новый драйвер под реальный источник): доступ к SQLite-баз |
| [T-117.md](../tasks/T-117.md) | task | done | Цель: закрыть `next` у `T-116`: новый read-only `sqlite` driver уже реализован, но остаётс |
| [T-118.md](../tasks/T-118.md) | task | done | Цель: убрать дрейф документации после последних шагов: knowledge corpus, reports, skills u |
| [T-119.md](../tasks/T-119.md) | task | done | Цель: после `T-111` и `T-112` закрепить поведение `tools/knowledge.py report --out` тестом |
| [T-120.md](../tasks/T-120.md) | task | done | Цель: перечитать ранние документы по AI-OS Bridge / Information Workbench Layer, сверить и |
| [T-121.md](../tasks/T-121.md) | task | done | Цель: создать чистовой документ не про историю разработки, а про настоящее состояние систе |
| [T-122.md](../tasks/T-122.md) | task | done | По запросу Stefan: единый present-tense документ для агента/человека, который «подключаетс |
| [T-123.md](../tasks/T-123.md) | task | done | Цель: сравнить несколько свежих вариантов обзора системы и не оставить их параллельными мо |
| [T-124.md](../tasks/T-124.md) | task | done | Консенсусный пункт из `agent-onboarding`, `top-agent-operating-manual` и recheck: актуальн |
| [T-125.md](../tasks/T-125.md) | task | done | Консенсусный пункт: людям нужны читаемые docs, но агентам нужна короткая машинная карта те |
| [T-126.md](../tasks/T-126.md) | task | done | Консенсусный пункт: документация уже несколько раз отставала от фактов. Это опасно для мно |
| [T-127.md](../tasks/T-127.md) | task | done | Консенсусный пункт: следующий прирост ценности должен идти не только от мета-документов, а |
| [T-128.md](../tasks/T-128.md) | task | done | Консенсусный пункт: новый агент сейчас должен читать несколько файлов вручную. Нужна одна  |
| [T-129.md](../tasks/T-129.md) | task | done | Реализован самый сильный консенсус-пункт синтеза мнений (оба независимо предложили: мой §8 |
| [T-130.md](../tasks/T-130.md) | task | done | Реализован согласованный пункт C2 (мой находка N/reconcile + Codex §6.4/§7.6.3): один инст |
| [T-131.md](../tasks/T-131.md) | task | done | Завершён последний friction-killer консенсус-очереди (C1 capabilities → C2 drift → **C3 on |
| [T-132.md](../tasks/T-132.md) | task | done | Реализация решения D-016 (Stefan): ядро универсально, домен — тематический **портал/плагин |
| [T-133.md](../tasks/T-133.md) | task | done | Разногласие D1 снято решением D-016: text-extract — **генерик-способность ядра** (любой по |
| [T-134.md](../tasks/T-134.md) | task | done | Старый долг 1 (генерик-песочница). Codex сделал контракт/policy (`docs/external-code-sandb |
| [T-135.md](../tasks/T-135.md) | task | done | Старый долг/новый вопрос Stefan: коммиты в общем дереве блокируют друг друга (index.lock)  |
| [T-136.md](../tasks/T-136.md) | task | done | Открытый вопрос был вынесен в котёл на коллективное решение (D-018), потому worktree-режим |
| [T-137.md](../tasks/T-137.md) | task | done | Пакет открытых вопросов был вынесен в котёл (D-018), чтобы решения принимались через форк- |
| [T-138.md](../tasks/T-138.md) | task | done | Прямой запрос Stefan: подстроить информационный движок под вершину пирамиды, чтобы людям и |
| [T-139.md](../tasks/T-139.md) | task | done | Оформить первый clean L2-портал `portals/example/` по рекомендации `docs/pyramid-candidate |
| [T-140.md](../tasks/T-140.md) | task | done | Проверить Stage 4 core-export механизм, добавленный в `39f8612`: |
| [T-141.md](../tasks/T-141.md) | task | done | Задача: после коммита `f9a4b26` сделать котёл-пакет навигируемым и связать его с текущими  |
| [T-142.md](../tasks/T-142.md) | task | done | Реализовать следующий низкорисковый шаг по D-020/T-137: добавить `.docx` в `tools/text_ext |
| [T-143.md](../tasks/T-143.md) | task | done | Проверить новый ратифицированный пакет `D-021` и привести состояние задач/документации в с |
| [T-144.md](../tasks/T-144.md) | task | done | После `D-021` политика понятна технически, но человеку и агенту при старте задачи всё ещё  |
| [T-145.md](../tasks/T-145.md) | task | done | Разблокировано `D-021` (п.2 ратифицировал **Вариант A**: чистый `portals/<name>/` L2 + опе |
| [T-146.md](../tasks/T-146.md) | task | done | Пользователь просит вернуться к уже обсуждённым вариантам и проблемам: |
| [T-147.md](../tasks/T-147.md) | task | done | Оформить повторяющиеся проблемы разработки в явную операционную документацию: |
| [T-148.md](../tasks/T-148.md) | task | done | Политика принята (`D-022`, детально `docs/parallel-work-policy.md`); триггеры детектируютс |
| [T-149.md](../tasks/T-149.md) | task | done | Пользователь уточнил, что повторяющиеся проблемы уже стали архетипами: одни и те же “грабл |
| [T-150.md](../tasks/T-150.md) | task | done | Цель: ретроспективно проверить повторяющиеся проблемы разработки инфраструктуры, описать а |
| [T-151.md](../tasks/T-151.md) | task | done | Критерии done: |
| [T-152.md](../tasks/T-152.md) | task | done | Критерии done: |
| [T-153.md](../tasks/T-153.md) | task | done | Критерии done: |
| [T-154.md](../tasks/T-154.md) | task | done | Проблема: в репозитории уже много хороших инструкций, но нет машинного шага, который перед |
| [T-155.md](../tasks/T-155.md) | task | done | Контекст: ревизия документации выявила три практических дефекта после Q-016/Q-017: |
| [T-156.md](../tasks/T-156.md) | task | done | Контекст: `tools/instructions.py preflight` уже показывает агенту обязательные правила, но |
| [T-157.md](../tasks/T-157.md) | task | done | Контекст: после T-156 `queues/done/<T-id>.done.md` хранит evidence в поле `applied` и стро |
| [T-158.md](../tasks/T-158.md) | task | done | Контекст: T-156 добавил `--applied`, а T-157 научил verifier принимать pipeline done-марке |
| [T-159.md](../tasks/T-159.md) | task | done | Контекст: в рабочем дереве появился `tools/repo_search.py` и тест. Инструмент полезен для  |
| [T-160.md](../tasks/T-160.md) | task | done | Контекст: T-159 сделал `repo-search` отдельной верхней командой, но стартовый сценарий аге |
| [T-161.md](../tasks/T-161.md) | task | done | Контекст: в текущей среде есть возможность запускать platform sub-agent'ов, но локальный р |
| [T-162.md](../tasks/T-162.md) | task | done | Сделать launch-пакет из T-161 пригодным не только для чтения человеком, но и для машинного |
| [T-163.md](../tasks/T-163.md) | task | done | Сделать runtime-надзиратель `tools/conveyor.py` доступным через верхний слой `tools/top.py |
| [T-164.md](../tasks/T-164.md) | task | done | Нужно сделать `landed`-состояние машинно обрабатываемым: при приземлении воркфлоу можно ук |
| [T-165.md](../tasks/T-165.md) | task | done | Нужно поднять `tools/assurance.py` в верхний слой `tools/top.py`, чтобы люди и агенты виде |
| [T-166.md](../tasks/T-166.md) | task | done | Нужно расширить `tools/instructions.py check-report`: кроме обязательных evidence-токенов  |
| [T-167.md](../tasks/T-167.md) | task | done | После T-166 `conveyor.py next` всё ещё предлагал `Instruction check-report: verify referen |
| [T-168.md](../tasks/T-168.md) | task | done | По запросу Stefan оформлена методология: сколько агентов возможно динамически, какие потол |
| [T-169.md](../tasks/T-169.md) | task | done | Задача закрывает уточнение Stefan: если реальный максимум агентов ограничен не запуском, а |
| [T-170.md](../tasks/T-170.md) | task | done | Реализована первая автоматизация верхнего слоя после методологии T-169: команда `python to |
| [T-171.md](../tasks/T-171.md) | task | done | Проведён полный технический и концептуальный аудит текущего состояния проекта. |
| [T-172.md](../tasks/T-172.md) | task | done | Аудит T-171 показал: прямой PowerShell write в `tmp-work` работает, но Python `tempfile.mk |
| [T-173.md](../tasks/T-173.md) | task | done | Аудит T-171 подтвердил две medium-находки `top.py assurance all`: |
| [T-174.md](../tasks/T-174.md) | task | done | Задача переведена в `done` на основании D-025. Стратегия по умолчанию для Windows-машин: * |
| [T-175.md](../tasks/T-175.md) | task | done | P3 из FINDER→роутер→SOLVER: `decisions/D-014.md` был пустым плейсхолдером, хотя |
| [T-176.md](../tasks/T-176.md) | task | done | Q-017 (открыт Stefan) — автоматизация слияния документации агентов: находить общие пункты  |
| [T-177.md](../tasks/T-177.md) | task | done | После закрытия T-176 `python tools\conveyor.py next` всё ещё предлагает Q-017 semantic doc |
| [T-178.md](../tasks/T-178.md) | task | done | T-177 обновил perspective backlog. Первый актуальный пункт — result-intake classifier: пер |
| [T-179.md](../tasks/T-179.md) | task | done | После T-177 `conveyor.py next` предлагает `Conveyor regulate` как следующий самостоятельны |
| [T-180.md](../tasks/T-180.md) | task | done | Из FINDER doc-vs-reality (P16, P17): два genuinely-undone пункта Q-016, корректно |
| [T-181.md](../tasks/T-181.md) | task | done | Это конвенция-разрыв: задачи помечены done без файла-маркера. Решение: либо **бэкфилл** |
| [T-182.md](../tasks/T-182.md) | task | done | После `doc_consensus.py --semantic` и `synthesis_helper.py` нужен gate (в `tools/validate. |
| [T-183.md](../tasks/T-183.md) | task | done | Use result-intake classes in `top.py process-landed` instead of simple string matching. |
| [T-184.md](../tasks/T-184.md) | — | done | Реализовать механизм, при котором агенты вместо создания отдельных тяжелых Git Worktrees ( |
| [T-185.md](../tasks/T-185.md) | — | done | Вопрос из Котла: Является ли "ядро" (core) уже полноценным движком (ОС) или это всё еще на |
| [T-186.md](../tasks/T-186.md) | task | done | **Цель:** разобраться с failed-маркерами в очереди и не дать им гнить. |
| [T-187.md](../tasks/T-187.md) | task | done | **Цель:** проверить, что новые инструменты Claude/Codex работают, не ломают канон. |
| [T-188.md](../tasks/T-188.md) | task | done | **Цель:** найти и устранить информацию, которая "лежит мёртвым грузом" — устарела, не испо |
| [T-189.md](../tasks/T-189.md) | task | done | **Цель:** агенты видят друг друга, отвечают на вопросы, не пропадают. |
| [T-190.md](../tasks/T-190.md) | task | done | Из self-improve workflow (`wt9v0foqy`, 9 предложений) роутер применил 5 чистых |
| [T-191.md](../tasks/T-191.md) | task | done | Согласно Q-017 (одобрено через Котёл-пакет), механического/лексического слияния документов |
| [T-192.md](../tasks/T-192.md) | task | done | Ретро code-fix переименовал `tools/queue.py` → `tools/agent_queue.py` (устранил затенение |
| [T-193.md](../tasks/T-193.md) | task | done | локальный `def configure_output()`. Первый батч (свободные+покрытые тестом: cohort, commit |
| [T-194.md](../tasks/T-194.md) | task | done | Этот id был создан как пустой резерв и не содержал реальной задачи, критериев done или вла |
| [T-195.md](../tasks/T-195.md) | task | done | Добавить минимальный read-only слой post-hoc evidence addendum: |
| [T-196.md](../tasks/T-196.md) | task | done | T-176 закрыл seam и budget guard для консенсуса, но широкая semantic-сборка требует безопа |
| [T-197.md](../tasks/T-197.md) | task | done | Файл перспективного бэклога (`topics/perspective-backlog-YYYY-MM-DD.md`) пока обновляется  |
| [T-198.md](../tasks/T-198.md) | task | done | **Цель:** проверить, что инструменты self-improve (Codex) работают и не ломают канон. |
| [T-199.md](../tasks/T-199.md) | task | done | **Цель:** README.md не содержит новые папки, созданные при масштабировании. |
| [T-200.md](../tasks/T-200.md) | task | done | **Цель:** зафиксировать изменения, не создавая хаоса в git. |
| [T-201.md](../tasks/T-201.md) | task | done | **Цель:** не оставлять failed-задачи гнить в очереди. |
| [T-202.md](../tasks/T-202.md) | task | done | **Цель:** зафиксировать всё выполненное за сессию. |
| [T-203.md](../tasks/T-203.md) | task | done | **Цель:** актуальный статус-отчёт для людей и агентов. |
| [T-204.md](../tasks/T-204.md) | task | done | **Цель:** quickstart-гайды содержат актуальную информацию. |
| [T-205.md](../tasks/T-205.md) | task | done | **Цель:** STATUS.md отражает текущее состояние. |
| [T-206.md](../tasks/T-206.md) | task | done | Из C (RSI-автоматизация). P15 (re-measure дельта) и P16 (auto-archive stale streams) **сде |
| [T-207.md](../tasks/T-207.md) | task | done | Из FINDER-фронтира P12/P13. **Дизайн доказан вживую** (гейт прогнан READY), но `promote.py |
| [T-208.md](../tasks/T-208.md) | task | done | Из FINDER-фронтира: крупнейший непостроенный слой (execute-sandbox, 10 пунктов). Дизайн — |
| [T-209.md](../tasks/T-209.md) | task | done | **Цель:** Единственная защита от затирания чужого done/failed (`require_holder/claim_id-fe |
| [T-210.md](../tasks/T-210.md) | task | done | **Цель:** Статус задачи T-174 (WinError-5 async-stdio MCP) лжёт на 4 поверхностях (frontma |
| [T-211.md](../tasks/T-211.md) | task | done | **Цель:** Закрыть gap'ы из finder-frontier (P7: `permissions.match()` glob без теста, P8:  |
| [T-212.md](../tasks/T-212.md) | task | done | Из трека T-208 (execute-sandbox). |
| [T-213.md](../tasks/T-213.md) | task | done | Q-010 открыт. Все задачи в котле выполнены или заблокированы — идеальное «окно без активно |
| [T-214.md](../tasks/T-214.md) | task | done | Этап 4 трека execute-sandbox (вариант B). |
| [T-215.md](../tasks/T-215.md) | task | done | — |
| [T-216.md](../tasks/T-216.md) | task | done | Этапы 5 и 6 трека execute-sandbox (вариант B). |
| [T-217.md](../tasks/T-217.md) | task | done | Этапы 7 и 8 трека execute-sandbox. |
| [T-218.md](../tasks/T-218.md) | task | done | Контекст: `tools/doc_synthesis.py` добавлен как первый read-only scanner для произвольных  |
| [T-219.md](../tasks/T-219.md) | — | done | Батч-тесты показали 19/19 успешных запусков, но замечена уязвимость: маскировка (`redactio |
| [T-220.md](../tasks/T-220.md) | — | done | В ходе аудита выявлено два пула проблем: техническая уязвимость пайплайна (нет строгих fen |
| [T-221.md](../tasks/T-221.md) | task | done | Взять один пункт из полосы `ratify-build` в `docs/cauldron-two-lane-board-2026-06-24.md` и |
| [T-222.md](../tasks/T-222.md) | task | done | Взять один пункт из полосы `divergence-detail` в `docs/cauldron-two-lane-board-2026-06-24. |
| [T-223.md](../tasks/T-223.md) | — | done | Согласно консенсусу (layered-architecture, metadata-indexes), нужно сделать D-Cards (визит |
| [T-224.md](../tasks/T-224.md) | — | done | Согласно решению D-XXX (Техническая безопасность важнее удобства), нам нужно внедрить стро |
| [T-225.md](../tasks/T-225.md) | — | done | Необходимо разрешить два архитектурных разногласия, выявленных в ходе синтеза: |
| [T-226.md](../tasks/T-226.md) | — | done | Нужно встроить проверку D-Cards в ядро проекта, но не ломать CI. |
| [T-227.md](../tasks/T-227.md) | task | done | Закрыть свежий assurance debt после параллельных задач `T-223` и `T-224`, не переписывая ч |
| [T-228.md](../tasks/T-228.md) | task | done | Устранить свежую жалобу из `queues/outbox/2026-06-24-t223-id-collision.md` и `queues/outbo |
| [T-229.md](../tasks/T-229.md) | task | done | Начать поэтапное закрытие metadata soft-check долга: добавить D-Card визитки в малый набор |
| [T-230.md](../tasks/T-230.md) | — | done | Продолжить уменьшение D-Card metadata debt после T-229 малым проверяемым пакетом для верхн |
| [T-231.md](../tasks/T-231.md) | — | done | Убрать актуальный warning `assurance currency`: принятое решение `decisions/D-025.md` имее |
| [T-232.md](../tasks/T-232.md) | — | done | Закрыть текущий metadata soft-check: `tools/portability_check.py` не имеет машинно читаемо |
| [T-233.md](../tasks/T-233.md) | task | done | Эксперимент Self-Reflection показал, что многие скрипты `tools/*.py` жестко привязаны к `R |
| [T-234.md](../tasks/T-234.md) | task | done | Во время dogfooding-эксперимента `result_intake.py` классифицировал скрипт `pipeline.py` к |
| [T-235.md](../tasks/T-235.md) | task | done | Наш текущий инструментарий (уровень C) видит код просто как текстовые файлы. Чтобы полноце |
| [T-236.md](../tasks/T-236.md) | task | done | В ходе глобального эксперимента Dogfooding мы попытались проанализировать директорию `driv |
| [T-237.md](../tasks/T-237.md) | task | done | При глобальном Dogfooding-эксперименте мы загрузили `indexes/` в песочницу. Оказалось, что |
| [T-238.md](../tasks/T-238.md) | task | done | The user asked whether agents may write experimental program code into a sandbox subfolder |
| [T-239.md](../tasks/T-239.md) | task | done | The multi-agent conveyor hit repeated reset and UI-indicator mismatch cases: agents disapp |
| [T-240.md](../tasks/T-240.md) | task | done | The completed agent-cell synthesis recommended `conveyor recover` first. T-239 is now done |
| [T-241.md](../tasks/T-241.md) | task | done | T-239 added `tools/conveyor.py recover` as a read-only advisory diagnostic. Chandrasekhar' |
| [T-242.md](../tasks/T-242.md) | task | done | 1. CLI tools with hostile `sys.argv` behavior where `--help` can fail or trigger normal si |
| [T-243.md](../tasks/T-243.md) | task | done | The remaining gap is visibility. Agents should not manually guess which tools still need w |
| [T-244.md](../tasks/T-244.md) | task | done | T-243 added `tools/cli_inventory.py` and showed 45 remaining CLI-risk entries. The next sa |
| [T-245.md](../tasks/T-245.md) | task | done | The user asked to stop before implementation and first produce a detailed plan for collect |
| [T-246.md](../tasks/T-246.md) | task | done | The user asked to formulate a deep, logically structured and grammatically clean numbered  |
| [T-247.md](../tasks/T-247.md) | task | done | The user asked to continue studying the numbered question tree, ask new clarifying and qua |
| [T-248.md](../tasks/T-248.md) | task | done | Сделать результаты `tools/question_tree.py` доступными через верхний слой `tools/top.py`,  |
| [T-249.md](../tasks/T-249.md) | task | done | Продолжить работу с накопившимися вопросами: не только показывать дерево вопросов, но и пр |
| [T-250.md](../tasks/T-250.md) | task | done | Ответить на Q-023: какая матрица полномочий нужна для людей, AI-агентов, scout/observer/in |
| [T-251.md](../tasks/T-251.md) | task | done | Продолжить работу не с готовых ответов, а с формулирования проблем: описать триадный фракт |
| [T-252.md](../tasks/T-252.md) | task | done | Уточнить политику репозитория: содержательный “дубль” вопроса, темы или архитектурного пре |
| [T-253.md](../tasks/T-253.md) | task | done | Продолжить новую политику `independent-first variants`: если stream помечен `ready-for-syn |
| [T-254.md](../tasks/T-254.md) | task | done | Сделать применение политики `independent-first variants` удобным для людей и агентов: одна |
| [T-255.md](../tasks/T-255.md) | task | done | Закрыть следующий недоделанный пункт политики independent-first variants: после `top.py va |
| [T-256.md](../tasks/T-256.md) | task | done | После T-255 `doc_synthesis.py` умеет читать `streams/<topic>/*/STREAM.md` как corpus. След |
| [T-257.md](../tasks/T-257.md) | task | done | Исправить методологический сбой: для вопроса о предварительной работе с кодом не начинать  |
| [T-258.md](../tasks/T-258.md) | task | done | Исправить верхний инструментальный процесс так, чтобы команда запуска варианта не подталки |
| [T-259.md](../tasks/T-259.md) | task | doing | Добавить минимальный верхний механизм для пачки независимых вариантов: несколько людей/аге |
