---
id: outbox-2026-06-25-variant-start-order-policy
status: final
author: codex
related: [T-258, T-254, D-017, D-028, variant-start-order-policy, top.py]
created: 2026-06-25
---

# Outbox - T-258 variant-start order policy

## Короткий итог

T-258 исправляет методологический сбой в верхнем слое: `variant-start` больше не должен по умолчанию выполнять `repo-search` до того, как агент записал самостоятельный вариант. Актуальный порядок для strict independent-first задач:

```text
stream create -> independent draft -> repo-search/compare -> ready-for-synthesis
```

Старый T-254-порядок `repo-search -> stream create` оставлен как исторический вариант, но в live-документации помечен как уточнённый через T-258. Если ранний поиск нужен осознанно, теперь используется явный флаг `--search-now`.

## Что было сделано

- Создана задача `tasks/T-258.md`.
- До чтения `tools/top.py` создан independent stream Codex: `streams/variant-start-order-policy/20260625-1839-codex/STREAM.md`.
- Подключены sub-agents:
  - Turing: read-only аудит документации и расхождений T-254/T-258.
  - Hegel: read-only code review для `tools/top.py` / `tools/test_top.py`.
  - Galileo: отдельный worker stream `streams/variant-start-order-policy/20260625-subagent-worker/STREAM.md`.
- `tools/top.py` изменён:
  - stream создаётся до любых веток поиска;
  - default repo-search теперь deferred;
  - `--search-now` запускает поиск только явно и уже после stream-create;
  - `--no-search` и `--search-now` стали mutually exclusive;
  - non-json output печатает `status: deferred`, `status: skipped` или `status: executed`.
- `tools/test_top.py` обновлён:
  - проверяет parser для `--search-now`;
  - проверяет конфликт `--no-search` + `--search-now`;
  - проверяет default-deferred JSON и non-JSON smoke;
  - проверяет `--no-search` без добавления реальной repo-search команды.
- Обновлены живые инструкции:
  - `docs/top-layer-command-groups.md`;
  - `docs/independent-variant-stream-policy.md`;
  - `tools/README.md`;
  - `tools/capabilities.py`.

## Consensus

- Содержательный вариант нельзя закрывать как дубль по названию темы.
- Для independent-first задач stream должен появляться раньше сравнения.
- Repo-search полезен, но только как second-phase context после первичного independent draft.
- Старый T-254 полезен как идея apex-команды, но порядок поиска в нём superseded для strict independent-first.
- Для sub-agents нужен фазовый barrier: сначала все пишут независимые streams, потом observer/synthesizer сравнивает.

## Divergence / открытые вопросы

- Нужен ли отдельный статус `independent-draft`, чтобы stream нельзя было пометить ready до сравнения?
- Нужна ли отдельная команда `variant-compare`, которая запускается после заполнения independent draft?
- Должен ли запрет раннего якорения распространяться на `instruction-preflight`, или только на `repo-search`?
- Какой минимальный объём independent draft достаточен перед compare: секции 01-03 или полный ответ до 07?

## Проверки

Выполнены локально:

```text
python -m py_compile tools\top.py tools\test_top.py tools\capabilities.py
python tools\test_top.py
python tools\stream.py check --max-age-days 7 --json
python tools\generate.py
python tools\validate.py
python tools\generate.py --check
python tools\top.py cauldron-lanes variant-start-order-policy --ready-only --json
```

Результат: `test_top` OK, `stream.py check` без stale/broken/incomplete_ready, `validate.py` -> `OK=12 WARN=0 ERROR=0`, generated state стабилен.

## Следующие шаги

1. Прогнать `generate.py`, `stream.py check`, `validate.py`.
2. Закрыть `T-258`, если gate зелёный.
3. Следующей задачей можно оформить phase barrier для групп sub-agents: `variant-start-batch` или `variant-compare`.

## Applied instructions

- AGENTS.md: outbox report preserved; no чужие сообщения удалялись.
- PROTOCOL.md: report kept as proposed/done evidence; no accepted decision is created here.
- docs/protocol-machine-layer.md: added explicit machine-readable evidence footer for check-report.

Checks:
- python tools\validate.py -> OK
- python tools\generate.py --check -> OK
- python tools\instructions.py check-report <this-file> -> OK after footer normalization
