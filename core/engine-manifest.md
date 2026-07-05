---
id: core-engine-manifest
type: core-export-manifest
level: L1
status: proposed
title: Переносимое ядро — file-native agent-coordination engine
files: [tools/_canon.py, tools/_ioutil.py, tools/_cli.py, tools/validate.py, tools/generate.py, tools/next_id.py, tools/commit_lock.py, tools/pipeline.py, tools/dispatch.py, tools/merge_gate.py, tools/knowledge.py]
candidates: [tools/text_extract.py]
tests: [tools/tests/test_commit_lock.py, tools/tests/test_merge_gate.py]
---

# Core engine manifest (L1) — proposed

Минимальный **переносимый** набор «движка координации агентов поверх файлов» (рекомендация Q2 из
`docs/pyramid-candidate-map.md`). Это L1: проверено тестами, не привязано к корпусу/домену, полезно
любому многоагентному file-native проекту.

- **Канон + гейт:** `_canon.py` (front-matter), `validate.py`, `generate.py`.
- **CLI/IO helper-базис:** `_ioutil.py` (UTF-8/safe_write), `_cli.py` (help_guard/die) — общий UX-слой для переносимых команд.
- **Атомарный котёл + лок + гейт:** `next_id.py`, `commit_lock.py`, `pipeline.py`, `dispatch.py`,
  `merge_gate.py`.
- **Тесты ядра:** `tests/test_commit_lock.py`, `tests/test_merge_gate.py` (тесты живут в `tools/tests/`, C14).

## Как материализовать (доказать переносимость)

```bash
python tools/promote.py export --to <target-dir> --manifest core/engine-manifest.md
```

Команда копирует (НЕ move) перечисленные файлы в `<target-dir>` с сохранением путей `tools/...` —
живой `tools/` остаётся mainline, а `<target-dir>` получает самостоятельный набор + `EXPORT.md`.

> **status: proposed.** Точный состав первого core-export — открытый вопрос пирамиды Q2; решает коллектив
> (D-018). Этот манифест — обоснованный кандидат и рабочий механизм, не финальное решение. Драйверы и
> knowledge-движок — кандидаты на ВТОРОЙ export (тянут MCP/SQLite-зависимости).
