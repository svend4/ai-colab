---
id: document-synthesis-mechanism-2026-06-24
type: methodology
status: proposed
owner: codex
date: 2026-06-24
last_verified: 2026-06-25
related:
  - decisions/D-017.md
  - decisions/D-018.md
  - tools/variants.py
  - tools/synthesis_helper.py
  - tools/doc_synthesis.py
  - docs/architecture-core-documents-synthesis-2026-06-24.md
  - streams/architecture-core/divergence.md
---

# Механизм сверки нескольких документов: consensus / near-consensus / divergence

## 00. File card

**Purpose.** Описать, какой механизм уже есть для сравнения нескольких вариантов документов от разных агентов/людей, чего ему не хватало и как теперь его применять.

**Status.** `proposed`: методология уже применена к корпусу `architecture-core`, но не является accepted policy без review.

**Audience.** Люди, Codex, Claude, Lagrange и другие агенты, которые пишут параллельные мнения, обзоры и архитектурные предложения.

## 01. Что уже было в проекте

В проекте уже есть хорошая база:

1. `decisions/D-017.md` — дубликат очереди не равен варианту решения; содержательные варианты надо сохранять.
2. `decisions/D-018.md` — спорные решения проходят котёл: техническая и гуманитарная перепроверка, агенты предлагают, человек утверждает.
3. `streams/` — место для ручейков/форков и semi-commit формата.
4. `tools/variants.py` — находит зарегистрированные варианты по темам.
5. `tools/synthesis_helper.py` — строит skeleton для тем, где уже есть несколько stream-вариантов.

Этого достаточно, когда документы заранее оформлены как streams.

## 02. Пробел

Текущий вопрос сложнее: часть вариантов уже лежит как обычные `docs/*.md` и `queues/outbox/*.md`, а не как `streams/<topic>/.../STREAM.md`.

Старый механизм плохо решал такие случаи:

1. `variants.py` видит только известные места и пары.
2. `synthesis_helper.py` требует topic из `variants.py`.
3. Если разные агенты написали обычные отчёты, они не становятся automatically synthesis candidates.
4. Нельзя быстро посчитать: сколько документов, какие общие темы, какие near-consensus, какие divergence.

## 03. Доработка

Добавлен read-only инструмент:

```powershell
python tools\doc_synthesis.py candidates architecture-core
python tools\doc_synthesis.py scan architecture-core
python tools\doc_synthesis.py scan architecture-core --with-streams
python tools\doc_synthesis.py scan architecture-core --out docs\architecture-core-documents-synthesis-2026-06-24.md
python tools\top.py synthesize-docs architecture-core --json
python tools\top.py synthesize-docs architecture-core --out docs\architecture-core-documents-synthesis-2026-06-24.md --with-streams
python tools\doc_synthesis.py scan custom --out report.md file1.md file2.md ...
python tools\doc_synthesis.py scan doc-synthesis-stream-corpus --json
python tools\top.py synthesize-docs doc-synthesis-stream-corpus --json
python tools\top.py synthesize-docs doc-synthesis-stream-corpus --ready-only --json
```

Он делает первый машинный проход:

1. собирает corpus документов;
2. считает повторяющиеся темы по keyword buckets;
3. выделяет сильный consensus;
4. выделяет near-consensus;
5. выделяет minority useful ideas;
6. создаёт список divergence topics;
7. извлекает вопросительные и proposal snippets;
8. сохраняет proposed synthesis;
9. показывает source-line evidence как `file:line`;
10. по явному `--with-streams` создаёт stream scaffold без перезаписи ручного `streams/<topic>/divergence.md`;
11. для custom topic без файлов читает `streams/<topic>/*/STREAM.md` как corpus, если такие stream-пакеты уже есть.

Важно: инструмент не принимает решения и не заменяет человека. Это intake/scaffold для котла.
## 04. Трёхслойный результат

### 04.01. Верхний слой

Туда попадают пункты, которые встречаются в большинстве документов. Их можно переносить в clean mainline или manuals.

Пример из текущего запуска:

- верхний фасад команд;
- evidence/assurance;
- execute OFF;
- workflow-conveyor;
- synthesis/divergence;
- worktree/merge-gate;
- metadata/indexes.

### 04.02. Средний слой

Туда попадают похожие пункты, где смысл близкий, но формат ещё требует нормализации.

Пример: universal core + portals оказался только 4/10 по keyword scan. Это не значит, что идея слабая: D-016 accepted. Это значит, что не все новые документы явно повторяют терминологию `core/portal`, и нужно улучшить propagation/onboarding.

### 04.03. Нижний слой разногласий

Спорные пункты не надо скрывать в середине общего документа. Их нужно держать отдельно:

```text
streams/architecture-core/divergence.md
```

Там каждый спор получает:

1. ID;
2. формулировку;
3. варианты;
4. почему это важно;
5. текущую рекомендацию;
6. что нужно для accepted.

## 05. Как применять вручную

1. Собрать список документов-вариантов.
2. Запустить `doc_synthesis.py scan custom` или тематический preset.
3. Проверить corpus: не попал ли мусорный runtime report.
4. Верхний consensus перенести в clean doc.
5. Near-consensus превратить в tasks или proposed decisions.
6. Divergence перенести в `streams/<topic>/divergence.md`.
7. Outbox-сообщением пригласить других агентов ответить именно по divergence IDs, а не переписывать весь mainline.

## 06. Статус v2

Реализовано в T-218:

1. `tools/doc_synthesis.py candidates <topic>` — поиск документов-кандидатов по теме.
2. Source-line evidence — темы и полосы получают проверяемые refs вида `file:line`.
3. `--with-streams` — создаёт `streams/<topic>/README.md` и `divergence.md`, а если ручные файлы уже существуют, пишет безопасные `README.generated.md` / `divergence.generated.md`.
4. `tools/top.py synthesize-docs <topic>` — верхняя обёртка для людей и агентов.
5. `tools/top.py cauldron-lanes <topic>` — короткая команда для двух полос `ratify-build` / `divergence-detail`.

Что ещё улучшить позже:

1. Добавить semantic fingerprint вместо простых keywords.
2. Связать `doc_synthesis.py` с `variants.py`, чтобы обычные docs могли временно регистрироваться как variants.
3. Добавить ranking-политику для candidates: fresh/manual/preset/agent-proposed.
4. Добавить diff-mode: сравнивать два synthesis-прогона и показывать, какие темы перешли между полосами.

## 07. Applied status

Этот механизм уже применён к 10 документам по архитектуре:

```powershell
python tools\top.py synthesize-docs architecture-core --out docs\architecture-core-documents-synthesis-2026-06-24.md --with-streams
```

Результат:

- documents scanned: 10;
- consensus themes: 9;
- near-consensus themes: 1;
- minority useful themes: 1;
- divergences listed: 7;
- question snippets: 26;
- proposal snippets: 43;
- stream scaffolds: `streams/architecture-core/README.generated.md`, `streams/architecture-core/divergence.generated.md`.
## 08. Реализация T-255: stream corpus

T-255 добавляет мост между independent-first streams и document synthesis:

1. `tools/doc_synthesis.py resolve_files()` сначала уважает явно переданные файлы.
2. `architecture-core` без файлов остаётся старым preset, чтобы не ломать существующий manual workflow.
3. Для custom topic без файлов вызывается `stream_topic_files(topic)`.
4. `stream_topic_files(topic)` ищет `STREAM.md` внутри `streams/<topic>/...` и возвращает отсортированный список repo-relative путей.
5. Если ни files, ни stream corpus не найдены, команда падает с понятной подсказкой: нужен файл или `streams/<topic>/*/STREAM.md`.

Проверочный сценарий:

```powershell
python tools\top.py variant-start codex doc-synthesis-stream-corpus --task T-255
python tools\stream.py mark 20260625-1756-codex ready-for-synthesis "variant completed"
python tools\doc_synthesis.py scan doc-synthesis-stream-corpus --json
python tools\top.py synthesize-docs doc-synthesis-stream-corpus --json
python tools\top.py synthesize-docs doc-synthesis-stream-corpus --ready-only --json
```

Это не auto-adoption. Результат остаётся `status: proposed` и идёт в котёл: consensus можно переносить дальше, divergence остаётся отдельной полосой.
## 09. Реализация T-256: ready-only corpus

T-256 добавляет фильтр зрелости для stream corpus:

1. `--ready-only` применяется только когда пользователь не передал явный список files.
2. Готовым считается stream с `status: ready-for-synthesis` или `synthesis_ready: true`.
3. Proposed/developing streams остаются в `streams/`, но не попадают в ready-only synthesis.
4. Если готовых stream-пакетов нет, команда падает с явной подсказкой, а не строит пустой synthesis.

Команды:

```powershell
python tools\doc_synthesis.py scan doc-synthesis-stream-corpus --ready-only --json
python tools\top.py synthesize-docs doc-synthesis-stream-corpus --ready-only --json
```

Это промежуточный слой между свободной генерацией вариантов и строгим adoption: писать можно много, синтезировать для строительства нужно только дозревшее.