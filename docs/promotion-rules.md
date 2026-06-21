# Promotion rules (workspace-pyramid gate)

Дата: 2026-06-21
Статус: draft policy
Связано: `docs/workspace-pyramid-levels.md`, `core/README.md`, `portals/README.md`, `collab/README.md`, `sandbox/README.md`, `tools/promote.py`

Этот документ отвечает на open-question 5 из `docs/workspace-pyramid-levels.md`
(«нужен ли `tools/promote.py`?»): да — нужен, но как **gate с явными критериями**, а
не как массовый мигратор. Инструмент формализует каждый переход пирамиды и
проверяет готовность материала перед подъёмом. Ничего не поднимается выше
автоматически; каждый переход требует review и clean summary.

```text
L4 sandbox/  -> L3 collab   -> L2 portals/ -> L1 core/
   хаос           спор/доказ.    чистовой       универсальное
                                 портал         ядро
```

## Общие принципы

1. **Только вверх по одному уровню.** `--from`/`--to` должны быть соседними (L4->L3, L3->L2, L2->L1). Перескок уровней запрещён.
2. **Атомарность.** Перемещение пишет новый путь и только потом удаляет старый (write-new-THEN-remove-old). Не должно оставаться half-move: либо старый путь есть и новый нет, либо новый путь есть и старый удалён.
3. **Stamp метаданных.** При перемещении в front-matter добавляются: `promoted_from`, `promoted_to`, `promotion_date`, `gate_checks_passed`, `reviewed_by`, `decision_ref`.
4. **collab/ остаётся ЛОГИЧЕСКИМ слоем.** L3 не переносится физически в `collab/`; mass-migration существующих `tasks/`, `decisions/`, `questions/`, `streams/`, `темы/` не делается. Они уже являются L3 по карте `collab/README.md`.

## L4 sandbox/ -> L3 collab

Хаотичный входной материал становится проверяемым report / task / question / stream.

Gate-критерии:

- **read_only_report** — у артефакта есть очищенный read-only summary (sandbox inventory report), а не сырой код. Артефакт находится под `sandbox/` (L4).
- **decision_ref** — есть ссылка на решение (`decision_ref` во front-matter или поле `decision`/`D-NNN`), легализующее подъём материала из quarantine. Без decision-ref материал не покидает L4.
- **no_raw_execute** — материал не требует запуска внешнего кода для подъёма (gate `docs/execute-sandbox-preflight.md` остаётся отдельным и закрытым).

## L3 collab -> L2 portals

Из полилога собирается чистовой текущий портал (present-tense).

Gate-критерии:

- **clean_present_tense** — материал переписан как чистовое текущее состояние, без длинной истории споров, версий обсуждения и черновых веток. Эвристика: нет маркеров истории (`done:`/`fail:`/`claim:`/`обсужд`) в чистовой части.
- **tests_green** — относящиеся тесты зелёные (для кода) или у документа есть verification-ссылка. Поле `tests`/`gate_checks_passed` подтверждает проверку.
- **portal_target** — назначение — конкретный портал `portals/<id>/` (L2), а не корень и не другой L3-каталог.

## L2 portals -> L1 core

Специализированная функция, доказавшая переносимость, поднимается в универсальное ядро.

Gate-критерии:

- **reuse_across_portals** — доказано повторное применение минимум в `>=2` порталах (поле `reused_in` со списком из 2+ порталов, либо явный список в decision-ref).
- **verification** — есть строгая проверка: тесты ядра зелёные и/или verification-ссылка (`tests`/`gate_checks_passed`). L1 change требует строгих тестов.
- **no_domain_coupling** — материал не привязан к одному домену/пользователю/корпусу (нет `portal:`/`domain:`/`corpus:` привязки в чистовой части).

## Метаданные promotion

После успешного `move` во front-matter артефакта добавляются:

| Поле | Значение |
|---|---|
| `promoted_from` | уровень-источник (например `L4`) |
| `promoted_to` | уровень-назначение (например `L3`) |
| `promotion_date` | дата перехода (YYYY-MM-DD) |
| `gate_checks_passed` | список пройденных критериев |
| `reviewed_by` | кто подтвердил review |
| `decision_ref` | ссылка на решение (`D-NNN`) |

## Инструмент

`tools/promote.py` — gate-инструмент:

```text
python tools/promote.py list
python tools/promote.py check --artifact <path>
python tools/promote.py move --artifact <path> --from L4 --to L3 \
    [--reviewed-by NAME] [--decision-ref D-NNN]
```

- `list` — перечисляет уровни и артефакты со статусом.
- `check` — проверяет готовность артефакта против правил этого документа (per-criterion pass/fail).
- `move` — атомарный подъём на соседний уровень со stamp метаданных.

`--root <dir>` переопределяет корень пирамиды (для герметичных тестов и временных пирамид).
