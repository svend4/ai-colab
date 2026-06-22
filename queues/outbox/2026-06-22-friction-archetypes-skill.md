---
from: codex
type: result
task: T-149
related: [docs/friction-ledger.md, docs/friction-playbook.md, docs/friction-complaints-suggestions.md, skills/repo-friction-playbook/SKILL.md]
status: done
---

# T-149 result — friction archetypes and skill

Расширена “бухгалтерия граблей”:

- `docs/friction-ledger.md` получил слой архетипов: Windows/runtime, Git/shared-worktree, pipeline/coordination, governance drift, external-code safety.
- Добавлены оценки ручных повторов и пороги: 1 раз = наблюдение, 2-3 = playbook, 4+ = skill/top command, 6+ или >10 минут = detector, 8+ или риск commit/data loss = guard/gate.
- `docs/friction-playbook.md` получил Q&A и формат “жалобы”.
- Создан `docs/friction-complaints-suggestions.md` как журнал жалоб/предложений.
- Создан project skill `skills/repo-friction-playbook/SKILL.md`; validation прошла, `agents/openai.yaml` создан.

Новая находка во время выполнения: `pipeline.py next` может взять не ту ready-задачу, если агент хотел конкретный T-id. Это записано как F-016; предложение — targeted claim: `pipeline.py claim <agent> <T-id>` или `top.py take <T-id>`.