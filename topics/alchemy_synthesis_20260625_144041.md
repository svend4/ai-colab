---
id: alchemy-synthesis-20260625-144041
type: topic
title: Алхимический синтез - спираль бабочки
status: proposed
date: 2026-06-25
author: synthesis-script
related:
  - cauldron-synthesis
  - commit-queue-and-synthesis-2026-06-26
---

# Алхимический Синтез (Спираль Бабочки)

**Дата генерации:** 2026-06-25 14:40:41.695715
**Источник данных:** `cauldron_graph.json`

## Исходные Атомы (Сырье)
1. Источник: `2026-06-21-core-export-acceptance-result.md`
   > Проверки зелёные: `test_promote_export`, `test_promote`, smoke export в `tmp-work/core-export-smoke`, `top.py health`.

2. Источник: `2026-06-21-ingest-acceptance-result.md`
   > Implementation note: `drivers/workbench/test_ingest.py` and `drivers/workbench/test_search.py` now use `drivers/test_tmp.py`, consistent with the temp workaround introduced during files/workbench acceptance.

3. Источник: `2026-06-24-t237-sandbox-link-checker.md`
   > - scans `.md` files recursively;
- resolves relative links from the source file directory;
- resolves root-style links from the sandbox root;
- ignores common external schemes and same-document anchors;
- strips local anchors before file existence checks;
- reports relative source path, line number, link text, target, and issue kind;
- reports `outside-root` for links that escape the isolated scan root;
- returns exit code `0` for clean scans, `1` for link issues, and `2` for bad input.

## Задача для LLM
Синтезировать эти 3 переменные в единый концепт или функцию. Как они связаны? Какую новую идею они рождают?
