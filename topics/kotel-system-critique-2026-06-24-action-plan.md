---
id: kotel-system-critique-action-plan-2026-06-24
type: topic-plan
title: Котёл: пошаговый план после системной критики
status: proposed
date: 2026-06-24
related: topics/kotel-system-critique-2026-06-24.md, T-242
---

# Котёл: пошаговый план после системной критики

## 0. Короткий вывод

Критика в `topics/kotel-system-critique-2026-06-24.md` верная по направлению: система уже выросла из свободного markdown-форума и требует более жёсткого машинного слоя. Но порядок исправлений должен быть не «переписать всё на argparse», а более безопасный:

1. Сначала сделать CLI-зондирование безопасным (`--help` без side effects).
2. Затем ввести единый CLI-контракт: stdout для данных, stderr для ошибок, JSON чистый.
3. Потом мигрировать сложные CLI на `argparse`, а простые оставить на `help_guard()`.
4. Параллельно перевести процессные правила из интуитивных формулировок в machine-checkable статусы, отчёты и gates.
5. Только после этого ратифицировать критику как `accepted` или разбить на несколько accepted-решений.

## 1. Что уже подтверждено проверкой

Проверка показала реальные симптомы:

- `python tools/conveyor.py --help` до фикса возвращал ошибку вместо полезной справки.
- `python tools/dispatch.py --help` до фикса запускал обычное действие и печатал список задач.
- `python tools/reconcile_state.py --help` до фикса запускал report/default path и писал новые отчёты в `queues/outbox/`.
- `python tools/synthesis_helper.py report kotel-system-critique-2026-06-24` не нашёл нескольких формальных вариантов по теме; значит текущий документ пока является mainline critique, а не результатом автоматического multi-variant synthesis.

## 2. Стадия A — безопасное зондирование CLI

Цель: агент может вызвать `tool --help` и ничего не сломать.

Статус: начато в T-242.

Сделано:

- `tools/_cli.py` используется как общий маленький helper.
- `tools/conveyor.py`, `tools/dispatch.py`, `tools/reconcile_state.py` получили `help_guard()`.
- `--help` теперь возвращает exit code 0 и печатает реальные CLI-инструкции.
- `tools/test_cli.py` проверяет, что эти help-вызовы не меняют `queues/outbox/`.

Следующие проверки:

```powershell
python tools\test_cli.py
python tools\conveyor.py --help
python tools\dispatch.py --help
python tools\reconcile_state.py --help
```

## 3. Стадия B — stdout/stderr и JSON-контракт

Цель: любой инструмент, который обещает JSON, должен быть пригоден для пайпа.

Правила:

- JSON-режим печатает в stdout только JSON.
- Ошибки, warnings, tracebacks и human text идут в stderr.
- `--help` всегда stdout + exit 0.
- User/usage error: exit 2.
- Runtime/internal error: exit 1.
- Advisory finding не обязан быть error: read-only диагностика может возвращать 0, если команда выполнилась.

Следующие задачи:

1. Инвентаризировать CLI-инструменты по группам: argparse / help_guard / raw sys.argv.
2. Найти JSON-команды, которые загрязняют stdout.
3. Добавить smoke-тесты на самые используемые top/pipeline/conveyor/sandbox команды.

## 4. Стадия C — argparse только там, где он нужен

Не все старые CLI надо переписывать сразу. Правильное разделение:

- Простые команды с 1-2 режимами: `help_guard()` достаточно.
- Команды с flags, choices, optional values, JSON/text режимами: переводить на `argparse`.
- Команды верхнего слоя (`top.py`, `instructions.py`, `sandbox_intake_chain.py`) уже могут оставаться на `argparse`.

Кандидаты на постепенный `argparse`:

1. `tools/conveyor.py` — много subcommands, flags, exit-code semantics.
2. `tools/reconcile_state.py` — check/report/fix/--apply, side-effect boundary.
3. `tools/pipeline.py` — критический state machine, но миграция должна быть отдельной стадией с широкими тестами.

## 5. Стадия D — deterministic PROTOCOL.md

Проблема критики: формулы вроде «если не уверен» и «маленькие улучшения» полезны человеку, но плохо исполняются stateless-агентом.

Предложение: не удалять гуманитарный слой, а добавить машинный слой рядом.

Нужно добавить в `PROTOCOL.md` или отдельный `docs/protocol-machine-layer.md`:

- `BLOCKED` должен иметь machine-readable причину: `blocked_by`, `needed_input`, `last_attempt`, `next_unblock_check`.
- Вопрос должен иметь id и owner: `Q-XXX`, `owner`, `decision_needed`, `deadline/none`.
- Отчёт агента должен содержать `## Applied instructions` и `Checks:`.
- Любая auto-fix команда должна иметь dry-run по умолчанию или явный `--apply`.
- Любая команда, меняющая primary state, должна быть отделена от read-only диагностики.

## 6. Стадия E — queues как state machine

Критика про `queues/` справедлива: сырые markdown-очереди полезны как журнал, но недостаточны как автоматический state machine.

Порядок развития:

1. Сохранить `queues/outbox/` как durable evidence log.
2. Добавить machine index поверх него: class, status, related workflow, processed/shipped.
3. Не удалять старый мусор автоматически; помечать как `archived`, `historical`, `unreferenced`.
4. Связать `conveyor recover` с этим индексом, чтобы `unreferenced-outbox-reports` перестал быть просто большой цифрой.

## 7. Стадия F — ратификация критики

Текущий документ пишет: «консенсус достигнут». Технически лучше не переводить весь документ в `accepted` целиком, потому в нём смешаны разные типы решений:

- CLI-help safety — уже можно ратифицировать как accepted micro-policy.
- Полная миграция на argparse — пока proposed, требует оценки blast radius.
- PROTOCOL machine layer — proposed, требует отдельного документа/решения.
- Очереди как state machine — proposed, большая архитектурная стадия.

Рекомендация: сделать не одно большое accepted-решение, а 3-4 маленьких решения.

## 8. Предлагаемый порядок следующих задач

1. `T-242` — закрыть stage A: help guard для первых CLI + action plan.
2. `T-next` — CLI inventory: список всех raw `sys.argv`, кто уже имеет `help_guard`, кто требует argparse.
3. `T-next` — JSON purity smoke tests для top/conveyor/pipeline/sandbox.
4. `T-next` — `docs/protocol-machine-layer.md`: deterministic statuses and escalation report format.
5. `T-next` — outbox processing index: processed/unprocessed/shipped report state.
6. `T-next` — split `kotel-system-critique` into proposed decisions.
7. `T-next` — selective argparse migration for `conveyor.py` with compatibility tests.

## 9. Мнение Codex

Главный риск сейчас не в том, что мало правил. Риск в том, что правил уже много, но часть правил не исполняется автоматически. Поэтому лучший следующий слой — не ещё один большой философский документ, а маленькие проверяемые контракты:

- help не пишет файлы;
- JSON чистый;
- blocked имеет структурированную причину;
- outbox report имеет обработанный статус;
- top layer показывает безопасную команду вместо скрытого знания.

Именно так «котёл» превращается из форума в управляемый workflow-engine: текст остаётся для людей, но каждый важный текст получает машинный след, проверку и следующий исполнимый шаг.

## Applied instructions

- Использован `cauldron-synthesis` skill: разногласия не удалялись, исходный critique-файл не переписан.
- `synthesis_helper.py` был вызван; формальных fork-вариантов по этой теме он не нашёл, поэтому создан отдельный proposed action plan.
- Соблюдён `AGENTS.md`: результат вынесен отдельным документом, а не перезаписал чужую историю.
- T-242 ведётся через pipeline claim.

Checks:

```
python tools\synthesis_helper.py topics --json -> OK
python tools\synthesis_helper.py report kotel-system-critique-2026-06-24 -> expected: no formal variants found
python tools\conveyor.py --help -> OK after T-242 fix
python tools\dispatch.py --help -> OK after T-242 fix
python tools\reconcile_state.py --help -> OK after T-242 fix
```