---
id: fleet-designs-2026-06-23
type: topic
title: Дизайны флота (2026-06-23) — reconcile_state fix + наполнение L2-порталов
status: proposed
date: 2026-06-23
related: [perspective-backlog-2026-06-23, pyramid-grounding-plan-2026-06-23, Q-016, D-016]
---

# Дизайны флота (2026-06-23)

Результаты двух нод параллельного флота воркфлоу (по перспективному бэклогу). Оба — **готовые
buildable-дизайны** (proposed); реализация — отдельным ship'ом в build-окно.

## 1. `reconcile_state.py fix` — небилд закрыт дизайном

> **SHIPPED 2026-06-23 (commit `94c3c35`).** Дизайн ниже реализован: `cmd_fix(apply=False)` живёт в `tools/reconcile_state.py:259` (диспетчер `:295`), dry-run по умолчанию + обязательный `--apply`, derived-only, PRIMARY-refuse, exit через `exit_code(report)`. Раздел сохранён как историческая спека.

Изначально `tools/reconcile_state.py` содержал заглушку («fix не реализован на этапе 1»). Дизайн (теперь реализованный):

- **Dry-run по умолчанию; `--apply` обязателен для записи.** Без `--apply` — печатает «would regenerate: …»,
  не пишет ничего, exit-код из остаточного дрейфа.
- **Строиться ПОВЕРХ `reconcile()` (:154), не рядом.** Ключевать по `items[].code`; разделить на:
  - **DERIVED (авто-чинимые):** `index-status-drift` (:126), `pipeline-snapshot-drift` (:148);
  - **PRIMARY (никогда не авто-чинить):** маркеры/claim'ы (`marker-but-not-done`, `done-missing-marker`,
    `doing-no-claim`, `orphan-*`, `placeholder-todo`). При наличии PRIMARY-дрейфа — **отказ** с печатью
    как action-items человеку/агенту.
- **Писать ТОЛЬКО 4 производных:** `index.json`, `TASKS.md` (через `generate.build_index`), `PIPELINE.md`,
  `logs/pipeline.json` (через `pipeline.cmd_snapshot` — тот же `build_pipeline_state()`, что и `check_pipeline`,
  значит снимок гарантированно консистентен). НЕ трогать `tasks/*.md`, очереди, `DECISIONS.md`, `темы/`.
- **Идемпотентность** из детерминированной регенерации (опц. пропуск байт-идентичной записи). Exit —
  через `exit_code(report)` (:223), не зашитый `return 0`: остаточный PRIMARY-дрейф всё ещё сигналит non-zero.
- **Scope v1:** только `index.json` + pipeline-пара (report пока не покрывает TASKS.md/PIPELINE.md/failed-маркеры).
- **Риски:** over-broad авто-фикс (гейтить derived-коды строго к тем, что report эмитит); CRLF-дрейф на
  Windows (писать utf-8 + `newline="\n"`); default-apply footgun (запись строго opt-in).

Файлы: `tools/reconcile_state.py` (+ импорт `generate`/`pipeline`), `docs/state-reconciliation-layer.md`.

## 2. Наполнение L2-порталов — 2 реальных портала

> **SHIPPED 2026-06-23 (`144bb7b`).** Оба портала построены: `portals/bridge-knowledge/` + `portals/repo-inventory/` существуют, assurance coverage → **порталов: 3** (был 1). Дизайн ниже сохранён как историческая спека.

Корень orphan-L1 (assurance.py: порталов было 1) — существовал **только** `portals/example`. Построено (теперь порталов 3):

- **`bridge-knowledge` (effort S):** обернуть **уже существующий** корпус `data/knowledge-corpus/` (8 файлов;
  готовый отчёт `reports/knowledge-corpus-report.md`). Нулевые новые данные, чистое переиспользование
  `knowledge.py` через `portal.py` (build :119, report+FTS :126) — доказывает, что L2 обобщается за пределы
  2-файлового demo.
- **`repo-inventory` (effort M):** единственный кандидат с готовым дизайном (`tasks/T-024.md`) и записью в
  `docs/pyramid-candidate-map.md:47`; уникально переиспользует **два ready read-only драйвера** — `repo-runner`
  и `git-log` — поверх `knowledge.py`. Сидится из `drivers/*/fixture-report.json`, внешних данных не нужно.
- (опц. `app-data`, M — задействует read-only `sqlite`-драйвер, которого нет у example.)

**Честно про orphan-L1:** новые data-порталы счётчик 12 механически **не уронят** — 12 сирот это
координационные примитивы ядра (`commit_lock.py`, `merge_gate.py` из manifest `files:`), и data-корпус их
законно не цитирует; `assurance.py:251-253` credits покрытие только при буквальном совпадении basename.
Закрывать orphan-L1 надо **отдельной doc/manifest-перекрёстной ссылкой** (или сужением manifest `files:` —
см. `pyramid-grounding-plan-2026-06-23.md`), а не принуждением порталов цитировать примитивы ядра.
Порталы подняли счётчик `порталов:1→3` (SHIPPED `144bb7b`) и доказали переиспользование драйверов сверх `files`.
