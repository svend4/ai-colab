# Project skills (L3)

Переносимые повторяемые процедуры команды AI-OS Bridge как `SKILL.md` (формат skill-папки:
front-matter `name`/`description` + инструкция). Извлечены из рабочей практики, чтобы агент
мог применить процедуру по описанию, не перечитывая всю историю.

| Skill | Когда применять |
|---|---|
| [`driver-acceptance`](driver-acceptance/SKILL.md) | добавлен/изменён драйвер → довести до `ready` (unit + sync MCP-приёмка + манифест + D-015) |
| [`pipeline-operator`](pipeline-operator/SKILL.md) | выполнение задач из пула: атомарно взять/закрыть, heartbeat, не ломая канон |
| [`repo-review`](repo-review/SKILL.md) | перепроверка/ревью репозитория: валидаторы, дрейф, плюсы/минусы, рекомендации |
| [`repo-friction-playbook`](repo-friction-playbook/SKILL.md) | повторяющееся трение разработки: Windows/runtime/git/pipeline/generated-index/streams проблемы → найти F-ID, применить playbook, обновить бухгалтерию |

Это L3 «project skills» из roadmap `docs/layers-coverage.md`. Каноническая нумерация слоёв —
там же. Связано: `docs/bridge-usage.md`, `decisions/D-015.md`.

Использование и переносимость описаны в `docs/skills-usage.md`. Важно: это project-local L3
skills, а не L5 plugin/marketplace package; автоматическая загрузка зависит от конкретной среды.
