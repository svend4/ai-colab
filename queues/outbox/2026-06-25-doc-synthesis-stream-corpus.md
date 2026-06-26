---
id: 2026-06-25-doc-synthesis-stream-corpus
type: report
status: done
owner: codex
date: 2026-06-25
related: [T-255, T-252, T-253, T-254, D-028, tools/doc_synthesis.py, tools/top.py]
---

# T-255 — doc_synthesis читает stream topic как corpus

## 01. Что сделано

Закрыт следующий шаг политики independent-first variants: после `top.py variant-start` observer/synthesizer теперь может запустить synthesis по topic без ручного списка stream-файлов.

Новый рабочий маршрут:

```powershell
python tools\top.py variant-start codex doc-synthesis-stream-corpus --task T-255
python tools\stream.py mark 20260625-1756-codex ready-for-synthesis "variant completed"
python tools\top.py synthesize-docs doc-synthesis-stream-corpus --json
```

## 02. Изменения

- `tools/doc_synthesis.py`: добавлен `stream_topic_files(topic)`.
- `tools/doc_synthesis.py`: `resolve_files()` теперь для custom topic без files ищет `streams/<topic>/*/STREAM.md`.
- `tools/test_doc_synthesis.py`: добавлен unit-test временного stream topic corpus.
- `streams/doc-synthesis-stream-corpus/20260625-1756-codex/STREAM.md`: создан и заполнен independent-first stream, затем помечен `ready-for-synthesis`.
- `docs/independent-variant-stream-policy.md`: пункт 12.3 переведён в DONE, добавлен раздел T-255.
- `docs/document-synthesis-mechanism-2026-06-24.md`: описан stream corpus workflow.
- `docs/top-layer-command-groups.md`: верхний слой описывает полный цикл `variant-start -> stream -> synthesize-docs`.
- `tools/README.md`: добавлена подсказка по `synthesize-docs <custom-topic>`.

## 03. Совместимость

Правило совместимости выбрано консервативно:

1. Явно переданные files имеют приоритет.
2. `architecture-core` без files остаётся историческим preset, потому в `streams/architecture-core` уже есть старый stream и молчаливое изменение default могло бы сломать привычный workflow.
3. Custom topic без files читает `streams/<topic>/*/STREAM.md`.
4. Если ни files, ни stream corpus нет, команда падает с понятной подсказкой.

## 04. Проверки

OK:

```powershell
python -m py_compile tools\doc_synthesis.py tools\test_doc_synthesis.py tools\top.py
python tools\test_doc_synthesis.py
python tools\doc_synthesis.py scan doc-synthesis-stream-corpus --json
python tools\top.py synthesize-docs doc-synthesis-stream-corpus --json
python tools\stream.py check --max-age-days 7 --json
python tools\generate.py
python tools\validate.py
python tools\generate.py --check
python tools\top.py status codex
python tools\top.py health
```

Ключевые результаты:

- `test_doc_synthesis.py`: 3 tests OK.
- `doc_synthesis.py scan doc-synthesis-stream-corpus --json`: documents[0] = `streams/doc-synthesis-stream-corpus/20260625-1756-codex/STREAM.md`.
- `top.py synthesize-docs doc-synthesis-stream-corpus --json`: тот же stream найден через верхнюю команду.
- `stream.py check --json`: `stale=[]`, `broken=[]`, `incomplete_ready=[]`.
- `validate.py`: `OK=12 WARN=0 ERROR=0`.
- `generate.py --check`: indexes актуальны.
- `top.py health`: exit 0; есть advisory-долги по D-Card и assurance, не внесённые T-255.

## 05. Applied instructions

- `AGENTS.md`: работал в разрешённых зонах `tools/`, `docs/`, `tasks/`, `streams/`, `queues/`; чужие сообщения не удалялись.
- `PROTOCOL.md`: правки обоснованы в stream и outbox; общий статус закрывается через pipeline.
- `D-017` / `D-028`: вариант не схлопнут как дубль, сначала раскрыт в отдельном stream.
- `D-018` / cauldron-synthesis: governance не переводился в `accepted`; результат остаётся proposed/ready-for-synthesis.
- `docs/parallel-work-policy.md`: shared tree dirty, поэтому commit не выполнялся и `git add -A` не использовался.
- `docs/friction-playbook.md`: применён известный fallback PowerShell UTF-8 вместо `apply_patch`, потому sandbox `apply_patch` в этой Windows-среде ранее падал на split writable roots.

## 06. Открытые вопросы

- Нужен ли отдельный флаг `--stream-corpus` для preset-тем вроде `architecture-core`?
- Должен ли future corpus provider читать только `ready-for-synthesis` stream-пакеты?
- Нужно ли объединить `variants.py`, `stream.py list --ready-only` и `doc_synthesis.py` в единый corpus provider?

## 07. Следующие задачи-кандидаты

1. Добавить режим ready-only corpus для stream synthesis.
2. Добавить `top.py synthesize-streams <topic> --ready-only` как более явную верхнюю команду.
3. Разобрать advisory `top.py health`: D-Card gaps в новых `tools/*.py` и assurance finding по weak evidence.

## Applied instructions

- AGENTS.md: outbox report preserved; no чужие сообщения удалялись.
- PROTOCOL.md: report kept as proposed/done evidence; no accepted decision is created here.
- docs/protocol-machine-layer.md: added explicit machine-readable evidence footer for check-report.

Checks:
- python tools\validate.py -> OK
- python tools\generate.py --check -> OK
- python tools\instructions.py check-report <this-file> -> OK after footer normalization
