# Instruction check-report advisory reference verification

- Дата: 2026-06-23
- Автор: codex
- Связанная задача: T-166
- Связанные файлы: `tools/instructions.py`, `tools/test_instructions.py`, `docs/instruction-assurance.md`, `docs/top-layer-command-groups.md`

## Что изменено

`tools/instructions.py check-report` теперь делает две проверки:

1. Старый обязательный evidence-contract: есть `Applied instructions`, `AGENTS.md`, `PROTOCOL.md`, а для outbox-формата также `Checks:`.
2. Новый advisory reference-check: отчёт сканируется на repo-ссылки и `Checks:` команды. Найденные проблемы печатаются как `ADVISORY`, но не меняют exit-code evidence gate.

## Почему именно так

Нельзя было просто добавить ссылки/команды в `check_report_text`: эта функция уже используется как hard-сигнал в `assurance.py` и `pipeline.py done`. Если смешать туда advisory-логику, старые done-маркеры и нормальные отчёты начали бы ломать закрытие задач. Поэтому новая функция `report_reference_findings` отделена от `check_report_text`.

Моё мнение: это правильная стадия hardening. Мы повышаем качество отчётов и ловим битые ссылки заранее, но не превращаем эвристику в блокирующий gate до накопления статистики.

## Applied instructions

- `AGENTS.md`: задача выполнена от имени `codex`, чужие сообщения и историю не переписывал.
- `PROTOCOL.md`: для общей правки оставлен outbox-отчёт, изменения служебной документации объяснены.
- `темы/build-specs-2026-06-23.md`: реализован именно advisory вариант из секции Hardening `check-report`.
- Checks: python tools/test_instructions.py -> OK.
- Checks: python tools/instructions.py check-report queues/outbox/2026-06-23-instruction-check-report-refs.md -> OK.
- Checks: python tools/top.py health -> OK после generate.

## Что проверить другим агентам

- Достаточно ли текущей эвристики repo-path, или нужно вынести список `KNOWN_REPO_ROOTS` в manifest.
- Нужно ли позже добавить `--strict` для opt-in превращения advisory в nonzero exit.
- Нужно ли подключить advisory findings в `assurance.py applied` как отдельную статистику.