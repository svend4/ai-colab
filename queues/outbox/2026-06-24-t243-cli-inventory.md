---
type: report
id: 2026-06-24-t243-cli-inventory
status: historical
agent: codex
task: T-243
related: [cli-help-guard-convention-2026-06-24, kotel-system-critique-2026-06-24]
---

# T-243 — CLI inventory report

## Что сделано

Добавлен read-only инструмент `tools/cli_inventory.py` и тест `tools/test_cli_inventory.py`.

Инструмент не импортирует и не исполняет сканируемые `tools/*.py`. Он читает исходники как текст и классифицирует CLI-поведение по признакам:

- `ok-argparse` — используется `argparse`;
- `ok-help-guard` — используется `_cli.help_guard()`;
- `manual-help` — есть ручная обработка `--help`, но не через общий helper;
- `unsafe-sysargv` — есть `sys.argv`, но нет видимого `argparse`/`help_guard`/ручного help;
- `entrypoint-no-argv` — есть entrypoint, но не виден контракт argv/help;
- `library-or-helper` — не CLI-кандидат.

## Проверенный снимок 2026-06-24

Команда:

```powershell
python tools\cli_inventory.py --status unsafe-sysargv --status manual-help --status entrypoint-no-argv --limit 80
```

Результат:

```text
files: 76
cli_candidates: 71
risky: 45
ok-argparse: 12
ok-help-guard: 14
manual-help: 2
unsafe-sysargv: 41
entrypoint-no-argv: 2
library-or-helper: 5
```

Первые явные кандидаты на следующие батчи:

- `manual-help`: `tools/dir_health.py`, `tools/sandbox_intake_demo.py`.
- `unsafe-sysargv`: `tools/assurance.py`, `tools/capabilities.py`, `tools/cohort.py`, `tools/commit_lock.py`, `tools/decision_propagation.py`, `tools/demo_bridge.py`, `tools/doc_consensus.py`, `tools/drivers_catalog.py`, `tools/execute_audit.py`, `tools/execute_human_gate.py`, `tools/execute_preflight.py`, `tools/flow.py`, `tools/folder_index.py`, `tools/generate.py`, `tools/header.py`, `tools/heading_check.py`, `tools/knowledge.py`, `tools/layer_check.py`, `tools/merge_gate.py`, `tools/metrics.py`, `tools/next_id.py`, `tools/onboard.py`, `tools/permissions.py`, `tools/pipeline.py`, `tools/portability_check.py`, `tools/portal.py`, `tools/promote.py`, `tools/race_test.py`, `tools/repo_search.py`, `tools/report_diff.py`, `tools/result_intake.py`, `tools/risk_gate.py`, `tools/sandbox.py`, `tools/sandbox_runner.py`, `tools/stream.py`, `tools/synthesis_helper.py`, `tools/text_extract.py`, `tools/two_track.py`, `tools/validate.py`, `tools/variants.py`, `tools/worktree.py`.
- `entrypoint-no-argv`: `tools/bulk_dcard_generator.py`, `tools/drift_check.py`.

## Вывод для котла

`docs/cli-help-guard-convention-2026-06-24.md` дал хорошую текстовую конвенцию. T-243 переводит её в машинную проверку: теперь верхний слой может не вспоминать вручную, где риск, а запускать инвентарь и брать следующий батч.

Моё предложение: не делать массовую правку 45 файлов одним коммитом. Лучше закрывать очередями:

1. Сначала `manual-help` и маленькие read-only/report tools.
2. Затем сервисные инструменты без активных пересечений.
3. Потом горячие инструменты `pipeline.py`, `generate.py`, `validate.py`, `next_id.py` только отдельными задачами и тестами.
4. После каждого батча запускать `tools/cli_inventory.py` и смотреть уменьшение `risky`.

## Проверки

```text
python tools\test_cli_inventory.py -> OK
python tools\cli_inventory.py --help -> OK
python tools\cli_inventory.py --json -> JSON parsed, schema cli_inventory.v1, files 76, risky 45
```