---
name: top-layer-orchestrator
description: Управлять верхним слоем AI-OS Bridge: принимать результаты агентов, проверять evidence, синтезировать варианты, регулировать conveyor target и безопасно готовить commit. Использовать, когда задача связана с множеством агентов/workflow, landed outputs, PROCESS/REFILL, синтезом отчётов, commit batching или вопросом “почему запуск агентов ограничен обработкой верхнего слоя”.
---

# Skill: top-layer-orchestrator

Используй этот skill, когда нужно быть не worker'ом, а верхним диспетчером потока результатов.

## Цикл

1. **Sense:**
   `python tools/top.py conveyor --json`, `python tools/top.py process-landed --json`, `python tools/top.py status codex`, `python tools/top.py health`.

2. **Intake:**
   Для каждого landed результата начни с `python tools/top.py process-landed`. Проверь, есть ли output path. Если output не привязан, не запускай новый fan-out;
   привяжи результат через `python tools/conveyor.py land <id> --output <path>` или dismiss с причиной.

3. **Triage:**
   Классифицируй результат: `read-only-report`, `variant`, `docs-change`, `build-change`, `governance`,
   `external-code`. Build/governance не обрабатывай как обычный report.

4. **Verify:**
   Запусти `python tools/instructions.py check-report <output>`, затем релевантные проверки:
   `python tools/validate.py`, `python tools/generate.py --check`, `python tools/top.py assurance all`.
   Для build добавь `python tools/top.py work-mode codex <T-id> --parallel --hot-files` и `merge_gate.py`.

5. **Synthesize:**
   Если есть несколько outputs по теме, не закрывай их как дубли автоматически. Составь consensus,
   disagreements, evidence, recommendation. Используй `synthesis_helper.py` или отдельного conductor-agent.

6. **Decide:**
   Low-risk docs/report можно готовить к commit. Governance, accepted decisions, AGENTS/PROTOCOL, execute/network
   оставляй proposed и требуй human approval.

7. **Commit:**
   До lock подготовь список файлов и message. Во время lock делай только explicit staging + commit. Не используй
   `git add -A` в dirty shared tree. Generated files коммить только вместе с источником.

8. **Feedback:**
   После commit/ship создай новые T/Q/D для долгов, запусти `generate`, `validate`, и обнови conveyor state.

## Регулятор target

- `landed_waiting=0`, `missing_output=0`, проверки зелёные: можно поднять target на 1-2.
- Есть `PROCESS` или missing output: не запускать новых агентов, сначала обработать очередь.
- Build в shared tree: target для build = 1, параллельность только через worktree.
- Governance: target = 1 и human approval.
- Дубли без нового сигнала: не fan-out, а synthesis/compare.

## Главная ссылка

Подробная методология: `docs/top-layer-throughput-methodology.md`.