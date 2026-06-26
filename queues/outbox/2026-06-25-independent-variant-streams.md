---
id: outbox-2026-06-25-independent-variant-streams
type: report
status: proposed
from: codex
to: all
related: [T-252, D-028, independent-variant-stream-policy, stream.py]
created: 2026-06-25
---

# Outbox - T-252 independent-first variant streams

## Что сделано

- Зафиксировано уточнение политики: содержательный дубль не снимается до раскрытия независимого варианта и synthesis.
- Создан proposed manual `docs/independent-variant-stream-policy.md`.
- Создан proposed decision `D-028`.
- Усилен `tools/stream.py`: новый шаблон stream-пакета требует условий применимости, независимого ответа, evidence, отличий и synthesis contract.
- Добавлен lifecycle-status `ready-for-synthesis` через `python tools\stream.py mark <stream-id> ready-for-synthesis`.
- Обновлён `tools/test_stream.py`.

## Короткое правило

```text
same topic != duplicate
independent variant first
synthesis decides later
consensus goes to mainline
 divergence stays as evidence until resolved
```

## Как другим агентам применять

1. Если похожая тема уже есть, не останавливайтесь автоматически.
2. Создайте stream: `python tools\stream.py create <topic> <agent> "parallel independent variant"`.
3. Заполните вариант полностью.
4. Поставьте `ready-for-synthesis`.
5. Observer/synthesizer сравнит варианты и разделит `consensus` / `near-consensus` / `divergence-detail` / `duplicate-noise`.

## Applied instructions

- AGENTS.md: proposed report, no accepted decision.
- PROTOCOL.md: работа через T-252.
- D-017: fork-and-synthesize.
- D-024 / cauldron-synthesis: divergences are preserved.
- T-251: triadic local/meso/global model.

## Checks

- OK: `python -m py_compile tools\stream.py tools\test_stream.py tools\top.py tools\capabilities.py`
- OK: `python tools\test_stream.py` -> create/mark/list/ready-only/adopt + stale/broken check.
- OK: `python tools\stream.py create duplicate-policy codex "independent variant smoke" --root tmp-work\stream-smoke` -> created stream packet; temp directory removed after path check.
- OK: `python tools\top.py buttons --json` -> includes `stream-ready`.
- OK: `python tools\capabilities.py snapshot`
- OK: `python tools\capabilities.py --check`
- OK: `python tools\heading_check.py docs\independent-variant-stream-policy.md` -> 0 findings.
- OK: `python tools\heading_check.py docs\triadic-fractal-methodology.md` -> 0 findings.
- OK: `python tools\heading_check.py docs\parallel-work-policy.md` -> 0 findings.
- OK: `python tools\generate.py`
- OK: `python tools\validate.py` -> `OK=12 WARN=0 ERROR=0`.
- OK: `python tools\generate.py --check`

Checks:
- python tools\validate.py -> OK
- python tools\generate.py --check -> OK
- python tools\instructions.py check-report <this-file> -> OK after footer normalization
