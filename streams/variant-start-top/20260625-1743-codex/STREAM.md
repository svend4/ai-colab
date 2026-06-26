---
id: 20260625-1743-codex
topic: variant-start-top
agent: codex
status: ready-for-synthesis
created: 2026-06-25
variant_policy: independent-first
synthesis_ready: true
status_note: implementation variant completed for T-254
related: [T-254, D-028, top.py, independent-variant-stream-policy]
---

# Stream: 20260625-1743-codex

## 00. Причина независимого варианта

Новая политика уже требует, чтобы агент начинал содержательный похожий вопрос через independent stream. Но вручную это всё ещё несколько команд. Нужна apex-команда, которая снижает трение и делает правильный путь самым коротким.

## 01. Условия применимости

Команда нужна для содержательных вопросов, методологии, архитектуры, ревью и больших предложений, где агенту нужно создать свой вариант до synthesis. Она не нужна для механических id/index/lock/generated задач.

## 02. Независимый ответ агента

Предлагаю `python tools/top.py variant-start <agent> <topic...> [--task T-id] [--reason TEXT] [--json]`. Команда должна:

1. выполнить `repo-search` по теме;
2. создать stream-пакет через `stream.py create`;
3. показать путь stream-файла;
4. показать команду `stream.py mark ... ready-for-synthesis`;
5. если указан `--task`, выполнить или показать `instruction-preflight`.

## 03. Потенциал, который нужно раскрыть до синтеза

- новые под-вопросы: делать preflight исполняемым или только планом;
- edge cases: JSON-режим должен возвращать path/id без шумных заголовков;
- альтернативные реализации: отдельный `variant.py`, shell script, или proxy в `stream.py`;
- риски и ограничения: команда создаёт stream, поэтому side-effect должен быть явно указан в buttons/capabilities.

## 04. Сравнение с известными вариантами

- Похожие пункты: `agent-start` делает onboarding/status/advice/search, но не создаёт variant stream.
- Отличия: `variant-start` конкретно запускает independent-first поток.
- Что этот вариант добавляет сверх уже написанного: один безопасный вход вместо ручной цепочки.
- Что может оказаться настоящим шумовым дублем после синтеза: будущий GUI/кнопка может обернуть эту команду, но CLI-контракт всё равно нужен.

## 05. Evidence / проверки

План проверок:

- `python -m py_compile tools\top.py tools\test_top.py`
- `python tools\test_top.py`
- `python tools\top.py variant-start codex variant-start-smoke --reason "smoke" --json`
- `python tools\stream.py check --max-age-days 7 --json`
- `python tools\validate.py`
- `python tools\generate.py --check`

## 06. Вопросы другим агентам и людям

- Нужно ли `variant-start` по умолчанию запускать `instruction-preflight` как команду, или только печатать следующую команду?
- Нужно ли автоматически ставить задачу observer, когда по теме появилось 2+ ready variants?

## 07. Synthesis contract

- consensus candidates: нужна apex-команда для старта independent-first варианта.
- divergence candidates: степень автоматичности preflight/search.
- adoption target: `tools/top.py`, `tools/test_top.py`, docs/capabilities.
- reject/supersede condition: отдельный `tools/variant.py` заменит top-wrapper.

## 08. Adoption

Перенос в mainline идёт через T-254. D-028 остаётся proposed до человека/integrator.