# Полный аудит стадии кода и документации — Codex — 2026-06-26

- Автор: codex
- Дата: 2026-06-26
- Тип: technical/conceptual audit
- Статус: рабочий отчет, без изменения решений
- Область: код, документация, governance, pipeline, drivers, generated indexes, текущий dirty tree

## 1. Короткий вердикт

Проект находится не на стадии "идеи" и не на стадии production. Текущая честная формулировка:

**working alpha control plane / операционный архитектурный прототип многоагентной repo-native платформы.**

Это уже система с исполняемым ядром: задачи, решения, вопросы, индексы, pipeline, drivers, sandbox, streams, assurance, gap/friction checks и первые headless-thread/workbench элементы. Но это еще не завершенный продуктовый workbench: ключевой долг находится в связке **"решение -> инструкция -> код -> гейт -> evidence -> приемка"**.

Главный риск: проект очень быстро производит новые механизмы, но часть механизмов остается в состоянии "построено, но не подключено" или "описано, но не является активным гейтом".

## 2. Проверки, выполненные для снимка

Команды запускались в рабочей папке `C:\Users\stefan\Documents\New project ai colab`.

| Проверка | Результат | Вывод |
|---|---:|---|
| `python tools/validate.py` | `OK=12 WARN=0 ERROR=0` | Канон структурно здоров: 264 задачи, 31 решение, 23 вопроса, 9 driver-манифестов. |
| `python tools/generate.py --check` | сначала stale, затем OK | Generated files были устаревшими во время аудита, затем стали актуальными, но рабочее дерево осталось dirty. |
| `python tools/pipeline.py status` | 0 active, 1 ready | Единственная ready-задача: `T-264` thread schema MVP. |
| `python tools/top.py health` | exit 1 | Верхний health-гейт красный: metadata soft-check, stale на момент запуска, wrapper timeouts, assurance ATTENTION. |
| `python tools/drift_check.py` | `OK: дрейфа не обнаружено` | Тихого drift между каноном и фактами не найдено прямой проверкой. |
| `python tools/gap_scan.py drift --strict` | 0 | Класс "(f) тихий дрейф деривата" сейчас закрыт. |
| `python tools/gap_scan.py` | 22 разрыва | 7 orphan tools, 15 dangling `tools/*.py` ссылок, drift 0. |
| `python tools/friction.py status` | `LEVEL 1 OR SELECTIVE-ADD` | Dirty/shared/gate-poison сигналы; запрещен широкий `git add -A`. |
| `python -m pytest tools drivers` | fail | `No module named pytest`; широкий pytest-слой не является текущим release-gate. |

## 3. Текущий dirty tree

На момент аудита рабочее дерево содержит параллельные/чужие изменения. Их нельзя смешивать широким staging.

Зафиксированы:

- modified generated/shared: `STATUS.md`, `board.md`, `index.json`, `indexes/topics.md`;
- staged/modified work from another stream: `docs/independent-first-pipeline.md`, `tools/fold.py`, `tools/independent_pipeline.py`, `tools/test_fold.py`, `tools/test_independent_pipeline.py`;
- modified top layer: `tools/top.py`, `tools/test_top.py`;
- untracked reports: `reports/gap-inventory-2026-06-26.json`, `reports/gap-inventory-2026-06-26.md`.

Практический вывод: до коммита нужен explicit file list или commit queue. Широкий `git add -A` сейчас технически опасен.

## 4. Стадия реализации кода

### 4.1. Что уже реально работает

1. **Канон и индексы.** `tasks/`, `questions/`, `decisions/`, `topics/` имеют front-matter и генерируемые индексы. `validate.py` подтверждает базовую целостность.
2. **Pipeline.** `pipeline.py` работает как pull/claim/status/done слой; сейчас активных задач нет, ready только `T-264`.
3. **Drivers / AI-OS Bridge.** В каталоге 9 driver-манифестов; schema и tools сверяются валидатором.
4. **Safety posture.** Execute закрыт по умолчанию; sandbox/preflight описаны и частично материализованы.
5. **Assurance/friction/gap diagnostics.** Есть реальные read-only проверки проблем: evidence, currency, orphan/dangling/drift, dirty tree, stream lifecycle.
6. **Top layer.** `top.py` уже выступает как агрегатор команд, но текущий health показывает, что обертка строже и хрупче прямых проверок.
7. **Headless-thread направление.** `T-264` содержит implementation note: `tools/thread.py` и `tools/test_thread.py` уже добавлены, но task status остается `todo`.

### 4.2. Что работает частично

1. **Generated indexes.** Проверка сначала была stale, затем стала OK, но generated files dirty. Это не логическая поломка, а операционный drift в процессе работы нескольких агентов.
2. **Top health.** Прямая `validate.py` зеленая, но `top.py health` ловит timeout на `validate.py`/`drift_check.py` внутри wrapper. Нужна настройка timeouts/streaming или разделение quick/deep health.
3. **Metadata D-Card.** Soft-check нашел 67 Python-файлов без D-Card. Это не блокирует сейчас, но показывает, что metadata-стандарт не доведен до покрытия.
4. **Assurance.** Вердикт ATTENTION: 4 evidence-замечания, `D-031` без `last_verified`, `D-031` не упомянут в instruction surface.
5. **Gap scan.** Drift закрыт, но 7 orphan tools и 15 ghost tool references остаются.
6. **Tests.** Много stdlib-тестов существует, но `pytest` не установлен, поэтому нельзя честно назвать полный тестовый слой зеленым.

### 4.3. Что еще не является приемочным продуктовым слоем

1. Единая workspace-cell карточка: task + thread + stream + worktree + outbox + checks.
2. Нормальный release-gate: быстрый health, deep health, tests, metadata, gap_scan, assurance, generated freshness.
3. UI/TUI/HTML dashboard поверх headless state.
4. Полная ратификация и enforcement новых решений, особенно `D-031`.
5. Автоматическое закрытие жизненного цикла "идея -> proposed decision -> task -> implementation -> evidence -> accepted/adopted".

## 5. Стадия документации

Документация богаче, чем кодовый приемочный слой. Это плюс и риск одновременно.

Сильные стороны:

- есть `PROTOCOL.md`, `AGENTS.md`, decision/task/question registers;
- есть explicit governance: append-only, D-003, D-014, D-017/D-018, D-031;
- есть архитектурные документы по AI middle layer, drivers, assurance, sandbox, top layer, independent-first;
- свежие отчеты уже фиксируют разные точки зрения: Claude audit, gap inventory, Codex outbox audits.

Слабые стороны:

- часть документов ссылается на несуществующие tools (`gap_scan dangling`: 15 случаев);
- часть тем не до конца промоутирована в accepted/implementation surface;
- `STATUS.md` исторически перегружен и не всегда лучший "первый файл" для фактического runtime-состояния;
- proposed-слой растет быстрее, чем слой ратифицированных и enforced решений;
- документация иногда описывает будущую архитектуру как почти действующую, хотя code gate еще advisory.

Итог: документация находится на стадии **rich design corpus + operational manual**, но требует санации ghost references и явного отделения "работает" от "предложено".

## 6. Концептуальная оценка

Проект инновационен не отдельным скриптом, а сочетанием идей:

1. **Repo as collaboration OS.** Git/Markdown/front-matter используются как долговечная операционная среда для людей и AI-агентов.
2. **Governance as code-adjacent state.** Решения, задачи, вопросы и evidence живут рядом с кодом и валидируются.
3. **Independent-first streams.** Содержательные дубли не схлопываются до синтеза; это снижает риск преждевременного консенсуса.
4. **Gap/friction/assurance diagnostics.** Проект строит не только функции, но и детекторы своих типовых дефектов.
5. **Drivers/portals/core pyramid.** Есть понятная траектория от raw sandbox к reusable core.
6. **Headless workbench direction.** `T-264` вводит долговечный объект thread как будущую ячейку работы, похожую на headless Zed-like workspace.

Главная концептуальная проблема: слой мышления уже уровня "AI collaboration platform", а приемка местами еще уровня "набор проверяемых локальных инструментов". Следующий этап должен не добавлять еще больше идей, а замыкать существующие идеи в enforceable loops.

## 7. Приоритеты

### P0 — немедленно

1. Не делать широкий staging. Только explicit file list.
2. Зафиксировать владельца текущего dirty stream (`top.py`, `fold.py`, `independent_pipeline.py`, generated indexes).
3. Закрыть статусный drift `T-264`: либо перевести в `review/done` с evidence, либо split на follow-up и оставить Stage A закрытой.
4. Добавить `D-031` в instruction surface и `last_verified`, иначе accepted decision висит вне применения.
5. Привести `top.py health` к честному quick/deep режиму, чтобы прямые зеленые проверки не превращались в wrapper timeout.

### P1 — ближайший цикл

1. Разобрать 7 orphan tools: подключить, явно пометить experimental, или списать.
2. Разобрать 15 dangling tool references: создать реальные tools или исправить документы.
3. Начать D-Card batch: снизить 67 missing D-Cards хотя бы до top/core entrypoints.
4. Установить/зафиксировать test strategy: либо добавить pytest в dev environment, либо явно поддерживать stdlib runner как канон.
5. Свести Claude audit, gap inventory и этот отчет в один prioritized audit backlog.

### P2 — следующий технологический скачок

1. Реализовать `workspace-cell` как read-only агрегатор:
   `task + claim + thread + stream + worktree + outbox + checks + decisions`.
2. Подключить `thread.py` к `top.py`, но не превращать его в оркестратор.
3. Сделать health tiers:
   - `quick`: validate/generate/drift/pipeline;
   - `deep`: metadata/gap/assurance/tests;
   - `release`: strict gates + explicit ownership.
4. Превратить `commit_queue`/`D-031` из решения в стандартный путь shipping.

### P3 — продуктовая стадия

1. Headless dashboard или TUI/HTML поверх workspace-cell.
2. Доказательный release process: каждый accepted decision имеет instruction surface, implementation, evidence, last_verified.
3. L2 portals и drivers получают реальные acceptance suites.
4. Execute остается закрытым до отдельного accepted решения и полного D-014 preflight.

## 8. Пошаговый план реализации

### Шаг 1. Стабилизировать рабочее дерево

- Снять свежий `git status --short`.
- Разделить изменения на owner buckets.
- Не трогать staged чужого потока.
- Для generated files проверить `python tools/generate.py --check`.

### Шаг 2. Закрыть T-264 как lifecycle defect

- Запустить focused test `python tools/test_thread.py`.
- Если test green, перевести `T-264` в `review` или `done` через pipeline/explicit evidence.
- Если есть остаток, создать новую follow-up задачу для workspace-cell aggregator.

### Шаг 3. Починить D-031 propagation

- Добавить `last_verified` в `decisions/D-031.md`.
- Упомянуть D-031 в instruction surface: `PROTOCOL.md`, `docs/commit-stream-policy.md` или отдельный commit queue guide.
- Прогнать `assurance.py all`.

### Шаг 4. Сделать gap cleanup wave

- Для каждого orphan из `gap_scan.py`: `connect | document as experimental | retire`.
- Для каждого dangling reference: `create tool | rename reference | mark historical`.
- После каждой пачки: `python tools/gap_scan.py`.

### Шаг 5. Укрепить metadata

- Начать с entrypoints: `top.py`, `pipeline.py`, `generate.py`, `validate.py`, `gap_scan.py`, `friction.py`, `assurance.py`, `thread.py`.
- Потом покрывать tests и экспериментальные tools батчами.
- Не делать массовую механическую вставку без проверки.

### Шаг 6. Разделить health tiers

- `top.py health --quick`: быстрый gate без долгих deep scans.
- `top.py health --deep`: metadata + gap + assurance + tests.
- `top.py health --release`: strict mode.

### Шаг 7. Материализовать workspace-cell

- Сделать read-only JSON агрегатор.
- Добавить top wrapper.
- Только после JSON — TUI/HTML/GUI.
- Не добавлять AI inference/model dependency на этом этапе.

## 9. Definition of Done для следующей стадии

Проект можно будет честно назвать **alpha-3 operational workbench** когда:

- `validate.py`, `generate.py --check`, `drift_check.py`, `gap_scan.py`, `pipeline.py status`, `assurance.py all` дают ожидаемый зеленый/accepted ATTENTION уровень;
- нет ready-задач, у которых body говорит "implemented", а front-matter остается `todo`;
- `D-031` принят не только в `DECISIONS.md`, но и в instruction surface;
- ghost tool references либо исчезли, либо явно помечены historical;
- orphan tools имеют owner/disposition;
- есть workspace-cell JSON;
- staging/commit path идет через explicit file list или commit queue.

## 10. Итог

Система сильная, но следующий рост должен быть не "еще один слой идей", а **замыкание контуров**:

`идея -> решение -> инструкция -> task -> код -> test/check -> evidence -> generated index -> audit`.

Если этот цикл станет регулярным и быстрым, проект перейдет из "мощного alpha control plane" в реальный локальный многоагентный workbench.
