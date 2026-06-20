# Expected Inventory

Ожидаемый результат для read-only `files` driver на `data/fixtures/`.

## Default scan

Команда уровня поведения:

```text
inventory("data/fixtures", include_hidden=false, hash=false)
```

Должен увидеть обычные файлы:

| Path | Kind | Extension |
|---|---|---|
| `README.md` | text | `.md` |
| `sample-doc.md` | text | `.md` |
| `sample-notes.txt` | text | `.txt` |
| `sample-data.json` | text | `.json` |
| `sample-table.csv` | text | `.csv` |
| `nested/topic-summary.md` | text | `.md` |
| `nested/case-outline.txt` | text | `.txt` |

Должен пропустить:

| Path | Причина |
|---|---|
| `.hidden-note.txt` | hidden file, включается только при `include_hidden=true` |

Минимальные summary-ожидания:

```text
total_files >= 7
extensions[".md"] >= 3
extensions[".txt"] >= 2
extensions[".json"] >= 1
extensions[".csv"] >= 1
kinds["text"] >= 7
```

## Include hidden

Команда уровня поведения:

```text
inventory("data/fixtures", include_hidden=true, hash=false)
```

Дополнительно должен увидеть:

| Path | Kind | Extension |
|---|---|---|
| `.hidden-note.txt` | text | `.txt` |

## Hash mode

Команда уровня поведения:

```text
inventory("data/fixtures", include_hidden=true, hash=true)
```

Ожидание:

- для маленьких файлов поле `sha256` заполнено;
- для файлов больше лимита hash может быть `null` + `hash_skipped: true`;
- driver не должен читать или печатать содержимое файлов целиком в inventory-output.

## PASS criteria

- Нет записи за пределы `data/fixtures`.
- Нет удаления/переименования.
- Hidden-файл пропущен по умолчанию.
- Hidden-файл появляется при `include_hidden=true`.
- JSON output валиден.
- Все paths относительные к scanned root.

