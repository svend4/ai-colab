---
id: 2026-06-24-top-conveyor-recover-integration-review
type: integration-review
status: historical
agent: codex
created: 2026-06-24
related: 
---

# Top conveyor-recover integration review

## Summary

Для следующей build-задачи лучший вариант - добавить в `tools/top.py` отдельную верхнеуровневую advisory-команду:

```powershell
python tools/top.py conveyor-recover [--json] [--limit N]
```

Она должна быть тонкой оберткой над:

```powershell
python tools/conveyor.py recover [--json] [--limit N]
```

Команда не должна делать automatic repair: не запускать `land`, `ship`, `dismiss`, `tick`, `launch`, `target`, `generate`, Git или любые исправляющие действия. Ее задача - поднять уже существующую read-only диагностику reset/hang/UI mismatch на уровень `top.py`.

## Minimal code pattern

Минимальный паттерн в `tools/top.py` лучше повторить по форме `cmd_conveyor`, а не смешивать с `cmd_conveyor`:

1. В верхнем usage-блоке добавить строку:

```python
python tools/top.py conveyor-recover [--json] [--limit N]
```

2. В `_BUTTONS` добавить отдельную кнопку рядом с `conveyor-status`:

```python
{
    "id": "conveyor-recover",
    "audience": "both",
    "command": "python tools/top.py conveyor-recover [--json] [--limit N]",
    "does": "Показать read-only диагностику восстановления conveyor: stale heartbeat, missing output, unreferenced outbox reports.",
    "effect": "read-only",
}
```

3. Добавить wrapper-функцию рядом с `cmd_conveyor`:

```python
def cmd_conveyor_recover(args):
    cmd = _tool("conveyor.py", "recover")
    if args.limit is not None:
        cmd += ["--limit", str(args.limit)]
    if args.json:
        cmd.append("--json")
        try:
            p = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True,
                               encoding="utf-8", errors="replace", timeout=45)
            if p.stdout:
                print(p.stdout.strip())
            if p.stderr:
                print(p.stderr.strip(), file=sys.stderr)
            return p.returncode
        except subprocess.TimeoutExpired:
            print(json.dumps({"error": "timeout", "command": " ".join(cmd)}, ensure_ascii=False))
            return 124
    return _run("conveyor recover", cmd, timeout=45, fail_ok=True)
```

4. В `build_parser()` зарегистрировать отдельный subcommand рядом с `conveyor`:

```python
p = sub.add_parser("conveyor-recover", help="show read-only conveyor recovery diagnostics")
p.add_argument("--limit", type=int, default=10)
p.add_argument("--json", action="store_true")
p.set_defaults(func=cmd_conveyor_recover)
```

Если нужно сохранить parity с прямым `tools/conveyor.py recover`, можно дополнительно прокинуть `--target` и `--idle`, потому что прямой recover их уже принимает через общий `_arg`. Но по формулировке build-задачи обязательны только `--json` и `--limit N`; минимальный scope лучше не расширять.

## Rationale

`tools/top.py` уже использует тонкие обертки над нижележащими скриптами: `_tool(...)`, `_run(...)`, отдельные `cmd_*`, отдельная регистрация в `argparse`. Для JSON-режимов важен существующий паттерн прямого `subprocess.run(..., capture_output=True)` без заголовка `===== ... =====`, чтобы stdout оставался машинно-чистым.

`tools/conveyor.py recover` уже является read-only диагностикой: функция `recover(...)` возвращает `schema: conveyor_recover.v1`, `mutates: False`, assessment, findings, referenced outputs и счетчик проверенных outbox reports. Прямой CLI уже поддерживает `--json` и `--limit`, поэтому `top.py` не должен дублировать логику диагностики.

Отдельная команда `conveyor-recover` лучше, чем расширение `top.py conveyor`, потому что `conveyor` сейчас означает routine supervisor status, а recover - recovery audit после reset/hang/UI mismatch. Смешивание сделает обычный статус шумнее и может подтолкнуть агентов к преждевременным repair-действиям.

## Risks

- Если wrapper будет вызывать `tools/conveyor.py recover` через `_run` и в `--json` режиме, JSON получит human-заголовки `===== conveyor recover =====`; поэтому для `--json` нужен чистый `subprocess.run` как в `cmd_conveyor`.
- Если top-команда начнет автоматически выполнять suggestions из recover, она нарушит advisory-boundary и может неверно `land`, `dismiss`, `ship` или `tick` workflow.
- Если `--limit` не прокинуть, большой outbox может дать слишком шумный sample unreferenced reports.
- Если добавить recover внутрь `top.py conveyor`, routine status и recovery audit смешаются; агенты могут чаще воспринимать informational findings как блокер.
- Если забыть кнопку в `_BUTTONS`, команда появится технически, но не станет discoverable в верхней панели.
- Если поменять `tools/conveyor.py`, возрастет blast radius. Для этой build-задачи достаточно `tools/top.py`.

## Needed tests and verification commands

Минимальные команды для build-задачи после внесения кода:

```powershell
python tools/top.py conveyor-recover --json
python tools/top.py conveyor-recover --limit 3
python tools/top.py buttons --json
python tools/conveyor.py recover --json --limit 3
python tools/validate.py
python tools/generate.py --check
```

Что проверить вручную в выводе:

- `python tools/top.py conveyor-recover --json` печатает чистый JSON без `===== ... =====`.
- JSON содержит `schema: conveyor_recover.v1` и `mutates: false`.
- `--limit 3` ограничивает sample для `unreferenced-outbox-reports`.
- `buttons --json` содержит новый button id `conveyor-recover` с `effect: read-only`.
- Ни одна команда не меняет `logs/conveyor.json`, pipeline state, Git index или workflow states.

Checks:

```powershell
python tools/instructions.py check-report queues/outbox/2026-06-24-top-conveyor-recover-integration-review.md
python tools/result_intake.py classify queues/outbox/2026-06-24-top-conveyor-recover-integration-review.md --json
```

## Applied instructions

- `AGENTS.md`: работал в режиме, совместимом с `PROTOCOL.md`; не удалял чужие сообщения, не переписывал историю, не менял финальные решения.
- Пользовательское ограничение read-only/outbox-only: не менял код, docs, tasks, decisions, logs или Git; единственная запись - этот отчет в `queues/outbox/2026-06-24-top-conveyor-recover-integration-review.md`.
- `PROTOCOL.md`: результат автоматической работы оставлен в `queues/outbox/` как proposed review, без переноса в канонические файлы.
- `queues/outbox/2026-06-24-conveyor-recover-adoption-review.md`: учтена рекомендация держать recover отдельной read-only top-layer command и не делать automatic repair.
