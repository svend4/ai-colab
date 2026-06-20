# Ingest pipeline hardening report

Дата: 2026-06-20
Автор: Codex
Связано: `T-053`, `T-054`, `T-056`, `T-057`

## Контекст

Claude закрыл `T-053`: добавлен `drivers/workbench/ingest.py` и `drivers/workbench/test_ingest.py`. Это первый сквозной поток:

```text
files/repo-runner scan -> workbench.db -> query/audit
```

Codex перепроверил код статически. После `T-047`, `T-050` и `T-054` у отдельных drivers уже появились allowed-root и лимиты, но `ingest.py` вызывал их без этих параметров. Это означало, что сквозной слой мог обойти boundary layer.

## Что изменено

В `drivers/workbench/ingest.py`:

- добавлен `DEFAULT_MAX_FILES`;
- `ingest_repo_path()` получил `db_base`, `source_base`, `max_files`;
- `ingest_dir()` получил `db_base`, `source_base`, `max_files`;
- `query()` получил `db_base`;
- CLI использует:
  - `WORKBENCH_BASE` для зоны записи БД;
  - `INGEST_SOURCE_BASE` для зоны чтения источника;
  - `INGEST_MAX_FILES` для лимита обхода/импорта;
- ошибки CLI возвращаются JSON-объектом `{error, message}`.

В `drivers/workbench/test_ingest.py`:

- добавлена проверка `max_files`;
- добавлена проверка `query(db_base=...)`;
- добавлена проверка запрета записи БД вне `db_base`.

## Что осталось не проверено

Codex не запускал Python-тесты из-за `T-039`.

Нужна runtime-приёмка `T-057`:

```powershell
python drivers\workbench\test_ingest.py
python drivers\workbench\test_workbench.py
python tools\validate.py
python tools\generate.py --check
```

Дополнительно:

- CLI `repo/dir` с `WORKBENCH_BASE`;
- CLI `repo/dir` с `INGEST_SOURCE_BASE`;
- `INGEST_MAX_FILES=1` даёт ограниченный ingest;
- попытка источника вне `INGEST_SOURCE_BASE` должна возвращать JSON-error.

## Мнение Codex

Сквозной ingest — это уже “живая” инфраструктура: данные переходят из файловой системы в память проекта. Поэтому именно здесь нельзя терять ограничения, которые были добавлены на отдельных слоях. Правильный принцип: каждый слой обязан передавать policy ниже, а не надеяться, что lower-level driver сам угадает контекст.

После `T-056` архитектурная связка выглядит правильнее:

```text
source allowed-root -> scanner max_files -> workbench allowed-root -> bounded query/audit
```

