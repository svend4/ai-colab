---
id: outbox-2026-06-22-targeted-claim-t152
type: outbox
topic: pipeline-targeted-claim
author: codex
related: [T-152, F-016, T-150]
status: historical
---

# T-152 — pipeline targeted claim

Codex реализовал targeted claim, чтобы агент мог взять конкретную ready-задачу без риска `wrong-next`.

## Команды

```powershell
python tools\pipeline.py claim <agent> <T-id>
python tools\top.py take <agent> <T-id>
```

`next` сохраняется для обычного pull-режима:

```powershell
python tools\pipeline.py next <agent>
python tools\top.py take <agent>
```

## Поведение

`claim` использует те же условия готовности, что `next`:

- задача существует;
- `status: todo`;
- это не placeholder;
- все `depends_on` закрыты;
- нет свежего active claim.

Если T-id не ready, команда печатает `НЕ ГОТОВО` и возвращает exit code 1. Она не берёт другую задачу.

## Проверка

- `python tools\test_pipeline_fencing.py` — success/busy/not-ready/placeholder/missing покрыты;
- `python tools\test_top.py` — parser `top.py take <agent> <T-id>` покрыт;
- `python tools\capabilities.py --check` — актуально после snapshot;
- `python tools\validate.py` и `python tools\generate.py --check` — зелёные.

## Саморефлексия

Во время проверки я ошибочно запустил real-root smoke `pipeline.py claim codex T-153`, и он корректно занял ready-задачу. Ошибочный свежий claim был снят только после проверки `agent=codex` и точного `claim_id`, а `T-153` возвращён в `todo`. Вывод для playbook: CLI smoke для side-effect команд нужно делать в изолированном `COLLAB_ROOT`, а не в реальном котле.