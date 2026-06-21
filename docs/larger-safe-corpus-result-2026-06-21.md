---
id: larger-safe-corpus-result-2026-06-21
title: Larger safe corpus result — T-127
status: done
related: tasks/T-127.md, tools/knowledge.py, tools/text_extract.py, tools/report_diff.py, reports/larger-safe-docs-bridge-report.md
---

# Larger safe corpus result — T-127

Дата: 2026-06-21.
Агент: Codex.

## Что проверено

В качестве безопасного большего корпуса выбран `docs/`:

- 69 Markdown-файлов;
- corpus находится внутри workspace;
- код не запускается;
- внешние/персональные источники не подтягиваются;
- runtime SQLite-БД лежит в `tmp-work/`, не в git.

Это не “идеальный пользовательский корпус”, но хороший self-hosted corpus для проверки самой системы: он содержит архитектуру, отчёты, usage, onboarding, safety и историю решений.

## Команды

```powershell
python tools\top.py knowledge docs --db tmp-work\t127-docs.db --query bridge --out reports\larger-safe-docs-bridge-report.md
python tools\top.py knowledge docs --db tmp-work\t127-docs.db --query pipeline --out reports\larger-safe-docs-pipeline-report.md
python tools\top.py report-diff reports\knowledge-corpus-report.md reports\larger-safe-docs-bridge-report.md --out reports\larger-safe-docs-bridge-vs-knowledge-corpus-diff.md
python tools\top.py report-diff reports\knowledge-corpus-report.md reports\larger-safe-docs-pipeline-report.md --out reports\larger-safe-docs-vs-knowledge-corpus-diff.md
```

## Артефакты

- `reports/larger-safe-docs-bridge-report.md`
- `reports/larger-safe-docs-pipeline-report.md`
- `reports/larger-safe-docs-bridge-vs-knowledge-corpus-diff.md`
- `reports/larger-safe-docs-vs-knowledge-corpus-diff.md`

## Результаты

Малый corpus `data/knowledge-corpus` содержит 8 документов. Большой corpus `docs/` содержит 69 документов.

Механический diff показывает:

- `documents`: 8 → 69 (`+61`);
- `shown_query_hits`: 7 → 10 (`+3`) для сравнения с top-10 выводом отчёта;
- типы: малый corpus смешанный (`md/txt/csv/json`), `docs/` сейчас полностью Markdown.

Важно: `shown_query_hits` — это не полный total по корпусу. Это число показанных результатов, потому `knowledge.py report` теперь явно пишет `показано ... (limit=10)`.

## Что система сама нашла о себе

При прогоне на 69 документах проявились два дефекта качества:

1. YAML/front-matter попадал в summary и ухудшал читаемость top-10 результатов.
2. Старый заголовок отчёта выглядел как полный hit-count, хотя фактически это top-10.

Оба дефекта исправлены:

- `tools/text_extract.py` теперь удаляет ведущий `--- ... ---` front-matter из Markdown перед нормализацией;
- `tools/knowledge.py` пишет `показано N совпадений (limit=10, ранжировано, FTS5)`;
- `tools/report_diff.py` понимает старый и новый формат заголовка отчёта;
- добавлены/обновлены тесты `tools/test_text_extract.py`, `tools/test_report_diff.py`.

## Оценка качества поиска

Плюсы:

- FTS5 на 69 документах работает быстро и воспроизводимо;
- `text_extract` после T-133 даёт поиск по телу Markdown, а не только по первой строке;
- top-10 по `bridge` и `pipeline` выдаёт ожидаемые документы: usage, onboarding, pipeline guides, result reports;
- отчёты можно сравнивать машинно через `report_diff`.

Минусы/ограничения:

- hit-count пока top-N, а не полный total;
- нет фрагментов с line number/source span;
- нет per-document freshness/source timestamp;
- corpus `docs/` не проверяет PDF/DOCX/CSV полноценно;
- отчёт не различает “исторический отчёт” и “живой current doc”, поэтому результаты смешивают current и history.

## Следующие улучшения

1. Добавить total-count режим для FTS: отдельно `total_matches`, отдельно `shown_matches`.
2. Добавить snippets/line hints для найденных документов.
3. Разделить corpus profiles: `current-docs`, `history-docs`, `reports`, `topics`.
4. Для T-137 решить DOCX/PDF: DOCX можно stdlib, PDF — только после решения о зависимости.
5. Для людей сделать GUI/web/MCP поверх `tools/top.py buttons --json`, а не поверх десятка отдельных команд.

## Вывод

T-127 подтверждает, что текущий L6 workflow уже полезен на corpus больше игрушечного. Главная польза прогона — не только новый отчёт, а обнаружение реальных дефектов в `text_extract/report/report_diff`, которые система смогла исправить и проверить сама.