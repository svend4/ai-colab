# No-verify / bulk-guard incident review — 2026-07-06

Автор: Codex  
Статус: review + technical hardening

## Что проверено

Проверялась цитата из переписки с другим агентом: массовое удаление было закоммичено через `git commit --no-verify`, из-за чего pre-commit hook с `bulk_guard` не сработал; затем агент сообщил, что откатил удаление.

## Факты в текущем репозитории

Подтверждено:

- `decisions/D-026.md` существует и имеет `status: accepted`.
- `PROTOCOL.md` содержит D-026-раздел и прямой запрет обхода `--no-verify` без обоснования.
- `tools/bulk_guard.py` существует.
- `tools/githooks/pre-commit` вызывает `python tools/bulk_guard.py --hook`.
- `git config --get core.hooksPath` возвращает `tools/githooks`, то есть hook path активирован.
- Текущий рабочий diff не содержит tracked deletions и не является bulk-операцией: около `+327/-92`, ниже порога `-500 строк / 10 файлов`.

Не может быть доказано только из git-истории:

- Сам факт использования `git commit --no-verify` конкретным агентом: Git не записывает этот флаг в объект коммита. Это можно установить только из shell history, логов агента или его отчёта.

## Главный вывод

Цитата технически правдоподобна и указывает на реальную архитектурную проблему: локальный `pre-commit` полезен, но **не является абсолютной защитой**, потому `git commit --no-verify` отключает pre-commit/commit-msg hooks.

Значит `bulk_guard` в pre-commit — нужный слой, но не последний слой.

## Уже сделанное Codex hardening

Обнаружена и исправлена отдельная слабость `bulk_guard`: старый `backup-*` тег мог считаться страховкой, даже если не указывал на текущий HEAD.

Изменено:

- `tools/bulk_guard.py`: добавлен `classify_verdict()`; insurance теперь засчитывается только если есть `backup-*`, указывающий на текущий HEAD (`git tag --points-at HEAD`).
- `tools/tests/test_bulk_guard.py`: добавлены тесты `strict backup-on-HEAD insurance`; fixture переведён с нестабильного `tempfile.mkdtemp()` на контролируемый `tmp-work`.

Проверки:

```text
PYTHONDONTWRITEBYTECODE=1 python tools\tests\test_bulk_guard.py -> OK
PYTHONDONTWRITEBYTECODE=1 python -m py_compile tools\bulk_guard.py tools\tests\test_bulk_guard.py -> OK
python tools\bulk_guard.py -> not bulk
python tools\bulk_guard.py --hook -> exit 0 on current diff
```

## Как избежать повторения

### Слой 1 — локальный быстрый gate

Оставить `tools/githooks/pre-commit` + `bulk_guard.py --hook`, но не считать это достаточным.

Почему: `--no-verify` отключает этот слой.

### Слой 2 — безопасная commit-обёртка

Использовать `python tools/commit.py ...` как основной путь коммита для агентов:

- запрещает `git add -A`, `.`, `*`, `-u`;
- стейджит только явные пути;
- проверяет удаления до коммита;
- запускает guards;
- делает `git commit` без `--no-verify`.

Политически: raw `git commit` для агентов должен считаться аварийным путём, а `git commit --no-verify` — incident-level action с обязательным отчётом.

### Слой 3 — CI / pre-receive / protected branch

Нужен gate, который нельзя обойти локальным `--no-verify`:

- protected `main/master`: запрещён direct push;
- merge только через PR/merge-gate;
- required CI check: bulk diff against base branch;
- для self-hosted Git лучше pre-receive hook.

Нужная доработка: режим `tools/bulk_guard.py --range <base>..<head>` или отдельный `tools/bulk_range_guard.py`, который анализирует уже созданные коммиты/PR diff. Такой gate поймает bulk deletion даже если локально использовали `--no-verify`.

### Слой 4 — post-commit/post-push audit

`post-commit` не может заблокировать коммит, но может сразу создать incident report, если последний commit содержит bulk deletion. Это полезно как сигнализация, но не как защита.

### Слой 5 — D-026 insurance manifest

Для массовых операций нужен не только `backup-*` тег, но и машинно-читаемый manifest:

```text
bulk-insurance/<date>-<topic>.json
- head: <sha>
- tag: backup-...
- files_expected: N
- deleted_lines_expected_max: N
- human_approval: link/id or null
- external_backup: path/bundle/checksum
```

Тогда guard может проверять не только наличие тега, но и соответствие страховки конкретной операции.

## Рекомендованный следующий шаг

1. Ратифицировать рабочую норму: агентам запрещён прямой `git commit --no-verify`; исключение только с human approval и incident report.
2. Сделать `tools/bulk_guard.py --range` для CI/merge-gate.
3. Подключить required CI/pre-receive gate, который нельзя обойти локально.
4. Перевести commit-процесс агентов на `tools/commit.py` или `tools/commit_queue.py`.