---
id: additive-enrichment-shortlist-2026-07-07
type: report
status: proposed
agent: codex
date: 2026-07-07
related: [T-294, T-295, T-296, D-017, D-018, D-026]
---

# Additive enrichment shortlist

## Принцип отбора

В этот список попали только задачи, которые обогащают проект и не требуют удаления истории, чужих отчётов, тем, очередей или кода. Формула отбора:

1. Добавляет защиту, индекс, отчёт, метод, wrapper, тест или новый прототип.
2. Не редактирует deny-пути: `tools/permissions.json`, `tools/githooks/**`, `sandbox/approvals/**`.
3. Не переводит решения в `accepted` без человека.
4. Не стирает альтернативные варианты: повторы становятся материалом для consensus, расхождения остаются divergence.

## Выбранные задачи

### 1. T-294 — Bulk guard range gate

Польза: закрывает слабое место локального pre-commit. Если агент обошёл hook через `git commit --no-verify`, range-gate всё равно может проверить уже созданный диапазон коммитов.

Зоны: `tools/bulk_guard.py`, `tools/tests/test_bulk_guard_range.py`, отчёты.

Риск: medium, потому range-проверка может дать false positive на rename/rewrite. Снижение риска: используется `--find-renames`, есть тест rename-only.

Статус: взято Codex и реализовано в этом проходе.

### 2. T-295 — Cauldron materializer

Польза: превращает отчёты и ответы агентов в явные варианты для синтеза. Это решает проблему, когда хорошие ответы лежат текстом, но не попадают в consensus/divergence pipeline.

Зоны: новый инструмент или новый режим, отчёт, outbox, возможно новые variant-файлы в `streams/` только при explicit apply.

Риск: medium, потому классификация отчёта может ошибиться. Снижение риска: dry-run по умолчанию, proposed-only, без удаления исходников.

Статус: готово к взятию из конвейера.

### 3. T-296 — Additive enrichment shortlist

Польза: создаёт постоянный список безопасных задач, которые агенты могут брать, когда надо развивать проект без риска разрушения истории.

Зоны: reports/outbox/tasks/indexes.

Риск: low. Это организационный слой, не исполняющий destructive actions.

Статус: создана задача и данный отчёт как начальная версия списка.

### 4. Proposed — package handoff

Источник: read-only подагент Nash.

Польза: сделать `PKG-*`-aware handoff для worker/scout без ложного claim/in-flight. Агент получает пакет как prompt/json и возвращает результат, не занимая основную задачу неправильно.

Возможные файлы: `tools/package_handoff.py`, `tools/tests/test_package_handoff.py`, optional wrapper в `tools/top.py`.

Риск: low-medium. Не должен менять package state автоматически.

### 5. Proposed — package gate wakeup advisory

Источник: read-only подагент Nash.

Польза: показывать medium-пакеты с истёкшим `review_deadline` и без veto как advisory-сигнал. Это ускоряет человека/координатора, но не подменяет утверждение.

Возможные файлы: `tools/package_gate.py`, `tools/tests/test_package_gate.py`, отчёт.

Риск: low-medium. Важно: silence is signal, not approval.

### 6. Proposed / T-280-adjacent — D-033 ratification brief only

Источник: read-only подагент Nash.

Польза: закрыть missing-artifact WARN по human-gate через нейтральный brief, не ратифицируя решение за человека.

Возможные файлы: `reports/d033-ratification-brief-2026-07-07.md`.

Риск: low. Только справка для human gate.

## Рекомендация Codex

Порядок после T-294:

1. Взять T-295, потому это напрямую включает работу подагентов и решает проблему “полезный совет есть, но не применяется”.
2. Затем сделать package handoff, чтобы рои получали задания более формально.
3. Затем package gate wakeup advisory, чтобы верхний слой видел зависшие пакеты.
4. T-280-adjacent brief делать отдельно, потому там есть human-gate и нельзя имитировать ратификацию.