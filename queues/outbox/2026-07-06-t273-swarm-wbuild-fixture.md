---
id: 2026-07-06-t273-swarm-wbuild-fixture
type: outbox
status: proposed
date: 2026-07-06
author: codex
related:
  - T-273
  - PKG-20260706-pilot-t273
  - reports/T-273-l2-inventory-wbuild-fixture-2026-07-06.md
---

# T-273 swarm update — W_build fixture ready

Codex запустил/использовал рой для пилота T-273:

- Newton проверил safety-boundary и нашёл gaps: `--db` внутри `--source`, symlink/reparse-point, неполные тесты.
- Copernicus проверил тест и обнаружил `NameError` в `stats()`.
- Halley дал стратегический refill: следующий шаг должен быть `W_run -> W_verify x2 -> W_report`, а верхний агент в это время ведёт intake/verify/refill.

Что применено:

- `tools/l2_inventory.py` теперь запрещает `--db` внутри `--source` и пропускает symlink/reparse-point элементы.
- `tools/tests/test_l2_inventory.py` использует project-local `tmp-work/` и проверяет отказ `db inside source`.

Проверки:

```powershell
python -m py_compile tools\l2_inventory.py tools\tests\test_l2_inventory.py
python tools\tests\test_l2_inventory.py
python tools\l2_inventory.py build --source drivers\file-inventory --db tmp-work\t273\fixture-l2-inventory.db --max-text-bytes 204800 --json
python tools\l2_inventory.py stats --db tmp-work\t273\fixture-l2-inventory.db --json
python tools\l2_inventory.py query --db tmp-work\t273\fixture-l2-inventory.db inventory --limit 5 --json
```

Результат: OK. `pytest` в этом окружении отсутствует (`No module named pytest`), поэтому надёжная проверка сейчас — standalone test.

Следующий шаг: выбрать/подтвердить источник для bounded read-only `W_run`; затем два независимых verifier и scribe.

## Bounded gate update

Socrates found that real `W_run` was still NO-GO while `--max-files` was incomplete. Codex completed it:

- CLI accepts `--max-files`.
- `build/stats` report bounded-run metadata (`max_files`, `limit_hit`, `read_errors`, skipped counters).
- Standalone test passes.
- Bounded fixture build with `--max-files 2` passes and reports `limit_hit: true`.

Next real W_run is allowed only with explicit source, DB under `tmp-work/t273/`, and bounded `--max-files`.