---
status: historical
---
# T-127 — larger safe corpus report

Дата: 2026-06-21.
Агент: Codex.
Связано: `T-127`, `docs/larger-safe-corpus-result-2026-06-21.md`, `reports/larger-safe-docs-bridge-report.md`, `tools/report_diff.py`.

## Что сделано

- В качестве безопасного corpus выбран `docs/` — 69 Markdown-файлов внутри workspace.
- Через `tools/top.py knowledge` созданы два knowledge-отчёта: `bridge` и `pipeline`.
- Добавлен `tools/report_diff.py` и кнопка `top.py report-diff` для сравнения отчётов.
- Созданы diff-отчёты против `reports/knowledge-corpus-report.md`.
- На реальном прогоне исправлены два дефекта: front-matter в summaries и неясный hit-count в `knowledge.py report`.

## Проверка

```powershell
python tools\test_text_extract.py
python tools\test_knowledge.py
python tools\test_report_diff.py
python tools\test_top.py
python tools\top.py health
```

## Вывод

L6 workflow уже применим к corpus 50-200 файлов. Следующий качественный шаг — total hit count, snippets/line hints и разделение current/history corpus profiles.