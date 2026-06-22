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

В портал не кладутся raw sandbox sources, длинные споры и вся история изменений. Для истории используются L3 folders: `темы/`, `tasks/`, `questions/`, `decisions/`, `streams/`.

Документ модели: `docs/workspace-pyramid-levels.md`.
## Текущий пример

`portals/example/` — первый clean L2 scaffold:

- `portal.md` — identity/config;
- `current-state.md` — текущее состояние;
- `workflows.md` — команды;
- `sources.md` — curated источники и ссылка на `data/portals/example/corpus/`.

После `D-021`/`T-145` split-модель принята: `portal.py` читает identity/config из `portals/example/portal.md`, а операционный корпус и runtime остаются в `data/portals/example/` через `corpus_ref`.
