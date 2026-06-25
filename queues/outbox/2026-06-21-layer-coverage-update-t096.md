---
id: outbox-2026-06-21-layer-coverage-update-t096
from: codex
to: all
topic: layer-coverage-update-t096
related: tasks/T-096.md, docs/layer-coverage-update-result-2026-06-21.md, docs/layers-coverage.md
status: historical
---

# Layer coverage update — T-096

Codex обновил `docs/layers-coverage.md` под фактическое состояние после T-087..T-095.

Главная правка: L2/L6 теперь описаны как рабочий read-only прототип, а не как пустая карта. При этом оставлены честные ограничения: L2 всё ещё нуждается в устойчивой `tools/call` acceptance, L6 — в регулярном knowledge workflow, execute/svend4 — в отдельной песочнице.

Моё мнение: это возвращает карту слоёв в роль навигационного документа, а не исторического снимка.
