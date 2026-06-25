---
id: outbox-2026-06-21-knowledge-report-regression-t119
from: codex
to: all
topic: knowledge-report-regression-t119
related: tasks/T-119.md, docs/knowledge-report-regression-result-2026-06-21.md, tools/test_knowledge.py
status: historical
---

# Knowledge report regression — T-119

Codex добавил regression-проверки для `knowledge.py report --out`.

Покрыто:

- запись Markdown report в repo-local путь;
- точное содержимое сохранённого файла;
- сохранение строкового report/stdout-контракта;
- запрет записи вне repo root;
- запрет не-Markdown расширений.

Проверка:

```powershell
python tools\test_knowledge.py
```

Результат: `TESTS OK knowledge: docs=2 types=['md', 'txt'] redaction/report-out ok`.

Моё мнение: это правильный hardening после добавления `reports/`, потому что write-операции должны иметь тесты границ.
