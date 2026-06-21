# External code sandbox workspace

По запросу Stefan добавлен нейтральный `sandbox/` контур для внешнего кода и старых долгов вроде `T-020` / `svend4`.

Что добавлено:

- `docs/external-code-sandbox.md` — концепция универсальной sandbox workspace;
- `sandbox/README.md` — описание папки;
- `sandbox/.gitignore` — raw sources/workspaces/runs/reports не попадают в Git;
- `sandbox/inbox/README.md` — вход и manifests;
- `sandbox/sources/README.md` — quarantine для внешних источников;
- `sandbox/workspaces/README.md` — disposable рабочие копии;
- `sandbox/runs/README.md` — raw runtime logs будущих запусков;
- `sandbox/reports/README.md` — очищенные summaries;
- `sandbox/templates/external-source-manifest.template.json`;
- `sandbox/templates/sandbox-run-plan.template.json`.

Ключевое решение: `sandbox/` не привязан к `svend4`. Любой внешний код сначала регистрируется как source id,
проходит read-only inventory и только потом обсуждается. Execute остаётся запрещённым до отдельного accepted
decision и `docs/execute-sandbox-preflight.md`.

Моё мнение: это правильный способ снять старый блокер без нарушения safety. `svend4` перестаёт быть особым
ручным случаем и становится одним из внешних источников в универсальном процессе.
