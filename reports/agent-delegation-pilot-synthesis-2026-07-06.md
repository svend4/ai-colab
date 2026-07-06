# Agent delegation pilot synthesis — 2026-07-06

Автор: Codex  
Статус: proposed synthesis  
Связано: `reports/agent-delegation-pilot-2026-07-06.md`, `reports/no-verify-bulk-guard-review-2026-07-06.md`, `reports/bulk-guard-range-gate-proposal-2026-07-06.md`

## Волна агентов

| Агент | Роль | Статус | Итог |
|---|---|---|---|
| Gauss | governance-scout | shutdown/timeout | Задача оказалась слишком широкой; следующий раз дробить на 2-3 коротких governance-вопроса. |
| Maxwell | safety-scout | completed | Подтвердил: локальный `pre-commit + bulk_guard` нужен, но `--no-verify` его обходит; нужен CI/pre-receive/merge-gate range guard. |
| Ramanujan | backlog-scout | completed | Подтвердил текущий pipeline и предложил безопасные read-only задания для следующей волны. |

## Consensus

1. Сейчас не надо давать многим агентам write-доступ в одно dirty tree.
2. Правильный текущий режим — `read-only scouts + lead integrator`.
3. Для writer-агентов нужны disjoint write scopes или worktree/merge-gate.
4. `T-269` и `T-280` не закрывать агентами: это human/governance gates.
5. `T-274` и `T-285` требуют разборки stale/orphan claim перед write-работой.
6. `T-286` подходит для следующей read-only D-015 верификации data driver.
7. `--no-verify` нельзя считать технически безопасным escape-path; нужна защита выше локального hook.

## Divergence / unresolved

1. `Gauss` не дал governance evidence из-за timeout. Нужно повторить governance-аудит как более мелкие задания:
   - только `AGENTS.md + PROTOCOL.md`;
   - только `workflow-conveyor-policy + agent-capacity-methodology`;
   - только `orchestrator-cycle` документы.
2. `Maxwell` создал proposed files, но не должен править `tools/githooks/**`, потому это deny-zone/human-integrator path.
3. Вопрос: кто назначен integrator для изменения pre-commit текста, где он предлагает `--no-verify`? Без этого агентам нельзя править hook.

## Next-wave assignments

### Agent D — data-driver-verifier

Mode: read-only.  
Scope: `tasks/T-286.md`, `drivers/data.md`, `drivers/data/data_driver.py`, `drivers/data/test_data.py`, `reports/driver-verification-2026-07-06.md`.  
Output: outbox/report only.  
Goal: проверить, какие замечания D-015 по `data` закрыты, какие остаются; предложить критерий для будущего `verified_by`.

### Agent E — pipeline-tripwire-designer

Mode: read-only.  
Scope: `tasks/T-274.md`, `tools/pipeline.py`, `queues/claimed/`, `logs/heartbeat*.json`, `docs/workflow-conveyor-policy.md`.  
Output: algorithm/design report only.  
Goal: дать точный алгоритм concurrency tripwire без правки `tools/pipeline.py`, потому у `T-274` stale claim.

### Agent F — bulk-range-guard-spec

Mode: read-only/spec.  
Scope: `tools/bulk_guard.py`, `tools/tests/test_bulk_guard.py`, `tools/commit.py`, `reports/bulk-guard-range-gate-proposal-2026-07-06.md`, `PROTOCOL.md`, `D-026`.  
Output: implementation spec for `bulk_guard --range <base>..<head> --strict`.  
Goal: подготовить будущую worker-задачу без изменения hook.

## Decision for current lead

Я не запускаю writer-агентов прямо сейчас, потому есть смешанное дерево и stale/orphan claims. Следующая безопасная активность — ещё одна scout-волна по D/E/F или один worker только после явного выбора disjoint scope.