# Глоссарий

Термины проекта в алфавитном порядке. Каждый термин: имя → определение → где встречается. Источник: задача `dogfood-glossary` (T-017).

## Латиница (A → Z)

- **board** — навигация по темам; генерируется из front-matter тем в `board.md`. (`tools/generate.py`)
- **claim** — отметка в `queues/claimed/<task>.claim.md` о взятии задачи агентом; создаётся через `queue.py claim`, завершается через `complete`/`fail` с тем же claim_id. (`tools/queue.py`, T-009)
- **DAG (directed acyclic graph)** — граф зависимостей задач: `depends_on` в front-matter `tasks/T-XXX.md`; используется диспетчером для определения ready/blocked. (`tools/dispatch.py`, T-014)
- **D-XXX** — id принятого решения; источник `decisions/D-XXX.md`. Статусы: `proposed`, `accepted`. Текущий канон: D-001..D-009, все `accepted`. (`DECISIONS.md`)
- **done** — финальное состояние задачи в `queues/done/<task>.done.md`; создаётся автоматически при `queue.py complete`. (`tools/queue.py`)
- **fencing-token** — уникальный `claim_id`, предъявляемый при `complete`/`fail`; защищает от перехвата. (`tools/queue.py`, T-009)
- **front-matter** — блок YAML в начале файла (`id`, `type`, `status`, ...); субстрат для генератора, валидатора и `index.json`. (`tools/generate.py`, `tools/validate.py`)
- **gate / гейт (hook)** — pre-commit hook `tools/githooks/pre-commit`; запускает `validate.py` и `generate.py --check`, блокирует коммит при ERROR. (`tools/githooks/pre-commit`)
- **generate** — `tools/generate.py`; собирает `STATUS.md`, `board.md`, `TASKS.md`, `QUESTIONS.md`, `DECISIONS.md`, `index.json` из front-matter файлов-источников. (`tools/generate.py`, T-007)
- **inbox** — папка `queues/inbox/` для заданий; свободные задачи в `queue.py list` помечены `[свободна]`. (`tools/queue.py`)
- **index** — машиночитаемая сводка `index.json`; генерируется из front-matter; одна точка вместо N файлов. (`index.json`, T-011)
- **lease / TTL** — срок жизни claim'а (по умолчанию 30 минут); после истечения другой агент может перехватить. (`tools/queue.py`, T-009)
- **message** — отдельный файл в `темы/<topic>/messages/` для больших тем; правило D-002 — одно сообщение = один файл. (`PROTOCOL.md` §3, `decisions/D-002.md`)
- **outbox** — папка `queues/outbox/` для результатов агента до внесения в основные файлы. (`PROTOCOL.md` §4)
- **permission** — `tools/permissions.py` + `tools/permissions.json`; проверяет, что изменения агента в его worker-зоне (совещательный guard). (`tools/permissions.py`, T-012)
- **protocol** — `PROTOCOL.md`; правила совместной работы (уровни, очереди, реестр агентов, обоснование, git). (`PROTOCOL.md`)
- **Q-XXX** — id вопроса в `questions/Q-XXX.md`; статусы: `open`, `answered` (со ссылкой на D-XXX). (`QUESTIONS.md`)
- **queue** — `tools/queue.py`; атомарная очередь задач (claim/complete/fail/release/list/check) с TTL-lease и fencing-token. (`tools/queue.py`, T-009)
- **shard / шардирование** — разделение большого реестра на маленькие файлы-источники (`tasks/*`, `questions/*`, `decisions/*`); убирает класс дрейфа «правки одной таблицы многими». (`tools/generate.py`, T-008)
- **status** — поле в front-matter; возможные значения зависят от типа (для задач — `todo`/`doing`/`done`; для вопросов — `open`/`answered`; для решений — `proposed`/`accepted`; для тем — `open`/`done`/`archive`). (`tools/validate.py`)
- **summary** — `темы/<topic>/summary.md`; собранный итог обсуждения в большой теме; пишется человеком или сборщиком по D-006. (`PROTOCOL.md` §8)
- **T-XXX** — id задачи в `tasks/T-XXX.md`; жизненный цикл: `todo` → `doing` → `done`. (`TASKS.md`)
- **topic** — обсуждение в `темы/<topic>.md` (маленькая) или `темы/<topic>/` (большая, с messages). (`PROTOCOL.md` §2)
- **validate** — `tools/validate.py`; проверяет канон (id, статусы, ссылки, depends_on); запускается pre-commit и вручную. (`tools/validate.py`, T-006)

## Кириллица (А → Я)

- **агент (agent)** — участник-исполнитель (ИИ или скрипт) с именем и ролью в `AGENTS.md`; имеет worker-зону в `tools/permissions.json`. (`AGENTS.md`)
- **гейт** — см. `gate`.
- **диспетчер (dispatcher)** — `tools/dispatch.py`; показывает задачи `todo` с выполненными `depends_on` (ready) и заблокированные (blocked); не редактирует файлы. `doing` и `done` намеренно не показываются (активная работа и сделано — не «готово к взятию»). (`tools/dispatch.py`, T-014)
- **доска (board)** — `board.md`; генерируемая навигация по темам. (`tools/generate.py`)
- **задача (task)** — единица работы в `tasks/T-XXX.md`; жизненный цикл: `todo` → `doing` → `done`. (`TASKS.md`)
- **индекс** — см. `index`.
- **канон (canon)** — `STATUS.md`, `TASKS.md`, `QUESTIONS.md`, `DECISIONS.md`, `board.md`, `PROTOCOL.md`, `AGENTS.md`, `index.json` плюс файлы-источники; согласованность проверяется валидатором. (`tools/validate.py`)
- **обоснование правки** — короткое объяснение в `темы/<topic>.md` или `dialog.md` при изменении служебных файлов; требуется для значимых правок по D-003, границы — D-008. (`PROTOCOL.md` §7, `decisions/D-003.md`, `decisions/D-008.md`)
- **онбординг (onboarding)** — процесс добавления нового агента; по D-009 — само-регистрация (вариант A) для 4 кооперативных, эволюция к C при росте числа агентов или снижении доверия. (`decisions/D-009.md`)
- **очередь (queue)** — `queues/` с подпапками `inbox/`, `claimed/`, `outbox/`, `done/`, `failed/`; атомарные операции через `tools/queue.py`. (`PROTOCOL.md` §4)
- **поддерживающий агент (maintainer)** — Claude или Codex; готовит задачи в inbox, ревьюит результаты, может переводить решения в `accepted` (явно по D-006). (`AGENTS.md`, T-012)
- **правка (edit)** — изменение файла; значимая правка (структура, правила, смысл) требует обоснования по D-003/D-008. (`decisions/D-003.md`, `decisions/D-008.md`)
- **рабочий агент (worker)** — Mavis или Novax; берёт задачи из inbox через `queue.py claim`, пишет в свою worker-зону, не утверждает решения. (`AGENTS.md`, T-012)
- **реестр агентов** — `AGENTS.md`; таблица всех участников-исполнителей с зонами записи и ограничениями. (`AGENTS.md`)
- **решение (decision)** — принятый итог в `decisions/D-XXX.md`; статусы: `proposed` (предложено), `accepted` (утверждено человеком или сборщиком по D-006). (`DECISIONS.md`, `decisions/D-006.md`)
- **риск-гейтинг (risk gate)** — `tools/risk_gate.py`; классифицирует задачу по полю `risk` (`low`/`medium`/`high`) и подсказывает режим AUTO/REVIEW/HUMAN. (`tools/risk_gate.py`, T-015)
- **сборщик итогов** — человек или AI-агент по D-006: переводит решения из `proposed` в `accepted`. (`decisions/D-006.md`)
- **служебный файл** — `STATUS.md`, `TASKS.md`, `QUESTIONS.md`, `DECISIONS.md`, `PROTOCOL.md`, `AGENTS.md`, `board.md`, `dialog.md`, файлы в `templates/`, `queues/README.md`; правка требует обоснования по D-003. (`PROTOCOL.md` §7)
- **сообщение (message)** — см. `message`.
- **статус (status)** — см. `status`.
- **тема (topic)** — см. `topic`.
- **шардирование (sharding)** — см. `shard`.