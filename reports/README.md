# Reports

`reports/` хранит воспроизводимые Markdown-отчеты, которые полезны людям и агентам при ревью состояния проекта.

Правила:

- Отчеты в `reports/*.md` можно версионировать в git.
- Runtime-базы и временные индексы не версионируются: `logs/*.db`, `tmp-work/`, локальные кеши.
- Отчет должен указывать команду или источник, из которого его можно повторить.
- Если отчет связан с задачей, добавляйте ссылку на task id и короткую запись в `queues/outbox/`.

Текущий первый сценарий: L6 `tools/knowledge.py report ... --out reports/<name>.md`.

## T-127 larger safe corpus

Воспроизводимые отчёты по большему безопасному corpus `docs/`:

```powershell
python tools\top.py knowledge docs --db tmp-work\t127-docs.db --query bridge --out reports\larger-safe-docs-bridge-report.md
python tools\top.py knowledge docs --db tmp-work\t127-docs.db --query pipeline --out reports\larger-safe-docs-pipeline-report.md
python tools\top.py report-diff reports\knowledge-corpus-report.md reports\larger-safe-docs-bridge-report.md --out reports\larger-safe-docs-bridge-vs-knowledge-corpus-diff.md
```

Артефакты:

- `larger-safe-docs-bridge-report.md`
- `larger-safe-docs-pipeline-report.md`
- `larger-safe-docs-bridge-vs-knowledge-corpus-diff.md`
- `larger-safe-docs-vs-knowledge-corpus-diff.md`
