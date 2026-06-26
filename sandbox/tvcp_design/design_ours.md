---
id: design-ours-textscene
type: design
angle: ours
title: "textscene — 2D полу-диффузионный канон-срез (интеграция гибрида TVCP в наш репо)"
related: [view.py, view_html.py, canon_index.py, thread_runner.py, crdt_merge.py, seq_merge.py]
date: 2026-06-26
---

# textscene — обращаем TVCP-пиксельную псевдо-диффузию на ТЕКСТ канона

**Угол E (ours):** не строим заново движок. Берём четыре уже работающих примитива TVCP
(`Grid.rect→upscaleBilinear→blur`, `scene.Op box/text`, raymeet `Region/Pose/ChatSync`,
`brain tvcp-ai/1`) и переносим их семантику с пикселей на ТЕКСТ, реализуя поверх НАШИХ
tools (`view`, `view_html`, `canon_index`, `thread_runner`, `crdt_merge`). Детерминированно,
офлайн, в терминале.

## 0. Ключевая аналогия (пиксель → смысл), построчно

| TVCP (пиксели) | textscene (текст/смысл) | где в нашем коде |
|---|---|---|
| `Grid.Rows` 12×8 цветных токенов = «сид» картинки | 2D-сетка **тем-токенов** (id канона + 1 строка-гист) = «сид» документа | новый `text_scene.py`, питается `canon_index.search` |
| `upscaleBilinear` (грубо→плотно) | **progressive disclosure**: гист → абзац → тело блока | уже есть: `view.assemble` live→frozen, `view_html` `<details>` |
| `blur` (3 прохода, сглаживание соседей) | «связное сглаживание»: соседние карточки делят общий контекст по рёбрам графа | `view.slice_ids` (BFS по related/[[links]]) |
| `DiffuseFrames`: noise→target, blur затухает по `alpha=i/(steps-1)` | **denoise-шаги**: «шум» (заголовки-плейсхолдеры) → проявление реального текста, детерминированно | новый `text_scene.py` `diffuse_steps()` |
| `seed = rand.NewSource(1)` (детерминизм) | seed = sha256(seed-id+query) → стабильный порядок карточек | `text_scene.py` |
| `mixed`: grid-фон + crisp sigils/labels | сетка карточек + «sigils» = маркеры статуса/типа (D/T/Q), labels = id | `text_scene.py` |
| raymeet `Region ~100Б` по проводу, рендер локально | по проводу идёт **карточка-сид** (id + гист + ребра, ~120Б), тело пересобирается из локального канона | `text_scene.py` `card_seed()` |
| raymeet `Pose 44Б` на тик | **курсор-фокус** агента: какую карточку он сейчас раскрывает (id + depth + step, ~40Б) | `mux` контур |
| `ChatSync` (id+dedup, hub re-broadcast) | append-only шаги тредов, дедуп по step-id; `crdt_merge` лечит коллизии | уже есть: `thread_runner.run`, `crdt_merge` |
| `brain tvcp-ai/1` (любой мозг за BRAIN_URL) | тот же `thread_runner --llama --endpoint` или offline-синтетик | уже есть: `thread_runner.step` |

Вывод: **3 из 4 «контуров» гибрида у нас уже построены** (раскрытие = view/view_html;
ретрив-сид = canon_index; агент-цикл = thread_runner; мёрж = crdt/seq_merge). Недостаёт
ровно одного нового артефакта — **2D-композитора** `text_scene.py` и тонкой
много-агентной обвязки `text_mux.py`.

## 1. Первый артефакт: `tools/text_scene.py` (канон-срез → 2D-сетка карточек)

Один stdlib-файл (как все наши tools: `_ioutil`/`_cli`, `COLLAB_ROOT`, FTS5-деградация).
Переиспользует напрямую: `view.load_canon`, `view.slice_ids`, `view._gist`,
`canon_index.search`, `view_html._CSS`.

### 1.1. Сид (аналог `Grid.Rows`)

```
seed(seed_id|query, cols, rows) -> Grid:
  ids = canon_index.search(query) ∪ view.slice_ids(canon, seed_id, depth)   # FTS-ось + граф-ось
  ids = stable_order(ids, key=sha256(seed_id+query))                        # детерминизм (как rand.Source(1))
  cells[r][c] = { id, type, gist=view._gist(body), links }                  # ровно как Grid-токен, но смысловой
  раскладка: «от общего к частному» — seed-id в (0,0), соседи по BFS-близости вправо/вниз
```

Это буквально `Grid.rect()`: ragged-сетка нормализуется в прямоугольник, «пустые»
ячейки добиваются последним соседом (как `extend the last color to pad ragged rows`).

### 1.2. Полу-диффузия (аналог `upscaleBilinear`+`blur`+`DiffuseFrames`)

Уровень детализации `L ∈ {0,1,2}` = три «прохода blur», детерминированные:

```
render(grid, L):
  L=0 (noise/coarse): только type-маркер + id       → "▦ D-014"            (как seeded-noise кадр)
  L=1 (mid):          + gist (1 строка)               → "◧ D-014 — execute off-by-ratification"
  L=2 (sharp/target): + тело блока (frozen-инлайн)    → полный текст        (как alpha=1 target)
diffuse_steps(grid, steps): по шагам поднимаем L части ячеек от 0→2
  порядок проявления = близость к seed (центр резкий раньше краёв — «blur затухает от центра»)
```

`alpha=i/(steps-1)` из `DiffuseFrames` ⇒ доля ячеек на уровне L=2 растёт линейно по шагу.
«blur fades out» ⇒ на ранних шагах далёкие-по-графу карточки ещё «размыты» (только id),
ближние уже «проявлены» (тело). Полностью детерминировано, без модели.

### 1.3. Выходы (три рендера одной сетки — как pseudo даёт grid/glyphs/mixed)

- **terminal** (по умолчанию): ASCII-таблица карточек cols×rows, рамки `box`-стиля
  (аналог `scene.Op{op:"box"}`), один экран = «2D-кадр». Уровень L управляется флагом
  `--level`/`--steps` (анимация denoise печатью кадров).
- **html**: переиспользуем `view_html.compile_html` НО в grid-раскладке (CSS grid вместо
  линейного списка `<details>`) — каждая карточка `<details>`, клик = L0→L2 локально.
  «mixed»-режим: соответствует grid-фон (свёрнутые) + sharp sigils (раскрытые ключевые).
- **wire/json**: `card_seed()` — что идёт «по проводу» (см. §3).

CLI:
```
python tools/text_scene.py <seed-id> --query "..." --cols 4 --rows 3 --level 1
python tools/text_scene.py <seed-id> --steps 5 --html out.html     # denoise-анимация + grid-HTML
```

## 2. Что переиспользуем БЕЗ изменений (минимизируем новый код)

| Нужда гибрида | Уже есть | Как зовём |
|---|---|---|
| ретрив сид-тем под промпт | `canon_index.search` (FTS5/bm25) | `text_scene.seed()` |
| связный подграф (blur-соседство) | `view.slice_ids` (BFS related/[[links]]) | `text_scene.seed()` |
| гист-однострочник карточки | `view._gist` | рендер L1 |
| прогрессивное раскрытие L0→L2 | `view.assemble(live/frozen)` + `view_html.<details>` | рендер + html |
| агент-цикл (мозг рисует текст) | `thread_runner.run` (task→FTS-ctx→llama/синтетик→append) | §3 многоагентность |
| мёрж параллельных правок карточек | `crdt_merge.merge3` (OR-Set+3way) + `seq_merge` (diff3 тела) | §3 разрешение конфликтов |

Новый код — только: `text_scene.py` (композитор 2D-сетки + diffuse-уровни) и
`text_mux.py` (тонкий MMORPG-контур, §3). Всё остальное — композиция существующего,
ровно в духе нашей концепт-карты «каждая новая фича = сплав старых».

## 3. Много-агентность (MMORPG / сетка камер) — `tools/text_mux.py`

Прямая калька raymeet на файл-нативный канон. **Хаб = единственный автор сетки-сида**
(как host в raymeet), участники (люди и ИИ за `thread_runner --llama`) раскрывают/
дописывают карточки.

```
mux(scene.json):
  participants: [ {name, kind: human|agent, endpoint?} ]    # endpoint = BRAIN_URL агента
  каждый участник = своя "камера" = свой view на ту же сетку (свой фокус-курсор)
  ПО ПРОВОДУ (meaning not pixels):
    card_seed  ~120Б  (id + gist + links + type)   ← аналог raymeet Region ~100Б, broadcast 1×/карточку
    focus_pose ~40Б   (participant, card_id, L, step) ← аналог Pose 44Б, на тик
    step_msg          (append-only в тред карточки)  ← аналог ChatSync (id+dedup)
  тело карточки НИКОГДА не идёт по проводу — пересобирается локально из канона (raymeet-тезис)
```

**Кто что видит:** у каждого агента свой `view.slice_ids`-срез (туман войны как
`QuestAgent`): агент A раскрыл карточку D-014 на L2 → broadcast `focus_pose` →
остальные видят «D-014 раскрывается агентом A», но тело каждый держит локально.

**Агенты ↔ агенты и ↔ люди:** общение = append шага в тред карточки (`thread_runner.run`
на `threads/<card-id>.md`). Агент B читает шаг A через FTS-ретрив (`assemble_context`),
дописывает свой. Человек — тот же append руками. Один канал, и «текст-чат», и «видеосвязь»
(= поток проявляющихся карточек), как в TVCP чат идёт поверх того же UDP-транспорта.

**Разрешение конфликтов (две правки одной карточки):** `crdt_merge.merge3` — list-поля
(related/tags/participants) OR-Set-объединением (ничего не теряется), тело — `seq_merge`
diff3 (маркеры только на пересечении). Это лечит «оракул-проблему» структурно: не один
LLM-судья решает, а **видимый кворум** — каждая правка остаётся, конфликт помечен, а не
переписан молча. Семантический арбитраж выносим в существующий `oracle_quorum`/
`consensus_by_meaning` поверх слитого результата.

**Детерминизм/безопасность как в raymeet:** сид-сетка санируется (битый ответ агента →
безопасная карточка-плейсхолдер, как «bad response falls back to a safe region»);
сессия пишется append-only (= `raymeet -record`), реплеится по шагам (denoise-таймлайн);
поздний агент догоняет по card-seed (ack-heal: ему шлют сиды карточек, тело он
пересобирает).

## 4. MVP-порядок постройки (что строим первым → последним)

1. **`tools/text_scene.py` seed+render(L)** — канон-срез (`canon_index`+`view.slice_ids`)
   → детерминированная 2D-сетка карточек, терминальный рендер с `--level`. Тесты:
   `test_text_scene.py` (детерминизм порядка по seed; L0⊂L1⊂L2; ragged→rect как `Grid.rect`).
   *Первый осязаемый артефакт — «2D-меню канона за один экран».*
2. **diffuse-анимация** — `diffuse_steps()` + `--steps` (печать кадров L растёт от центра);
   `--html` grid-раскладка поверх `view_html.compile_html`.
3. **`tools/text_mux.py`** — `card_seed()`/`focus_pose` JSON + сборка `threads/<card>.md`
   на карточку; прогон `thread_runner.run` по фокус-карточке агента (синтетик-фолбэк).
4. **конфликт-контур** — `crdt_merge.merge3` на параллельных правках карточки; вынос
   спорного в `oracle_quorum`. Тест: две правки одной карточки → обе выживают.
5. (поздн.) **запись/реплей** сессии mux (= raymeet `-record`), поздний-агент ack-heal.

Каждый шаг автономен, офлайн, в терминале, детерминирован, покрыт тестом — как все
наши tools.

## 5. Риски и как сняты

- **«2D» вырождается в 1D-список.** Снято: жёсткая cols×rows раскладка + BFS-близость
  определяет соседство (это и есть `blur`-соседство), не плоский поток.
- **Оракул-проблема (один LLM-судья).** Снято структурно: `crdt_merge` сохраняет ВСЕ
  правки + видимый `oracle_quorum`, как в нашей методологии; не молчаливый LWW.
- **Недетерминизм рендера.** Снято: seed=sha256, стабильная сортировка, уровни L —
  чистые функции (как `Grid.DiffuseFrames` с `rand.Source(1)`).
- **Раздувание нового кода.** Снято: новых файлов 2 (`text_scene.py`+`text_mux.py`),
  остальное — вызовы view/canon_index/thread_runner/crdt_merge.
- **Поздний агент / потеря шага.** Снято калькой raymeet: card-seed ack-heal +
  append-only дедуп (ChatSync-семантика), тело локально.
