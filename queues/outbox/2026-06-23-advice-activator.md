# Advice activator — советы, которые не должны лежать мёртвым текстом

Дата: 2026-06-23
Агент: codex
Тип: outbox-report

## Проблема

В проекте уже есть хорошие инструкции и инструменты, но часть из них используется только если агент сам вспомнил нужную команду. Пример: Level 1 worktree уже был описан и реализован, но фактически агент мог продолжить работу в общем дереве.

## Что сделано

Добавлен read-only активатор советов:

```powershell
python tools\advice.py current <agent> [T-id] [--parallel] [--hot-files]
python tools\top.py advice <agent> [T-id] [--parallel] [--hot-files]
```

Он связывает текущие симптомы с уже существующими советами:

- `friction.py status` -> F-id рецепты и команды `friction.py recipe F-XXX`;
- parallel/hot/dirty -> `top.py work-mode ... --parallel --hot-files --dirty-mainline`;
- `assurance.py all` findings -> `top.py assurance all`, applied-evidence и будущие strict-gate кандидаты;
- placeholder tasks -> `pipeline.py status` и рецепт `F-009`.

## Что найдено и применено

Первый запуск показал stale generated indexes. После этого был запущен:

```powershell
python tools\generate.py
```

Он обновил `DECISIONS.md` и `index.json`; повторный `generate.py --check` стал зелёным.

Также `advice` поднял assurance-currency warnings по `D-019`. Перепроверка показала, что это были исторические/related ссылки на superseded proposal, а не живые нормативные ссылки. Поэтому `tools/assurance.py` доработан: он больше не считает `Связано:`/`related`/исторические ссылки drift, но продолжает ловить живые нормативные ссылки на rejected/superseded решения.

## Текущий результат

Проверки:

```text
python tools\test_advice.py       -> OK
python tools\test_assurance.py    -> OK
python tools\test_top.py          -> OK
python tools\validate.py          -> OK=10 WARN=0 ERROR=0
python tools\generate.py --check  -> OK
python tools\drift_check.py       -> OK: дрейфа не обнаружено
python tools\top.py health        -> hard checks OK; assurance ATTENTION только по T-180 weak evidence
```

## Оставшийся актуальный сигнал

`tools\top.py advice codex T-188 --parallel --hot-files` сейчас показывает:

- A-001: запускать instruction-preflight;
- A-002: применять friction recipes;
- A-003: выбирать work-mode, для текущей параллельной/hot ситуации — Level 1 worktree;
- A-005: не давать placeholder tasks входить в нормальное исполнение;
- A-006: закрыть assurance evidence finding по T-180.

## Правило на будущее

Совет считается живым только если у него есть:

1. источник (`docs/...`, `decisions/...`, `tools/...`),
2. текущий симптом, который его активирует,
3. команда, которую агент или человек может запустить,
4. evidence в outbox/done отчёте.

Если совет повторяется дважды — он должен попасть в `friction.py` или `advice.py`. Если совет блокирует безопасный commit — он должен стать частью `merge_gate`, `assurance --strict` или pre-commit.