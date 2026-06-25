---
id: outbox-2026-06-23-project-audit
type: report
status: historical
agent: codex
related: T-171, T-172, T-173, docs/project-audit-2026-06-23.md
---

# Project audit — отчёт Codex

Проведён полный технический и концептуальный аудит проекта.

Канонический отчёт: `docs/project-audit-2026-06-23.md`.

Краткий итог:

- hard checks зелёные: `validate`, `generate --check`, `top.py health`;
- conveyor healthy, но `n_inflight=5` при `target=2`, поэтому новый fan-out не нужен;
- `top.py process-landed --json` работает и показывает `state: empty`; финальный conveyor-снимок: target=2, in-flight=5, landed=0, shipped=28, healthy;
- полный прогон tools test suite: 32/35 OK;
- 3 падения связаны с Python `tempfile.mkdtemp` PermissionError даже внутри `tmp-work`;
- assurance имеет 2 medium-находки: orphan-L1 и accepted decisions вне instruction surface;
- dirty tree требует selective-add, не `git add -A`;
- unknown untracked `data/portals/...` нельзя включать без ownership-проверки.

Follow-up:

- `T-172` — temp/ACL defect + friction F-004 coverage;
- `T-173` — закрыть assurance medium findings.

Applied instructions:

- `AGENTS.md` / `PROTOCOL.md`: аудит записан в `docs/project-audit-2026-06-23.md`, `queues/outbox/2026-06-23-project-audit.md`, `tasks/T-171.md`; чужие файлы не удалялись и не коммитились.
- `docs/instruction-assurance.md`: отчёт содержит applied instructions и Checks.
- `docs/top-layer-throughput-methodology.md`: аудит использовал `process-landed` как верхний read-only intake check.
- Checks: `python tools/validate.py`; `python tools/generate.py --check`; `python tools/top.py health`; `python tools/top.py assurance all --json`; `python tools/top.py process-landed --json`; `python tools/test_top.py`; full tools test runner; `python tools/instructions.py check-report queues/outbox/2026-06-23-project-audit.md`.