# Sandbox workspaces

Disposable рабочие копии для экспериментов.

Формат:

```text
sandbox/workspaces/<source-id>/<run-id>/
```

Workspace не является canonical source. Его можно удалить и создать заново. Любой полезный результат должен быть вынесен в report.

Запуск кода из workspace запрещён до отдельного accepted decision и закрытого `execute-sandbox-preflight`.
