---
status: historical
---
﻿# T-124 — quickstart pipeline cleanup

Завершён cleanup входных инструкций после перехода на `pipeline.py` как основной task engine.

Изменено:

- `docs/quickstart.md`;
- `docs/agent-quickstart.md`;
- `docs/pipeline-operator-guide.md`;
- `PROTOCOL.md`;
- `tools/test_drift_check.py`.

Что исправлено:

- входные инструкции больше не предлагают `queue.py claim/list` как актуальный способ взять задачу;
- основной цикл теперь: `pipeline.py status -> next -> work -> done --claim -> generate/validate/snapshot`;
- `queues/inbox/outbox` описаны как файловый форум, а не как основной claim-механизм;
- `git add -A` во входных инструкциях заменён на `commit_lock.py` + selective-add;
- `tools/test_drift_check.py` исправлен для Windows: тест использует реально writable root вместо проблемного `tempfile` в `tmp-work`.

Проверки:

- `python tools/test_drift_check.py` — OK;
- `python tools/test_onboard.py` — OK;
- `python tools/validate.py` — OK=9 WARN=0 ERROR=0;
- `python tools/drift_check.py` больше не показывает legacy `queue.py` во входных инструкциях.

Оставшийся drift не относится к T-124: L0-L8 в отдельных docs и orphan `T-020`.
