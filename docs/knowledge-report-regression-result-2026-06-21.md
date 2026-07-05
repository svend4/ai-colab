---
id: knowledge-report-regression-result-2026-06-21
title: Knowledge report regression — T-119
status: done
owner: Codex
related: tasks/T-119.md, tools/tests/test_knowledge.py, tools/knowledge.py
---

# Knowledge report regression — T-119

Дата: 2026-06-21.

## Что сделано

`tools/tests/test_knowledge.py` расширен проверками для `tools/knowledge.py report --out` и `write_report()`.

Новые проверки:

- Markdown report можно записать в repo-local путь;
- сохранённый файл равен `report + "\n"`;
- строковый report остаётся обычной строкой, то есть stdout-контракт не меняется;
- путь вне repo root запрещён;
- не-Markdown расширение запрещено.

## Команда

```powershell
python tools\test_knowledge.py
```

Результат:

```text
TESTS OK knowledge: docs=2 types=['md', 'txt'] redaction/report-out ok
```

## Мнение Codex

Это закрывает маленький, но важный риск: после появления `reports/` у инструмента появилась write-операция. Теперь у неё есть regression-тест на полезное поведение и на границы безопасности.
