---
id: outbox-2026-06-25-variant-batch-barrier
status: final
author: codex
related: [T-259, T-258, D-017, D-028, variant-batch-barrier, top.py]
created: 2026-06-25
---

# Outbox - T-259 variant-batch barrier

## Короткий итог

T-259 добавляет следующий слой после `variant-start`: пачка independent-first агентов теперь может запускаться через manifest/barrier, а не только через ручной чат.

Команда:

```powershell
python tools\top.py variant-batch <topic...> --agents codex,mavis,reviewer [--task T-id] [--quorum N] [--batch-id ID]
```

Она пишет manifest:

```text
streams/<topic>/_batches/<batch-id>.json
```

и не создаёт `STREAM.md` за других агентов. Это важно: независимый вариант должен написать сам агент через `variant-start`, иначе возникает ghost ownership.

## Что было сделано

- Создана задача `tasks/T-259.md`.
- До сверки создан independent stream Codex: `streams/variant-batch-barrier/20260625-1913-codex/STREAM.md`.
- Подключены sub-agents:
  - Ramanujan: документационно-архитектурный аудит batch/barrier.
  - Anscombe: code-extension review для `top.py` / `stream.py` / `doc_synthesis.py`.
  - Boyle: независимый worker stream `streams/variant-batch-barrier/20260625-subagent-worker/STREAM.md`.
- Реализован `tools/top.py variant-batch`.
- Добавлены тесты в `tools/test_top.py`.
- Обновлены live docs/capabilities:
  - `docs/top-layer-command-groups.md`;
  - `docs/independent-variant-stream-policy.md`;
  - `tools/README.md`;
  - `tools/capabilities.py`.
- Dogfood: создан `streams/variant-batch-barrier/_batches/t259.json`.

## Consensus

- Batch/barrier нужен для пачки independent-first агентов после T-258.
- Manifest должен жить рядом со stream corpus, но не быть содержательным stream: `streams/<topic>/_batches/<batch-id>.json`.
- Wrapper не должен loop-ить `_variant_start_payload`, потому это создаст stream-файлы за агентов.
- Default barrier для малых batch: all-ready (`quorum = число агентов`).
- `--quorum N` допустим как заранее объявленный режим, но silent downgrade запрещён.
- Comparison/synthesis открываются после `ready_count >= quorum`.
- Synthesis должен читать только `--ready-only` stream-пакеты.

## Divergence / future work

- Нужна ли отдельная команда `variant-batch-status`, или достаточно повторного `variant-batch` для обновления manifest/status?
- Нужно ли в manifest schema v2 явно разделить roles: observer и synthesizer?
- Как фиксировать late streams после quorum synthesis: appendix, second synthesis pass или divergence-detail?
- Нужен ли timeout/fallback в manifest v2?

## Проверки

Выполнены:

```text
python -m py_compile tools\top.py tools\test_top.py tools\capabilities.py
python tools\test_top.py
python tools\top.py variant-batch variant-batch-barrier --agents codex,subagent-worker --task T-259 --batch-id t259 --json
python tools\stream.py check --max-age-days 7 --json
python tools\top.py cauldron-lanes variant-batch-barrier --ready-only --json
python tools\generate.py
python tools\validate.py
python tools\generate.py --check
```

Результат: `test_top` OK, `stream.py check` без stale/broken/incomplete_ready, manifest `phase: comparison-open`, `ready_count: 2`, `missing_agents: []`, `validate.py` -> `OK=12 WARN=0 ERROR=0`, generated state стабилен.

## Следующие шаги

1. Если понадобится, добавить `variant-batch-status` как read-only команду.
2. Добавить manifest schema v2 с roles/timeouts/late-stream policy.
3. Обернуть `variant-batch` в workflow/sub-agent launcher, если появится стабильный внешний агентный runtime.

## Applied instructions

- AGENTS.md: outbox report preserved; no чужие сообщения удалялись.
- PROTOCOL.md: report kept as proposed/done evidence; no accepted decision is created here.
- docs/protocol-machine-layer.md: added explicit machine-readable evidence footer for check-report.

Checks:
- python tools\validate.py -> OK
- python tools\generate.py --check -> OK
- python tools\instructions.py check-report <this-file> -> OK after footer normalization
