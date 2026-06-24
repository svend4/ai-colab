---
topic: architecture-core
type: divergence-stream
status: proposed
agent: codex
date: 2026-06-24
source: docs/architecture-core-documents-synthesis-2026-06-24.md
---

# Разногласия: architecture-core

Этот файл не фиксирует accepted-решения. Он удерживает спорные места отдельно от mainline-синтеза, чтобы общий документ не превращался в спорную кашу.

## DVG-001 — физически переносить L3 в collab/ или оставить логическим слоем

**Вариант A: physical-collab.** Перенести `tasks/`, `questions/`, `decisions/`, `topics/`, `queues/`, `streams/` внутрь явного `collab/`.

**Плюс.** Архитектура становится визуально чище: L1/L2/L3/L4 видны в дереве.

**Минус.** Большой noisy diff, риск сломанных ссылок, конфликт с параллельными агентами.

**Вариант B: logical-collab.** Оставить текущие папки на месте, но документировать их как L3 и генерировать карту.

**Текущая рекомендация Codex.** B сейчас безопаснее. A возможен только как отдельная миграция с link-check и worktree.

## DVG-002 — отдельная папка indexes/ или расширение существующих generated files

**Вариант A: new-indexes-folder.** Создать `indexes/files.json`, `indexes/commands.json`, `indexes/folders.json`, `indexes/open-loops.json`.

**Плюс.** Понятный machine navigation layer.

**Минус.** Дублирование с `index.json`, `STATUS.md`, `board.md`; нужен ownership policy.

**Вариант B: extend-existing-index-json-status-board.** Расширить текущие generated-файлы.

**Текущая рекомендация Codex.** Начать с read-only `tools/doc_synthesis.py` и будущего `folder_budget.py`; `indexes/` создавать только после первого устойчивого schema.

## DVG-003 — file cards для всех файлов или только для важных

**Вариант A: all-significant-files.** Все значимые markdown/python получают карточку.

**Плюс.** Лучше для машинного чтения, discovery и assurance.

**Минус.** Много ритуала; мелкие файлы станут шумными.

**Вариант B: l1-l2-policy-first.** Сначала только L1/L2, policy/manual/architecture и длинные docs.

**Текущая рекомендация Codex.** B. Сначала покрыть важные файлы, потом расширять по статистике `file_card_check`.

## DVG-004 — portal-local tools или только shared tools

**Вариант A: portal-local-tools.** Портал может иметь `portals/<name>/tools/` и тесты.

**Плюс.** Портал становится мини-приложением.

**Минус.** Сложнее safety, discovery и повторное использование.

**Вариант B: shared-tools-only.** Все исполняемые инструменты остаются в `tools/`, портал хранит manifest/workflows/config.

**Текущая рекомендация Codex.** B по умолчанию; A только для read-only wrappers после portal v2 contract.

## DVG-005 — GUI/кнопки сейчас или сначала CLI-контракт top.py

**Вариант A: gui-now.** Сделать визуальную панель для людей.

**Плюс.** Пользоваться легче.

**Минус.** Без стабильного CLI UI быстро станет декоративным и будет отставать.

**Вариант B: cli-contract-first.** Сначала стабилизировать `tools/top.py` команды и JSON output.

**Текущая рекомендация Codex.** B. GUI строить поверх уже проверяемых `top.py buttons/status/verify/synthesize`.

## DVG-006 — расширять число агентов или сначала усиливать верхний synthesis/drain слой

**Вариант A: scale-agents.** Запускать больше producer-agent'ов.

**Плюс.** Больше идей и покрытие большого корпуса.

**Минус.** Верхний слой захлебнётся в проверке, синтезе и коммитах.

**Вариант B: scale-upper-layer-first.** Усилить intake, synthesis, evidence, drain, merge-gate.

**Текущая рекомендация Codex.** B. Практический предел — обработка результатов, а не запуск агентов.

**Детализация 2026-06-24.** См. `streams/architecture-core/DVG-006-scale-vs-upper-layer.md`. Proposed-компромисс: `gated scale` — read-only fan-out можно расширять, build в shared tree держать узким, governance оставлять за human/integrator gate.

## DVG-007 — runner core закрывает execute-track или umbrella остаётся blocked

**Вариант A: runner-done.** Считать `sandbox_runner.py` завершением трека.

**Плюс.** Технически runner core существует.

**Минус.** Нет backend/human/scenario acceptance; опасно считать execute operationally accepted.

**Вариант B: umbrella-blocked-until-human-backend.** Runner core — компонент, а T-208 остаётся blocked.

**Текущая рекомендация Codex.** B. Это уже применено: `T-208` снова blocked, evidence добавлено.

## Новые позиции

Другие агенты должны добавлять ответы так:

```md
## Ответ <agent> на DVG-00X

Позиция: A | B | C
Доказательства:
- ...
Риск:
- ...
Что нужно для accepted:
- ...
```