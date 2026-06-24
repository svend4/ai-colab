---
id: cauldron-two-lane-board-2026-06-24
type: cauldron-board
status: proposed
owner: codex
date: 2026-06-24
last_verified: 2026-06-24
related:
  - docs/architecture-core-documents-synthesis-2026-06-24.md
  - docs/document-synthesis-mechanism-2026-06-24.md
  - streams/architecture-core/divergence.md
  - tasks/T-221.md
  - tasks/T-222.md
---

# Две рабочие полосы котла

## 00. File card

**Purpose.** Сделать видимыми две большие категории информации, которые попадают в котёл: уже сходящиеся пункты для ратификации/реализации и ещё спорные пункты для детализации.

**Status.** `proposed`: board основан на текущем synthesis-прогоне `architecture-core`, но не является accepted governance rule.

## 01. Модель

Котёл должен маркировать входящую информацию двумя большими lane:

```text
ratify-build       -> уже сходится, осталось ратифицировать и строить

divergence-detail  -> ещё не готово, нужны варианты, детали, доказательства
```

Это не разделение на “хорошее” и “плохое”. Это разделение по стадии зрелости.

## 02. Lane A — ratify-build

Условие попадания:

1. пункт встречается в нескольких документах/мнениях;
2. нет сильного открытого спора по смыслу;
3. можно сформулировать proposed ratification/build packet;
4. дальнейшая работа в основном инженерная: уточнить контракт, написать код/тест/обёртку, обновить docs.

Текущие пункты: 9.

| ID | Evidence | Следующий тип работы |
|---|---|---|
| evidence-assurance | 10/10 docs | ратифицировать evidence-required closure, затем усилить pipeline/assurance gates |
| safety-execute-off | 10/10 docs | подтвердить execute boundary, держать runner за human/backend gates |
| top-layer-facade | 10/10 docs | ратифицировать vocabulary команд, затем строить `top.py` wrapper/bundle |
| layered-pyramid | 9/10 docs | ратифицировать L1/L2/L3/L4 contract, затем folder/layer checks |
| metadata-indexes | 9/10 docs | уточнить scope metadata/indexes, затем file/folder/command index checks |
| parallel-worktree | 9/10 docs | уточнить triggers, затем улучшать guard/top recommendations |
| synthesis-divergence | 9/10 docs | закрепить split consensus/divergence, затем интегрировать с streams/top.py |
| workflow-conveyor | 9/10 docs | закрепить intake/verify/synthesize/integrate, затем связать с conveyor drain |
| recursive-self-improvement | 8/10 docs | закрепить advice activation path, затем friction/advice -> tools/guards |

Конвейерная задача: `T-221`.

## 03. Lane B — divergence-detail

Условие попадания:

1. пункт встречается слабо или непоследовательно;
2. есть открытые варианты выбора;
3. нужно больше доказательств, примеров, edge cases;
4. дальнейшая работа аналитическая: написать позицию, сравнить варианты, уточнить риски.

Текущие пункты: 9.

| ID | Evidence | Что делать |
|---|---|---|
| universal-core-portals | 4/10 docs | выяснить, почему D-016 плохо propagated в новых docs |
| file-section-cards | 2/10 docs | собрать варианты schema и решить coverage scope |
| DVG-001 | open divergence | physical collab vs logical L3 |
| DVG-002 | open divergence | new indexes folder vs existing generated files |
| DVG-003 | open divergence | file cards all vs L1/L2/policy-first |
| DVG-004 | open divergence | portal-local tools vs shared tools |
| DVG-005 | open divergence | GUI now vs CLI contract first |
| DVG-006 | open divergence | scale agents vs strengthen upper-layer first |
| DVG-007 | open divergence | runner done vs umbrella blocked until gates |

Конвейерная задача: `T-222`.

## 04. Как агент выбирает пропорцию

### 50/50

Использовать, если проекту нужно и двигаться вперёд, и не накапливать спорный долг.

Пример цикла:

1. взять один пункт `ratify-build`;
2. взять один пункт `divergence-detail`;
3. закрыть оба evidence/outbox;
4. повторить.

### 70/30

Использовать, если консенсуса уже много и надо быстрее строить код/обёртки.

Пример: два пункта `ratify-build`, один пункт `divergence-detail`.

### 30/70

Использовать, если архитектурные развилки тормозят реализацию.

Пример: один пункт `ratify-build`, два пункта `divergence-detail`.

### 100% ratify-build

Использовать только в короткое release/integration окно, когда спорные вопросы не блокируют выбранный build.

### 100% divergence-detail

Использовать, если основные build-решения заблокированы разногласиями или человеческим approval.

## 05. Правило перемещения между полосами

`divergence-detail -> ratify-build`, когда:

1. есть минимум две независимые позиции;
2. есть evidence и risks;
3. выбран один proposed вариант;
4. человек или котёл готов к ratification.

`ratify-build -> divergence-detail`, когда:

1. найден новый серьёзный риск;
2. другой агент принёс сильный альтернативный вариант;
3. implementation показывает, что consensus был поверхностным.

## 06. Механическое применение

Текущий инструмент:

```powershell
python tools\doc_synthesis.py scan architecture-core --json
python tools\doc_synthesis.py scan architecture-core --out docs\architecture-core-documents-synthesis-2026-06-24.md
```

Сейчас `doc_synthesis.py` уже отдаёт `lanes.ratify-build` и `lanes.divergence-detail` в JSON и печатает обе полосы в markdown.

## 07. Реализация v2

`T-218` закрыл следующий кодовый шаг:

1. `doc_synthesis.py candidates`;
2. `--with-streams`;
3. source-line evidence;
4. `top.py synthesize-docs`;
5. `top.py cauldron-lanes`.

Следующий уровень развития: semantic fingerprint, diff-mode между synthesis-прогонами и связь с `variants.py`.