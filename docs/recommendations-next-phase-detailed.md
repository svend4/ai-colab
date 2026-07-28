---
id: doc-recommendations-next-phase
type: doc
title: "Детализированные рекомендации по следующей фазе: рационализация без удаления, инновационное reuse и закрытие Beta-0"
status: proposed
date: 2026-07-06
author: claude
related:
  - T-273
  - T-274
  - T-275
  - beta0-acceptance-checklist-2026-07-06
  - D-037
  - D-036
  - reports/fix-wave2-plan-2026-07-02
  - docs/next-stage-action-plan-2026-07-06
---

# Детализированные рекомендации по следующей фазе

> **Мета-принцип:** Ничего не удалять, не стирать. Код, текст, идеи — переиспользовать, улучшать, рационализировать. Мёртвый груз трансформировать в фундамент. Этот документ — инженерный план, а не декларация.

---

## 0. Резюме и диагностика

Проект находится в состоянии **Alpha-3 / pre-beta control plane**. Технический каркас силён: 289 задач, 38 решений, 119 инструментов, 9 драйверов, валидатор, генератор, pipeline, commit-queue, AST-sandbox. Но **следующий скачок — не через добавление новых слоёв**, а через **рационализацию существующего массива в управляемую систему**.

Главный риск: **методологическая инфляция**. 84 темы, десятки proposed-документов, архитектурные слои L0–L8 — часть из них существует только в тексте, не в коде. Главная возможность: **система уже самоприменяется** (канон управляет собой через канон), и это редкий актив, который нужно закрепить.

**Цель следующей фазы:** честный переход в Beta-0 через 10 измеримых критериев, а не через декларацию. После Beta-0 — фокус на human UX и продуктовой зрелости.

---

## 1. Критический путь: закрытие Beta-0 гейта (P0)

### 1.1. T-274: оживить heartbeat и реализовать живой tripwire параллельности

**Проблема.** `LIVE.md` пуст. Критерий Beta-0 #6 («Работающий tripwire параллельности») — ❌ НЕТ. T-274 заявлен сделанным, но heartbeat как live-инфраструктура не работает. Без этого «многоагентная работа» остаётся теорией.

**Рекомендация.** Не переписывать `pipeline.py heartbeat`. **Reuse:** использовать существующую инфраструктуру `pipeline.py heartbeat` и `logs/heartbeat/*.json`. Добавить **agent thermal map** — read-only команду `top.py thermal [--json]`, которая агрегирует `logs/heartbeat/*.json` в таблицу:
- Агент | Задача | Claim age | Время без пульса | Статус (active / stale / orphan)
- При ≥2 агентов на одной задаче → WARNING
- При claim без heartbeat > 15 мин → ERROR (tripwire)

**Техническая реализация.**
1. Переиспользовать `tools/pipeline.py` функцию `heartbeat()` — она уже пишет JSON.
2. Добавить `top.py thermal` (новый subcommand, ~80 строк): читает `logs/heartbeat/*.json`, сравнивает с `pipeline.py status` (doing/claimed), выявляет orphan doing (heartbeat мёртв, но задача в doing).
3. Не менять формат heartbeat-файлов — добавить поле `thermal_ts` опционально.
4. Reuse `tools/friction.py` логику stale-detection — аналогичный паттерн для claim-ttl.

**Обоснование.** Heartbeat существует, но нет потребителя данных. «Термальная карта» — это инновация не через новый протокол, а через **визуализацию существующего сигнала**. Tripwire = детектор аномалии на существующих данных, не новый канал связи.

**Метрика успеха.** `top.py thermal` показывает ≥1 активного агентов, Beta-0 #6 = ✅, `LIVE.md` обновляется командой, а не руками.

---

### 1.2. T-273: завершить L2 payload и дать субъективную оценку удобства портала

**Проблема.** Критерий Beta-0 #5 (≥1 end-to-end L2 payload) — 🔄 В ПРОЦЕССЕ. Пилот запущен, но нет evidence.

**Рекомендация.** Reuse существующий `drivers/files`, `drivers/workbench`, `tools/knowledge.py` для **сценария «аутентичный рабочий день агента»**:
1. Агент A запускает `top.py agent-start`, получает задачу T-273.
2. Агент A использует `drivers/files` + `drivers/repo-runner` для чтения 3–5 реальных файлов проекта.
3. Агент A складывает summary в `workbench.db` через `drivers/workbench`.
4. Агент A генерирует report через `tools/knowledge.py report --out`.
5. Человек (Stefan) открывает report и оценивает удобство по шкале 1–5 (структура, полнота, скорость).

**Техническая реализация.**
- Не создавать новый драйвер. Использовать **существующую связку** files → workbench → knowledge, которая уже прошла runtime-приёмку (T-048, T-055, T-057).
- Добавить **оценочный фреймворк** `docs/portal-evaluation-framework.md` (reuse D-016 «портал = домен как плагин») — чеклист: найти файл, прочитать, понять контекст, сгенерировать summary, проверить ссылки.
- Reuse `data/portals/bridge-knowledge/` и `data/portals/repo-inventory/` — уже есть корпус.

**Обоснование.** L2 payload не нужен как «ещё один слой», он нужен как **proof that the bridge carries traffic**. Оценка удобства — субъективна, но формализованная шкала даёт бинарный гейт.

**Метрика.** Оценка ≥3/5 по всем пунктам фреймворка → Beta-0 #5 = ✅.

---

### 1.3. T-275: пропагировать 6 accepted-решений в instruction surface

**Проблема.** `top.py health` показывает ATTENTION: D-001, D-010, D-013 (и др.) — accepted, но не отражены в `AGENTS.md`/`PROTOCOL.md`/quickstart. Агенты не видят правил, которые уже ратифицированы.

**Рекомендация.** Создать **living decision propagation pipeline** — не ручное копирование, а reuse `tools/generate.py` + `tools/decisions_usage_scan.py`:
1. Добавить в `tools/generate.py` (или отдельный `tools/decision_propagate.py`) чтение `decisions/D-*.md` со статусом `accepted`.
2. Для каждого `accepted` D-XXX проверить: есть ли его ID в `AGENTS.md`, `PROTOCOL.md`, `docs/quickstart.md`, `docs/agent-quickstart.md`.
3. Если нет — генерировать **advisory diff** (не авто-применять!): `queues/outbox/decision-propagation-D-XXX-gap.md` с рекомендуемой вставкой и rationale.
4. Человек (Stefan) или уполномоченный агент (integrator) применяет diff через обычный commit.

**Техническая реализация.**
- Reuse `tools/_canon.py` (parse_front_matter) для чтения решений.
- Reuse `tools/repo_search.py` для поиска ссылок на D-XXX в target-файлах.
- Reuse `tools/generate.py` pattern для вывода diff (GEN-блоки).
- Выход: `reports/decision-propagation-gaps.md` — список дыр, не автоправка.

**Обоснование.** Это инновация: **самоподдерживающийся instruction surface**. Система не просто знает, что решения приняты — она знает, где они *не* упомянуты, и генерирует work items. Это не удаление, это **эволюция generate.py из passive index в active consistency checker**.

**Метрика.** `top.py health` ATTENTION → 0 orphan accepted decisions → Beta-0 #4 = ✅.

---

## 2. Технический долг: fail-closed, тесты, pre-commit (P1)

### 2.1. Исправить `immune.py`: заменить fail-open на fail-closed с явным circuit breaker

**Проблема.** Находка аудита C0: `immune.py` при git-сбое возвращает «недостаточно истории (0 < 10 коммитов)», exit 0. Детектор массовых стираний самоотключается без предупреждения. Это **security-critical bug**.

**Рекомендация.** Не переписывать `immune.py`. **Reuse** логику профилирования (200 коммитов, порог 13 файлов). Добавить **circuit breaker**:
1. Если `git rev-list` возвращает пустой результат или ошибку — не fallback на «0 коммитов», а `raise ImmuneGitError("git unavailable, cannot verify safety")`.
2. Верхний уровень (`if __name__ == '__main__'`): `sys.exit(2)` при `ImmuneGitError` (не 0, не 1 — отдельный код для CI/hook).
3. Pre-commit hook: если `immune.py` exit 2 → блокировать коммит с сообщением «git safety check unavailable — verify manually or retry».
4. Добавить флаг `--fail-closed` (default True). Для ручного обхода — `--fail-closed=false` с явным WARNING.

**Техническая реализация.**
- Изменить только `immune.py` wrapper (~20 строк), не логику профиля.
- Reuse `tools/friction.py` exit-кодовую схему (0/1/2 различаются).
- Обновить `tools/githooks/pre-commit` для обработки exit 2.
- Добавить тест: `test_immune_git_failure.py` — мокает `subprocess.run` с `CalledProcessError`, проверяет exit 2.

**Обоснование.** Fail-open в security-инструменте — антипаттерн. Circuit breaker — классическая инженерная практика, применённая к существующему коду без его уничтожения. Git-сбой = неизвестность, а не «всё в порядке».

**Метрика.** Искусственный тест git failure → exit 2, pre-commit блокирует. `immune.py` не деградирует молча.

---

### 2.2. Создать `tools/test_all.py` — unified test orchestra без переписывания тестов

**Проблема.** Находка C12/C13: 6 errors под pytest (fixture `root` not found), 104 из 123 тест-файлов — самозапускающиеся `__main__`-скрипты. Pytest покрывает 19/123 файлов. Нет единого полного прогона.

**Рекомендация.** Не мигрировать 104 файла на pytest (дорого, риск поломки). **Reuse** существующую dual-pattern архитектуру:
1. Создать `tools/test_all.py` — **test orchestra conductor**.
2. Два режима:
   - **Symphony mode** (`--symphony`): прогоняет все `test_*.py` с `if __name__ == '__main__': run()` через `subprocess.run([sys.executable, path])`, агрегирует exit codes, выводит сводную таблицу (pass/fail/error/timeout).
   - **Pytest mode** (`--pytest`): запускает `pytest tools/`, но с `conftest.py` fixture `root` (фикс C12-a), добавляя совместимость для 6 ошибочных файлов.
3. Команда `top.py test` (новый subcommand) вызывает `test_all.py --symphony` как canonical full run, `--pytest` как quick run.
4. CI `.github/workflows/...` использует `test_all.py --symphony --timeout=120` для полного покрытия.

**Техническая реализация.**
- `test_all.py` (~150 строк): `glob.glob('tools/test_*.py')`, фильтрует по `__main__` guard, параллельный или последовательный прогон.
- `tools/conftest.py` (~10 строк): fixture `root` возвращает `tmp_path` + `make_drivers` (reuse логику из `test_capabilities.py` и др.).
- Не трогать 104 самозапускающихся скриптов — они остаются валидными standalone тестами.
- Переименовать проблемные функции в `test_capabilities.py` etc. только если `--pytest` mode активен (или добавить `conftest.py` сразу).

**Обоснование.** Инновация: **оркестровый паттерн** для тестов. Не «все тесты в одном формате», а «все тесты запускаются одной командой, независимо от их внутреннего устройства». Это рационализация: существующий код работает, покрытие растёт, CI честен.

**Метрика.** `test_all.py --symphony` проходит 123/123 файлов, 0 необъяснённых ошибок. Pytest mode — 70+/70+ тестов.

---

### 2.3. Pre-commit: staged-snapshot check вместо working-tree check (C1-b)

**Проблема.** Находка C1: `faab828` оставил stale индексы в HEAD, потому что pre-commit проверяет рабочее дерево, а не staged. Частичный `git add` проходит гейт.

**Рекомендация.** Reuse `tools/generate.py --check` и добавить **staged-snapshot comparison layer**:
1. В `tools/githooks/pre-commit` перед `generate.py --check`:
   - `git stash push --keep-index` (сохранить рабочее дерево, оставить только staged).
   - `python tools/generate.py --check` (проверяет staged).
   - Если FAIL → `git stash pop`, exit 1.
   - Если OK → `git stash pop`, exit 0.
2. Альтернатива (легче): добавить `generate.py --check --staged-only`, который читает `git diff --cached --name-only` и проверяет только staged-файлы на stale GEN-блоки.

**Техническая реализация.**
- Изменить только `tools/githooks/pre-commit` (~+10 строк stash logic) или добавить `--staged-only` в `generate.py`.
- Reuse `tools/generate.py` логику парсинга GEN-блоков.
- Не менять формат GEN-блоков.

**Обоснование.** Это закрывает регрессию частичного стейджинга, не меняя workflow разработчика. Stash-keep-index — стандартный git-приём для atomic pre-commit checks.

**Метрика.** Ручной тест: partial `git add` + `git commit` (без `--no-verify`) → блокировка, если GEN-блоки stale.

---

## 3. Инструментальная рационализация: 119 → управляемый флот (P2)

### 3.1. Orphan-инструменты: подключить, allowlist или архивировать через gap_scan

**Проблема.** Находка C15: 8 orphan-инструментов (`repo_hygiene.py`, `workflow_recover.py`, `cli_inventory.py`, `fold.py`, `retrieval_bench.py`, `text_brain.py`, `text_scene.py`, `thread_runner.py`) не подключены к `top.py`/`README.md`/hooks. Они либо полезны, либо мёртвый груз, но статус неопределённости — вред.

**Рекомендация.** Не удалять. Создать **instrument lifecycle manifest** (`tools/instrument_lifecycle.md` или `indexes/instrument_lifecycle.json`, генерируемый):
1. Для каждого orphan-инструмента audit:
   - Есть ли `test_*.py`? Проходит ли standalone?
   - Есть ли references в `topics/` или `tasks/`?
   - Есть ли импорты из других `tools/`?
2. Классификация (не удаление!):
   - **Active candidate** (есть тесты, есть references) → подключить к `top.py`/`README.md` (C15-a).
   - **Reserve/Hibernated** (нет тестов/ссылок, но код полезен) → добавить в `indexes/orphan_allowlist.json` с обоснованием (C15-b), убрать из `gap_scan` WARN.
   - **Archived/Deprecated** (устарел, есть замена) → переместить в `archive/tools/deprecated/` (не `rm`!), добавить `README.md` в архиве с указанием замены. Физическое удаление — запрещено принципом документа.
3. Автоматизировать через `gap_scan.py`:
   - Добавить `--classify` subcommand: анализирует каждый orphan и предлагает категорию с evidence.
   - Выход: `queues/outbox/orphan-classification-report.md` для человеческого подтверждения.

**Техническая реализация.**
- Reuse `tools/gap_scan.py` (существующий orphan-detector).
- Reuse `tools/repo_search.py` для поиска references.
- Reuse `tools/generate.py` для обновления `indexes/instrument_lifecycle.json`.
- Новый `archive/tools/` — создать папку (не удаление!).

**Обоснование.** Инновация: **lifecycle management без deletion**. Это архивология применительно к коду. Каждый инструмент сохраняет provenance, но ясно помечен статус. Это не «мусор», это «музей с каталогом».

**Метрика.** `gap_scan.py` без `--strict` → 0 orphan WARN (все классифицированы). `dir_health` для `tools/` → manageable.

---

### 3.2. Шардирование `tools/` и `queues/done`: reuse dir_health порогов, но добавить архивную логику

**Проблема.** Находка C14: `dir_health.py` FAIL — `tools/` 244 файла, `queues/done` 226 файла > порога 200.

**Рекомендация.**
1. **`tools/`**: выделить `tools/tests/` как отдельный каталог (по аналогии с `tasks/` шардированием). Переместить `test_*.py` туда (104+ файла), оставив в `tools/` только CLI-инструменты. **Не удалять тесты**, только переместить. Пути в `test_all.py` обновить.
2. **`queues/done/`**: reuse D-034 (отдельные пороги архивных каталогов). Добавить **auto-archive** — скрипт `tools/queue_archive.py`, который ежемесячно (или по триггеру) перемещает `queues/done/T-*.md` старше 90 дней в `queues/done/archive/YYYY-MM/`. Файлы сохраняются, пути логируются, но `queues/done/` остаётся <200.
3. **Root-dirs** (25 > 15): добавить в `dir_health.py` exception-list для **core directories** (`.git`, `.agents`, `tools`, `topics`, `tasks`, `docs`, `drivers`, `queues`, `data`) — они осознанно многочислены, остальные считаем.

**Техническая реализация.**
- `mkdir tools/tests/`, `git mv tools/test_*.py tools/tests/` (сохраняет историю git!).
- `tools/queue_archive.py` (~60 строк): glob, parse timestamp из filename, `shutil.move` с логированием.
- Обновить `tools/README.md` — `tests/` отдельная секция.
- Обновить `dir_health.py` core-dir exception list (~5 строк).

**Обоснование.** Шардирование — это не удаление, это **пространственная реорганизация**. Git сохраняет историю перемещения. Queue archive — классическая log rotation, применённая к markdown-задачам.

**Метрика.** `dir_health` → 0 FAIL по `tools/` (после шардинга тестов) и `queues/done` (после archive или D-034 exception).

---

## 4. Концептуальная рефакторинг: уменьшить энтропию тем (P3)

### 4.1. Тематический consolidation: merge-варианты вместо новых тем

**Проблема.** 84 темы, многие proposed, часть — перекрывающиеся концепции («алхимический синтез», «триадный фрактал», «золотая середина», «MMORPG 2D text workbench»). Это методологический мусор, который отвлекает.

**Рекомендация.** Не удалять темы. Применить **D-028 (Independent-first variants) и D-029 (Consensus-by-meaning)** к существующему корпусу тем:
1. Создать `topics/consolidation-queue/` (новая папка) — куда складывать **consolidation proposals**.
2. Для каждой группы перекрывающихся тем (например, 3 темы про «2D workbench»):
   - Создать `topics/consolidation-queue/2d-workbench-merge-proposal.md`.
   - Содержание: «Темы A, B, C содержат варианты решения X. Консенсус по смыслу: [суть]. Рекомендуется: пометить A, B как `archive`/`superseded-by-C`, не удалять.»
   - Ссылка из `topics/` front-matter: `superseded_by: consolidation-queue/...`.
3. Reuse `tools/knowledge.py` для поиска семантически близких тем (bm25/FTS5 уже есть) — автоматически предлагать consolidation candidates.
4. Добавить в `board.md` статус `superseded` для тем.

**Техническая реализация.**
- `tools/knowledge.py search "2D workbench"` → выдаёт 3 темы.
- Агент (human или claude/codex) создаёт consolidation proposal.
- `tools/generate.py` обновляет `board.md` — добавляет колонку `status` значения `superseded`.
- Не удалять оригинальные файлы — добавить `superseded_by` в их front-matter.

**Обоснование.** Это **консерваторский подход** к знаниям. Темы не стираются, но их статус становится ясным. Knowledge engine (уже построенный) используется для обнаружения дублирования, а не для создания нового.

**Метрика.** 10+ consolidation proposals созданы, 20+ тем помечены `superseded`, но файлы на месте. Новые темы без attached task — не создаются (D-037 enforcement).

---

### 4.2. D-037 enforcement: «no new tools without friction pain» gate

**Проблема.** D-037 (мягкая заморозка мета-развития) принят, но нет автоматического gate. Новые `tools/*.py` могут появляться без проверки.

**Рекомендация.** Reuse `tools/friction.py` и `tools/risk_gate.py`:
1. Добавить `tools/friction.py new-tool-gate <path>`:
   - Проверяет: есть ли `tasks/T-*.md` со статусом `doing`/`done`, связанный с этим файлом?
   - Есть ли запись в `docs/friction-ledger.md` или `tools/friction.py log` о pain, который решает этот инструмент?
   - Если нет task и нет friction-evidence → exit 1 (gate closed), с advisory: «D-037: новый инструмент требует friction-evidence или task link».
2. Добавить в `tools/githooks/pre-commit` (опционально, как WARN): если новый `tools/*.py` не проходит gate → WARN, но не блокировать (advisory, не enforcement — чтобы не создавать rigid bureaucracy).
3. В `tools/top.py health` добавить счётчик `new-tools-without-task-last-7-days`.

**Техническая реализация.**
- Reuse `friction.py` log parsing.
- Reuse `validate.py` front-matter checking для поиска task links.
- Новый subcommand ~50 строк.

**Обоснование.** D-037 — решение, но без enforcement это декларация. Advisory gate (не hard block) сохраняет гибкость, но добавляет **visibility**. «Вы можете создать инструмент, но система спросит: зачем?»

**Метрика.** `top.py health` показывает 0 новых инструментов без task/friction-link за последние 7 дней.

---

## 5. Human UX: от 40% к 70% (P4)

### 5.1. `top.py beta0` — единая команда проверки гейта

**Проблема.** Beta-0 чеклист проверяется вручную по 10 пунктам. Нет единой команды «готовы ли мы?»

**Рекомендация.** Reuse **все существующие инструменты** (`validate.py`, `generate.py --check`, `repo_hygiene.py`, `top.py health`, `friction.py`, `dir_health.py`) и агрегировать их в `top.py beta0`:
1. `top.py beta0` последовательно запускает:
   - `validate.py` → ERROR=0?
   - `generate.py --check` → STALE=0?
   - `repo_hygiene.py` → ≥95?
   - `top.py health` → не красный?
   - `friction.py status` → нет критических WARN?
   - `dir_health.py` → FAIL=0? (или с D-034 exceptions)
   - `pipeline.py status` → ready pool не пуст? (или T-273/T-274 статус)
   - Проверка T-273: есть ли `reports/portal-evaluation-*.md` с оценкой ≥3?
   - Проверка T-274: `LIVE.md` не пуст? `top.py thermal` видит агентов?
   - Проверка T-275: `top.py health` ATTENTION=0?
2. Вывод: таблица 10×2 (критерий | статус), итог: `BETA-0: NOT READY (N/10)` или `BETA-0: READY (10/10)`.
3. Флаг `--history`: сохраняет результат в `logs/beta0-history.jsonl` для отслеживания прогресса (три прогона подряд для объявления перехода).

**Техническая реализация.**
- Reuse `subprocess.run` для вызова существующих инструментов (как `drift_check.py` агрегирует другие).
- Reuse `top.py` command dispatch pattern.
- Парсинг вывода: validate.py и repo_hygiene.py уже машиночитаемы (OK/WARN/ERROR, score). Для остальных — добавить `--json` flag (если нет).
- Новый код: ~120 строк wrapper + history logger.

**Обоснование.** Это **инновация в observability**: не новый инструмент, а **композиторная панель** из существующих датчиков. Система становится самооценивающейся. History-лог позволяет увидеть тренд: «вчера 6/10, сегодня 8/10».

**Метрика.** `top.py beta0` запускается за <30 секунд, даёт бинарный ответ. Три consecutive 10/10 → объявление Beta-0.

---

### 5.2. `top.py commit-plan` — guided selective-add workflow

**Проблема.** Beta-0 #7 (понятный commit-plan workflow) — 🟡 Частично. `commit_queue.py` и `commit_lock.py` есть, но нет единой «кнопки» для человека.

**Рекомендация.** Reuse `tools/commit_queue.py`, `tools/commit_lock.py`, `tools/friction.py` (dirty classification) для **guided commit wizard**:
1. `top.py commit-plan`:
   - Запускает `friction.py status` → показывает dirty files с классификацией: mine / generated / volatile / foreign / unknown.
   - Для каждого foreign/volatile: предупреждение «Consider Level 1 worktree (D-022)».
   - Предлагает selective-add группировки: «Add all mine files», «Add generated (validate first)?», «Skip foreign».
   - Генерирует готовый shell-script или PowerShell-script: `git add file1 file2 ... && git commit -m "T-XXX: description"`.
   - Проверяет `commit_lock.py` — если lock занят, ждёт или предлагает `--wait`.
2. Выход: `queues/outbox/commit-plan-TIMESTAMP.sh` (или `.ps1`), который человек может review и execute.

**Техническая реализация.**
- Reuse `friction.py` dirty classifier (T-153).
- Reuse `commit_queue.py` для очереди.
- Reuse `commit_lock.py` для advisory lock.
- Новый wrapper ~100 строк.
- Генерация скрипта — простой string template, не сложный.

**Обоснование.** Это **human-in-the-loop automation**. Система не коммитит за человека, но готовит **reviewable plan**, уменьшая когнитивную нагрузку при 40+ changed files. Это reuse существующей инфраструктуры safety.

**Метрика.** Человек делает коммит через `top.py commit-plan` → review script → execute → 0 accidental `git add -A`.

---

## 6. Инновации следующего горизонта (P5 — после Beta-0)

### 6.1. Instruction Surface Reconciliation (ISR) — автоматический аудит применимости решений

**Идея.** Расширение T-275/D-037. Создать `tools/instruction_reconcile.py` — **периодический аудит** того, принимаются ли решения на практике:
1. Для каждого `accepted` D-XXX: искать evidence применения в `tasks/*.md`, `topics/*.md`, `docs/*.md` за последние 30 дней.
2. Если решение не упоминается в рабочих файлах 30+ дней → статус `stale` (не `rejected`!), advisory: «Решение D-XXX не применяется — review needed».
3. Если решение активно применяется → статус `live`, добавляется в `indexes/live-decisions.json`.

**Reuse:** `tools/repo_search.py`, `tools/decisions_usage_scan.py`, `tools/knowledge.py` (timestamp search).

**Инновация.** Канон становится **саморегулирующейся правовой системой**: не только принимает законы, но и видит, какие законы действуют.

---

### 6.2. Agent Capacity Thermodynamics — модель нагрузки

**Идея.** Reuse heartbeat-данные и `pipeline.py` метрики для **энергетической модели** агентов:
- Каждый агент = термодинамическая система: capacity (CPU/time), entropy (число переключений задач), temperature (частота ошибок/retries).
- `top.py thermodynamics` — визуализация (ASCII heatmap или JSON для dashboard): какой агент перегружен, где «тепловые потоки» задач.
- При `temperature` > threshold → `conveyor.py regulate` автоматически снижает target (уже есть T-179, расширить).

**Reuse:** `pipeline.py`, `conveyor.py`, heartbeat JSON, `metrics.py`.

**Инновация.** Метафора «температуры» для многоагентной системы — не просто красиво, а предсказательно: перегретый агент делает больше ошибок, система должна охлаждать его load.

---

### 6.3. Text Diffusion Canvas — reuse TVCP-идей для агентской коллаборации

**Идея.** Темы `topics/tvcp-text-diffusion-hybrid-2026-06-26.md` и `topics/textscene-unified-spec-2026-06-26.md` содержат концепцию 2D-канвы для текстовой коллаборации. Не стирать их, а **рационализировать** в MVP:
1. Создать `drivers/textcanvas/` — minimal read-only Python API: плоский файл `.canvas.md` с YAML front-matter + grid of cells (Markdown sections).
2. Агенты могут «писать» в разные ячейки без merge-конфликтов (ячейки = изолированные блоки).
3. Reuse `drivers/workbench` для индексации ячеек.
4. Пилот: одна тема (например, `topics/ai-os-bridge.md`) переносится в `.canvas.md` формат, агенты пишут в разные ячейки параллельно.

**Reuse:** Существующие темы, workbench, front-matter parser.

**Инновация.** Это **spatial markdown** — не замена git, а дополнение: визуальная топология текста для параллельной работы.

---

## 7. Roadmap и приоритеты

### Фаза 1: Beta-0 Lock (0–5 дней)
| Пункт | Задача | Инструмент | Критерий |
|---|---|---|---|
| 1.1 | T-274 оживить | `top.py thermal` | `LIVE.md` не пуст, ≥1 агент активен |
| 1.2 | T-273 завершить | `knowledge.py` + портал | Оценка удобства ≥3/5 |
| 1.3 | T-275 закрыть | `decision_propagate.py` | `top.py health` ATTENTION=0 |
| 2.1 | immune.py fix | `immune.py` + hook | Git failure → exit 2, не 0 |
| 5.1 | `top.py beta0` | `top.py` | 10/10 green → ready |

### Фаза 2: Технический долг (5–12 дней)
| Пункт | Задача | Инструмент | Критерий |
|---|---|---|---|
| 2.2 | test_all.py | `test_all.py` + `conftest.py` | 123/123 прогоняются |
| 2.3 | pre-commit staged | `pre-commit` hook | Partial add блокирует stale |
| 3.1 | Orphan audit | `gap_scan --classify` | 8 orphans классифицированы |
| 3.2 | Шардирование | `git mv` + `queue_archive.py` | `dir_health` FAIL=0 |

### Фаза 3: Рационализация (12–20 дней)
| Пункт | Задача | Инструмент | Критерий |
|---|---|---|---|
| 4.1 | Consolidation | `knowledge.py` + proposals | 10+ proposals, 20+ superseded |
| 4.2 | D-037 gate | `friction.py new-tool-gate` | 0 orphaned new tools |
| 5.2 | commit-plan | `top.py commit-plan` | Human UX коммита = 1 команда |

### Фаза 4: Инновации (после Beta-0)
| Пункт | Задача | Инструмент | Критерий |
|---|---|---|---|
| 6.1 | ISR | `instruction_reconcile.py` | Live/stale decision map |
| 6.2 | Thermodynamics | `top.py thermodynamics` | Capacity prediction |
| 6.3 | Text Canvas | `drivers/textcanvas/` | 1 pilot topic in canvas |

---

## 8. Принципы исполнения

1. **No deletion.** Все файлы сохраняются. Шардирование — через `git mv` (сохраняет историю). Archive — через `mkdir archive/` + move. Superseded — через front-matter tag.
2. **No new layers without task.** Каждый пункт имеет attached task ID (T-273, T-274, etc.) или создаётся через `next_id.py`.
3. **Reuse first.** Каждая рекомендация явно указывает, какой существующий код/идею/тему она переиспользует.
4. **Advisory before enforcement.** Новые gates (D-037, pre-commit) начинаются как WARN, затем — по решению человека — могут стать ERROR.
5. **Evidence-based.** Каждая метрика проверяется командой, а не декларируется.
6. **Human-in-the-loop.** `top.py commit-plan`, `decision_propagate.py`, `gap_scan --classify` — все генерируют proposals для review, не применяют автоматически.

---

## 9. Ссылки и зависимости

- `reports/audit-claude-2026-07-02.json` — источник находок C0–C57.
- `reports/fix-wave2-plan-2026-07-02.md` — детали подвариантов C1, C7, C12, C13, C14, C15.
- `docs/beta0-acceptance-checklist-2026-07-06.md` — критерии гейта.
- `docs/next-stage-action-plan-2026-07-06.md` — фазовый план.
- `DECISIONS.md` — D-034, D-035, D-036, D-037.
- `TASKS.md` — T-273, T-274, T-275.

---

*Документ создан как рекомендация. Не является решением (D-006). Для принятия — вынести на котёл или ратифицировать через D-035/D-036 процесс.*
