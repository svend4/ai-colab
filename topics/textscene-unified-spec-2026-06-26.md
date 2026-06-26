---
id: textscene-unified-spec-2026-06-26
type: topic
title: Единый спек 2D-текст-workbench — консолидация 3 независимо сошедшихся дизайнов
status: proposed
date: 2026-06-26
author: claude-opus-4-8
related:
  - tvcp-text-diffusion-hybrid-2026-06-26
  - mmorpg-2d-text-workbench-2026-06-26
  - text-diffusion-canvas-from-infon-2026-06-26
  - tvcp-live-repo-eval-2026-06-26
---

# Единый спек 2D-текст-workbench (консолидация)

> Три дизайна, написанные НЕЗАВИСИМО разными агентами в один день, сошлись на одной архитектуре —
> это сам по себе сильнейший сигнал (independent-consensus: согласие без сговора = зрелость идеи).
> Свожу их в один контракт и строю из него.
>
> Источники: [[tvcp-text-diffusion-hybrid-2026-06-26]] (моё/рой: субстрат·CRDT·диффузионное раскрытие),
> [[mmorpg-2d-text-workbench-2026-06-26]] (codex: организационная механика MMORPG·роли·зоны),
> [[text-diffusion-canvas-from-infon-2026-06-26]] (codex: cell/frame-протокол·agent-lanes·brain-граница).

# 1. Что сошлось (консенсус 3/3)
| Тезис | textscene | mmorpg-wb | canvas |
|---|---|---|---|
| 2D, не 1D-лента (положение несёт смысл) | §2 | §2,§4 | §1 |
| Атом = типизированная **ячейка** (id/kind/owner/status/links/body) | карточка | text_cell.v1 | text_cell.v1 |
| **Frame = снимок с changed_cells** (диффузия = прогрессивное уточнение поля, НЕ denoising) | §3 | §5 | §4.2/4.3 |
| Agent-lanes: расхождение видно **пространственно**, не тонет в хронологии | §5 | §4 | §4.4 |
| Brain **предлагает** ячейки, не решает/не исполняет | §5 | §6,§9 | §3,§4.5,§5 |
| Конфликт виден, consensus **выводится**, не угадывается | §6 | §11 | §4.3 |
| Canon (MD+JSON+git) = истина; canvas = **вид**, не canon | §10 | §11 | §3 |
| Порядок снизу-вверх (thread→cell→canvas→brain) | Step 0→1→2 | §9,§14 | §5 |

# 2. Что разошлось — и как примирено
- **Оси вида.** textscene: Y=абстракция (общее→частное), X=тема-кластер. canvas/mmorpg: rows=вид-ячейки/тема,
  cols=актор/владелец (матрица консенсуса). → **Примирение: это ДВА режима проекции одного cell-store.**
  `abstraction` (дерево раскрытия от seed) и `lanes` (матрица актор×вид). Хранилище одно — рендеров много
  (canvas §4.1 «position fixed or derived?» закрывается: position **выводится** из метаданных, не фиксируется).
- **Первый артефакт.** mmorpg/canvas: «workspace-cell aggregator». textscene: `text_scene.py` (canon→карточки→
  раскрытие). → Не конфликт: workspace-cell (codex/T-264) = миникарта ОДНОГО задания; `text_scene` = вид
  МНОГИХ узлов канона. Стыкуются через общий `text_cell.v1`. Строю свою половину, не трогая T-264.
- **«Диффузия».** textscene честно демотировал её до прогрессивного раскрытия (нет token-Blend оператора);
  canvas/mmorpg тоже трактуют как «frame→diff→frame», не image-denoising. → Согласовано: **reveal-staging +
  changed-cells diff**, имя «полу-диффузия» оставляем как метафору, не как изоморфизм денойзингу.

# 3. Единая архитектура (слои)
```
canon (tasks/topics/decisions/*.md + git)          ← истина, неизменна видом
  │  view.load_canon / slice_ids (детерм., R1 fixed)
  ▼
cell-store  text_cell.v1  (id,kind,owner,topic,position,depth,status,links,body)
  │  crdt_merge (OR-Set ячеек + tombstone, R7 fixed; конфликт-тела виден, не молча)
  ├─► view «abstraction»  → text_scene.py  (Y=depth общее→частное, L0/L1/L2 раскрытие, ANSI/HTML)
  └─► view «lanes»        → text_mux.py     (rows=kind/topic × cols=owner; consensus/conflict; frames diff)
governance (actor.v1 роли, zone.v1 правила) ─ кто что может; human/integrator принимает
brain-граница (tvcp-ai/1-стиль): модель ПРЕДЛАГАЕТ ячейки (proposal-only), не пишет canon
```

# 4. Канонические схемы (общий контракт)
```jsonc
text_cell.v1   {id, canvas_id, kind:question|answer|claim|risk|evidence|task|decision|status|patch|summary,
                owner, topic, position:{row,col}, depth:int, status:draft|proposed|confirmed|conflict|accepted,
                links:[{rel:supports|contradicts|derived_from, target}], body, lamport:int}
text_frame.v1  {canvas_id, frame_no, view:overview|risks|consensus|lanes|abstraction|timeline,
                cells:[id], changed_cells:[id], summary}
actor.v1       {id, kind:human|agent|script|tool, role:researcher|builder|reviewer|synthesizer|integrator|
                red-team|maintainer, zone, status:idle|working|blocked|reviewing}
zone.v1        {id, path, purpose, rules:[...]}
```
`lamport` добавлен к ячейке (versus codex-черновика) — нужен для детерм. tie-break в CRDT-мёрже (R9).

# 5. Что строю (эта реализация) vs что у codex
| Артефакт | Кто | Статус |
|---|---|---|
| **Step 0** crdt/view fixes (R1/R7/R9) | я | ✅ done (4afae95) |
| `tools/text_scene.py` (abstraction-view: canon→карточки→раскрытие L0/L1/L2, ANSI+HTML, diffuse-кадры) | я | Стадия 2 |
| `tools/text_mux.py` (lanes-view: cell-store + consensus/conflict + frames diff + presence, файл-нативный провод) | я | Стадия 3 |
| `workspace-cell` / `thread.py` / T-264 | codex | их нить (не трогаю) |
| brain-adapter (proposal-only) | позже | после canvas |

# 6. Инварианты (тестируемые)
1. **canon ≠ view** — text_scene/text_mux только ЧИТАЮТ canon/cells, не мутируют истину.
2. **Раскладка детерминирована** — порядок по (depth, id), без bm25 в ядре раскладки (R2-урок).
3. **Конфликт виден** — двойная правка тела → `conflict`-ячейка/маркеры, не молчаливый LWW.
4. **Consensus выводится** — ≥2 владельца с совпадающим телом → кандидат; не угадывается.
5. **Brain proposal-only** — модель пишет `status:proposed`, принятие — human/integrator.
6. **Compact не прячет load-bearing** — recall-тест: сжатый кадр не теряет несущее исключение (canvas §6 / mmorpg §11).

# 7. Приёмочный тест (10-секундный критерий codex §12)
Хороший workbench за 10 c отвечает: кто работает · над чем · что изменилось · где конфликт · что проверено ·
что принять · что опасно запускать · где доказательства · следующий шаг · что спросить у человека.
→ Это и есть выходные поля `text_mux report`.

# 8. Вердикт
Три независимых дизайна = один контракт `text_cell.v1`/`text_frame.v1` с двумя режимами вида над общим
CRDT-cell-store. Несущее ядро (как и в [[tvcp-text-diffusion-hybrid-2026-06-26]]): **детерминированная
раскладка + видимый конфликт/оракул**; «диффузия» — прогрессивное раскрытие, не денойзинг. Строю по §5.
