# Portals

`portals/` — уровень L2: чистовые специализированные рабочие области.

Портал — это present-tense слой поверх `core/`, привязанный к теме, домену, пользователю, группе или workflow. Он чище, чем исторический полилог, но конкретнее, чем универсальное ядро.

Пример будущей структуры:

```text
portals/<portal-id>/
  portal.md
  current-state.md
  workflows.md
  sources.md
  reports/
```

В портал не кладутся raw sandbox sources, длинные споры и вся история изменений. Для истории используются L3 folders: `topics/`, `tasks/`, `questions/`, `decisions/`, `streams/`.

Документ модели: `docs/workspace-pyramid-levels.md`.

## L1 grounding for portal layer

Этот раздел является явной поверхностью для `tools/assurance.py coverage`: L2-порталы должны быть
связаны не только с `tools/knowledge.py`, но и с переносимым control-plane ядром из
`core/engine-manifest.md`. Порталы не обязаны вызывать каждый файл напрямую, но должны показывать,
какой L1-движок поддерживает их жизненный цикл: front-matter canon, generation, validation,
ID allocation, commit lock, task pipeline, dispatch и merge gate.

L1 core-export basis for portals: `tools/_canon.py`, `tools/validate.py`, `tools/generate.py`,
`tools/next_id.py`, `tools/commit_lock.py`, `tools/pipeline.py`, `tools/dispatch.py`,
`tools/merge_gate.py`, `core/engine-manifest.md`.

## Текущий пример

`portals/example/` — первый clean L2 scaffold:

- `portal.md` — identity/config;
- `current-state.md` — текущее состояние;
- `workflows.md` — команды;
- `sources.md` — curated источники и ссылка на `data/portals/example/corpus/`.

После `D-021`/`T-145` split-модель принята: `portal.py` читает identity/config из `portals/example/portal.md`, а операционный корпус и runtime остаются в `data/portals/example/` через `corpus_ref`.
