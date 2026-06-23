# Agent-start advice integration — activation of existing recommendations

Дата: 2026-06-23
Агент: codex
Статус: implemented, checked

## Что изменено

`tools/top.py agent-start` теперь принимает `--task T-id` и автоматически запускает advisory `tools/advice.py current <agent> [T-id]` после onboarding/status/assurance.

Это также отражено в:

- `tools/test_top.py`
- `tools/capabilities.py`
- `system-capabilities.json`
- `tools/README.md`
- `docs/agent-onboarding.md`
- `docs/top-layer-command-groups.md`

## Почему именно так

В репозитории уже накоплено много хороших рекомендаций: friction recipes, work-mode, instruction preflight, assurance. Проблема была не в отсутствии советов, а в том, что агент мог начать работу, не активировав эти советы.

Новый порядок делает совет видимым на верхнем слое:

1. agent-start показывает состояние проекта.
2. assurance показывает проверяемость инструкций.
3. advice связывает текущие симптомы с уже существующими командами.
4. только после этого агент берёт задачу или делает правки.

Так уменьшается риск повторять уже решённые проблемы: dirty shared tree, placeholder tasks, слабое applied evidence, забытый worktree/work-mode, забытый friction recipe.

## Что не делалось

- Не трогал T-193: задача занята `antigravity`.
- Не заполнял T-184/T-185/T-194: это placeholders; T-184/T-185 зарезервированы за Novax, T-194 отмечен в `dialog.md` как placeholder-кандидат на cleanup/архивирование.
- Не переписывал `queues/done/T-180.done.md` и `queues/done/T-182.done.md`: это чужие done-маркеры. Assurance-долг нужно закрывать отдельным addendum/cleanup-процессом, а не молчаливой правкой истории.

## Текущие остаточные долги

`python tools/assurance.py all` всё ещё показывает:

- T-180: слабое evidence, нет `AGENTS.md`, `PROTOCOL.md`; дополнительно `instructions.py check-report` видит устаревшую ссылку `engine-manifest.md`.
- T-182: слабое evidence, нет `AGENTS.md`, `PROTOCOL.md`.

Рекомендация: сделать отдельный малый механизм evidence-addendum, например `queues/evidence/<T-id>.evidence.md`, и научить `assurance.py` учитывать такие addendum без изменения исходного done-маркера.

## Проверки

```powershell
python tools\test_top.py
python tools\test_advice.py
python tools\top.py cycle codex
python tools\top.py agent-start codex --task T-180
python tools\capabilities.py snapshot
python tools\validate.py
python tools\generate.py --check
python tools\capabilities.py --check
python tools\drift_check.py
python tools\assurance.py all
```

Результат:

- `test_top.py` OK
- `test_advice.py` OK
- `validate.py` OK=10 WARN=0 ERROR=0
- `generate.py --check` OK
- `capabilities.py --check` OK
- `drift_check.py` OK
- `top.py agent-start codex --task T-180` OK; advice activator printed A-001/A-002/A-003/A-005/A-006 before any claim
- `assurance.py all` ATTENTION только по T-180/T-182 evidence debt

Applied instructions: AGENTS.md, PROTOCOL.md, docs/friction-retrospective-2026-06-22.md, docs/instruction-assurance.md, docs/top-layer-command-groups.md
Checks: test_top.py, test_advice.py, validate.py, generate.py --check, capabilities.py --check, drift_check.py, assurance.py all