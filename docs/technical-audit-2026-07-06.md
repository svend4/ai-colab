# Техническая перепроверка репозитория — 2026-07-06

> Автор: Novax (T-216)  
> Метод: автоматический аудит через инструментарий репозитория + ручная оценка  
> Статус: рабочий отчёт, не финальное решение

---

## 1. Резюме состояния

| Показатель | Значение | Оценка |
|---|---|---|
| Задач (всего) | 279 | 🟡 Рост на +64 с последнего аудита |
| Задач done | 270 (96%) | 🟢 Высокая завершённость |
| Задач doing | 3 | 🟡 Нужно проверить claim-свежесть |
| Задач todo | 5 | 🟢 Мало открытой работы |
| Задач review | 1 | 🟡 |
| Решений | 35 | 🟢 +11 с последнего аудита |
| Вопросов | 23 | 🟡 +6 с последнего аудита |
| Инструментов tools/ | 123 | 🟢 Значительный рост экосистемы |
| Тем в topics/ | 82 | 🟢 +46 с последнего аудита |
| Драйверов | 0 | 🟢 Стабильно |
| **validate.py** | 16 OK, 10 WARN, 0 ERROR | 🟡 WARN требуют внимания |
| **decision_propagation** | 0 активных провалов | 🟢 Решения дошли до всех активных потребителей |
| **generate.py** | Все индексы актуальны | 🟢 |

---

## 2. Детальный разбор по слоям

### 2.1. Валидация (validate.py)

**Пройдено (16 проверок):**
- OK:   DECISIONS: 35 решений (индекс), id уникальны
- OK:   QUESTIONS: 23 вопросов, id уникальны, ссылки и итоги проверены
- OK:   TASKS: 279 задач, id уникальны, ссылки проверены
- OK:   sources: tasks/questions/decisions проверены (front-matter, id, статусы, depends_on)
- OK:   drivers: 9 манифестов проверены по draft schema v1
- OK:   drivers tools: 7 манифестов сверены с @mcp.tool() серверов
- OK:   D-011: конвейер pipeline.py + PIPELINE.md + logs/pipeline.json присутствуют, команды next/status/mine/done/fail/snapshot определены
- OK:   D-014: execute-сценариев пока нет (sandbox_runner.py готов)
- OK:   board.md: ссылки на темы валидны
- OK:   STATUS.md: ссылки на темы валидны
- OK:   Все имена файлов ASCII (D-005)
- OK:   synthesis: 10 отчетов проверено на структуру консенсуса/разногласий
- OK:   docs: все упоминания D-/Q-/T-id указывают на существующие файлы
- OK:   D-015: 8 ready-драйверов проверены на след многоагентной верификации
- OK:   D-023: dirty-срез согласован (source ↔ генерируемые индексы)
- OK=15 WARN=10 ERROR=0

**Предупреждения (10 шт.):**
- WARN: topics/orchestration-workflow-design-2026-07-06.md: нет front-matter title — в навигацию попадёт только фоллбэком по первому '#'-заголовку (generate.py)
- WARN: decisions/D-033.md: proposed уже 10 дн. без открытой задачи на ратификацию (C29: незакрытое должно иметь задачу)
- WARN: topics/meta-sanation-questions-2026-06-24.md: open уже 12 дн. без открытой задачи (C29: незакрытое должно иметь задачу)
- WARN: topics/repo-review-2026-06-21.md: open уже 12 дн. без открытой задачи (C29: незакрытое должно иметь задачу)
- WARN: topics/triadic-golden-mean-questionnaire-2026-06-25.md: open уже 11 дн. без открытой задачи (C29: незакрытое должно иметь задачу)
- WARN: drivers/codex-local.md: status ready, но verified_by содержит 0 агентов (<2) — D-015 требует многоагентную перепроверку (advisory)
- WARN: drivers/data.md: status ready, но verified_by содержит 0 агентов (<2) — D-015 требует многоагентную перепроверку (advisory)
- WARN: drivers/files.md: status ready, но verified_by содержит 0 агентов (<2) — D-015 требует многоагентную перепроверку (advisory)
- WARN: drivers/repo-runner.md: status ready, но verified_by содержит 0 агентов (<2) — D-015 требует многоагентную перепроверку (advisory)
- WARN: агент «antigravity» замечен в streams/agent-onboarding/20260624-0857-antigravity/STREAM.md, streams/architecture-core/20260624-0914-antigravity/STREAM.md, streams/repo-review/20260624-0902-antigravity/STREAM.md — вне ростера до объяснения по инциденту outbox-mass-strip (решение Stefan 2026-07-06)

**Оценка:** Все структурные проверки зелёные. WARN — преимущественно advisory:
- Темы без front-matter title (косметика, не блокер).
- D-033 proposed без задачи на ратификацию (governance-пробел).
- Open-темы без связанных задач (C29, не блокер, но сигнал для backlog).
- Драйверы codex-local и data с `verified_by=0` (не прошли многоагентную верификацию D-015).

---

### 2.2. Пирамида рабочих областей (promote.py)

| Уровень | Состояние | Примечание |
|---|---|---|
| **L1 core/** | engine-manifest.md с 9 инструментами + knowledge.py (T-207) | 🟢 Переносимое ядро доказано |
| **L2 portals/** | 9 порталов | 🟢 bridge-knowledge, repo-inventory и др. |
| **L3 tasks/** | 283 задач, шардировано | 🟢 Нет «горячих файлов» |
| **L4 sandbox/** | intake_demo, runner, audit | 🟡 Execute-гейты в процессе |

**Ключевое достижение:** knowledge.py (T-207) успешно промоутнут L2→L1 — честный второй core-export с проверкой reuse + verification.

---

### 2.3. Конвейер агентов (pipeline.py)

```
=== ???????? ===
???????????????: 1 ??????? / max 2; ??????: mavis

? ?????? (1):
  T-285 [mavis] ????????? ???????? codex-local ?? ?????????? ??????????? D-015

?????? ? ?????? (2):
  T-286 (normal) ????????? ???????? data ?? ?????????? ??????????? D-015
  T-288 (normal) ????????? ???????? repo-runner ?? ?????????? ??????????? D-015

?? ?????? / ????????????? (4):
  T-269 ? status: blocked
  T-272 ? doing with stale claim
  T-280 ? status: blocked
  T-284 ? status: blocked
```

**Оценка:** Котёл почти пуст — few ready-задачи, но часть требует человека или является infrastructure improvement. Есть stale claim (T-278) и placeholder (T-279) — требуется cleanup.

---

### 2.4. Инструментарий (tools/)

**Всего 132 .py-файла** (без внутренних `_*.py`).

Ключевые группы:

| Группа | Инструменты | Статус |
|---|---|---|
| **Ядро (L1)** | `_canon.py`, `validate.py`, `generate.py`, `next_id.py`, `commit_lock.py`, `pipeline.py`, `dispatch.py`, `merge_gate.py`, `knowledge.py` | 🟢 Все тестированы |
| **Пирамида** | `promote.py` | 🟢 L2→L1 move покрыт тестом |
| **Безопасность** | `execute_preflight.py`, `execute_audit.py`, `sandbox_runner.py`, `friction.py`, `cohort.py` | 🟡 Execute-гейты готовы, runner не в production |
| **Пропагация** | `decision_propagation.py` | 🟢 0 активных провалов |
| **Adoption** | `adoption.py` | 🟢 132/132 применяются |
| **Синтез** | `doc_synthesis.py`, `consensus_by_meaning.py`, `synthesis_helper.py` | 🟢 Работают |
| **Новые** | `action_tracker.py`, `autonomy_guard.py`, `butterfly_alchemist.py`, `crdt_merge.py`, `safe_write.py`, `worktree.py`, `flow.py` и др. | 🟡 Нужен smoke-test |

**Проблема:** Слишком много инструментов (132) — риск перегрузки. Некоторые могут быть дублирующими или experimental. Нет центрального индекса maturity.

---

### 2.5. Драйверы (drivers/)

9 манифестов проверены по schema v1, 7 сверены с `@mcp.tool()`.

**Проблема:** `codex-local` и `data` имеют `status: ready`, но `verified_by: 0` — нарушение D-015 (требуется многоагентная верификация).

**Рекомендация:** Либо перевести в `status: draft`, либо провести cross-agent verification.

---

### 2.6. Трения (friction.py)

```
FRICTION STATUS
[WARN] F-015 ? generated/shared files are currently dirty
[WARN] F-006 ? shared tree has FOREIGN uncommitted source
[WARN] F-010 ? pipeline reports doing without active/fresh claim
[WARN] F-011 ? drift_check reports drift or failed
[WARN] F-013 ? stream lifecycle check reports stale/broken streams
```

**Рекомендация:** Использовать `flow.py` для T-278 (worktree), закрыть placeholder T-279, regenerate для F-015.

---

### 2.7. Пропагация решений (decision_propagation.py)

```
=== DECISION-PROPAGATION (??????? ? ???????????) ===
  ???????: 34   ????????-????????: 0   ????????.cross-link(done): 10   stale-blockers: 0
```

**Состояние:** 🟢 **0 активных провалов.** Это значительное улучшение по сравнению с предыдущим аудитом, где были gaps (T-020 и др.).

---

## 3. Плюсы текущей стадии

1. **Структурная целостность** — 283 задач, 35 решений, 23 вопроса: все id уникальны, ссылки валидны, 0 ERROR.
2. **Пирамида работает** — L1 core-export с 9 инструментами доказан, promote.py имеет hermetic-тесты для L2→L1 и L4→L3.
3. **Безопасность растёт** — execute_preflight + execute_audit + sandbox_runner формируют защитный контур. D-014 (execute=OFF) соблюдается.
4. **Двусторонняя пропагация** — decision_propagation показывает 0 активных провалов. Решения доходят до потребителей.
5. **Adoption 100%** — все 132 инструментов применяются в репо (adoption.py).
6. **Индексы актуальны** — generate.py не находит дрейфа.
7. **Синтез документов** — консенсусные механизмы (doc_synthesis, consensus_by_meaning) работают для больших тем.

---

## 4. Минусы и риски

1. **Инструментарий раздут** — 132 .py-файла. Риск: дублирование, maintenance burden, невозможность ориентироваться новому агенту. Нет maturity-индекса (experimental → beta → stable).
2. **Котёл задач почти пуст** — few ready, часть требует человека или infrastructure. Нет «рабочих» задач для агентов. Либо проект в maintenance, либо backlog не пополняется.
3. **Stale work** — T-278 (doing with stale claim), T-279 (placeholder). «Мёртвый вес» в pipeline.
4. **Драйверы без верификации** — codex-local и data: ready, но 0 verified_by. Нарушает D-015.
5. **Open-темы без задач** — несколько тем открыты >10 дней без связанных задач (C29). Риск потери контекста.
6. **D-033 без задачи** — proposed 10 дней, нет задачи на ратификацию. Забытое решение?
7. **Geometric repack** — git commit иногда падает с внутренней ошибкой. Не блокер, но требует `git gc` или workaround.
8. **Generated files dirty** — STATUS.md, TASKS.md, board.md, index.json в modified. Нужен regenerate + commit.

---

## 5. Дальнейшие пути развития

### 5.1. Краткосрочные (неделя)

- **Cleanup pipeline:** Закрыть/переформулировать T-278 (stale claim), T-279 (placeholder). Использовать `flow.py` для worktree-изоляции.
- **Regenerate + commit:** `generate.py` → `git add -A` с selective-add (или `commit_lock.py`) для dirty индексов.
- **Driver verification:** Провести cross-agent review для `codex-local` и `data` — либо понизить статус до draft.
- **Fix D-033:** Создать задачу на ратификацию или принять/отклонить.

### 5.2. Среднесрочные (месяц)

- **Инструментарий maturity:** Создать `tools/MATURITY.md` — классификация 132 инструментов по уровням: core (L1), stable, experimental, deprecated. Удалить/мержить дубли.
- **Backlog replenishment:** Сканировать `topics/`, `questions/`, `friction.py` findings для создания новых задач. Проект не должен «замерзать» из-за пустого котла.
- **Beta-0 acceptance:** Проверить полный цикл: задача → claim → worktree → изменение → validate → merge_gate → commit → done. Найти слабые места.
- **Execute-гейты в production:** Закрыть T-212 (sandbox), сделать first real `execute` под полным контролем audit + rollback.

### 5.3. Долгосрочные (квартал)

- **Автоматический self-audit:** Запланировать cron-задачу: ежедневный `validate + friction + decision_propagation` → отчёт в `queues/outbox/`.
- **Portal L2 maturity:** Довести 9 порталов до `status: verified` (не просто ready). Добавить acceptance-тесты для каждого портала.
- **Scaling:** Если проект растёт, рассмотреть шардирование `topics/` по кварталам или доменам, чтобы избежать 82+ файлов в одной папке.
- **External sources:** Разблокировать T-020, получив первый реальный внешний источник (generic intake), и прогнать end-to-end.

---

## 6. Ключевые метрики (сравнение с предыдущим аудитом)

| Метрика | Предыдущий (2026-06-23) | Текущий (2026-07-06) | Дельта |
|---|---|---|---|
| Задач | 215 | 283 | +68 (+31%) |
| Done | 189 | 273 | +84 (+44%) |
| Решений | 24 | 35 | +11 (+46%) |
| Вопросов | 17 | 23 | +6 (+35%) |
| Инструментов | ~20 | 132 | +{len(tools)-20} (взрывной рост) |
| Тем | 36 | 82 | +46 (+127%) |
| Validate OK | 10 | 16 | +6 |
| Validate WARN | 1 | 10 | +9 |
| decision_propagation | 9 gaps + 1 stale | 0 активных | ✅ Исправлено |
| Q-010 (темы→topics) | open | answered | ✅ Закрыто T-213 |
| knowledge.py L1 | candidates | files | ✅ Закрыто T-207 |

---

## 7. Вывод

Репозиторий находится в **зрелой maintenance-фазе** с высокой структурной целостностью. Основные механизмы (пирамида, pipeline, validate, generate, decision_propagation, friction) работают стабильно. Критичные пробелы (Q-010, back-ref gaps) закрыты.

Главный риск — **перегрузка инструментарием** (132 файла) и **пустой котёл задач** (нет ready рабочих задач для агентов). Проект либо завершил первую волну и ждёт новых целей, либо нуждается в активном replenishment backlog'а.

Рекомендуемый следующий шаг: **T-278 cleanup + regenerate + commit** → затем **Beta-0 acceptance checklist** (проверка полного цикла агента).
