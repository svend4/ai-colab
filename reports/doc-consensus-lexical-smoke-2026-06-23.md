# Doc-consensus отчёт

Документы (2): `docs/commit-stream-policy.md`, `docs/parallel-work-policy.md`
Пунктов всего: 307 · консенсус-кластеров: 0 · одиночных: 293

## Консенсус (пункты в >=2 документах) — кандидаты в mainline-описание

_(общих пунктов не найдено при текущем пороге)_

## Разногласия (пункт только в одном документе) — детализировать/обосновать (D-017)

### `docs/commit-stream-policy.md` — уникальные пункты (88)
- Commit streams policy  _(docs/commit-stream-policy.md:1)_
- Дата: 2026-06-21 Статус: draft policy Связано: `PROTOCOL.md`, `docs/pipeline-operator-guide.md`, `docs/onboarding-opinions-comparison-2026-06-21.md`, `streams/R  _(docs/commit-stream-policy.md:3)_
- Эта политика отвечает на вопрос: как многим людям и агентам работать в одной папке, не блокировать друг друга и не коммитить чужую незавершённую работу.  _(docs/commit-stream-policy.md:9)_
- Git commit — это mainline snapshot, а не место для полусырых идей всех участников.  _(docs/commit-stream-policy.md:13)_
- Очередь `tasks/` отвечает за исполнение.  _(docs/commit-stream-policy.md:14)_
- Темы и вопросы отвечают за обсуждение.  _(docs/commit-stream-policy.md:15)_
- `streams/` отвечает за промежуточные варианты: уже больше, чем текстовый комментарий, но ещё не commit в основную линию.  _(docs/commit-stream-policy.md:16)_
- Если несколько агентов работают одновременно, появляются три риска:  _(docs/commit-stream-policy.md:20)_
- 1. Агент делает `git add -A` и случайно коммитит чужие незавершённые файлы. 2. Один агент первым сделал вариант, и другой вариант исчезает как "дубль", хотя мог  _(docs/commit-stream-policy.md:22)_
- Значит нужен промежуточный формат: маленькие "ручейки" вариантов, которые могут течь параллельно, сравниваться и только потом вливаться в основную линию.  _(docs/commit-stream-policy.md:26)_
- Integration commit  _(docs/commit-stream-policy.md:37)_
- Уровни фиксации  _(docs/commit-stream-policy.md:39)_
- Обычный комментарий в теме или outbox.  _(docs/commit-stream-policy.md:43)_
- Подходит для идеи, замечания, вопроса, короткой критики.  _(docs/commit-stream-policy.md:45)_
- L1. Variant note  _(docs/commit-stream-policy.md:47)_
- Отдельный Markdown-файл с вариантом A/B/C.  _(docs/commit-stream-policy.md:49)_
- Подходит, если надо сравнить несколько подходов, но ещё нет кода или патча.  _(docs/commit-stream-policy.md:51)_
- L2. Stream packet  _(docs/commit-stream-policy.md:53)_
- Это "полу-коммит": структурированный пакет предложения, но не mainline. Его можно читать, ревьюить, сравнивать и потом принять или отклонить.  _(docs/commit-stream-policy.md:66)_
- L3. Mainline change  _(docs/commit-stream-policy.md:68)_
- Правка обычных файлов проекта: `docs/`, `tools/`, `drivers/`, `tasks/`, `questions/`, `decisions/`.  _(docs/commit-stream-policy.md:70)_
- Должна быть связана с task/claim или явным запросом человека.  _(docs/commit-stream-policy.md:72)_
- L4. Git commit  _(docs/commit-stream-policy.md:74)_
- Финальный snapshot выбранной mainline-правки.  _(docs/commit-stream-policy.md:76)_
- Коммит не должен случайно включать:  _(docs/commit-stream-policy.md:78)_
- чужие незавершённые stream/work files;  _(docs/commit-stream-policy.md:80)_
- чужие generated files, если они не входят в integration scope;  _(docs/commit-stream-policy.md:81)_
- half-done tasks другого агента;  _(docs/commit-stream-policy.md:82)_
- sandbox raw sources;  _(docs/commit-stream-policy.md:83)_
- runtime logs.  _(docs/commit-stream-policy.md:84)_
- … ещё 58

### `docs/parallel-work-policy.md` — уникальные пункты (205)
- Политика параллельной работы (детальная)  _(docs/parallel-work-policy.md:1)_
- Дата: 2026-06-22 · Статус: **accepted** (ратифицировано `D-022`, Stefan по D-006). Источник: 4 решения Stefan + требование детализировать под-случаи. История и   _(docs/parallel-work-policy.md:3)_
- Цель — однозначное правило на каждую конкретную ситуацию параллельной много-агентной работы, чтобы убрать «ожидание другого агента» и потерю работы при коллизия  _(docs/parallel-work-policy.md:5)_
- Матрица быстрого выбора: ситуация → механизм  _(docs/parallel-work-policy.md:7)_
- Чужие незакоммиченные source-файлы (tasks/ decisions/ questions/ tools/ drivers/ docs/ topics/ streams/*/STREAM.md) в git status  _(docs/parallel-work-policy.md:11)_
- generate.py --check краснеет (STALE), и stale-источник НЕ мои staged-изменения  _(docs/parallel-work-policy.md:12)_
- Планирую правку HOT-файла (TASKS.md, QUESTIONS.md, DECISIONS.md, index.json, PIPELINE.md, tools/top.py, tools/portal.py, генераторы, _canon/*)  _(docs/parallel-work-policy.md:13)_
- Stefan/owner явно просит параллельную многоагентную работу / fork-and-synthesize над одной темой  _(docs/parallel-work-policy.md:14)_
- Предсказана same-file коллизия: я начинаю править файл, который уже правит другой агент  _(docs/parallel-work-policy.md:15)_
- Общий validate-гейт КРАСНЫЙ (`validate ERROR`) из-за чужой half-done (битая ссылка на файл / front-matter / дубль id) — коммит заблокирован ВСЕМ  _(docs/parallel-work-policy.md:16)_
- STALE-индекс возник из-за МОИХ собственных незакоммиченных источников  _(docs/parallel-work-policy.md:17)_
- Канонический индекс изменился из-за чужого УЖЕ ЗАКОММИЧЕННОГО источника  _(docs/parallel-work-policy.md:18)_
- Меняю только source-файлы (tasks/decisions/questions) → нужно обновить канонические индексы  _(docs/parallel-work-policy.md:19)_
- Работа только в ВОЛАТИЛЬНЫХ файлах (LIVE.md, PIPELINE.md, logs/*, heartbeat)  _(docs/parallel-work-policy.md:20)_
- Same-file, КРУПНАЯ/содержательная правка (>500 строк, code, архитектура, substantive)  _(docs/parallel-work-policy.md:21)_
- Same-file, МЕЛКАЯ правка/ревью, есть owner (claim)  _(docs/parallel-work-policy.md:22)_
- Same-file, маленький draft (<100 строк), одобренная синтез-последовательность  _(docs/parallel-work-policy.md:23)_
- Изолированная работа: дерево чисто, generate --check зелёный, файл не hot, чужих claim нет  _(docs/parallel-work-policy.md:24)_
- Экстренный hot-fix (security/data-loss/blocker), нельзя ждать merge-gate  _(docs/parallel-work-policy.md:25)_
- commit_lock BUSY >2 раз / >120с ИЛИ generate.py пришлось гонять >5 раз из-за чужого stale  _(docs/parallel-work-policy.md:26)_
- 1. Уровень-1 (worktree) vs Уровень-0 (общее дерево) — триггеры  _(docs/parallel-work-policy.md:28)_
- **Принцип:** Level-1 (per-agent git worktree with isolated index, branch `agent/<agent>/<task>`) is MANDATORY when any of three trigger-conditions are met: (1)   _(docs/parallel-work-policy.md:30)_
- Coworker has uncommitted source-files AND they touch Source-Dirs (tasks/, decisions/, questions/, tools/, drivers/, docs/, topics/)  _(docs/parallel-work-policy.md:34)_
- generate --check returns non-zero (STALE detected) and stale changes are NOT from current agent's own staged work  _(docs/parallel-work-policy.md:35)_
- Task size is LARGE (multi-file change across 5+ files OR touches multiple source-directories) AND coworker is currently active (has live claim OR uncommitted wo  _(docs/parallel-work-policy.md:37)_
- same-file collision: both current agent AND coworker have uncommitted changes to the SAME file (e.g., tools/text_extract.py, portals/example/config.md)  _(docs/parallel-work-policy.md:38)_
- Review/small-doc-fix (touching 1–2 files, docs/ only, no task/decision changes) but D-017 fork-variant already exists from coworker  _(docs/parallel-work-policy.md:39)_
- Work is ONLY in generated/volatile files (LIVE.md, heartbeat logs, temp pipeline-state snapshots) and does NOT touch source-truth files (tasks/, decisions/, too  _(docs/parallel-work-policy.md:40)_
- Code work (drivers/, tools/ implementation) AND coworker is NOT currently active (no live claims in that subsystem for >10 minutes AND no uncommitted source-fil  _(docs/parallel-work-policy.md:41)_
- Emergency hot-fix or critical patch required immediately (e.g., security bug, production-data corruption, blocking-bug) AND Level-0 ship cannot wait for merge-g  _(docs/parallel-work-policy.md:42)_
- … ещё 175

