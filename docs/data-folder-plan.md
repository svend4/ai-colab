# Data Folder Plan

Дата: 2026-06-20
Связано: `docs/mvp-roadmap.md`, `docs/l2-candidates.md`, `docs/driver-safety-policy.md`, `tasks/T-037.md`

## Цель

`data/` должен стать рабочей областью для большого корпуса файлов: входящие документы, копии, извлечённый текст, chunks, индексы, отчёты и audit. Это не замена `docs/`: `docs/` хранит согласованную документацию проекта, а `data/` хранит рабочие данные и результаты обработки корпуса.

## Рекомендуемая структура

```text
data/
  README.md
  inbox/
  originals/
  copies/
  text/
  chunks/
  indexes/
  reports/
  audit/
  fixtures/
  workbench.db
```

## Назначение папок

| Путь | Назначение | Кто пишет | Правило |
|---|---|---|---|
| `data/inbox/` | входящие файлы для обработки | человек или import-driver | не менять оригиналы вне проекта |
| `data/originals/` | неизменяемые копии оригиналов внутри проекта | copy/import driver | write-once, без перезаписи |
| `data/copies/` | рабочие копии для нормализации | драйверы с safe-write | только после dry-run или явной задачи |
| `data/text/` | извлечённый текст | text-extract driver | можно перегенерировать из originals/copies |
| `data/chunks/` | фрагменты для поиска/RAG | chunking/search driver | machine-generated |
| `data/indexes/` | FTS/BM25/vector/JSON индексы | search-index driver | generated, пересобираемо |
| `data/reports/` | отчёты по корпусу | report driver/агенты | человекочитаемые Markdown/CSV/HTML |
| `data/audit/` | журналы операций | все драйверы medium/high risk | append-only по смыслу |
| `data/fixtures/` | маленький безопасный тестовый корпус | инженеры/агенты | без персональных данных |
| `data/workbench.db` | SQLite-память корпуса | data driver | schema/migrations через отдельные задачи |

## Что можно писать автоматически

Разрешено автоматически, если задача явно назначена и нет персональных/секретных данных:

- `data/text/`;
- `data/chunks/`;
- `data/indexes/`;
- `data/reports/`;
- `data/audit/`;
- `data/fixtures/` для synthetic/test данных.

Условие: результат должен быть восстановимым или иметь audit-запись.

## Что требует осторожности

Требует dry-run или отдельной задачи:

- импорт в `data/originals/`;
- массовое копирование в `data/copies/`;
- перезапись `workbench.db`;
- anonymization;
- merge/split больших документов;
- любые операции с внешними папками вне workspace.

Запрещено по умолчанию:

- удалять оригиналы;
- менять файлы вне проекта;
- хранить секреты;
- отправлять корпус во внешние API без решения;
- запускать код из корпуса.

## Связь с `workbench.db`

Минимальная схема должна отражать файловую структуру:

```text
documents
  id
  source_path
  project_path
  sha256
  file_type
  size_bytes
  title
  status
  pii_level
  imported_at

audit_log
  id
  timestamp
  actor
  action
  target
  result
  details
```

Позже добавить:

```text
chunks
entities
topics
document_links
```

## Поток обработки

```text
external source
  -> data/inbox/
  -> data/originals/       # immutable project copy
  -> data/copies/          # normalized working copy
  -> data/text/            # extracted text
  -> data/chunks/          # passages
  -> data/indexes/         # search
  -> data/reports/         # human outputs
  -> data/audit/           # operation log
```

## Минимальные правила для драйверов

- `files` driver читает `data/` и строит inventory.
- `copy` driver пишет только в `data/originals/` или `data/copies/`.
- `text-extract` driver пишет только в `data/text/`.
- `search-index` driver пишет только в `data/indexes/`.
- `report` driver пишет только в `data/reports/`.
- Любой driver с `risk: medium|high` пишет audit.

## Рекомендация

Создать `data/README.md` перед первым массовым импортом. До этого не переносить реальные большие или чувствительные данные в `data/`. Сначала подготовить `data/fixtures/` и проверить `files`, `text-extract`, `search-index`, `report` на безопасном маленьком корпусе.

