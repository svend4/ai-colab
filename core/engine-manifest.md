---
id: core-engine-manifest
type: core-export-manifest
level: L1
status: proposed
title: Переносимое ядро — file-native agent-coordination engine
files: [tools/_canon.py, tools/validate.py, tools/generate.py, tools/next_id.py, tools/commit_lock.py, tools/pipeline.py, tools/dispatch.py, tools/merge_gate.py, tools/test_commit_lock.py, tools/test_merge_gate.py]
---

# Core engine manifest (L1) — proposed

Минимальный **переносимый** набор «движка координации агентов поверх файлов» (рекомендация Q2 из
`docs/pyramid-candidate-map.md`). Это L1: проверено тестами, не привязано к корпусу/домену, полезно
любому многоагентному file-native проекту.

- **Канон + гейт:** `_canon.py` (front-matter), `validate.py`, `generate.py`.
- **Атомарный котёл + лок + гейт:** `next_id.py`, `commit_lock.py`, `pipeline.py`, `dispatch.py`,
  `merge_gate.py`.
- **Тесты ядра:** `test_commit_lock.py`, `test_merge_gate.py`.

## Как материализовать (доказать переносимость)

```bash
python tools/promote.py export --to <target-dir> --manifest core/engine-manifest.md
```

Команда копирует (НЕ move) перечисленные файлы в `<target-dir>` с сохранением путей `tools/...` —
живой `tools/` остаётся mainline, а `<target-dir>` получает самостоятельный набор + `EXPORT.md`.

> **status: proposed.** Точный состав первого core-export — открытый вопрос пирамиды Q2; решает коллектив
> (D-018). Этот манифест — обоснованный кандидат и рабочий механизм, не финальное решение. Драйверы и
> knowledge-движок — кандидаты на ВТОРОЙ export (тянут MCP/SQLite-зависимости).
