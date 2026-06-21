# Карта кандидатов пирамиды (Этап 2)

Дата: 2026-06-21 · Статус: **proposed** (материал для котла, Q2/Q3 решает коллектив, D-018)
Связано: `docs/workspace-pyramid-levels.md`, `docs/promotion-rules.md`, `tools/promote.py`, `D-016`

Этап 1 (контракты `core/ portals/ collab/ sandbox/`) сделан. Этап 2 — назвать, что куда кандидат,
чтобы Этапы 3-4 (первый портал, первый core-export) шли по доказательной базе, а не наугад.
Инвентарь снят `python tools/promote.py list` (L1=1, L2=1, L3=194, L4 — контракты).

## L1 `core/` — кандидаты в переносимое ядро

Критерий: проверено тестами, не привязано к корпусу/персоне/теме, переносимо в другой проект.

| Артефакт | Почему универсально | Готовность | Тест |
|---|---|---|---|
| `_canon.py` | парсер front-matter — основа file-native канона | стабилен | косвенно |
| `next_id.py` | атомарная выдача id (O_EXCL) против коллизий | стабилен, самопроверен | да |
| `commit_lock.py` | сериализация коммитов в общем дереве | стабилен | `test_commit_lock` |
| `pipeline.py` (+`dispatch.py`) | атомарный котёл задач (claim+DAG) | стабилен | `test_pipeline_fencing` |
| `merge_gate.py` | merge-гейт (validate+generate --check+permissions) | новое, протестировано | `test_merge_gate` |
| `validate.py`/`generate.py` | гейт качества канона | стабильны | прогон |
| read-only драйверы `files/git-log/sqlite` + `drivers/SCHEMA.md`+`redaction.py` | переносимый контракт «информационных драйверов» | 8/9 ready | acceptance |
| `knowledge.py`+`text_extract.py` | generic L6 знание-движок (ingest→index→search) | T-133 done | `test_knowledge/_text_extract` |

### Рекомендация по Q2 (первый core-export) — proposed

Первый export — **связный минимум «file-native agent-coordination engine»**, а не россыпь:

```
core/
  README.md            "движок координации агентов поверх файлов"
  canon/   _canon.py validate.py generate.py        # канон + гейт
  concur/  next_id.py commit_lock.py pipeline.py dispatch.py merge_gate.py   # атомарный котёл + лок + гейт
  tests/   соответствующие test_*.py
```

Почему этот набор: он (а) полностью покрыт тестами, (б) ничего не знает про конкретный корпус/домен,
(в) сам по себе полезен любому многоагентному file-native проекту. Драйверы и knowledge — **второй**
export (крупнее, тянут MCP/SQLite-зависимости). Экспорт = курируемая КОПИЯ в `core/` (не move живых
`tools/`, иначе сломаются ссылки) с собственным README/contract; живой `tools/` остаётся mainline.

## L2 `portals/` — кандидаты и первый портал

| Кандидат | Что это | Статус |
|---|---|---|
| `data/portals/example` (generic demo) | минимальный портал поверх knowledge | существует, тест зелёный |
| `repo-inventory` | портал read-only инвентаря репозиториев | концепт (T-024) |
| `legal-social-de` | доменный портал | требует данных/решения D2 |

### Рекомендация по Q3 (первый L2 портал) — proposed

По Этапу 3 пирамиды — начать с **generic demo**: оформить `portals/example/` (`portal.md` +
`current-state.md` + `workflows.md`) на основе уже зелёного `data/portals/example`. Это проверит слой
L2 без доменного спора (legal/social откладываем до данных). Открытый технический вопрос для котла:
порталы живут в `portals/` (пирамида) или `data/portals/` (текущий `portal.py`) — свести при синтезе.

## L3 `collab/` — остаётся логическим слоем (без массовой миграции)

194 файла: `decisions/ questions/ tasks/ streams/ темы/ queues/ reports/` + навигация. Это история и
доказательная база. По D-консенсусу (и мнению Codex) — НЕ переносить физически: сломает ссылки,
конфликтует с параллельными агентами, утяжелит diff. `collab/README.md` уже карта.

## L4 `sandbox/` — вход

`sandbox/` (intake/quarantine) + `data/fixtures` (тестовый внешний источник). Подъём выше — только через
`report → decision` (см. `tools/sandbox.py`, `sandbox_intake_demo.py`). Ничего не поднимать автоматически.

## Путь продвижения (как это исполнить)

`tools/promote.py` + `docs/promotion-rules.md` уже дают механику: `list` (инвентарь) → `check --artifact`
(готовность по гейту уровня) → `move --from --to` (атомарно + метаданные). Для core-export уместен не
`move`, а курируемая копия (export-режим) — кандидат на доработку `promote.py` после выбора набора Q2.

## Перепроверка (D-018)

- **Техническая:** L1-кандидаты покрыты тестами; export = копия (не move) — нулевой риск поломки ссылок;
  L3 не двигаем (избегаем noisy diff и конфликтов с агентами).
- **Гуманитарная:** ядро как отдельный переносимый engine = ценность вне этого корпуса (другие команды
  смогут взять координацию агентов поверх файлов); порталы дают людям чистовую рабочую область без шума истории.

> Q2 (какой первый core-export) и Q3 (какой первый портал) — открытые вопросы пирамиды; эта карта их НЕ
> закрывает соло, а даёт обоснованные кандидаты и рекомендации в котёл (D-018).
## Update 2026-06-21 — first L2 example portal scaffold

Первый L2 scaffold реализован аддитивно: `portals/example/portal.md`, `current-state.md`,
`workflows.md`, `sources.md`. Это не закрывает Q4 окончательно: `tools/portal.py` пока работает с
`data/portals/example`, а `portals/example` — clean present-tense слой со ссылками. Вопрос location
model вынесен в `streams/portal-location/20260621-1931-claude/STREAM.md`.
