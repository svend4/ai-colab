---
id: project-audit-2026-06-23
type: audit
title: Полный аудит проекта — технический и концептуальный
status: proposed
owner: codex
date: 2026-06-23
related: [T-171, T-172, T-173, agent-capacity-methodology, top-layer-throughput-methodology, workflow-conveyor-policy, instruction-assurance]
---

# Полный аудит проекта — технический и концептуальный

Дата аудита: 2026-06-23. Аудит сделан по текущей рабочей папке, включая незакоммиченные изменения последних шагов.

## 1. Краткий вывод

Проект уже вышел из стадии “только документация и идеи”. Текущее состояние — **рабочий repo-native прототип AI-collaboration / AI middle layer**: есть задачи, решения, вопросы, генерируемые индексы, pipeline, конвейер workflow, верхняя панель `top.py`, assurance, friction ledger, skills, sandbox contracts, knowledge/report инструменты и первые элементы управления множеством агентов.

Но это ещё не зрелая автономная платформа. Главный bottleneck теперь не в запуске агентов, а в верхнем слое: обработка landed results, evidence, synthesis, review, commit, governance. Последние изменения правильно сместили развитие в эту сторону: добавлены методология верхнего слоя и read-only команда `top.py process-landed`.

Итоговая оценка:

| Область | Стадия | Оценка |
|---|---|---|
| Концепция | зрелая рабочая архитектура | сильная, связная, уже самоприменяется |
| Документация | широкая, живая, но объёмная | хорошо, нужен периодический synthesis |
| Инструменты | рабочий CLI-control-plane | хорошо, но не production-hardening |
| Тесты | в основном зелёные | 32/35 OK; 3 падают из-за Python temp PermissionError |
| Конвейер | работает | healthy, но in-flight выше target; не расширять |
| Верхний слой | появился | `top.py`, `assurance`, `process-landed`, skills |
| Параллельная работа | частично решена | commit_lock/worktree/merge_gate есть; нужна дисциплина selective-add |
| Внешний код/svend4 | контракт есть | execute не готов; T-020 blocked |
| Продуктовая зрелость | прототип | нужна упаковка, UI/MCP/plugin позже |

## 2. Технический снимок

### 2.1. Git / рабочее дерево

На момент аудита dirty tree содержит:

```text
M TASKS.md
M docs/top-layer-command-groups.md
M index.json
M skills/README.md
M tools/tests/test_top.py
M tools/top.py
?? data/portals/bridge-knowledge/
?? data/portals/repo-inventory/
?? docs/top-layer-throughput-methodology.md
?? queues/outbox/2026-06-23-agent-capacity-methodology.md
?? queues/outbox/2026-06-23-top-layer-throughput-methodology.md
?? queues/outbox/2026-06-23-top-process-landed.md
?? skills/top-layer-orchestrator/
?? tasks/T-168.md
?? tasks/T-169.md
?? tasks/T-170.md
```

Аудиторская интерпретация:

- изменения `TASKS.md`, `index.json`, `docs/top-layer-command-groups.md`, `skills/README.md`, `tools/top.py`, `tools/tests/test_top.py`, `docs/top-layer-throughput-methodology.md`, `skills/top-layer-orchestrator/`, `tasks/T-168..T-170`, outbox — ожидаемые изменения последних шагов;
- `data/portals/bridge-knowledge/` и `data/portals/repo-inventory/` выглядят как параллельные/чужие артефакты; их нельзя коммитить без отдельной проверки ownership и назначения;
- friction рекомендует **selective-add / Level 1**, не `git add -A`.

### 2.2. Hard checks

Команды:

```powershell
python tools\validate.py
python tools\generate.py --check
python tools\top.py health
```

Результат:

```text
validate: OK=9 WARN=0 ERROR=0
generate --check: OK, generated files актуальны
top.py health: validate OK, generate OK, capabilities OK, drivers catalog OK, drift OK
```

Вывод: канонические индексы, front matter, ссылки, драйверные манифесты и базовая консистентность сейчас зелёные.

### 2.3. Assurance / instruction surface

Команды:

```powershell
python tools\top.py assurance all --json
```

Результат:

```text
applied-evidence: OK, 11/11 задач конвенц-эры T>=156 с evidence
currency: OK, 0 находок актуальности
promotion-coverage: medium, orphan-L1: 11
flow: medium, accepted decisions not in instruction surface: D-001, D-010, D-013
```

Вывод: evidence-дисциплина последних задач работает. Главный долг — не отсутствие проверок, а неполное покрытие: часть ядра не связана с portals, а несколько accepted decisions не доведены до instruction surface.

Follow-up: T-173.

### 2.4. Конвейер workflow

Команда:

```powershell
python tools\top.py conveyor --json
```

Результат:

```text
target: 2
n_inflight: 5
n_landed: 0
n_shipped: 28
healthy: true
inflight: qa-adversarial-shipped, brigade-testing-quality, brigade-knowledge-search, brigade-cauldron-governance, solver-finder-problems
```

Вывод: конвейер здоров, но он уже шире target. Во время аудита один landed-result появился и был быстро переведён в shipped внешним/параллельным процессом; финальный снимок снова имеет `landed=0`. Методологически нельзя запускать больше workflow: надо ждать новых landed results или обрабатывать их через `top.py process-landed`.

### 2.5. Верхний слой / process-landed

Новая команда:

```powershell
python tools\top.py process-landed --json
```

Результат:

```json
{
  "schema": "top_process_landed.v1",
  "state": "empty",
  "counts": {"landed": 0, "with_output": 0, "missing_output": 0},
  "advice": ["No landed outputs. Keep target unchanged; wait for in-flight workflows or tick the conveyor."]
}
```

Вывод: верхний слой получил безопасную read-only кнопку для стадии INTAKE -> VERIFY -> SYNTHESIZE. Пока landed нет, она правильно не предлагает fan-out.

### 2.6. Тесты

Полный прогон tools test suite: 35 тестовых файлов.

Результат:

```text
32 / 35 OK
FAIL tools/tests/test_core_export.py
FAIL tools/tests/test_ownership.py
FAIL tools/tests/test_text_extract_docx.py
```

Все 3 падения одного класса: `PermissionError` при записи в подпапку, созданную Python `tempfile.mkdtemp`.

Дополнительная проба:

```powershell
Set-Content tmp-work\audit-write-probe.txt ok  # OK
python -c "import tempfile, os; d=tempfile.mkdtemp(dir='tmp-work'); open(os.path.join(d,'x.txt'),'w').write('ok')"
```

Результат: PowerShell пишет прямо в `tmp-work`, но Python не может писать в созданную им temp-подпапку.

Вывод: это не просто “системный TEMP запрещён”. Это воспроизводимый defect temp-helper/ACL/sandbox на Windows. Текущий `friction.py` F-004 считает `tmp-work` writable, но не ловит этот сценарий. Нужно усилить friction-check и дать общий safe temp helper.

Follow-up: T-172.

## 3. Концептуальный аудит

### 3.1. Что проект уже умеет

Проект фактически реализует несколько уровней “середины пирамиды” между обычной ОС и AI-agent на вершине:

- общая память в файлах Markdown/JSON;
- канон задач, вопросов, решений;
- generated indexes (`TASKS.md`, `index.json`, `STATUS.md`, `board.md`);
- протоколы полилога и append-only работы;
- инструменты проверки (`validate`, `generate`, `drift_check`, `assurance`);
- friction ledger/playbook для повторяющихся проблем;
- workflow conveyor для фоновых/параллельных результатов;
- верхняя панель `tools/top.py` как “кнопки” для людей и агентов;
- project skills как L3-процедуры;
- sandbox contracts для внешнего кода;
- knowledge/report/search слой.

Это уже не “чат с файлами”, а repo-native операционная среда для совместной работы людей и агентов.

### 3.2. Сильные стороны

1. **Проверяемость вместо надежды.** `validate`, `generate --check`, `assurance`, `instructions.py check-report`, evidence markers.
2. **Память процесса.** Решения, вопросы, задачи, outbox, done markers, friction ledger.
3. **Самоприменение.** Проект улучшает собственную инфраструктуру теми же tools, которые описывает.
4. **Безопасная граница.** Execute и external code не включены без preflight/sandbox.
5. **Параллельная работа осмыслена.** Есть streams, worktree, merge_gate, commit_lock, selective-add policy.
6. **Верхний слой начал формироваться.** `top.py` уже не просто shortcuts, а control plane: assurance, conveyor, process-landed, handoff, work-mode.

### 3.3. Слабые места

1. **Dirty shared tree.** Много незакоммиченных файлов; без selective-add легко случайно включить чужие/unknown artifacts.
2. **Temp PermissionError.** Несколько тестов ломаются из-за Python temp dirs; friction пока не ловит этот частный случай.
3. **Assurance medium findings.** Orphan-L1 и D-001/D-010/D-013 вне instruction surface.
4. **Слишком много документации без регулярного synthesis.** Документы сильные, но объём растёт быстрее, чем чистовые карты.
5. **Нет полноценного result intake classifier.** `process-landed` уже есть, но классификация пока простая.
6. **Нет зрелого UI/plugin/MCP верхнего слоя.** CLI есть; кнопки для человека пока текстовые.
7. **T-020/svend4 всё ещё blocked.** Sandbox contract есть, но реальный внешний источник/execute не закрыт.
8. **Lagrange не зарегистрирован как постоянный агент.** Может использоваться как temporary sub-agent, но governance-role ещё не оформлена.

### 3.4. Концептуальная стадия

Текущая стадия: **переход от архитектурного прототипа к операционному прототипу**.

- Концепция уже стабильная: верх/середина/основание пирамиды, repo flow vs platform orchestration, reduce tree 3:1, control plane.
- Техническая реализация частичная, но рабочая: CLI-tools, проверки, skills, конвейер, evidence.
- Продуктовая форма ещё ранняя: нет UI, installer, plugin packaging, multi-project portability, полноценного server orchestrator.

Корректная формулировка: проект находится в стадии **working prototype / alpha control plane**, а не production system.

## 4. Приоритеты

### P0 — сейчас

1. Не расширять workflow-флот: `n_inflight=5`, `target=2`, `landed=0`.
2. Не делать `git add -A`: есть unknown `data/portals/...` и много generated/shared files.
3. Обработать или дождаться in-flight outputs через `top.py process-landed`.
4. Перед commit — selective-add только своих файлов + повторный `validate/generate --check`.

### P1 — ближайшие задачи

1. **T-172:** исправить Python temp dir PermissionError / safe temp helper / friction F-004 coverage.
2. **T-173:** закрыть assurance medium findings: orphan-L1 и accepted decisions D-001/D-010/D-013 в instruction surface.
3. Развить `process-landed` в `result_intake` classifier после 2-3 реальных landed cycles.
4. Синтезировать растущие docs в более компактные top-level карты.

### P2 — стратегическое развитие

1. UI/ChatGPT App/MCP wrapper над `top.py buttons --json`.
2. Server orchestrator для sub-agent fleet, но только после устойчивого handoff/result contract.
3. Execute sandbox для внешнего кода, отдельно от read-only intake.
4. Multi-project packaging: какие skills/tools переносить в L1 core.
5. GitHub/PR интеграция, если проект будет жить не только локально.

## 5. Рекомендованный следующий цикл

```powershell
python tools\top.py conveyor --json
python tools\top.py process-landed --json
# если landed появятся:
python tools\instructions.py check-report queues\outbox\<result>.md
python tools\validate.py
python tools\generate.py --check
python tools\top.py assurance all
# затем synthesis/review/commit через selective-add
```

Для temp-defect:

```powershell
python -X utf8 tools\test_core_export.py
python -X utf8 tools\test_ownership.py
python -X utf8 tools\test_text_extract_docx.py
```

Ожидаемо сейчас они могут падать с PermissionError; это и есть предмет T-172.

## 6. Итоговое мнение Codex

Проект технически живой и быстро взрослеет. Самое ценное — не отдельный скрипт, а связка: канон файлов + проверяемость + верхняя панель + конвейер + skills. Это уже даёт основу для работы множества людей и агентов над одним информационным полем.

Главная опасность — перегрузить систему количеством агентов и документов раньше, чем верхний слой научится стабильно принимать и синтезировать результаты. Поэтому правильный вектор сейчас: меньше fan-out, больше intake/synthesis/gate automation. `process-landed` — правильный первый шаг; следующий — temp hardening и assurance coverage.
## 7. Update after T-172

P1 temp/ACL defect из аудита закрыт в T-172.

Новая проверенная картина:

```text
full tools test suite -> 36/36 OK
driver tests -> 15/15 OK
F-004 -> warn, потому project-safe helper работает, но stdlib tempfile остаётся unsafe в этой Windows runtime
```

Вывод: тестовая поверхность проекта больше не должна использовать `tempfile.mkdtemp()` / `TemporaryDirectory()` напрямую. Для hermetic tests использовать `drivers/test_tmp.py`.
## 8. Update after T-173

P1 assurance finding из аудита закрыт.

Новая проверенная картина:

```text
python tools/top.py assurance all --json -> applied OK, currency OK, promotion-coverage OK, flow OK
promotion-coverage -> L1-инвентарь: 10, порталов: 3, orphan-L1: 0
flow -> файлов реестра: 14, висячих accepted-решений: 0
```

Что изменено концептуально:

- `tools/instructions.py` теперь не просто перечисляет документы, а связывает accepted decisions с instruction surface через `surfaces`.
- `drivers/SCHEMA.md` оформлен как инструкция верхнего слоя для D-010/D-013: каталог драйверов и schema v1 стали частью проверяемого пути от решения к действиям агента.
- `portals/README.md` стал L2-grounding поверхностью для переносимого control-plane ядра, чтобы core-export не висел отдельно от порталов.

Оставшийся риск: assurance проверяет наличие surface и связей, но не качество фактического применения. Для качества нужны review, tests, outbox evidence и будущий stricter merge gate.