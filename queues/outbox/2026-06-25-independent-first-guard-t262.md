---
id: 2026-06-25-independent-first-guard-t262
type: report
task: T-262
agent: codex
status: proposed
created: 2026-06-25
---

# T-262 — independent-first guard and self-critique

## Что произошло

В работе по новой политике я сначала начал сверяться с уже существующими механизмами репозитория, хотя для variant/synthesis задач порядок должен быть обратный: сначала собственный вариант агента, затем поиск, сравнение и синтез.

Это не была техническая необходимость. Это был процессный дефект: старый инженерный рефлекс “сначала изучить текущую реализацию, чтобы не дублировать” оказался сильнее нового правила independent-first. Для обычного bugfix такой рефлекс полезен. Для методологических, архитектурных и форк-синтез задач он вреден, потому что преждевременно якорит ответ и уменьшает разнообразие вариантов.

## Исправленный порядок

1. Классифицировать задачу: если это концепт, методология, архитектура, политика или спорный формат, включить independent-first.
2. Создать личный stream-пакет до поиска по репозиторию.
3. Заполнить собственные секции 01-03: применимость, независимый ответ, потенциал до синтеза.
4. Явно записать алгоритм и псевдокод.
5. Проверить stream командой `python tools\independent_first.py check <stream> --json`.
6. Только после `ready_for_repo_search: true` выполнять repo-search/comparison.
7. После сравнения выносить consensus и divergence в synthesis/adoption, а не заменять один вариант другим.

## Что добавлено

- `tools/independent_first.py` — guard перед repo-search/comparison.
- `tools/test_independent_first.py` — тесты template-fails/full-passes/id-lookup/path-safety.
- `tools/top.py variant-start` теперь печатает `independent_first.py check` как next command до `repo-search`.
- `tools/test_top.py` проверяет наличие этой команды в `variant-start` output.
- `tools/capabilities.py`, `tools/README.md`, `docs/independent-variant-stream-policy.md`, `docs/top-layer-command-groups.md` обновлены описанием команды.
- Stream evidence: `streams/independent-first-process-guard/20260625-2142-codex/STREAM.md`.

## Проверки

```powershell
python -m py_compile tools\top.py tools\test_top.py tools\independent_first.py tools\test_independent_first.py tools\capabilities.py
python tools\test_independent_first.py
python tools\test_top.py
python tools\independent_first.py check streams\independent-first-process-guard\20260625-2142-codex\STREAM.md --json
```

Все четыре проверки прошли.

## Вывод для других агентов

Не достаточно написать правило в документации. Если правило должно менять поведение агента, оно должно появиться в верхнем рабочем цикле как команда, проверка или блокирующий gate. T-262 делает первую такую проверку для independent-first политики.

## Applied instructions

- AGENTS.md: outbox report preserved; no чужие сообщения удалялись.
- PROTOCOL.md: report kept as proposed/done evidence; no accepted decision is created here.
- docs/protocol-machine-layer.md: added explicit machine-readable evidence footer for check-report.

Checks:
- python tools\validate.py -> OK
- python tools\generate.py --check -> OK
- python tools\instructions.py check-report <this-file> -> OK after footer normalization
