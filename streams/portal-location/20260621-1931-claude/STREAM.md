---
id: 20260621-1931-claude
topic: portal-location
agent: claude
status: proposed
created: 2026-06-21
---

# Stream: 20260621-1931-claude

## Причина форка

portals/ (clean L2) vs data/portals/ (corpus): unify under portal.py or keep split?

## Вариант

При создании первого реального L2-портала вскрылось расхождение локаций:
- пирамида (`docs/workspace-pyramid-levels.md`) кладёт порталы в **`portals/<name>/`** (чистовая L2:
  `portal.md`+`current-state.md`+`workflows.md`);
- инструмент `tools/portal.py` оперирует **`data/portals/<name>/`** (`portal.md`+`corpus/`+`.db`).

Это ровно открытый вопрос пирамиды **Q4** («`portals/` хранит data или только clean config + ссылки?»).

### Два варианта

| | A. Раздельно (рекомендую) | B. Свести в одно |
|---|---|---|
| `portals/<name>/` | чистовой L2: config + current-state + workflows + ссылки | всё, включая корпус |
| `data/portals/<name>/` | операционный корпус + `.db` (часть gitignored) | упразднить |
| `portal.py` | читает identity из `portals/<name>/portal.md`, корпус резолвит по `corpus_ref` в `data/` | читает всё из `portals/` |
| Плюс | data (тяжёлое, .db, сырое) не пачкает чистовой L2; совпадает с Q4-леном пирамиды | один путь = «один портал» |
| Минус | две папки на портал | корпус/.db в clean-слое; конфликт с правилом «L2 без raw data» |

### Рекомендация (proposed, не решение)

**Вариант A.** Я уже реализовал чистовую часть: `portals/example/{portal.md,current-state.md,workflows.md}`
ссылается на корпус `data/portals/example/corpus`. Доработка `portal.py`: принимать имя L2-портала,
читать `portals/<name>/portal.md`, брать `corpus_ref` и строить индекс из `data/`. Тогда `portals/` —
чистовой вход, `data/portals/` — операционные данные. **Эта доработка трогает `portal.py` (горячая зона
Codex) — поэтому только после синтеза, не соло.**

### Перепроверка (D-018)

- **Техническая:** A не ломает текущий `portal.py` (он продолжает работать с `data/portals/`); L2-файлы
  аддитивны; `.db` остаётся вне clean-слоя.
- **Гуманитарная:** человек видит чистовой портал без шума корпуса/индексов; «один смысл портала» при A
  достигается ссылкой `corpus_ref`, не смешиванием.

## Adoption

Перенос в mainline — только после review и явного `adopt` (governance-решение остаётся в котле, D-018).
