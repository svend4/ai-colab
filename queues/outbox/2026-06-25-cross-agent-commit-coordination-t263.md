---
id: 2026-06-25-cross-agent-commit-coordination-t263
type: report
task: T-263
agent: codex
status: proposed
created: 2026-06-25
participants: Codex, Averroes, Kierkegaard
related: [T-244, T-263, D-017, D-018, D-027, D-028, Q-023]
---

# T-263 — cross-agent commit coordination before future git commit

## 1. Цель

Подготовить накопленные изменения к будущему безопасному commit. Эта задача не делает commit. Она разделяет работу нескольких агентов и тем на группы: что можно фиксировать как готовое, что требует synthesis/human review, что является runtime-шумом или чужой незавершённой работой.

Применён принцип D-017/D-018: консенсус сохраняется отдельно, разногласия не стираются, proposed governance не превращается в accepted без человека или назначенного integrator.

## 2. Участники сверки

- Codex: снял локальный pipeline/git/stream/generated статус и подготовил этот synthesis.
- Averroes: read-only аудит stream-пакетов, outbox-отчётов, task-файлов и готовности к adoption.
- Kierkegaard: read-only аудит commit-readiness, staging рисков и batch-структуры.

Оба независимых аудита сошлись в главном выводе: один широкий commit сейчас опасен.

## 3. Машинное состояние на момент сверки

- Pipeline after closure: in progress = 0, ready = 0, blocked = 0.
- T-244 through T-262: все `done`.
- `T-263`: closed as `done`; done marker created by `pipeline.py done`.
- `stream.py check --max-age-days 7 --json`: `stale=[]`, `broken=[]`, `incomplete_ready=[]`.
- `validate.py`: `OK=12 WARN=0 ERROR=0`.
- `generate.py --check`: initially stale after creating T-263; resolved by `python tools\\generate.py`, final check OK.
- Claims: старый `queues/claimed/T-202.claim.md` остаётся legacy/stale candidate; не трогать широким commit/cleanup без отдельной проверки. T-263 claim was consumed by pipeline done.

Dirty tree по верхним папкам на момент аудита:

| Группа | Файлов |
|---|---:|
| `queues/` | 192 |
| `tools/` | 28 |
| `tasks/` | 20 |
| `streams/` | 12 |
| `docs/` | 8 |
| `sandbox/` | 7 |
| `topics/` | 6 |
| `reports/` | 4 |
| `decisions/` | 2 |
| `questions/` | 1 |
| `indexes/` | 1 |
| root/generated/support | several |

Вывод: `git add -A` запрещён. Нужен selective-add по явным спискам файлов или hunk staging для `tools/top.py` и других hot-files.

## 4. Консенсус между аудитами

1. Один общий commit сейчас нельзя делать.
2. T-244 through T-262 по задачам закрыты, но закрытая task не означает accepted governance.
3. `D-027` и `D-028` остаются `proposed`; их можно сохранить как proposed material, но нельзя объявлять принятыми решениями.
4. `Q-023` остаётся `open`, пока человек или appointed integrator не примет матрицу полномочий.
5. `streams/` сейчас технически чисты по `stream.py check`, но adoption/superseded/rejected статусы ещё требуют synthesis/human review.
6. Draft-code и info-draft должны оставаться evidence-зонами, не mainline canon.
7. Старые массовые изменения old outbox reports dated 2026-06-19 through 2026-06-24 похожи на отдельную bulk-нормализацию; не смешивать с кодовыми commit.
8. audit JSON/log files, `test_guard.md`, and `.md.test` files — не включать без отдельной причины.

## 5. Разногласия и открытые вопросы

### 5.1 Consensus по смыслу, а не по счёту

Claude merge-side report поднимает важный вопрос: текущий consensus-инструмент местами ориентирован на `>=2 documents`, но новая политика требует consensus by meaning/evidence, а не только по количеству совпадений. Это кандидат на отдельную задачу и, возможно, новое решение `D-029`.

### 5.2 Strictness independent-first guard

`T-262` добавил `tools/independent_first.py`, но ещё нужно решить, где guard становится strict:

- только advisory-команда;
- обязательный шаг перед `stream.py mark ready-for-synthesis`;
- часть `top.py variant-start` workflow;
- pre-synthesis gate в `doc_synthesis.py`.

### 5.3 Governance authority

`D-027` предлагает матрицу полномочий, но пока не accepted. До ратификации агент не должен сам принимать решения уровня accepted governance, execute sandbox, массовая санация истории, чужие commits.

### 5.4 Старый claim T-202

`queues/claimed/T-202.claim.md` существует, но pipeline сейчас показывает только T-263 в работе. Это похоже на stale/legacy claim. Нужна отдельная reconcile-проверка перед удалением или commit cleanup.

## 6. Рекомендуемые commit batches

### Batch A — T-244 CLI/help guard cleanup

Сохранять отдельно, если scope подтверждён:

- `tasks/T-244.md`;
- `queues/done/T-244.done.md`;
- удаление старого the old T-244 claim marker, если оно действительно результат закрытия;
- `queues/outbox/2026-06-24-t244-cli-help-guard-batch-1.md`;
- только связанные tool/test файлы T-244.

### Batch B — question tree / information refactoring

- `tools/question_tree.py`;
- `tools/test_question_tree.py`;
- `topics/information-refactoring-*.md`;
- question-tree outbox reports dated 2026-06-25;
- task files T-246 through T-249 и done-маркеры.

### Batch C — proposed agent approval governance

- `docs/agent-approval-matrix.md`;
- `decisions/D-027.md`;
- `questions/Q-023.md`;
- scout reports Planck/Huygens;
- `tasks/T-250.md` и done-маркер.

Commit message должен явно говорить `proposed`, не `accepted`.

### Batch D — triadic/fractal methodology and architecture notes

- `docs/triadic-fractal-methodology.md`;
- `queues/outbox/2026-06-25-triadic-golden-mean.md`;
- связанные topics/tasks around `T-251`.

Это conceptual batch, не смешивать с executable tool changes.

### Batch E — independent-first streams policy and guard

- `docs/independent-variant-stream-policy.md`;
- `decisions/D-028.md`;
- `tools/independent_first.py`;
- `tools/test_independent_first.py`;
- `streams/independent-first-process-guard/`;
- `queues/outbox/2026-06-25-independent-first-guard-t262.md`;
- related task files and done markers for `T-252`, `T-258`, `T-262`.

`D-028` stays proposed unless human accepts it.

### Batch F — stream/top/doc_synthesis implementation

- `tools/stream.py`;
- `tools/test_stream.py`;
- `tools/doc_synthesis.py`;
- `tools/test_doc_synthesis.py`;
- scoped parts of `tools/top.py`, `tools/test_top.py`;
- `docs/top-layer-command-groups.md`;
- stream evidence and outbox reports for T-253 through T-259.

Risk: `tools/top.py` contains several features at once. If possible, use hunk staging or one explicit integration commit.

### Batch G — draft-code and info-draft managers

- `tools/draft_code.py`, `tools/test_draft_code.py`, `queues/outbox/2026-06-25-draft-code-manager-t260.md`, `tasks/T-260.md`, done marker.
- `tools/info_draft.py`, `tools/test_info_draft.py`, `sandbox/info-drafts/README.md`, `sandbox/templates/info-draft-manifest.template.json`, `queues/outbox/2026-06-25-info-draft-manager-t261.md`, `tasks/T-261.md`, done marker.
- `sandbox/.gitignore` only if diff is scoped to this feature.

### Batch H — conveyor/action tracker and other high-risk tools

- `tools/conveyor.py`;
- `tools/action_tracker.py`;
- possibly `tools/top.py` integration;
- related reports and task files.

This batch needs focused diff review. Do not mix with governance docs.

### Batch I — bulk outbox/report normalization

The many modified old old outbox reports dated 2026-06-19 through 2026-06-24 files should be one separate normalization commit or no commit until reviewed. They are not part of T-263/T-262 implementation.

### Batch J — generated sync last

Only after selecting source files for a batch:

- `TASKS.md`;
- `index.json`;
- `indexes/tasks.md`;
- `system-capabilities.json`;
- other generated indexes only if regenerated from the same source batch.

Generated files should not reference uncommitted source task and tool files unless the commit intentionally includes those sources.

## 7. Explicit do-not-commit list for the next step

Do not include automatically:

- `tasks/T-263.md` before T-263 is done;
- T-263 former claim marker is already consumed by pipeline done;
- `queues/claimed/T-202.claim.md` before reconcile;
- audit JSON/log files;
- `test_guard.md`;
- .md.test files under outbox;
- old mass-modified `queues/outbox/*` unless doing Batch I;
- runtime logs/databases/snapshots unless explicitly required;
- any `accepted` status change for D-027/D-028 without human/integrator approval.

## 8. Pre-commit command set

Before any future commit batch:

```powershell
python tools\generate.py
python tools\validate.py
python tools\generate.py --check
python tools\stream.py check --max-age-days 7 --json
python tools\pipeline.py status
git diff --check -- <explicit-file-list>
```

For tool batches, also run relevant tests:

```powershell
python tools\test_question_tree.py
python tools\test_stream.py
python tools\test_doc_synthesis.py
python tools\test_top.py
python tools\test_draft_code.py
python tools\test_info_draft.py
python tools\test_independent_first.py
```

Use explicit staging:

```powershell
git add -- <file1> <file2> <file3>
```

Avoid:

```powershell
git add -A
git commit -a
```

## 9. Recommended next action

1. T-263 is now closed; keep this report as commit-coordination evidence.
2. Run final validate/generate/stream/pipeline checks.
3. Ask human/integrator which commit batch to save first.
4. Use `tools/commit_lock.py` or the accepted repository commit procedure for the selected batch only.
5. After each commit, rerun generated/check gates and proceed to the next batch.
## Applied instructions

- `AGENTS.md`: не удалять чужие сообщения, не переписывать историю, использовать `queues/outbox/` для результата автоматической работы.
- `PROTOCOL.md`: commit является mainline snapshot; при грязном workspace использовать explicit selective-add, streams и synthesis вместо широкого commit.
- `docs/commit-stream-policy.md`: не использовать `git add -A`; спорные варианты сначала сохранять как stream/evidence.
- `docs/parallel-work-policy.md`: при смешанных source/hot/generated изменениях commit должен идти через отдельный integration/selective flow.
- `docs/independent-variant-stream-policy.md`: consensus и divergence не смешивать; proposed decisions не переводить в accepted без человека или appointed integrator.
Checks:
- `python tools\instructions.py check-report queues\outbox\2026-06-25-cross-agent-commit-coordination-t263.md` — rerun after report formatting fixes.
- `python tools\validate.py` — OK=12 WARN=0 ERROR=0 before report formatting fixes.
- `python tools\generate.py --check` — OK after regeneration.
- `python tools\stream.py check --max-age-days 7 --json` — stale/broken/incomplete_ready empty.
- `git diff --check -- tasks\T-263.md queues\outbox\2026-06-25-cross-agent-commit-coordination-t263.md TASKS.md index.json indexes\tasks.md indexes\docs.md indexes\topics.md` — OK.
