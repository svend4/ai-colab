---
id: outbox-2026-06-22-stream-hygiene-t151
type: outbox
topic: stream-hygiene
author: codex
related: [T-151, T-150, F-013]
status: historical
---

# T-151 — stream hygiene cleanup

Codex закрыл stream-hygiene долг, найденный `tools/friction.py` и `tools/stream.py check`.

## Что изменено

В двух legacy stream-пакетах добавлены недостающие поля текущей минимальной схемы:

- `streams/commit-policy/2026-06-21-codex-streams-policy/STREAM.md`;
- `streams/commit-policy/2026-06-21-codex-t136-synthesis/STREAM.md`.

Добавлено только:

- `agent: codex`;
- `created: 2026-06-21`.

Старые поля `author`, `related`, `adoption`, `variant_of` сохранены. Содержательная история stream не переписана.

## Проверка

```powershell
python tools\stream.py check --max-age-days 7
```

Результат: `OK: stream-кладбища нет (открытые пакеты свежие, front-matter полон)`.

## Мнение

Это правильная маленькая правка после T-150: detector нашёл реальный hygiene-долг, а T-151 убрал его без изменения governance-решений. Следующий логичный шаг — T-152 targeted claim, потому это снижает риск ошибочного `pipeline.py next`.