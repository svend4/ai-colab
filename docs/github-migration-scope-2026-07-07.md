---
id: docs/github-migration-scope-2026-07-07
type: doc
title: Перенос на GitHub при 3+ агентах — что переносить, что покрывает нативный GitHub, как активируются динамические скрипты (MCP/CI/hook/CLI)
status: draft
related: [docs/scaling-storage-nas-vs-github-2026-07-07, D-036, D-039, D-026, D-010, work_admission, worktree_gate, next_id, crdt_merge]
created: 2026-07-07
source: workflow github-migration-scope-analysis (7 агентов: 4 классификатора × срезы + 2 перспективы + синтез)
---

# Перенос репозитория на GitHub при работе 3+ агентов над одним проектом: единый архитектурный ответ

*Отвечает на 4 вопроса Stefan: (1) переносить ли ВСЁ, (2) наши скрипты — динамика и её использование, (3) КАК активируется (MCP или иначе), (4) технически ли оправдано и для чего конкретно.*

## 1. Короткий прямой ответ

**Нет, переносить «всё как есть» не нужно, и одной нативной инфраструктуры GitHub тоже НЕ достаточно.** Правильный ответ — не «репо → GitHub» и не «оставить локально», а **смена архитектурной модели** плюс **разделение труда между GitHub и нашим кодом**:

1. **Сменить модель координации.** Уйти от «N агентов дерутся за ОДНО рабочее дерево на 4-ядерной локальной машине» к «**клон/ветка-на-агента + Pull Request + merge queue**». У каждого агента свой `index` и своё дерево — общего `index.lock` больше нет.
2. **Целый класс наших скриптов при этом становится ненужным** (`commit_lock.py`, `worktree.py`, `worktree_gate.py`, `_claims.py`, `queue.py`, `seq_merge.py`) — их единственная причина существования это гонки за общее дерево, которых в PR-модели нет. Это **отрицательный оверхед**: минус код, минус сложность.
3. **Но GitHub принципиально не знает нашу ДОМЕННУЮ семантику.** Целостность канона (D-026), ссылки/статусы/драйверы, недеструктивная политика, DAG `depends_on`-приоритизация, эпистемика независимости/кворума судей, budget-aware frozen-срез канона, приватная память `workbench.db`, атомарная выдача ID между клонами, кап нагрузки по ЯДРАМ хоста — **всё это остаётся нашим кодом**. Оно не удаляется, а **перемещается** с локальных choke-point'ов на серверные `required status checks` и в MCP-инструменты рантайма.

**Честная граница:** нативный GitHub покрывает **ГДЕ и КОГДА** запускать гейт и **КАК** сериализовать слияние. Наш код покрывает **ЧТО именно** проверять и **рантайм-подачу контекста** агенту. Репо уже реализует этот паттерн: `.github/workflows/bulk-guard.yml` запускает `validate.py` + `generate.py --check` + инлайн-D-026-guard как блокирующие проверки на PR/push в main.

**Итог по объёму:** ~60–70% инвентаря упрощается/удаляется почти бесплатно; но 2–3 критических узла (**выдача ID**, **кап нагрузки по ядрам**, **приватная память/MCP-политика**) требуют сфокусированной работы и НЕ должны быть наивно переброшены на GitHub.

## 2. Разделение труда: нативный GitHub vs наш код

### Забирает нативный GitHub (наш код — subsumed/adapt)

| Задача координации | Нативный механизм GitHub | Наши скрипты | Судьба |
|---|---|---|---|
| Изоляция агентов (свой index/worktree) | clone/branch-per-agent — изоляция по построению | `worktree.py`, `worktree_gate.py`, `ownership.py` | **subsumed** |
| Сериализация слияния в main | merge queue + required checks | `commit_lock.py`, `commit_queue.py`, `seq_merge.py` | **subsumed** |
| Запрет прямого push / обязательный PR | branch protection (`--no-verify` НЕ обходит) | барьер-роль `commit.py`, `worktree_gate.py` | **subsumed как барьер** |
| Место запуска гейтов | Actions + required status check | `bulk-guard.yml`, `canon-check.yml` (живут) | **keep-essential** |
| Claim/очередь задач | Issues + assignees + Projects + labels | `_claims.py`, `queue.py`; `agent_queue`/`cohort`/`flow`/`top` → `gh`-обёртки | **subsumed / adapt** |
| Человек в цикле / подтверждение | required reviewers + CODEOWNERS | human-gate в `autonomy_guard.py` | частично **subsumed** |
| Защита путей/авторство | CODEOWNERS + path filters | `permissions.py` | **adapt** |
| Remote git-история | REST/GraphQL + code search | `drivers/git-log` (remote) | **adapt** (самый заменяемый) |
| Публикация HTML-срезов | Pages / Actions-artifact | `view_html.py` | **adapt** |

### Остаётся нашим кодом (GitHub не может)

| Задача | Почему GitHub не может | Скрипты | Судьба |
|---|---|---|---|
| Доменная целостность канона | GitHub умеет лишь запустить exit-код и блокнуть merge — логику не знает | `validate.py` | **keep-essential** |
| Недеструктивная политика D-026 | нет нативной фичи; единственный барьер, что `--no-verify` не обходит | `bulk_guard.py --range` | **keep-essential** |
| Детекторы дрейфа/коллизий | нет нативной reconcile-политики | `status_drift.py`, `reconcile.py` | **keep-useful** (non-required + annotations) |
| DAG `depends_on` + приоритет | Projects дают доску, но резолвинг зависимостей — нет | `dispatch.py`, `pipeline.py` | **keep-essential / adapt** |
| Эпистемика независимости/кворума судей | у GitHub НЕТ аналога (required reviewers — для людей, не для LLM-судей) | `independent_first.py`, `oracle_quorum.py`, `two_track.py`, `variants` | **keep-essential** |
| Governance сверх «человек подтвердил» | required reviewers = только факт ревью | `autonomy_guard.py`, `risk_gate.py`, `red_team_gate.py` | **keep-essential / adapt** |
| **Кап нагрузки по ЯДРАМ хоста** | Actions concurrency капит лишь СЕРВЕРНЫЕ прогоны; clone-per-agent НЕ снижает нагрузку на 4 ядра | `work_admission.py` / Gate B | **keep-essential (критично)** |
| Durability локальной оркестрации | нет нативного («оркестратор замолчал», смерть на компакции) | `workflow_recover.py`, `thread_runner.py`, `conveyor.py` | **keep-essential / keep-useful** |
| Семантический field-merge генератов | GitHub делает лишь построчный merge | `crdt_merge.py`, `git_reconcile.py` (merge-driver) | **keep-useful / adapt** |
| **Атомарная выдача ID между клонами** | файловый мьютекс между клонами не работает; нативного аналога нет | `next_id.py` | **adapt (самый опасный)** |
| Budget-aware frozen-срез по НАШИМ рёбрам | code search груб — не знает `related:`/`[[ссылки]]`, нет FTS5/bm25 | `view.py`, `canon_index.py`, `repo_search.py`, `knowledge.py` | **keep-essential (MCP)** |
| Приватная память + табличные данные | вне области GitHub API | `drivers/sqlite` (workbench.db), `drivers/data` | **keep (MCP)** |
| Композиция движков + политика D-010 | GitHub MCP покрывает публичный repo, не приватную память | `drivers/gateway/mcp_server.py` | **keep-essential (MCP)** |
| Локальный незакоммиченный срез | Contents API видит только committed | `drivers/files`, `drivers/git-log` (local), `drivers/codex-local` | **keep (MCP)** |
| Рендереры подачи людям | чистые stdin→stdout | `card.py`, `decision_menu.py`, `question_tree.py`, `doc_synthesis.py` | **keep-useful (agent-cli)** |

## 3. Модель активации динамических скриптов — четыре поверхности

Активация определяется не типом файла, а тремя осями: **(А) обходимость** (`--no-verify` обходит только локальные хуки), **(Б) где живёт состояние** (общее дерево → гонки; клон-на-агента снимает), **(В) статика vs динамика** (канон `.md`/`index.json` — данные; исполняются только `tools/*.py` и `drivers/*/mcp_server.py`). Скрипт не «угадывается по файлу»: MCP-инструменты видны в `list_tools` (модель выбирает по имени/докстрингу); CLI — по документированным точкам входа; гейты агент не «зовёт» — их триггерит git-событие.

**Поверхность 1 — CI-Actions (авторитетный барьер).** На `pull_request`/`push` в main: блокирующие доменные гейты как **required status checks**; nav-генерация ПОСЛЕ merge; governance. `--no-verify` серверный check не обходит. Примеры: `validate.py`, `bulk_guard.py --range`, `generate.py --check`; после merge — `generate.py`/`folder_index.py write-all; `oracle_quorum`/`risk_gate`/`red_team_gate`; advisory — `status_drift`/`reconcile` (non-required). **Уже живёт:** `bulk-guard.yml`, `canon-check.yml`, `nightly-tests.yml`.

**Поверхность 2 — Local-hook (быстрый fail-fast, НЕ барьер).** На `git commit` в клоне агента; merge-driver при merge/rebase хот-файлов. Мгновенный отказ до push (эргономика, не авторитет). Примеры: `tools/githooks/pre-commit`, `validate_staged.py` (секунды vs ~2-мин полный), `crdt_merge.py`/`git_reconcile.py` как `merge=crdt` через `.gitattributes` (**уже подключён** для tasks/decisions/questions/topics). `commit.py` → тонкая обёртка.

**Поверхность 3 — Agent-CLI (координация + durability + локальный кап).** При claim/ship задачи; при запуске/восстановлении фоновых прогонов; **перед допуском нового локального агента**. Примеры: `work_admission.py`/Gate B (кап по ЯДРАМ), `workflow_recover`/`thread_runner`/`conveyor` (durability), `agent_queue`/`cohort`/`flow`/`top`/`stream` → `gh issue/pr/edit`-обёртки + Projects, форматтеры (`card`/`decision_menu`/`question_tree`).

**Поверхность 4 — MCP-сервер (рантайм-контекст агенту) — прямой ответ на «КАК активируется».** В рантайме по запросу («дай срез канона», «найди решение», «выдай ID», «читай workbench.db»). Механика: агент зовёт **MCP-tool вместо запуска сырого скрипта** — и получает **allowed-root + audit (`audit.py`) + redaction (`redaction.py`) «бесплатно»** на уровне сервера. Транспорт: `stdio + FastMCP`, песочница через env `*_BASE`. Примеры: `next_id.py` (централизованный выдатчик), `view`/`canon_index`/`repo_search`/`knowledge` (frozen-срез + FTS5/bm25), `drivers/gateway` (композиция + D-010), `drivers/sqlite` (`mode=ro`), `data`/`files`/`git-log`/`repo-runner`/`codex-local`.

**Кто держит MCP-сервер — локально у агента или общий:**

| Сервер | Размещение | Причина |
|---|---|---|
| `gateway/mcp_server.py` | **ОБЩИЙ** (1 процесс у оркестратора) | единая точка политики D-010, один endpoint |
| `sqlite` (workbench.db) | **ОБЩИЙ** | память команды — один источник |
| `next_id.py` | **ОБЩИЙ** | атомарность ID только из одного источника |
| `repo-runner` | **ОБЩИЙ** (с кэшем) | инвентарь одинаков на коммите — считать раз |
| `data` | общий при shared `DATA_DRIVER_BASE` | иначе локально |
| `files` | **ЛОКАЛЬНО** | `BASE` = приватный worktree, незакоммиченное |
| `git-log` (local) | **ЛОКАЛЬНО** | незапушенная история; remote → GitHub API |
| `codex-local` | **ЛОКАЛЬНО** | детект окружения конкретной машины |

**Ответ на вопрос 3 буквально:** динамика активируется в основном **через MCP-сервер** (рантайм-контекст + уникальность) и через **git-события Actions** (гейты) — НЕ через «запуск сырого .py агентом». Общими делаются gateway/sqlite/next_id/repo-runner; локальными — files/git-log(local)/codex-local, каждый с `BASE`, суженным до зоны агента.

## 4. Что переносить (сводка)

- **keep-essential:** `validate.py`, `bulk_guard.py`, `dispatch.py`, `independent_first.py`, `oracle_quorum.py`, `autonomy_guard.py`, `work_admission.py`, `workflow_recover.py`, `next_id.py` (MCP), `view.py`, `canon_index.py`, `repo_search.py`, `drivers/gateway`, `drivers/files`, `bulk-guard.yml`.
- **keep-useful:** `status_drift`, `reconcile`, `crdt_merge`, `two_track`, `conveyor`, `thread_runner`, `knowledge`, `view_html`, `card`, `decision_menu`, `question_tree`, `doc_synthesis`, `autolink`, `decision_propagation`, `drivers/sqlite|data|repo-runner|codex-local`, `pre-commit`.
- **adapt:** `generate`, `folder_index`, `command_index` (→ Actions после merge), `pipeline`, `permissions` (→ CODEOWNERS), `cohort`/`flow`/`top`/`stream`/`agent_queue` (→ `gh`-обёртки), `risk_gate`, `red_team_gate`, `git_reconcile`, `validate_staged`, `commit.py` (→ тонкая обёртка), `next_id` (модель ID).
- **subsumed-by-github:** `commit_lock`, `worktree`, `worktree_gate`, `ownership`, `_claims`, `seq_merge`, `commit_queue`.
- **drop:** `queue.py`; `work_admission` — **только в CI-части**.

> **Ловушка (важно).** `work_admission`/Gate B помечен и как subsumed (для CI), и как keep-essential (для локальных агентов). Это НЕ противоречие: Actions concurrency капит облачные прогоны, но локальные 6 клонов + локальные MCP-серверы так же насыщают 4 ядра (git 24–59с под 6 агентами — стресс-тест). **Клон-на-агента изолирует ДЕРЕВО, но не ЯДРА.**

## 5. Статика vs динамика

**Статика (данные — читаются/генерируются, не «запускаются»):** канон `tasks|decisions|questions|topics/**/*.md`; деривативы nav (`STATUS.md`, board, `index.json`, `indexes/*.md`). GitHub хранит их нативно. Дериваты nav лучше **не коммитить** (генерить в CI/на чтение) — тогда гейт свежести для них не нужен; если оставить трекуемыми — обязателен `crdt` merge-driver, иначе 3 агента, регенерящие один `STATUS.md`/`index.json`, дают детерминированный merge-конфликт.

**Динамика (исполняется):** GitHub исполняет узкий класс (доменные гейты в Actions как exit-код); основную динамику исполняют агенты через MCP и agent-CLI. **Ответ на вопрос 2:** да, скрипты используются динамически — но GitHub «активно использует» не логику, а их **вердикт** (pass/fail) для блокировки merge; остальное — на стороне агентов.

## 6. Технически ли оправдано и нагрузка

Оправдано, но избирательно — там, где перенос **снимает координацию с локальной ФС на сервер/сервис**:
- Гейты в Actions уводят ~2-мин `validate.py` с каждого локального коммита в облако (иначе коммиты по 5–10 мин у 3 агентов).
- Nav-генерация после merge в ОДНОМ процессе устраняет детерминированный merge-конфликт `STATUS.md`/`index.json`.
- Удаление subsumed-класса — отрицательный оверхед.
- MCP-ретривал даёт budget-aware срез под задачу вместо «тянуть весь репо».

Где нагрузка МЕШАЕТ: (1) `work_admission`/Gate B нельзя выкинуть — локальные клоны+MCP насыщают ядра; (2) общий MCP-сервис — точка сериализации, нужен кэш + кап.

Оверхед переноса: **дёшево** — гейты в CI (почти сделано) + branch protection/required checks/merge queue (конфиг, ~0 кода); **средне** — `depends_on` поверх Projects, `gh`-обёртки, merge-driver (уже в `.gitattributes`); **дорого/рискованно** — `next_id` (смена модели) + глобальный локальный кап.

## 7. Риски + разделение «человек / агенты»

**Топ-риски:**
1. **ID-выдача между клонами — тихий баг двойной выдачи.** `O_CREAT|O_EXCL` в `next_id.py` атомарен только в общей ФС; между клонами общей ФС нет → мьютекс молча не срабатывает → два агента получают один `T-id`. **Самый опасный.** Нужен централизованный MCP-выдатчик или git-branch-per-id.
2. **Кап нагрузки нельзя делегировать GitHub** — ложная вера «PR решил concurrency» → насыщение ядер.
3. **Merge queue сериализует, но не сливает по полям** — хот-файлы дадут построчные конфликты; смягчение: nav только в CI после merge + `crdt` driver.
4. **Утрата эпистемики** — required reviewers ≠ кворум LLM-судей ≠ `independent_first` (produce-before-reading).
5. **MCP в общем контуре без прогона = канал утечки** — сузить `allowed-root` (`*_BASE`) до зоны агента; прогон `mcp_handshake_test`/`mcp_acceptance_test` до сети; `codex-local` за пределы `--version` выводит из read-only (D-010).
6. **Durability** — «оркестратор замолчал»/смерть на компакции GitHub не покрывает.
7. **Общий MCP как единая точка отказа** — падение = слепнут все агенты.
8. **Рассинхрон версий скриптов между клонами** — авторитет только на серверном required check (там версия одна).
9. **Потеря file-native формата** — держать канон file-native как источник истины, Issues — как проекцию.

**Решает ЧЕЛОВЕК:** санкция на смену модели (клон/ветка + PR + merge queue); настройка branch protection/required checks/merge queue/CODEOWNERS; выбор модели `next_id`; значение глобального локального капа под число ядер; санкция на шаги `codex-local` за пределы `--version`; что остаётся file-native, что становится проекцией.

**Дорабатывают АГЕНТЫ:** `gh`-обёртки поверх Issues/Projects; `depends_on`-резолвинг поверх Projects API; единый Actions-job nav после merge; оформление `next_id` как MCP-сервиса (после решения человека); прогон MCP-приёмок; идентичная установка `crdt` driver во всех клонах и на раннере; перевод локального `pre-commit` в WARN/fail-fast + дублирование истинных барьеров как required checks.

---

**Одной фразой:** переносить не «всё», а **менять модель** — GitHub берёт оркестрацию доступа к дереву и место запуска гейтов (клон-на-агента + PR + merge queue + required checks + branch protection), а наш код (доменные гейты, MCP-ретривал, выдача ID, кап по ядрам, эпистемика кворума) переезжает с локальных choke-point'ов на серверные required checks и в MCP-инструменты рантайма; наивно на GitHub нельзя перебрасывать три узла — **ID, кап нагрузки и приватную память/MCP-политику**.
