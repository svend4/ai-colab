---
id: blocks-layer
type: doc
title: Блок-слой — сборные кластеры проверенных примитивов (не стройматериалы, а блоки)
status: proposed
date: 2026-06-23
related: [adoption-statistics-2026-06-23, finder-solver-pipeline-methodology, workflow-conveyor-policy]
---

# Блок-слой: `tools/blocks.py` + `tools/adoption.py`

> Adoption-аудит (`topics/adoption-statistics-2026-06-23.md`) показал: проверенное **работает**, но
> применяется **россыпью** (отдельные скрипты = «стройматериалы»). Блок-слой собирает проверенные
> примитивы в **блоки** — переиспользуемые, автоматические, кластерные единицы, запускаемые одной
> командой. Это переход «стройматериалы → блочный дом»: строим из готовых блоков, в т.ч. для
> рекурсивного само-улучшения (над ошибками, кодом, доками).

## `tools/blocks.py` — реестр + раннер блоков

Блок = именованный кластер проверенных tools, запускаемых **параллельно** (`threading.Thread`;
обходит коллизию `tools/agent_queue.py`↔stdlib `queue`), сводимых в единый вердикт. Шаги классифицируются
`gate` (rc решает вердикт — `validate`, `generate --check`) или `advisory` (собираются, не валят).

| Блок | Кластер | Назначение |
|---|---|---|
| `audit` | validate+generate ‖ friction+assurance+reconcile+drift | самопроверка над ошибками |
| `adoption` | adoption.py | само-мониторинг применения |
| `self` | validate+generate ‖ friction+assurance+adoption+metrics | рекурсивная самопроверка целиком |
| `improve` | adoption+friction+assurance+drift ‖ validate+generate | петля само-улучшения → вход роутеру |
| `pyramid` | assurance coverage/flow ‖ promote+portal | здоровье пирамиды L4→L1 |

```
python tools/blocks.py list
python tools/blocks.py audit [--json] [--seq]
python tools/blocks.py self
```

## `tools/adoption.py` — статический детектор применения

Операционализирует один-разовый 30-агентный adoption-аудит в **дешёвый повторяемый** детектор:
dormant-инструменты (0 code-вызывателей и 0 `.py`-doc-ссылок), `doc-only`-решения (D-NNN ни в одном
не-test инструменте), orphan-доки (0 inbound по имени файла). Встроен нюанс FINDER: **manual-cli**
(есть `main` + `.py`-ссылки, но 0 code-вызывателей) ≠ dead. Это прокси нижней границы; точное
«enforced» судит FINDER. Рекурсивно ловит и сам себя — `blocks.py`/`adoption.py` числятся применёнными
только когда подключены (этот док + блок `adoption` дают им ссылку/вызыватель).

```
python tools/adoption.py            # сводка
python tools/adoption.py --json
python tools/adoption.py --list dormant   # dormant|declarative|orphan
```

## Зачем блоки (а не россыпь)

- **Применение, не накопление.** Информации/аудитов/советов достаточно; блок делает их **исполняемыми** одной командой.
- **Параллельно + автоматично.** Кластер бежит конкурентно; `self`-блок — единая точка рекурсивной самопроверки.
- **Рекурсивное само-улучшение.** Блоки применяются к собственному коду/докам: `adoption` находит, что не
  применяется → `audit` ловит ошибки → правки → снова блок. Цикл, а не один проход.
