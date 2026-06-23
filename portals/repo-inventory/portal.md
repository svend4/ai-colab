---
id: portal-repo-inventory-l2
type: portal
level: L2
title: Repo-inventory (L2 — инвентарь репо + git-история)
description: L2-портал поверх ядра (D-016, T-024) над read-only инвентарём репозитория и git-историей. Уникально переиспользует драйверы repo-runner + git-log СВЕРХ files — доказывает обобщение ядра на другие драйверы.
l1_basis: [tools/knowledge.py, tools/text_extract.py]
corpus_ref: data/portals/repo-inventory/corpus
topics: [inventory, git-history, structure]
links:
  current_state: current-state.md
  sources: sources.md
---

# Портал: repo-inventory (L2)

**Чистовая** L2-область над read-only инвентарём репозитория и его git-историей. Дизайн — `tasks/T-024.md`,
запись в карте кандидатов — `docs/pyramid-candidate-map.md`. Уникальность: помимо ядра
`tools/knowledge.py`, портал опирается на **два ready read-only драйвера** — `repo-runner` (скан репо) и
`git-log` (summary истории) — то есть доказывает переиспользование ядра не только через `files`, как
`portals/example`/`bridge-knowledge`.

- **Идентичность/настройки** — этот файл.
- **Текущее состояние** — `current-state.md`.
- **Источники** — `sources.md`.
- **Корпус (данные)** — `data/portals/repo-inventory/corpus/` (сидится из `drivers/repo-runner/fixture-report.json`
  + `drivers/file-inventory/fixture-report.json` + `git-log` summary; внешних данных не требует).

> Read-only: драйверы `repo-runner`/`git-log` — `mode: read-only`; execute-гейт закрыт (D-013, driver-safety).
