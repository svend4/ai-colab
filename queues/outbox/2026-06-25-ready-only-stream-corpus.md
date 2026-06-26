---
id: 2026-06-25-ready-only-stream-corpus
type: report
status: done
owner: codex
date: 2026-06-25
related: [T-256, T-253, T-254, T-255, D-017, D-018, D-028, tools/doc_synthesis.py, tools/top.py]
---

# T-256 — ready-only stream corpus

## Что сделано

Добавлен режим, в котором synthesis читает только готовые stream-варианты:

```powershell
python tools\doc_synthesis.py scan <topic> --ready-only --json
python tools\top.py synthesize-docs <topic> --ready-only --json
python tools\top.py cauldron-lanes <topic> --ready-only
```

Готовыми считаются stream-пакеты с `status: ready-for-synthesis` или `synthesis_ready: true`.

## Изменения

- `tools/doc_synthesis.py`: добавлены `read_front_matter()`, `stream_is_ready()`, `stream_topic_files(topic, ready_only=False)`.
- `tools/doc_synthesis.py`: `resolve_files(..., ready_only=False)` теперь умеет режим ready-only.
- `tools/top.py`: `--ready-only` проброшен в `synthesize-docs` и `cauldron-lanes`.
- `tools/test_doc_synthesis.py`: добавлен тест, где proposed stream не попадает в ready-only corpus.
- `tools/test_top.py`: parser/buttons проверяют `--ready-only`.
- Docs обновлены в `independent-variant-stream-policy`, `document-synthesis-mechanism`, `top-layer-command-groups`, `tools/README.md`.

## Почему так

Новая политика разрешает нескольким агентам писать независимые варианты. Но synthesis для строительства не должен брать недозревшие proposed/developing черновики. Поэтому появились два режима:

| Режим | Что читает |
|---|---|
| без `--ready-only` | все stream-пакеты topic |
| `--ready-only` | только готовые к synthesis |

Явно переданные files не фильтруются: если агент вручную передал corpus, ответственность за подбор corpus остаётся у него.

## Проверки

OK:

```powershell
python -m py_compile tools\doc_synthesis.py tools\top.py tools\test_doc_synthesis.py tools\test_top.py
python tools\test_doc_synthesis.py
python tools\test_top.py
python tools\doc_synthesis.py scan doc-synthesis-stream-corpus --ready-only --json
python tools\top.py synthesize-docs doc-synthesis-stream-corpus --ready-only --json
```

Результаты:

- `test_doc_synthesis.py`: 4 tests OK.
- `test_top.py`: OK.
- `doc_synthesis.py scan ... --ready-only`: corpus = `streams/doc-synthesis-stream-corpus/20260625-1756-codex/STREAM.md`.
- `top.py synthesize-docs ... --ready-only`: тот же corpus через верхний слой.

## Applied instructions

- `AGENTS.md` / `PROTOCOL.md`: работал через T-256, без удаления чужих сообщений.
- `D-017` / `D-028`: варианты сохраняются, ready-only только фильтрует maturity для synthesis.
- `D-018` / cauldron-synthesis: decisions не переводились в `accepted`; результат proposed/tooling.
- Dirty shared tree: commit не делался, `git add -A` не использовался.

Checks:
- python tools\validate.py -> OK
- python tools\generate.py --check -> OK
- python tools\instructions.py check-report <this-file> -> OK after footer normalization
