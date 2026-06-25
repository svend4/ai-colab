---
type: report
agent: codex
date: 2026-06-24
topic: optimal-information-architecture
status: historical
applied: AGENTS.md, PROTOCOL.md, docs/workspace-pyramid-levels.md, docs/engine-state-2026-06-22.md, decisions/D-016.md, tools/synthesis_helper.py
related: 
---

# Отчёт: оптимальная информационная архитектура

## Что сделано

Создан предложенный архитектурный синтез:

- `docs/optimal-information-architecture-2026-06-24.md`

Документ отвечает на вопрос, как организовать проект дальше и как я бы строил его заново: L1 `core/`, L2 `portals/`, L3 `collab`, L4 `sandbox`, отдельный индексный слой, file cards, section cards, folder budget, верхний фасад команд и future checks.

## Ключевой вывод

Проект уже стал прототипом информационного двигателя. Следующий скачок должен быть не в добавлении ещё большего количества текста, а в превращении существующих правил в активные контракты:

1. file cards;
2. generated indexes;
3. top-layer command groups;
4. assurance/evidence gates;
5. synthesis streams для спорных вариантов;
6. portal manifests как рабочие мини-приложения поверх ядра.

## Консенсус из текущей документации

- D-016: ядро универсальное, домен живёт в порталах.
- D-017/D-018: варианты не стирать, спорное синтезировать через котёл.
- D-021/D-022: параллельную разработку выводить в worktree/streams, не ждать чужой коммит.
- D-023: generated indexes коммитятся ownership-aware, не вместе с чужой незавершённой работой.
- Execute-track остаётся gated; без human/preflight/evidence runner не включать.

## Открытые разногласия для будущих streams

1. Делать ли физическую миграцию L3 в `collab/` или оставить логическую карту.
2. Нужна ли отдельная папка `indexes/` поверх существующих `index.json`, `STATUS.md`, `board.md`.
3. Делать ли file cards обязательными для всех файлов или только для L1/L2/policy/manual.
4. Хранить ли portal-local code в `portals/<name>/tools/` или только в общем `tools/`.
5. Делать ли GUI/кнопки сейчас или сначала укрепить `tools/top.py` CLI.

## Следующий практический пакет

Предлагаю следующую реализацию по шагам:

1. Future file-card-standard document — стандарт визитной карточки файла.
2. Future file-card-check tool — read-only проверка покрытия file cards.
3. Future folder-budget tool — отчёт по большим папкам и отсутствующим index/README.
4. Future advice-activation document — какие советы уже автоматизированы, какие лежат пассивно.
5. Future architecture-core stream — место для альтернативных мнений по спорным пунктам.
6. `tools/top.py verify` или аналогичный bundle — одна команда для стандартной проверки.

## Проверки

```powershell
python tools\synthesis_helper.py topics
python tools\instructions.py check-report queues\evidence\T-216.evidence.md
python tools\assurance.py all
python tools\validate.py
```

## Applied instructions

- `AGENTS.md` / `PROTOCOL.md`: чужие done-файлы не переписывались; новый материал добавлен append-only.
- Локальный cauldron-synthesis skill: документ создан как `proposed`; консенсус и разногласия разделены; спорные пункты не помечены accepted.
- `docs/workspace-pyramid-levels.md`: сохранена модель L1/L2/L3/L4.
- `decisions/D-016.md`: ядро остаётся универсальным, домены через порталы.
Checks:
- python tools\synthesis_helper.py topics
- python tools\instructions.py check-report queues\evidence\T-216.evidence.md
- python tools\assurance.py all
- python tools\validate.py