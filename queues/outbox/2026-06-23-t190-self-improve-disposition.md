# T-190 — self-improve disposition

Дата: 2026-06-23
Агент: codex
Claim: `a879d8faae8d`
Тип: outbox-report

## Контекст

T-190 содержала 4 отложенных self-improve пункта: `risk_gate.py`/D-006 wire, D-020 supersede, `sandbox_intake_demo.py` manual-doc, `race_test.py` rename.

Цель прохода — не внедрить governance без человека, а разобрать каждый пункт: applied или closed/deferred с явным основанием.

## Диспозиция

| Пункт | Решение | Причина |
|---|---|---|
| 1. `risk_gate.py` -> wire D-006 | deferred/governance | `risk_gate.py` является advisory tool; принудительное включение в `validate.py` изменит governance semantics и требует котёл/D-006/D-018. Агент не утверждает это соло. |
| 2. `D-020` -> supersede | deferred/governance | `D-020` уже содержит postscript, что D-021 стал accepted decision of record. Перевод `proposed -> superseded` остаётся governance-review для Stefan/интегратора. |
| 3. `sandbox_intake_demo.py` -> keep-manual-documented | applied | В `tools/top.py` у кнопки `sandbox-demo` добавлены machine-readable поля `status: manual-demo` и `adoption: keep-manual...`. Это делает demo намеренно ручным, не dead code. Документация `docs/top-layer-command-groups.md` уточнена. |
| 4. `race_test.py` -> rename `test_race_test.py` | closed-wontfix now | `python tools\race_test.py 8 1` не вернулся за ~70 секунд; пришлось остановить только свежие PID теста. Переименование в `test_*.py` сейчас внесло бы зависание в быстрый test-suite. Оставить как manual stress-test. |

## Проверки

```text
python tools\test_top.py                 -> OK
python tools\test_sandbox_intake_demo.py -> OK
python tools\risk_gate.py T-190          -> risk=low, status=doing at check time
python tools\top.py buttons --json       -> sandbox-demo содержит status/adoption
python tools\race_test.py 8 1            -> hung; stopped fresh race_test/queue python processes only
```

## Вывод

T-190 закрывается как disposition, а не как полный governance-merge. Это правильнее технически: применён только low-risk metadata/doc пункт, а governance-пункты оставлены человеку/котлу. `race_test.py` доказал, что его нельзя поднимать в auto-discovered test без отдельной hardening-задачи.

## Следующие возможные задачи

- Создать отдельную governance-задачу: `D-020 proposed -> superseded?` с явным human approval.
- Создать отдельную hardening-задачу для `race_test.py`: timeout, no-hang wrapper, bounded subprocess cleanup, затем решать вопрос `test_` rename.
- Создать отдельную advisory-задачу: стоит ли `risk_gate.py` подключать в `top.py advice`/`assurance`, а не в `validate.py` напрямую.