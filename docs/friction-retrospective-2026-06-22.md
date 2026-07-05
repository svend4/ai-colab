# Friction retrospective — 2026-06-22

Связано: `T-150`, `T-147`, `T-149`, `D-017`, `D-019`, `D-021`, `D-022`, `Q-015`, `docs/friction-ledger.md`, `docs/friction-playbook.md`, `tools/friction.py`.

## Краткий вывод

Проект уже прошёл несколько повторяющихся классов трения. Это не случайные ошибки, а устойчивые архетипы: Windows/runtime, shared-worktree/git, pipeline/claims, generated-index drift, stream lifecycle, external-code sandbox, skill/docs drift. Каждый архетип сначала решался вручную, затем был описан в документах, затем частично перенесён в инструменты. `T-150` переводит следующий слой в автоматизацию: появляется `tools/friction.py`, который не чинит репозиторий сам, а быстро показывает симптомы, доказательства и рецепт.

Главный инженерный вывод: автоматизировать нужно не “большого автономного диспетчера”, а короткие проверяемые detector/guard слои вокруг уже доказанных процедур. Автоисправление пока опаснее диагностики, потому что в shared workspace есть чужие half-done изменения, generated indexes и governance-артефакты.

## Метод исследования

Проверка выполнена по четырём источникам:

1. Поиск по репозиторию через `rg` по ключевым симптомам: `PermissionError`, `TEMP`, `index.lock`, `commit_lock`, `apply_patch`, `PowerShell`, `UTF-8`, `stale`, `volatile`, `placeholder`, `doing without active claim`, `stream`, `worktree`, `svend4`, `sandbox`, `drift`.
2. Повторное чтение канонических документов: `docs/friction-ledger.md`, `docs/friction-playbook.md`, `docs/friction-complaints-suggestions.md`, `docs/parallel-work-policy.md`, `docs/commit-stream-policy.md`, `docs/runtime-recovery-playbook.md`, `docs/external-code-sandbox.md`.
3. Проверка текущего состояния инструментами: `python tools/friction.py status`, `python tools/top.py friction`, `python tools/validate.py`, `python tools/generate.py --check`, `python tools/stream.py check`.
4. Саморефлексия по текущей задаче: `apply_patch` снова упал в Windows sandbox; первый вариант `test_friction.py` снова поймал `%TEMP% PermissionError`; `friction status` выявил unrelated dirty streams и skill-link drift.

## Хронология повторяющихся проблем

### Этап 1. Markdown-полилог и первые горячие файлы

Первичная идея была правильная: для многих людей и агентов нужен не монолог, а файловый форум. Markdown удобен людям, JSON/front-matter удобен скриптам. Но общий файл быстро становится горячей точкой, поэтому проект перешёл к шардированию: `tasks/*.md`, `questions/*.md`, `decisions/*.md`, `queues/outbox/`, `streams/`, generated indexes.

Вывод: Markdown остаётся хорошим человеческим слоем, но каждый рабочий объект должен иметь отдельный файл и машинный front-matter. Общие таблицы должны генерироваться.

### Этап 2. Runtime/PowerShell/TEMP

Сначала проект не мог уверенно прогонять Python, validators и driver tests. Были зависания, mojibake, `py --version` timeout, `Stop-Job -Force` несовместимость Windows PowerShell, `tempfile.mkdtemp()` создавал каталоги без последующего доступа на запись.

Где зафиксировано:

- `docs/runtime-recovery-playbook.md`;
- `docs/runtime-diagnostics.md`;
- `docs/powershell-utf8-output.md`;
- `docs/files-mcp-acceptance-blocked-2026-06-21.md`;
- `docs/workbench-acceptance-result-2026-06-21.md`;
- `queues/done/T-070.done.md`, `T-071`, `T-072`, `T-073`, `T-078`, `T-079`, `T-081`.

Ручное решение стало стабильным: короткие команды, таймауты, UTF-8 setup, `tmp-work/` или `C:\tmp`, `drivers/test_tmp.py`, `stdin=subprocess.DEVNULL` для subprocess.

В `T-150` этот архетип повторился буквально: первый `tools/tests/test_friction.py` использовал `tempfile.mkdtemp()` и упал с `PermissionError`. Исправление: тестовый root выбирается из `C:\tmp` или repo `tmp-work/`.

### Этап 3. Git/index.lock/shared-worktree

Когда несколько агентов работают в одном дереве, `git add -A` и обычный commit становятся опасными: можно случайно включить чужую half-done работу или stale generated indexes. Появились `commit_lock.py`, selective-add, `merge_gate.py`, `flow.py --worktree`, `cohort guard`, `D-019`, `D-021`, `D-022`.

Где зафиксировано:

- `docs/commit-stream-policy.md`;
- `docs/parallel-work-policy.md`;
- `docs/parallel-streams-problems-review-2026-06-22.md`;
- `tasks/T-135.md`, `T-136`, `T-143`, `T-146`, `T-148`;
- `tools/commit_lock.py`, `tools/worktree.py`, `tools/merge_gate.py`, `tools/cohort.py`.

Ручное решение: `commit_lock` сериализует commit window, но не защищает от чужих файлов. Поэтому второе правило важнее первого: stage only explicit files. Если есть hot files, stale generated indexes, foreign half-done или ожидание чужого commit — использовать Level 1 worktree.

### Этап 4. Pipeline/claims/placeholders/orphans

Котёл задач сделал работу динамичной, но появились новые дефекты: placeholder-задачи попадали в not-ready, `doing` без claim выглядело занятой навсегда, `pipeline.py next` мог взять не ту задачу, если агент имел в виду конкретный T-id.

Где зафиксировано:

- `docs/pipeline-placeholder-gating.md`;
- `docs/pipeline-orphan-doing-detection.md`;
- `docs/stale-work-cleanup-policy-2026-06-21.md`;
- `docs/friction-complaints-suggestions.md`;
- `tasks/T-067.md`, `T-068`, `T-091`.

Ручное решение: placeholder нужно заполнить до claim; orphan doing показывать как проблему, но не закрывать молча; если нужен конкретный T-id, не вызывать `next` вслепую. Следующая автоматизация была реализована в T-152: targeted claim (`pipeline.py claim <agent> <T-id>` или `top.py take <agent> <T-id>`).

### Этап 5. Docs/generated-index drift

После шардирования появилось другое трение: source-файлы могут быть актуальны, а generated indexes устарели. Или наоборот: generated index может втянуть чужой half-done source. Поэтому появились `generate.py --check`, `validate.py`, `drift_check.py`, `top.py health`, pre-commit hook.

Где зафиксировано:

- `tools/generate.py`, `tools/validate.py`, `tools/drift_check.py`, `tools/merge_gate.py`;
- `tasks/T-120.md`, `T-126`, `T-130`, `T-131`;
- `queues/done/T-120.done.md`, `T-130.done.md`.

Ручное решение: сначала понять источник drift, потом регенерировать только вместе со своими source-файлами. Не коммитить смешанный индекс из чужой работы.

### Этап 6. Streams/fork-and-synthesize

Проблема дублей была переосмыслена: если два агента решают одну тему независимо, второй вариант не должен автоматически считаться дубликатом. Нужен semi-commit stream: вариант, доказательства, условия adoption, затем синтез.

Где зафиксировано:

- `D-017`, `D-018`, `D-019`, `D-021`, `D-022`;
- `docs/commit-stream-policy.md`;
- `streams/README.md`;
- `tools/stream.py`, `tools/variants.py`, `tools/synthesis_helper.py`;
- `tasks/T-135.md`, `T-136`, `T-137`, `T-143`, `T-146`.

Текущее состояние не идеально: `python tools/stream.py check` во время `T-150` показал broken commit-policy streams без `agent`/`created`. Значит lifecycle уже есть, но старые stream-пакеты нужно довести до схемы или закрыть отдельной cleanup-задачей.

### Этап 7. External code / svend4 / sandbox

Старый долг `svend4` был важным концептуально: внешний код нельзя просто запускать на Windows host. Проект правильно сделал универсальную песочницу, не привязанную к одному профилю: `sandbox/`, `docs/external-code-sandbox.md`, `docs/execute-sandbox-preflight.md`, `tools/sandbox.py`, `tools/sandbox_intake_demo.py`.

Где зафиксировано:

- `docs/external-code-sandbox.md`;
- `docs/execute-sandbox-preflight.md`;
- `docs/workspace-pyramid-levels.md`;
- `tasks/T-020.md`, `T-114`, `T-134`, `T-137`;
- `D-020`, `D-021`.

Вывод: read-only intake работает, execute остаётся закрытым до отдельного accepted decision и реальной изоляции. Это не торможение, а safety boundary.

### Этап 8. Skill/docs/tool drift

После появления skill `repo-friction-playbook` возник новый риск: skill может стать вторым источником правды. Поэтому правильная модель: skill короткий, указывает на docs и tools, а канон остаётся в `docs/friction-*`.

В `T-150` `friction status` нашёл, что skill ещё не упоминает `tools/friction.py`. Это не критическая ошибка, но хороший пример F-018: когда появляется новый tool, нужно синхронизировать skill.

## Сводная карта архетипов

| ID | Архетип | Доказательства в репозитории | Оценка повторов | Ручное решение | Текущая автоматизация | Оставшийся долг |
|---|---|---|---:|---|---|---|
| F-001 | `apply_patch` Windows sandbox | текущие Codex-правки, `docs/friction-ledger.md` | 4+ | UTF-8 PowerShell fallback внутри workspace | playbook/skill | отдельный safe writer пока не нужен |
| F-002 | PowerShell mojibake | `docs/powershell-utf8-output.md`, `T-071`, пользовательские выводы | 3+ | `chcp 65001`, explicit UTF-8 encoding | playbook | encoding roundtrip detector можно добавить позже |
| F-003 | runtime hangs | `T-039`, `T-065`, `T-070`, `T-081`, MCP stdio docs | 6+ | short commands, timeouts, DEVNULL | runtime playbook, friction runtime identity | полноценный runtime smoke bundle |
| F-004 | TEMP PermissionError | `files`, `workbench`, `T-137`, `T-150` test failure | 6+ | `tmp-work/`, `C:\tmp`, `drivers/test_tmp.py` | `friction.py` temp probe, test pattern | общий helper для всех tests |
| F-005 | git lock/index.lock | `commit_lock.py`, `T-135`, `D-019` | 4+ | `commit_lock acquire/release` | `commit_lock.py`, `friction.py` lock status | tighter integration in ship/commit UI |
| F-006 | foreign half-done | D-022, T-146, current stream dirty signal | 8+ | selective-add, Level 1 worktree | `cohort guard`, `friction.py` dirty signal | ownership-aware dirty classification |
| F-007 | stale generated indexes | T-078, T-120, T-130, T-146 | 8+ | `generate --check`, source attribution | `generate.py`, `drift_check.py`, `friction.py` | identify stale owner automatically |
| F-008 | volatile snapshots | T-148, `LIVE.md`, `PIPELINE.md`, logs | 4+ | do not stage runtime views | `.gitignore`, `test_volatile.py`, `friction.py` | keep CI/preflight aware |
| F-009 | placeholder tasks | T-067, T-091 | 3+ | fill/retire before claim | pipeline gating, `friction.py` pipeline scan | none urgent |
| F-010 | doing without claim | T-068, T-091, T-020 cleanup | 3+ | report/reconcile, do not close silently | pipeline status, drift_check, `friction.py` | better stale owner report |
| F-011 | docs drift | T-120, T-126, T-130 | 4+ | validate/generate/drift_check | `top.py health`, `merge_gate.py`, `friction.py` | drift taxonomy by severity |
| F-012 | external sandbox | T-020, T-114, T-134, D-020/D-021 | constant | read-only intake, execute off | `sandbox.py`, `sandbox_intake_demo.py`, `friction.py` | execute sandbox decision/tools |
| F-013 | stream lifecycle | T-135/T-136/T-143/T-146, current `stream.py check` broken=2 | growing | `stream.py check`, adoption fields | `stream.py`, `friction.py` | cleanup legacy stream front-matter |
| F-014 | too many commands | top-layer docs, user feedback | 4+ | wrappers/buttons | `top.py`, `friction.py`, `top.py friction` | integrate friction into agent-start |
| F-015 | check→commit race | D-022, shared dirty tree | 4+ | re-check status before stage | `friction.py`, `cohort guard` | snapshot-based precommit audit |
| F-016 | wrong task via `next` | T-149 complaint | 1+ but high-risk | release own mistaken claim | `pipeline.py claim`, `top.py take` | реализовано T-152 |
| F-017 | approximate repeat counts | T-147/T-149/T-150 | systemic | estimate buckets | ledger/playbook | `logs/friction.jsonl` or `friction.py note` |
| F-018 | skill/docs drift | T-149/T-150 | 2+ | skill stays thin, docs canonical | `friction.py` skill link check | validator link check |
| F-019 | skill metadata UTF-8/YAML | T-149 metadata generation | 1+ | `PYTHONUTF8=1`, YAML block scalar | complaints/playbook | skill metadata lint |

## Что произошло прямо в T-150

Эта задача сама подтвердила несколько архетипов:

1. `apply_patch` снова отказался работать из-за Windows sandbox wrapper. Решение: documented PowerShell UTF-8 fallback.
2. `tools/tests/test_friction.py` сначала упал на `%TEMP% PermissionError`. Решение: тестовый temp root переведён на `C:\tmp` / repo `tmp-work/`.
3. `tools/friction.py status` выявил текущие dirty/generated файлы как ожидаемый сигнал активной работы.
4. `tools/friction.py status` выявил unrelated dirty `streams/*`, которые нельзя включать в T-150 commit без отдельного решения.
5. `tools/friction.py status` выявил F-018: skill ещё не знает про новый `tools/friction.py`.
6. `validate.py` сначала был красным, потому `T-150.topic` указывал на ещё не созданный retrospective doc. Решение: создать этот документ до финального validate.

Это важный результат: friction tool не просто теоретический. Он уже поймал реальные проблемы текущей сессии.

## Почему не auto-fix

Для этого репозитория auto-fix должен быть последним шагом, не первым. Причины:

- shared workspace содержит чужие незавершённые изменения;
- generated indexes могут отражать чужой source;
- stream/adoption/governance требуют человеческого или интеграторского решения;
- execute/sandbox границы нельзя “чинить” автоматически;
- commit-lock сериализует только commit window, но не доказывает ownership файлов.

Поэтому `tools/friction.py` сделан read-mostly: собрать симптомы, показать evidence, дать рецепт. Исключение — короткий temp probe внутри `tmp-work/`, который создаёт и удаляет probe-файл для проверки F-004.

## Новый автоматический слой T-150

Команды:

```powershell
python tools\friction.py status
python tools\friction.py status --json
python tools\friction.py recipe F-007
python tools\friction.py list
python tools\top.py friction
```

Что проверяется сейчас:

- Python/runtime identity;
- dirty shared tree;
- volatile runtime files in status and git tracking;
- `generate.py --check`;
- `commit_lock.py status`;
- `pipeline.py status` for placeholders/orphans;
- `drift_check.py`;
- `stream.py check`;
- project `tmp-work/` write probe;
- external-code sandbox contract;
- top-level friction button;
- skill links to canonical friction docs/tool.

## Рекомендации по дальнейшей разработке

### P0. Закрыть найденный stream hygiene debt

`tools/stream.py check` показывает legacy commit-policy streams с неполным front-matter. Нужно отдельной маленькой задачей:

- добавить недостающие `agent`/`created` или оформить terminal status;
- прогнать `python tools/stream.py check`;
- не смешивать это с T-150, потому это чужой governance/history слой.

### P0. Targeted claim

Статус после `T-152`: реализовано. Используйте `pipeline.py claim <agent> <T-id>` или `top.py take <agent> <T-id>`, чтобы агент мог взять конкретную ready-задачу без обходов через priority и без риска F-016.

### P0. Включить friction в старт агента

`top.py agent-start <agent>` должен печатать краткий friction summary или хотя бы совет `python tools/top.py friction`. Это уменьшит повторение старых ошибок у нового агента.

### P1. Ownership-aware dirty classifier

`friction.py` сейчас видит dirty files, но не знает ownership. Следующий слой:

- сверить dirty files с текущим task topic/files/outbox;
- выделить `mine`, `generated`, `volatile`, `foreign`, `unknown`;
- отдавать рекомендацию Level 0/Level 1 точнее.

### P1. `friction.py note` / `logs/friction.jsonl`

Повторы пока оцениваются вручную. Когда формат стабилизируется, добавить:

```powershell
python tools\friction.py note F-004 --where tools/tests/test_friction.py --result fixed-with-tmp-work
```

Это даст точные счётчики и поможет решать, когда playbook превращать в guard.

### P1. Skill/link validation

Добавить проверку в `validate.py` или отдельный `tools/skills_check.py` [planned]: skill `repo-friction-playbook` должен ссылаться на `docs/friction-ledger.md`, `docs/friction-playbook.md`, `docs/friction-complaints-suggestions.md`, `tools/friction.py`.

### P2. Safe writer вместо ручного PowerShell fallback

Если F-001 продолжит повторяться, можно сделать `tools/safe_write.py`:

- принимает relative path внутри workspace;
- запрещает выход за root;
- пишет UTF-8 без BOM;
- требует `--why` для audit;
- не удаляет и не перемещает файлы.

Но этот инструмент надо делать осторожно: он не должен стать обходом policy.

### P2. Friction dashboard in JSON

Для агентов `--json` уже есть. Следующий шаг — компактная JSON-сводка для `cohort.py board` или `top.py status`:

```json
{"recommendation":"LEVEL 1 OR SELECTIVE-ADD","warn":["F-006","F-013"],"fail":[]}
```

## Что я бы сделал иначе, если начинать сначала

1. Сразу ввёл бы `top.py friction` как обязательный preflight рядом с `status` и `health`.
2. Раньше перевёл бы tests на project-safe temp helper, потому `%TEMP%` в этой Windows-среде доказанно ненадёжен.
3. Раньше разделил бы “вариант решения” и “дубликат задачи”: stream lifecycle нужен до массового fork-and-synthesize.
4. Раньше сделал бы targeted claim, потому `next` хорош для общего котла, но неудобен для конкретной ручной задачи.
5. Оставил бы execute/svend4 строго закрытым, как сейчас. Это правильная граница.
6. Не стал бы строить большой “AI-OS router” до появления измеримых повторов. Тонкие detectors и wrappers уже дают больше пользы и меньше риска.

## Итоговая стадия

Концептуально система находится не на стадии “хаотичная папка”, а на стадии раннего самоуправляемого middleware: есть канон, индексы, pipeline, claims, decisions, stream variants, sandbox intake, top buttons, merge gates, skills, friction ledger. Технически это ещё не автономная multi-agent OS: нет полноценной изоляции execute, нет ownership-aware dirty classifier, нет exact friction counters, targeted claim реализован в T-152, stream legacy cleanup закрыт T-151.

Правильный следующий вектор: продолжать превращать повторяющиеся ручные процедуры в маленькие read-only detectors, затем в guard/gate только там, где риск подтверждён практикой.