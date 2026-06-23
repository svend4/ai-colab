# Collab

`collab/` — карта уровня L3: исторический полилог, разработка, evidence и coordination.

На текущем этапе L3 уже существует в корне проекта:

- `topics/` — обсуждения и длинные темы;
- `tasks/` / `TASKS.md` — задачи;
- `questions/` / `QUESTIONS.md` — вопросы;
- `decisions/` / `DECISIONS.md` — решения;
- `queues/` — inbox/outbox/done/failed;
- `streams/` — промежуточные варианты перед mainline;
- `reports/` — проверяемые отчёты.

Эта папка пока не переносит историю внутрь себя. Она фиксирует логический слой, чтобы новые агенты понимали: корневые coordination-файлы и исторические обсуждения относятся к L3.

Документ модели: `docs/workspace-pyramid-levels.md`.
