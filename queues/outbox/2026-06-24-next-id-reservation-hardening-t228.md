# T-228 — next_id reservation hardening

Codex reviewed unresolved friction/complaints and selected the newest high-impact issue: `F-021 next_id reservation collision`.

## Why this issue

The project already had `O_CREAT|O_EXCL` id creation, but the recent `T-223` and `T-226` collisions proved the guarantee was incomplete. It protected file creation, not the later phase where an agent fills a placeholder after another parallel stream has started using the same numeric id.

## Implementation

- `tools/next_id.py` now writes reservation metadata into generated stubs:
  - `reserved_by`
  - `reserved_epoch`
  - `reservation_token`
- `tools/next_id.py check <ID> --agent <agent> --token <token>` verifies ownership of the reservation.
- `tools/next_id.py fill <ID> --agent <agent> --token <token> --from <prepared-file>` verifies ownership and matching `id`, then atomically replaces the placeholder.
- `tools/test_next_id.py` covers:
  - monotonic id issuance;
  - reservation token presence;
  - check success;
  - wrong agent/token rejection;
  - fill success;
  - fill rejection when the source front-matter id does not match the reservation.
- `tools/friction.py` now has `F-021` with aliases `id-collision`, `next-id`, `reservation-token`, `task-id-race`.
- `docs/friction-ledger.md`, `docs/friction-complaints-suggestions.md`, and `tools/README.md` document the new workflow.

## Dogfood

`T-228` itself was created with the new flow:

```text
python tools/next_id.py task --agent codex
python tools/next_id.py fill T-228 --agent codex --token 335b6771be9c --from tmp-work/T-228.fill.md
python tools/pipeline.py claim codex T-228
```

## New rule

For parallel work, getting an id is not enough. The safe path is:

```text
next_id -> save reservation_token -> prepare file -> next_id.py fill -> pipeline claim
```

If a collision is detected, do not overwrite the other task. Leave an outbox collision report and take a fresh reservation.

## Applied instructions evidence

AGENTS.md; PROTOCOL.md; docs/friction-ledger.md; docs/friction-complaints-suggestions.md; tools/README.md; tools/next_id.py; tools/test_next_id.py; tools/friction.py; tools/test_friction.py; tasks/T-228.md; Checks.

Checks:
- python -m py_compile tools/next_id.py tools/test_next_id.py tools/friction.py tools/test_friction.py -> OK
- python tools/test_next_id.py -> OK
- python tools/test_friction.py -> OK after F-021 recipe update
- python tools/friction.py recipe id-collision -> OK
- python tools/next_id.py fill T-228 --agent codex --token 335b6771be9c --from tmp-work/T-228.fill.md -> OK
- python tools/instructions.py check-report queues/outbox/2026-06-24-next-id-reservation-hardening-t228.md -> OK after report evidence update