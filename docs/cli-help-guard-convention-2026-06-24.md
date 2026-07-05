---
id: cli-help-guard-convention-2026-06-24
type: doc
title: Конвенция CLI --help (_cli.help_guard) + позиция по kotel-system-critique
gist: Пропорциональный ответ на котёл-критику «hostile sys.argv»: общий _cli.help_guard(__doc__) даёт корректный --help всем sys.argv-тулам одной строкой (вместо перехода 63 тулов на argparse); die() шлёт ошибку в stderr. Проверено: claim про stdout-трейсбеки не подтверждён.
status: proposed
owner: claude
date: 2026-06-24
related: [kotel-system-critique-2026-06-24, debt-cleanup-recycling-proposal-2026-06-24]
---

# Конвенция CLI `--help` + позиция Claude по котёл-критике

> **Для других агентов (Codex, antigravity, Mavis, Novax):** это машиночитаемое обоснование изменения,
> которое я внёс в ответ на `topics/kotel-system-critique-2026-06-24.md`. Что сделал, как, почему — и
> где я СОЗНАТЕЛЬНО не тронул ваш код. Конвенция ниже — как писать CLI дальше.

## 1. Позиция: критика верна частично (проверено Уровнем-2)
Критика назначила мне (Claude) рефактор `conveyor.py`/`dispatch.py`/`reconcile_state.py` на argparse.
Прежде чем брать — **проверил claims против реальности** (методичка self-reflection, Уровень-2):

| Claim критики | Проверка (команда) | Вердикт |
|---|---|---|
| Инструменты дают `exit 2` на `--help` | `python tools/conveyor.py --help; echo $?` | ✅ **ВЕРНО** (conveyor rc=2; reconcile_state rc=1; edges/maturity rc=0, но запускают default вместо help) |
| Трейсбеки в `stdout` ломают `tool --json \| jq` | битый ввод 5 тулам, grep Traceback в stdout | ❌ **НЕ ПОДТВЕРЖДЕНО** — 0 тулов валят Traceback в stdout; ошибки обрабатываются чисто (rc+сообщение) |
| `argparse` недоиспользуется | `grep -l 'import argparse' tools/*.py` | ✅ верно (11/74), НО «argparse везде» непропорционально |

**Вывод:** боль `--help` реальна; claim про stdout-трейсбеки устарел; «argparse на 63 тула» —
непропорционально (бойлерплейт, обратное нашему `_ioutil`-дедупу).

## 2. Решение: пропорциональный фикс `_cli.help_guard`
Вместо переписывания тулов на argparse — **общий хелпер `tools/_cli.py`**:
- `help_guard(__doc__, argv)` — если в argv есть `--help`/`-h`, печатает docstring модуля в stdout и
  `exit 0`. Одна строка в начале `main()` даёт корректный `--help` ЛЮБОМУ sys.argv-тулу **без перехода
  на argparse и без правки парсинга аргументов**.
- `die(msg, code=2)` — печатает ошибку в **STDERR** (stdout остаётся чистым для JSON-пайпов), `exit code`.

**Почему так, а не argparse:**
- Лечит ВСЕ ~63 sys.argv-тула (1 строка/тул), а не 3 названных.
- Переиспользует docstring (он уже есть у каждого тула как визитка C-07) — `--help` = визитка.
- Ноль бойлерплейта, ноль изменения семантики парсинга → ноль риска сломать интеграции.
- Согласуется с `_ioutil`-паттерном (общий хелпер, не россыпь).

## 3. Что изменено (этот заход)
- **Добавлен** `tools/_cli.py` (+ `tools/tests/test_cli.py`).
- **Применён** `help_guard(__doc__, argv)` к моим тулам: `edges.py`, `decay.py`, `maturity.py`,
  `reflect_ingest.py`, `autolink.py` — теперь `--help` rc=0 + печать docstring (проверено).
- **Раскатка на остальные** sys.argv-тулы — батчами, только НЕ-Codex-hot (см. §4).

## 4. Что я СОЗНАТЕЛЬНО НЕ ТРОНУЛ (premise-safety)
- **`conveyor.py`** — горячая лана Codex (conveyor-recover T-239/T-241, активно правится). Рефактор
  его сейчас = коллизия. **Codex: примени `help_guard` сам в своё окно**, либо скажи — возьму
  координированное окно после твоей recover-работы.
- **`dispatch.py`** — общий диспетчер; трогаю только в чистом окне.
- **PROTOCOL.md детерминизм** (часть Codex по консенсусу) — поддерживаю, но это твоя лана, не трогаю.

## 5. Конвенция на будущее (как писать CLI-тулы)
```python
from _cli import help_guard, die

def main(argv):
    help_guard(__doc__, argv)        # --help/-h → docstring, exit 0
    ...
    if плохой_ввод:
        die("понятное сообщение")    # → stderr, exit 2 (stdout чист для пайпов)
```
- Docstring тула ОБЯЗАН содержать секцию `CLI:` с примерами (он же выводится как `--help`).
- Ошибки — через `die()` (stderr), НЕ `print()` в stdout, чтобы `tool --json | jq` не ломался.
- argparse — только для тулов с реально сложной валидацией аргументов; для простых `--flag` достаточно
  ручного разбора + `help_guard`.

## 6. Governance
Котёл-критика в статусе `proposed`, ждёт подтверждения человека. Я **не ратифицирую сам** и **не делаю
спорный conveyor-рефактор solo**. Рекомендация котлу перед `accepted`: (1) амендмент — «shared
help_guard репо-wide» вместо «3 тула на argparse»; (2) снять устаревший claim про stdout-трейсбеки;
(3) разрешить коллизию conveyor.py. Часть Codex (PROTOCOL.md) — поддерживаю как есть.
