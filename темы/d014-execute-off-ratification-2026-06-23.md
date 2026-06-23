---
id: d014-execute-off-ratification-2026-06-23
type: cauldron-packet
status: proposed
title: D-014 execute OFF ratification packet
related: [D-014, D-006, D-018, D-021, T-175, docs/execute-sandbox-preflight.md]
---

# D-014 execute OFF — пакет ратификации

Дата: 2026-06-23.
Автор пакета: Codex.

## Предложение

Ратифицировать `decisions/D-014.md` как `accepted`: запуск чужого или непроверенного кода выключен по умолчанию; `mode: execute` допускается только после реальной песочницы, отдельного accepted-решения на конкретный сценарий и закрытия всех 10 preflight-гейтов из `docs/execute-sandbox-preflight.md`.

Важно: это не разрешение на запуск. Это запретительный governance-контракт, который фиксирует уже действующую практику read-only-first.

## Техническая проверка

- `docs/execute-sandbox-preflight.md` уже содержит 10 gate-пунктов: решение, источник, песочница, права, сеть, лимиты, логи, rollback, validation, человек.
- `decisions/D-021.md` уже цитирует D-014 как binding: `execute = OFF по умолчанию`.
- `tools/validate.py` уже содержит guard: `mode: execute` без реальной изоляции не должен проходить как нормальное состояние.
- Проверка `Select-String -Path drivers\*.md -Pattern '^mode:\s*execute' -Encoding UTF8` не нашла активных execute-драйверов.
- `python tools/validate.py` проходит `OK=9 WARN=0 ERROR=0`.
- `tools/instructions.py` теперь surface'ит D-014 через `execute-preflight`, чтобы после accept решение доходило до agent preflight.

## Гуманитарная проверка

Плюсы:

- снижает риск запуска непроверенного кода на Windows host;
- защищает личные файлы, токены, SSH, браузерные профили, Docker socket и системные каталоги;
- даёт людям и агентам простое правило: сначала read-only intake/report, execute только после отдельного решения;
- не блокирует полезную работу: `files`, `repo-runner`, `git-log`, `knowledge.py`, `sandbox/` intake остаются доступными.

Минусы и ограничения:

- замедляет эксперименты с внешним кодом, потому first-run требует человека;
- настоящая песочница ещё не реализована, поэтому D-014 пока запрещает больше, чем разрешает;
- может создать ложное ощущение безопасности, если кто-то примет текст preflight за готовый runner;
- D-014 требует дисциплины: запрет должен оставаться проверяемым валидатором и outbox evidence, иначе он станет декларацией.

## Консенсусная позиция Codex

Технически и гуманитарно D-014 стоит принять как `accepted`, но только Stefan может сделать этот перевод по D-006. Агентская рекомендация: принять D-014 в текущей формулировке, оставив `docs/execute-sandbox-preflight.md` как рабочий preflight-документ, а не как разрешение на запуск.

## Точный human gate

Stefan, если согласны, напишите в чате одну из командных формулировок:

```text
Принимаю D-014: execute OFF по умолчанию, 10 preflight-гейтов обязательны.
```

или:

```text
Не принимаю D-014; нужно изменить: <что именно>.
```

После явного `принимаю` агент может безопасно сделать follow-up: `decisions/D-014.md status: accepted`, добавить `last_verified`, обновить агрегаты и закрыть T-175 как done.