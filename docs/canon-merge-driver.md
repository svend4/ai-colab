# Merge-драйвер канона (field-level, grow-only)

Активирует кластер `git_reconcile → crdt_merge → seq_merge` как **git merge-driver** для канон-файлов
front-matter. Цель — убрать гонки «кто последний перезаписал» на общих файлах: при коллизии git сливает
их **на уровне поля**, а list-поля (`related`, `tags`, …) **объединяются (union) — ни один вклад не теряется**
(grow-only, контр-инвариант C-II формулы `defect-class-formula-2026-06-26`). См. `D-032`, T-263.

## Активация (одноразово на клон)

```bash
python tools/git_reconcile.py --install --apply
```

Это (идемпотентно):
- регистрирует драйвер: `git config merge.crdt.driver 'python tools/git_reconcile.py %O %A %B'`;
- дописывает `.gitattributes`: `tasks/**/*.md`, `decisions/**/*.md`, `questions/**/*.md`, `topics/**/*.md` → `merge=crdt`.

`.gitattributes` версионируется и работает у всех; но **сам драйвер локален** (git config не коммитится),
поэтому на новом клоне нужно один раз выполнить команду выше (как и `git config core.hooksPath tools/githooks`
для хуков). Без драйвера атрибут `merge=crdt` мягко деградирует к стандартному слиянию — поломки нет.

## Что делает при коллизии
- **list-поля front-matter** (`related`/`tags`/…) → **union** (оба вклада сохранены);
- **скаляры** → 3-way (base/ours/theirs);
- **тело** при двусторонней правке → маркеры `<<<<` (НЕ потеряно, на доразбор человеку);
- exit 0 = чисто слито; exit 1 = остались конфликты, но файл уже field-merged (не строчная каша).

Проверено реальным `git merge`: две ветки добавили в `related` разные элементы (C и D) → результат
`[A, B, C, D]` (оба выжили). Тест: `tools/test_git_reconcile.py`.

## Границы
- Драйвер — для **front-matter markdown канона** (T-*/D-*/Q-*/темы). Сгенерированные файлы (`index.json`,
  `STATUS.md`, `board.md`) **не сливать, а РЕГЕНЕРИРОВАТЬ** после слияния источников (`python tools/generate.py`)
  — это следующий шаг кластера (generated-not-merged).
- Кооперативность: помогает при реальном `git merge`; одновременный raw-`git` в общем рабочем дереве —
  отдельная защита (`commit_queue` D-031, worktree D-022).
