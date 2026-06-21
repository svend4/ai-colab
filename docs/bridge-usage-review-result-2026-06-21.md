---
id: bridge-usage-review-result-2026-06-21
title: Bridge usage review result — T-099
status: done
owner: Codex
related: tasks/T-099.md, tasks/T-098.md, docs/bridge-usage.md, tools/demo_bridge.py
---

# Bridge usage review result — T-099

Дата: 2026-06-21.

## Что проверено

Codex проверил `docs/bridge-usage.md`, созданный в T-098, как операционный usage-гайд среднего слоя.

Проверки:

```text
python tools\demo_bridge.py
```

Проходит: показывает files summarize/list/search, repo-runner inspect и workbench memory на `data/fixtures`.

```text
python drivers\mcp_sync_probe.py gateway --timeout 60
```

Проходит: `OK gateway tools=6`.

```text
python drivers\gateway\test_gateway.py
```

Проходит: `TESTS OK gateway: composition+redaction+confinement+audit`.

```text
python tools\validate.py
```

Проходит: `OK=9 WARN=0 ERROR=0`.

## Вывод

`docs/bridge-usage.md` можно добавлять в репозиторий как пользовательский операционный гайд. Он правильно разделяет:

- что работает сейчас: read-only drivers, gateway, workbench, demo, tests, audit;
- что в работе: устойчивый `tools/call` sync path, knowledge workflow, project skills;
- что нельзя делать без отдельной песочницы: execute/svend4.

Моё мнение: это полезный “первый вход” для людей и агентов. Концептуальные документы объясняют зачем, а `bridge-usage.md` отвечает как запустить и проверить.
