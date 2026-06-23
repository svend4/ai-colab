# Top assurance apex

- Дата: 2026-06-23
- Автор: codex
- Связанная задача: T-165
- Связанные файлы: `tools/top.py`, `tools/test_top.py`, `tools/capabilities.py`, `system-capabilities.json`, `docs/top-layer-command-groups.md`, `tools/README.md`

## Что изменено

`tools/top.py` получил новый сценарий `assurance`:

```powershell
python tools/top.py assurance
python tools/top.py assurance currency --json
python tools/top.py assurance flow --strict
```

Сценарий вызывает `tools/assurance.py` и поднимает Q-016 applied/currency/coverage/flow в верхнюю панель. `top.py health` теперь дополнительно печатает `assurance (warning layer)`, но не делает его hard gate. `agent-start` также показывает assurance как advisory-снимок после статуса.

## Почему именно так

Проблема была концептуальная: инструкции, freshness и coverage уже есть в нижнем слое, но новый человек или агент на вершине пирамиды мог их не увидеть, если не знает отдельный скрипт `assurance.py`. Поэтому правильная форма на этой стадии — не новый тяжёлый policy-engine, а тонкая верхняя команда.

Моё мнение: это делает систему более управляемой без преждевременного блокирования. Default режим advisory сохраняет скорость работы, а `--strict` даёт явный gate для ревью/CI, когда команда сознательно хочет жёсткую проверку.

## Проверки

- `python tools/test_top.py` — OK.
- `python tools/top.py assurance all --json` — exit 0, печатает sections.
- `python tools/top.py assurance flow --strict` — exit 1 на реальной medium-находке, что подтверждает opt-in strict.
- `python tools/capabilities.py snapshot` — обновил `system-capabilities.json`.

## Что дальше

- Закрыть orphan-L1 в `assurance.py coverage`: наполнить L2 portals для core-модулей.
- Решить flow-находки: вплести accepted decisions D-001/D-002/D-004/D-008/D-009/D-010/D-013 в instruction surface.
- После нескольких чистых циклов можно обсуждать, какие секции assurance переводить из warning-layer в opt-in gate шире.