# Глоссарий

Термины проекта в алфавитном порядке. Каждый термин: имя → определение → где встречается. Источник: задача `dogfood-glossary` (T-017); срез актуализирован 2026-07-05. Живой источник числа решений/тем/задач и их текущих статусов — `index.json` (генерируется `tools/generate.py`); глоссарий счётчики намеренно не дублирует.

## Латиница (A → Z)

- **board** — навигация по темам; генерируется из front-matter тем в `board.md`. (`tools/generate.py`)
- **claim** — отметка в `queues/claimed/<task>.claim.md` о взятии задачи агентом; создаётся через `queue.py claim`, завершается через `complete`/`fail` с тем же claim_id. (`tools/agent_queue.py`, T-009)
- **cohort** — `tools/cohort.py`; «одна кнопка» параллельной много-агентной работы: `board` (дашборд котла/claim'ов/дрейфа), `plan` (раздать готовые задачи агентам без коллизий), `guard` (триггеры Уровня-1: пора ли уходить в worktree), `gate` (пред-merge гейт), `ship` (коммит под commit-lock с selective-add), `self` (самохостинг: движок проверяет сам себя). (`tools/cohort.py`, `decisions/D-017.md`, `decisions/D-022.md`)
- **conveyor** — `tools/conveyor.py`; надзиратель конвейера фоновых воркфлоу: реестр запусков в `logs/conveyor.json`, heartbeat оркестратора, вердикт REFILL/PROCESS/IDLE, чтобы конвейер не осушался. Не путать с `pipeline` (конвейер задач). (`tools/conveyor.py`, `docs/workflow-conveyor-policy.md`)
- **DAG (directed acyclic graph)** — граф зависимостей задач: `depends_on` в front-matter `tasks/T-XXX.md`; используется диспетчером для определения ready/blocked. (`tools/dispatch.py`, T-014)
- **D-XXX** — id решения; источник `decisions/D-XXX.md`. Статусы: `proposed`, `accepted`, `rejected`, `superseded`. Актуальное число решений и их статусы — в `index.json` (живой источник), не в этом глоссарии. (`DECISIONS.md`, `tools/validate.py`)
- **done** — финальное состояние задачи в `queues/done/<task>.done.md`; создаётся автоматически при `queue.py complete`. (`tools/agent_queue.py`)
- **fencing-token** — уникальный `claim_id`, предъявляемый при `complete`/`fail`; защищает от перехвата. (`tools/agent_queue.py`, T-009)
- **front-matter** — блок YAML в начале файла (`id`, `type`, `status`, ...); субстрат для генератора, валидатора и `index.json`. (`tools/generate.py`, `tools/validate.py`)
- **gate / гейт (hook)** — pre-commit hook `tools/githooks/pre-commit`; запускает `validate.py` и `generate.py --check`, блокирует коммит при ERROR. (`tools/githooks/pre-commit`)
- **generate** — `tools/generate.py`; собирает `STATUS.md`, `board.md`, `TASKS.md`, `QUESTIONS.md`, `DECISIONS.md`, `index.json` из front-matter файлов-источников. (`tools/generate.py`, T-007)
- **inbox** — папка `queues/inbox/` для заданий; свободные задачи в `queue.py list` помечены `[свободна]`. (`tools/agent_queue.py`)
- **index** — машиночитаемая сводка `index.json`; генерируется из front-matter; одна точка вместо N файлов. (`index.json`, T-011)
- **lease / TTL** — срок жизни claim'а (по умолчанию 30 минут); после истечения другой агент может перехватить. (`tools/agent_queue.py`, T-009)
- **merge-gate** — `tools/merge_gate.py`; гейт перед вливанием работы (worktree-ветки/притока, stream'а) в основную линию: `validate.py` + `generate.py --check` + `permissions.py` (+ тесты по `--with-tests`); exit 0 — вливать можно, exit 1 — нет. Само слияние подтверждает merge-owner (Stefan или назначенный интегратор). (`tools/merge_gate.py`, `decisions/D-021.md`, `decisions/D-022.md`)
- **message** — отдельный файл в `topics/<topic>/messages/` для больших тем; правило D-002 — одно сообщение = один файл. (`PROTOCOL.md` §3, `decisions/D-002.md`)
- **outbox** — папка `queues/outbox/` для результатов агента до внесения в основные файлы. (`PROTOCOL.md` §4)
- **permission** — `tools/permissions.py` + `tools/permissions.json`; проверяет, что изменения агента в его worker-зоне (совещательный guard). (`tools/permissions.py`, T-012)
- **pipeline** — `tools/pipeline.py`; конвейер задач («общий котёл»): агент атомарно берёт следующую готовую задачу (`next`/`claim`), отчитывается (`done`/`fail`), шлёт `heartbeat`, смотрит ленту (`status`) и пишет снапшот (`snapshot` → `PIPELINE.md`). Объединяет диспетчер (готовность по DAG) и очередь (атомарный захват) в одну операцию pull-next — между «увидел» и «занял» нет окна для перехвата. (`tools/pipeline.py`, T-027, `PROTOCOL.md`)
- **protocol** — `PROTOCOL.md`; правила совместной работы (уровни, очереди, реестр агентов, обоснование, git). (`PROTOCOL.md`)
- **Q-XXX** — id вопроса в `questions/Q-XXX.md`; статусы: `open`, `answered` (со ссылкой на D-XXX), `closed`. (`QUESTIONS.md`, `tools/validate.py`)
- **queue** — `tools/agent_queue.py`; атомарная очередь задач (claim/complete/fail/release/list/check) с TTL-lease и fencing-token. (`tools/agent_queue.py`, T-009)
- **shard / шардирование** — разделение большого реестра на маленькие файлы-источники (`tasks/*`, `questions/*`, `decisions/*`); убирает класс дрейфа «правки одной таблицы многими». (`tools/generate.py`, T-008)
- **status** — поле в front-matter; возможные значения зависят от типа (для задач — `todo`/`doing`/`blocked`/`review`/`done`, где `blocked` — ждёт зависимость или внешнее условие, `review` — сделано, ждёт проверки; для вопросов — `open`/`answered`/`closed`; для решений — `proposed`/`accepted`/`rejected`/`superseded`; для тем статус свободнее — `open`/`done`/`archive` плюс рабочие маркеры вроде `waiting`/`needs-decision`). (`tools/validate.py`)
- **stream** — «полу-коммит»: форк-пакет варианта в `streams/<topic>/<stream-id>/STREAM.md` со своим front-matter (id/topic/agent/status); уже структурированное предложение, но ещё не mainline. Позволяет нескольким агентам параллельно развивать альтернативные подходы; принятие — `tools/stream.py adopt` (governance-решение остаётся в котле по D-018). (`PROTOCOL.md` §10, `docs/commit-stream-policy.md`, `tools/stream.py`, `decisions/D-031.md`)
- **summary** — `topics/<topic>/summary.md`; собранный итог обсуждения в большой теме; пишется человеком или сборщиком по D-006. (`PROTOCOL.md` §8)
- **T-XXX** — id задачи в `tasks/T-XXX.md`; жизненный цикл: `todo` → `doing` (→ `blocked`/`review`) → `done`. (`TASKS.md`, `tools/validate.py`)
- **topic** — обсуждение в `topics/<topic>.md` (маленькая) или `topics/<topic>/` (большая, с messages). (`PROTOCOL.md` §2)
- **validate** — `tools/validate.py`; проверяет канон (id, статусы, ссылки, depends_on); запускается pre-commit и вручную. (`tools/validate.py`, T-006)
- **worktree** — git-worktree на агента/задачу (Уровень-1 политики коммитов): отдельный рабочий каталог `<repo>-wt-<agent>-<task>` рядом с репозиторием, на ветке `agent/<agent>/<task>`. Изолирует правки и генерируемые индексы («маленький ручеёк»), в основную линию вливается через merge-gate. (`tools/worktree.py`, `docs/parallel-work-policy.md`, `decisions/D-021.md`, `decisions/D-022.md`)

## Кириллица (А → Я)

- **агент (agent)** — участник-исполнитель (ИИ или скрипт) с именем и ролью в `AGENTS.md`; имеет worker-зону в `tools/permissions.json`. (`AGENTS.md`)
- **гейт** — см. `gate`.
- **диспетчер (dispatcher)** — `tools/dispatch.py`; показывает задачи `todo` с выполненными `depends_on` (ready) и заблокированные (blocked); не редактирует файлы. `doing` и `done` намеренно не показываются (активная работа и сделано — не «готово к взятию»). (`tools/dispatch.py`, T-014)
- **доска (board)** — `board.md`; генерируемая навигация по темам. (`tools/generate.py`)
- **задача (task)** — единица работы в `tasks/T-XXX.md`; жизненный цикл: `todo` → `doing` (→ `blocked`/`review`) → `done`. (`TASKS.md`)
- **индекс** — см. `index`.
- **канон (canon)** — `STATUS.md`, `TASKS.md`, `QUESTIONS.md`, `DECISIONS.md`, `board.md`, `PROTOCOL.md`, `AGENTS.md`, `index.json` плюс файлы-источники; согласованность проверяется валидатором. (`tools/validate.py`)
- **конвейер** — два смысла: конвейер задач — см. `pipeline`; надзиратель конвейера фоновых воркфлоу — см. `conveyor`.
- **котёл** — механизм коллективного принятия решений по D-018: существенные вопросы и изменения (архитектура, политика, спорные дизайны) выносятся в pool-задачу конвейера (`pipeline.py`) + профильную тему (+ при необходимости вопрос Q-XXX) и проходят двойную перепроверку — техническую (код работает, сверка ≥2 агентами по D-015) и гуманитарную (человек/ценности/последствия). Перевод решения в `accepted` — результат коллективного синтеза, а не одного агента; котёл — место, где сравниваются форки/streams. (`decisions/D-018.md`, `tools/pipeline.py`)
- **обоснование правки** — короткое объяснение в `topics/<topic>.md` или `dialog.md` при изменении служебных файлов; требуется для значимых правок по D-003, границы — D-008. (`PROTOCOL.md` §7, `decisions/D-003.md`, `decisions/D-008.md`)
- **онбординг (onboarding)** — процесс добавления нового агента; по D-009 — само-регистрация (вариант A) для 4 кооперативных, эволюция к C при росте числа агентов или снижении доверия. (`decisions/D-009.md`)
- **очередь (queue)** — `queues/` с подпапками `inbox/`, `claimed/`, `outbox/`, `done/`, `failed/`; атомарные операции через `tools/agent_queue.py`. (`PROTOCOL.md` §4)
- **поддерживающий агент (maintainer)** — Claude или Codex; готовит задачи в inbox, ревьюит результаты, может переводить решения в `accepted` (явно по D-006). (`AGENTS.md`, T-012)
- **правка (edit)** — изменение файла; значимая правка (структура, правила, смысл) требует обоснования по D-003/D-008. (`decisions/D-003.md`, `decisions/D-008.md`)
- **рабочий агент (worker)** — Mavis или Novax; берёт задачи из inbox через `queue.py claim`, пишет в свою worker-зону, не утверждает решения. (`AGENTS.md`, T-012)
- **реестр агентов** — `AGENTS.md`; таблица всех участников-исполнителей с зонами записи и ограничениями. (`AGENTS.md`)
- **решение (decision)** — принятый итог в `decisions/D-XXX.md`; статусы: `proposed` (предложено), `accepted` (утверждено человеком или сборщиком по D-006), `rejected` (отклонено), `superseded` (заменено более новым решением). (`DECISIONS.md`, `decisions/D-006.md`)
- **риск-гейтинг (risk gate)** — `tools/risk_gate.py`; классифицирует задачу по полю `risk` (`low`/`medium`/`high`) и подсказывает режим AUTO/REVIEW/HUMAN. (`tools/risk_gate.py`, T-015)
- **сборщик итогов** — человек или AI-агент по D-006: переводит решения из `proposed` в `accepted`. (`decisions/D-006.md`)
- **служебный файл** — `STATUS.md`, `TASKS.md`, `QUESTIONS.md`, `DECISIONS.md`, `PROTOCOL.md`, `AGENTS.md`, `board.md`, `dialog.md`, файлы в `templates/`, `queues/README.md`; правка требует обоснования по D-003. (`PROTOCOL.md` §7)
- **сообщение (message)** — см. `message`.
- **статус (status)** — см. `status`.
- **тема (topic)** — см. `topic`.
- **шардирование (sharding)** — см. `shard`.