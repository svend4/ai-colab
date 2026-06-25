---
status: historical
---
# Outbox: driver acceptance batch passed (19/19)

Автор: Claude
Дата: 2026-06-20
Адресаты: люди, AI-агенты, reviewer, summarizer.

Связанное: `drivers/mcp_acceptance_test.py`, `topics/ai-os-bridge.md`.

## Кратко

Приёмочный батч драйверов (реальные `call_tool`, не только handshake) прошёл **19/19**:
`files` 4/4 (вкл. redaction), `repo-runner` 3/3, `data` 4/4, `codex-local` 2/2, `gateway` 6/6.
Прогон: Linux-песочница, python 3.10, пакет `mcp`.

## Что проверено по факту

- `files.search` находит подстроку; `files.read_file` маскирует `api_key`-секрет (redaction);
- `repo-runner.repo_risks` помечает `run.sh`; `data` читает CSV (`columns`/`head`/`summarize`);
- `codex-local.codex_available/info` не падают (Codex не на PATH — обрабатывается корректно);
- `gateway` отдаёт files/repo и `memory_query` возвращает занесённый документ.

## Наблюдение (не блокер)

redaction в `files_driver` покрывает только `api_key|token|secret|password|passwd`.
Предложение: расширить `SECRET_RE` на `aws_key|secret_key|access_key` и `AKIA[0-9A-Z]{16}`.

## Просьба

1. Прогнать `python drivers\mcp_acceptance_test.py` на Windows для подтверждения среды.
2. Решение человека (D-006): перевести `files`/`repo-runner`/`data`/`codex-local`/`gateway` `draft→ready`?
3. Замечания и несогласия — в `topics/ai-os-bridge.md` или отдельным файлом в `queues/outbox/`.
