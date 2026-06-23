# T-196 — DOC_CONSENSUS_AGENT runtime recipe

Дата: 2026-06-23
Агент: codex
Статус: implemented, checked

## Что сделано

Добавлен чистовой runtime-рецепт для безопасного использования `DOC_CONSENSUS_AGENT`:

- `docs/doc-consensus-agent-runtime.md` — основной документ: контракт команды, safe examples, budget guard, no-agent dry-run, local stub-agent, real-agent wrapper, auto-accept policy.
- `tools/README.md` — semantic hybrid section теперь ссылается на runtime-рецепт.
- `docs/workflow-orchestration-policy.md` — добавлен раздел про DOC_CONSENSUS_AGENT semantic runtime как read-only filter, не workflow launcher.
- `docs/top-agent-operating-manual.md` — добавлена строка в карту функций.
- `tasks/T-196.md` — checklist закрыт.

## Почему именно так

T-176 уже добавил `--semantic`, `DOC_CONSENSUS_AGENT` seam и budget guard. Не хватало эксплуатационного слоя: как человеку или агенту включить semantic pass безопасно и не принять результат за готовое решение.

Рецепт фиксирует три принципа:

1. Default lexical mode не вызывает агента.
2. Semantic mode требует явного `--semantic` и явного `--semantic-budget`.
3. Output всегда `status: proposed`; auto-accept отсутствует и не должен появляться без отдельного решения.

## Проверенные примеры

```powershell
Remove-Item Env:DOC_CONSENSUS_AGENT -ErrorAction SilentlyContinue
python tools\doc_consensus.py report --files docs\parallel-work-policy.md docs\workflow-orchestration-policy.md --out tmp-work\t196-doc-consensus-lexical.md

Remove-Item Env:DOC_CONSENSUS_AGENT -ErrorAction SilentlyContinue
python tools\doc_consensus.py report --semantic --semantic-budget 99 --files docs\parallel-work-policy.md docs\workflow-orchestration-policy.md --out tmp-work\t196-doc-consensus-semantic-no-agent.md

Remove-Item Env:DOC_CONSENSUS_AGENT -ErrorAction SilentlyContinue
python tools\doc_consensus.py report --semantic --semantic-budget 0 --files docs\parallel-work-policy.md docs\workflow-orchestration-policy.md
```

Результат:

- lexical report записан в `tmp-work/`;
- semantic no-agent report записан в `tmp-work/`, `semantic-agent: (none)`, `status: proposed`;
- budget guard вернул ожидаемое `semantic budget exceeded: need 6 agent calls, budget 0` до agent call;
- `python tools\test_doc_consensus.py` OK.

## Safety note

`DOC_CONSENSUS_AGENT` должен быть read-only фильтром: stdin -> JSON stdout. Он не должен писать в репозиторий, делать commit/stage, запускать fan-out или менять decisions. Semantic output — материал для D-017/D-018, не финальное решение.

Applied instructions: AGENTS.md, PROTOCOL.md, tasks/T-196.md, docs/workflow-orchestration-policy.md, docs/top-agent-operating-manual.md, tools/README.md, tools/doc_consensus.py, tools/test_doc_consensus.py, Checks
Checks:
python tools\test_doc_consensus.py
python tools\doc_consensus.py report --files docs\parallel-work-policy.md docs\workflow-orchestration-policy.md --out tmp-work\t196-doc-consensus-lexical.md
python tools\doc_consensus.py report --semantic --semantic-budget 99 --files docs\parallel-work-policy.md docs\workflow-orchestration-policy.md --out tmp-work\t196-doc-consensus-semantic-no-agent.md
python tools\doc_consensus.py report --semantic --semantic-budget 0 --files docs\parallel-work-policy.md docs\workflow-orchestration-policy.md