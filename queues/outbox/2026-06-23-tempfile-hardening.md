---
id: outbox-2026-06-23-tempfile-hardening
type: report
status: historical
agent: codex
related: T-172, drivers/test_tmp.py, tools/friction.py, docs/project-audit-2026-06-23.md
---

# Tempfile hardening — T-172

По результатам полного аудита исправлен повторяющийся Windows/runtime дефект: стандартный Python
`tempfile.mkdtemp()` / `TemporaryDirectory()` может создать директорию, в которую тот же Python потом не может писать.

Что изменено:

- `drivers/test_tmp.py` усилен write-probe: temp-директория считается созданной только после реальной записи/чтения файла.
- `tools/test_core_export.py`, `tools/test_ownership.py`, `tools/test_text_extract_docx.py` переведены на `drivers/test_tmp.py`.
- `tools/test_promote_reuse.py`, `drivers/data/test_data.py`, `drivers/repo-runner/test_inventory.py`, `drivers/workbench-db/test_db.py` также переведены с stdlib temp на workspace-safe helper.
- `tools/friction.py` F-004 теперь проверяет две вещи: project-safe helper и stdlib `tempfile`. Если helper работает, а stdlib temp небезопасен, F-004 возвращает `warn` с рецептом, а не ложный `ok`.

Итог проверок:

```text
full tools test suite -> 36/36 OK
driver tests -> 15/15 OK
python tools/friction.py status --json -> F-004 warn: project helper works, stdlib tempfile unsafe
```

Applied instructions:

- `AGENTS.md` / `PROTOCOL.md`: изменения внесены в scoped code/tests/docs/task/outbox, чужие сообщения не переписаны.
- `docs/friction-ledger.md`: применён архетип F-004, решение переведено из ручного рецепта в тестовый helper + detector.
- `docs/project-audit-2026-06-23.md`: закрыт P1 follow-up T-172.
- Checks: `python -X utf8 tools/test_core_export.py`; `python -X utf8 tools/test_ownership.py`; `python -X utf8 tools/test_text_extract_docx.py`; `python -X utf8 tools/test_friction.py`; full tools test suite; driver tests; `python tools/validate.py`.