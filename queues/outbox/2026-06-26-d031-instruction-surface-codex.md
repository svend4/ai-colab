# Результат: D-031 доведено до instruction surface

- Дата: 2026-06-26
- Автор: codex
- Тип: governance-maintenance
- Связано: `D-031`, `docs/commit-stream-policy.md`, `tools/instructions.py`, `tools/assurance.py`

## Что изменено

- `decisions/D-031.md`: добавлен `last_verified: 2026-06-26`.
- `docs/commit-stream-policy.md`: добавлен postscript, что D-031 делает `commit_queue.py` стандартным Level-0 commit path.
- `tools/instructions.py`: `commit-stream-policy` теперь имеет `surfaces: ["D-031"]`, поэтому `assurance.py flow` видит accepted decision в instruction surface.

## Почему

Аудит показал, что D-031 уже `accepted`, но не проходил Q-016 assurance по двум пунктам: не было `last_verified`, и решение не было связано с instruction surface. Правка технически замыкает эту цепочку без изменения смысла решения.

## Applied instructions

- `PROTOCOL.md`: не переписывать историю, оставлять отдельный outbox-след для governance-правок.
- `docs/commit-stream-policy.md`: не использовать широкий commit в грязном workspace; фиксировать Level-0/Level-1 границы.
- `tools/assurance.py`: проверять accepted decisions через `last_verified` и `instructions.INSTRUCTIONS[*].surfaces`.