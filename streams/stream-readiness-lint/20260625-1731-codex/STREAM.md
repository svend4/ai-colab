---
id: 20260625-1731-codex
topic: stream-readiness-lint
agent: codex
status: ready-for-synthesis
created: 2026-06-25
variant_policy: independent-first
synthesis_ready: true
status_note: implementation variant completed for T-253
related: [T-253, D-028, independent-variant-stream-policy]
---

# Stream: 20260625-1731-codex

## 00. Причина независимого варианта

Нужно применить `independent-first` не только как текстовую политику, но и как проверяемое правило: если агент пометил stream как `ready-for-synthesis`, инструмент должен проверить минимальную полноту варианта.

## 01. Условия применимости

Вариант применяется только к stream-пакетам, которые явно заявили готовность к сверке: `status: ready-for-synthesis` или `synthesis_ready: true`. Старые `proposed`, `developing`, `ready-for-review` и terminal-пакеты не должны ломаться из-за нового правила.

## 02. Независимый ответ агента

Предлагаю добавить в `tools/stream.py check` третий тип диагностики рядом со `stale` и `broken`: `incomplete_ready`. Он будет показывать stream-пакеты, которые уже готовы к synthesis по статусу, но не имеют обязательных разделов или оставили стандартные placeholder-тексты.

## 03. Потенциал, который нужно раскрыть до синтеза

- новые под-вопросы: какие секции считать обязательными для `ready-for-synthesis`;
- edge cases: старые streams без новой схемы, ручные divergence-файлы, adopted streams;
- альтернативные реализации: strict-lint отдельной командой, advisory внутри `stream.py check`, или `top.py stream-health`;
- риски и ограничения: слишком строгая проверка может заблокировать legacy streams, поэтому первая версия должна быть узкой и backwards-compatible.

## 04. Сравнение с известными вариантами

- Похожие пункты: `docs/independent-variant-stream-policy.md` пункт 12.1 уже требует такой проверки.
- Отличия: текущий вариант реализует именно low-risk проверку внутри существующего `stream.py check`, без нового инструмента и без изменения governance.
- Что этот вариант добавляет сверх уже написанного: машинный сигнал `incomplete_ready`.
- Что может оказаться настоящим шумовым дублем после синтеза: отдельный future `triad_lint.py` может потом заменить часть этой проверки, но сейчас он шире по scope.

## 05. Evidence / проверки

План проверок:

- `python -m py_compile tools\stream.py tools\test_stream.py`
- `python tools\test_stream.py`
- `python tools\stream.py check --max-age-days 7`
- `python tools\validate.py`
- `python tools\generate.py --check`

## 06. Вопросы другим агентам и людям

- Нужно ли в будущем считать `ready-for-review` тоже обязательным к полноте, или только `ready-for-synthesis`?
- Должен ли `incomplete_ready` быть hard error всегда, или advisory в `top.py health`?

## 07. Synthesis contract

- consensus candidates: `stream.py check` должен видеть неполные ready-for-synthesis пакеты.
- divergence candidates: степень строгости проверки и список обязательных секций.
- adoption target: `tools/stream.py`, `tools/test_stream.py`, `docs/independent-variant-stream-policy.md`.
- reject/supersede condition: если отдельный `triad_lint.py` будет принят как общий checker для all artifacts.

## 08. Adoption

Перенос в mainline — через T-253, проверки и outbox. Accepted governance не создаётся; D-028 остаётся proposed до человека/integrator.