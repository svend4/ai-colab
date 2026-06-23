# Repo-inventory — текущее состояние

- **Дизайн:** `tasks/T-024.md` (read-only repo inventory); кандидат в `docs/pyramid-candidate-map.md`.
- **Ядро (L1):** `tools/knowledge.py` + драйверы `repo-runner` (`drivers/repo-runner.md`, read-only) и
  `git-log` (`drivers/git-log.md`, ready).
- **Корпус:** `data/portals/repo-inventory/corpus/` — сидится из `drivers/repo-runner/fixture-report.json`
  и `drivers/file-inventory/fixture-report.json` + git-log summary; внешних данных не нужно.
- **Статус:** L2-манифест объявлен; наполнение корпуса — операционный шаг (`tools/portal.py` build),
  не требует execute-драйверов.
