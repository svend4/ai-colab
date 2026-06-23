# Driver Schema Acceptance Checklist

Дата: 2026-06-20
Связано: `decisions/D-013.md`, `questions/Q-008.md`, `drivers/SCHEMA.md`, `tools/validate.py`

## Цель

Этот checklist нужен человеку или явно назначенному сборщику перед переводом `D-013` из `proposed` в `accepted`.

Codex и другие агенты могут подготовить материалы, но не должны сами принимать `accepted`, если человек их явно не назначил.

## Проверки перед accepted

### 1. Содержательная проверка Q-008

- [ ] Q-008 всё ещё актуален.
- [ ] Вариант B действительно выбран как компромисс.
- [ ] Вариант C с MCP metadata явно отложен до L2/MCP PoC.
- [ ] Нет возражений от активных агентов/человека.

### 2. Проверка schema-файлов

- [ ] `drivers/SCHEMA.md` существует.
- [ ] `drivers/_template.md` содержит поля schema v1.
- [ ] Все настоящие `drivers/*.md` содержат обязательные поля.
- [ ] `risk: medium|high` требует `audit: true`.
- [ ] `source_last_verified` имеет формат `YYYY-MM-DD`.
- [ ] `timeout_seconds` и `max_output_bytes` положительные числа.

### 3. Проверка валидатора

Требует разблокировки T-039.

```powershell
python tools\validate.py
python tools\generate.py --check
```

Ожидание:

- [ ] `validate.py` не даёт ERROR.
- [ ] `generate.py --check` не показывает устаревшие индексы.
- [ ] `index.json` содержит актуальные `drivers`.

### 4. Проверка текущих драйверов

- [ ] `drivers/files.md`
- [ ] `drivers/data.md`
- [ ] `drivers/repo-runner.md`
- [ ] `drivers/codex-local.md`

Для каждого:

- [ ] поля schema v1 заполнены;
- [ ] статус соответствует фактической готовности;
- [ ] режим не превышает фактические возможности;
- [ ] нет секретов;
- [ ] безопасность описана.

### 5. Решение

Если всё выше выполнено:

- [ ] изменить `decisions/D-013.md`: `status: accepted`;
- [ ] обновить `QUESTIONS.md`/`questions/Q-008.md`: Q-008 → `answered`;
- [ ] обновить generated индексы через `tools/generate.py`;
- [ ] записать обоснование в `topics/ai-os-bridge.md`.

Если не выполнено:

- [ ] оставить D-013 `proposed`;
- [ ] добавить конкретный blocker в Q-008 или новую task.

## Текущий blocker

На момент создания checklist главный blocker — T-039: внешние процессы/Python runtime зависают в текущей shell-сессии. До восстановления `validate.py` и `generate.py` нельзя честно принимать schema v1 как fully verified.

