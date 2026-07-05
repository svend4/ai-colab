# Протухшие stream'ы — эскалационный список для решения человека — 2026-07-05

> **Что это.** Исполнение пункта **C41 (подвариант C41-b)** плана волны 2
> (`reports/fix-wave2-plan-2026-07-02.md`) по находке аудита 2026-07-02
> (`reports/audit-claude-2026-07-02.json`, confirmed #41): 5 открытых stream-пакетов старше
> канонического порога 7 дней (P-11 «кладбище потоков», F-013) ждут решения adopt/reject/archive.
> Это **только эскалация списка** в котёл (Q-W2-11): никаких автоматических adopt/reject/archive
> не выполнено, статусы потоков не менялись, ревьюеры не назначались — все решения за человеком.
>
> **TTL-WARN здесь не дублируется**: семейство TTL-проверок закрывается пунктами C29-b/C30-b
> волны 2 (validate/gap_scan); при желании тем же порогом туда добавляются и streams.

## Как собран список

- `python tools/friction.py status` → WARN **F-013**: «Гигиена потоков (P-11): stale=16, broken=0 (порог 7д)» (вывод evidence обрезан до 8 строк — полный список ниже).
- `python tools/stream.py check --max-age-days 7 --json` → полный machine-readable список (16 stale на 2026-07-05, broken=0, incomplete_ready=0).
- Front-matter всех 5 потоков находки проверен чтением STREAM.md; статусы связанных объектов (T-136, T-146, T-225, Q-015, D-019, D-021, D-022) проверены по файлам канона.

**Нюанс порогов (зафиксирован ещё вердиктом аудита).** Голый `python tools/stream.py check`
использует собственный дефолт **14 дней** (`tools/stream.py:241,431`) и на 2026-07-05 отвечает «OK»;
канонический порог **7 дней** (docs/parallel-work-policy.md, P-11) применяет `friction.py`
(`--stream-max-age-days=7` по умолчанию). Для воспроизведения находки нужно явно передавать
`--max-age-days 7`.

## Пять потоков находки C41 (аудит 2026-07-02)

| # | Stream (путь) | Топик | Статус | Владелец | Создан | Возраст на 07-02 | Возраст на 07-05 |
|---|---|---|---|---|---|---|---|
| 1 | `streams/commit-policy/2026-06-21-codex-t136-synthesis/STREAM.md` | commit-policy | **ready-for-review** | codex | 2026-06-21 | 11д | 14д |
| 2 | `streams/commit-policy/20260622-0555-codex/STREAM.md` | commit-policy | proposed | codex | 2026-06-22 | 10д | 13д |
| 3 | `streams/agent-onboarding/20260624-0857-antigravity/STREAM.md` | agent-onboarding | proposed | antigravity | 2026-06-24 | 8д | 11д |
| 4 | `streams/architecture-core/20260624-0914-antigravity/STREAM.md` | architecture-core | proposed | antigravity | 2026-06-24 | 8д | 11д |
| 5 | `streams/repo-review/20260624-0902-antigravity/STREAM.md` | repo-review | proposed | antigravity | 2026-06-24 | 8д | 11д |

## Рекомендации по каждому потоку (решение — за человеком, Q-W2-11)

### 1. commit-policy / 2026-06-21-codex-t136-synthesis — рекомендация: **adopt (задним числом)** или archive «поглощён»

Синтез Codex по T-136 (Level 0 сейчас, streams как полу-формат, Level 1 worktree + merge-gate).
Содержание фактически **уже принято мейнлайном**: T-136 закрыта (`status: done`, «Закрыто
D-021/T-143 — Уровень 0 остаётся дефолтом, Уровень 1 worktree-streams принят как явный режим
--worktree»), D-019 (где этот синтез значился `adoption: proposed-in-D-019`) имеет
`status: superseded` → D-021, D-022. Статус `ready-for-review` завис: review по существу состоялся
через котёл (D-021/D-022), отдельный ревьюер, вероятно, уже не нужен — но подтвердить это должен
человек. Варианты: `stream.py adopt` с `adopted_commit` на коммит D-021 (честная фиксация
«вариант принят») либо archive с пометкой «поглощён D-021/D-022».

### 2. commit-policy / 20260622-0555-codex — рекомендация: **adopt (задним числом)** или archive «поглощён»

Предложение «Level 1 worktree обязателен по триггерам» (чужие source-файлы, красный
`generate.py --check` из-за чужой работы, hot files, явная параллельная работа, невозможность
отделить свои изменения). Связанный Q-015 имеет `status: answered` с outcome «Принят **D-022** —
вариант B; Level 1 worktree обязателен по триггерам…» — то есть предложение потока принято
практически дословно. Варианты: `stream.py adopt` с `adopted_commit` на коммит D-022 либо archive
с пометкой «поглощён D-022».

### 3. agent-onboarding / 20260624-0857-antigravity — рекомендация: **archive** (перед этим при желании спасти тезис)

Эссе «Ядро как LLM-OS» для онбординга. Секция «Вариант» — незаполненный шаблонный placeholder,
patch/evidence нет, follow-up работ не породил. Как stream (вариант к adoption) пакет несостоятелен;
как текст — возможно, ценен. Варианты: archive как есть; если человек считает тезис «LLM-OS вместо
папки со скриптами» полезным для онбординга — сначала перенести суть в топик agent-onboarding или
docs (например, рядом с `docs/agent-quickstart.md`), затем archive.

### 4. architecture-core / 20260624-0914-antigravity — рекомендация: **adopt после ратификации вердиктов** (не архивировать до решения)

Deliverable закрытой T-225 (`status: done`): анализ и предлагаемые вердикты по DVG-001
(**logical-collab** — не переносить L3 физически в `collab/`) и DVG-004 (**shared-tools-only** —
только общий `tools/`). Сам поток прямо просит: «Прошу других агентов и человека высказаться…или
ратифицировать». Это единственный из пяти, где **ждёт содержательное решение**, а не гигиена:
человеку/котлу нужно ратифицировать (или отклонить) оба вердикта, после чего adopt (с фиксацией
исхода в decision/topic) или reject. До ратификации архивировать не стоит — потеряется точка
принятия решения.

### 5. repo-review / 20260624-0902-antigravity — рекомендация: **archive** с пометкой «Этап 1 реализован»

Приоритизация «Fencing прежде фантомных блокеров». Этап 1 (строгая проверка `claim_id` в
`tools/pipeline.py done/fail`) **уже реализован**: fencing-token проверяется в `_check_holder`
(`tools/pipeline.py`, «claim_id не совпадает (перехвачен/протух)…»). Этап 2 (зачистка фантомных
блокеров / audit устаревших задач) частично покрывается TTL-семейством волны 2 (C29-b/C30-b —
WARN на залежавшиеся объекты). Варианты: archive с пометкой «Этап 1 реализован, Этап 2 → TTL-WARN
C29-b/C30-b»; если человек хочет отдельную зачистку фантомных блокеров как работу — при разборе
завести T-задачу и сослаться на этот поток.

## Контекст на 2026-07-05: порог 7д теперь ловит 16 потоков

После аудита (2026-07-02) порог 7 дней пересекли ещё **11 потоков**, все созданы 2026-06-25 в ходе
конвейера вариантов и все в статусе `ready-for-synthesis` — то есть ждут **синтеза**, а не
adopt/reject/archive по отдельности. Они **не входят в находку C41**, но относятся к тому же
решению по гигиене потоков (Q-W2-11), поэтому перечислены для полноты:

| Stream (путь) | Топик | Статус | Владелец | Возраст на 07-05 |
|---|---|---|---|---|
| `streams/code-variant-draft-manager/20260625-1942-codex/STREAM.md` | code-variant-draft-manager | ready-for-synthesis | codex | 10д |
| `streams/code-variant-sandbox/20260625-1818-codex/STREAM.md` | code-variant-sandbox | ready-for-synthesis | codex | 10д |
| `streams/doc-synthesis-stream-corpus/20260625-1756-codex/STREAM.md` | doc-synthesis-stream-corpus | ready-for-synthesis | codex | 10д |
| `streams/independent-first-process-guard/20260625-2142-codex/STREAM.md` | independent-first-process-guard | ready-for-synthesis | codex | 10д |
| `streams/info-draft-manager/20260625-2013-codex/STREAM.md` | info-draft-manager | ready-for-synthesis | codex | 10д |
| `streams/stream-readiness-lint/20260625-1731-codex/STREAM.md` | stream-readiness-lint | ready-for-synthesis | codex | 10д |
| `streams/variant-batch-barrier/20260625-1913-codex/STREAM.md` | variant-batch-barrier | ready-for-synthesis | codex | 10д |
| `streams/variant-batch-barrier/20260625-subagent-worker/STREAM.md` | variant-batch-barrier | ready-for-synthesis | subagent-worker | 10д |
| `streams/variant-start-order-policy/20260625-1839-codex/STREAM.md` | variant-start-order-policy | ready-for-synthesis | codex | 10д |
| `streams/variant-start-order-policy/20260625-subagent-worker/STREAM.md` | variant-start-order-policy | ready-for-synthesis | subagent-worker | 10д |
| `streams/variant-start-top/20260625-1743-codex/STREAM.md` | variant-start-top | ready-for-synthesis | codex | 10д |

Рекомендация по этой группе (тоже за человеком): решить судьбу синтез-конвейера 2026-06-25 одним
пакетным решением (запустить синтез по топикам / отложить с явной пометкой), а не разбирать
по одному; в паре топиков по два конкурирующих потока (variant-batch-barrier,
variant-start-order-policy) — это вход для синтеза, не дубликат.

## Что НЕ сделано (намеренно, по C41-b)

- Ни один поток не переведён в adopted/rejected/archived; `stream.py archive --apply`
  (auto-archive P16) **не запускался**.
- Ревьюер для ready-for-review потока не назначался (процессное действие человека).
- TTL-WARN на streams в validate не добавлялся отдельно — закрывается семейством C29-b/C30-b.

**Следующий шаг:** человек проходит по 5 строкам таблицы (плюс пакетное решение по 11 потокам
синтез-конвейера) и фиксирует adopt/reject/archive по каждому — Q-W2-11.
