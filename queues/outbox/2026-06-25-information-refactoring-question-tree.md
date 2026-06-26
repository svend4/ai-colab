---
type: report
id: 2026-06-25-information-refactoring-question-tree
status: proposed
agent: codex
task: T-246
related: [information-refactoring-question-tree-2026-06-25]
---

# Information refactoring question tree

По запросу пользователя оформлен пронумерованный вопросник для мета-работы над репозиторием:

- `topics/information-refactoring-question-tree-2026-06-25.md`

Смысл документа: рассматривать репозиторий как большой живой черновик, рабочую машину и исторический корпус одновременно. Главный подход — не удалять историю, а санировать её через статусы, индексы, верхние команды, synthesis и promotion/demotion между уровнями.

Основные блоки:

- [x] Дано определение информационного рефакторинга.
- [x] Дано определение санации и омоложения репозитория.
- [x] Описана золотая середина между агентом и ОС/файловой средой.
- [x] Составлены вопросы о начале проекта, повторяемых удачных решениях и том, что было бы сделано иначе.
- [x] Разделены решённые, частично решённые и открытые вопросы.
- [x] Предложен формат дальнейшей работы с question units.

## Applied instructions

- AGENTS.md
- docs/protocol-machine-layer.md
- User request: numbered, deep, logically structured question tree

Checks:
- python tools/generate.py -> OK
- python tools/validate.py -> OK
- python tools/generate.py --check -> OK
