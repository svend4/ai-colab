# External code sandbox — universal workspace

Дата: 2026-06-21  
Статус: draft policy / folder contract  
Связано: `docs/execute-sandbox-preflight.md`, `tasks/T-020.md`, `Q-014`, `D-016`, `sandbox/README.md`

## Назначение

Эта документация описывает нейтральную песочницу для внешнего кода и внешних репозиториев.

Она не привязана к `svend4`, одной персоне, одному GitHub-профилю или одному домену. `svend4` — только первый старый долг и пример источника. Та же схема должна работать для любого внешнего кода:

- GitHub/GitLab/архив;
- локальная папка с кодом;
- экспорт проекта;
- доменный портал;
- тестовый corpus с кодом и документацией.

Главная идея: внешний код **не интегрируется напрямую** в ядро проекта. Он сначала попадает в controlled sandbox intake, проходит read-only inventory, затем обсуждается через reports. Execute допускается только после отдельного safety gate.

## Что создано в рабочей папке

Корневая папка:

```text
sandbox/
  README.md
  .gitignore
  inbox/
    README.md
  sources/
    README.md
  workspaces/
    README.md
  runs/
    README.md
  reports/
    README.md
  templates/
    external-source-manifest.template.json
    sandbox-run-plan.template.json
```

Эта папка является **локальной рабочей зоной**, а не местом для постоянного хранения чужого кода в Git. В репозиторий попадают README, template и очищенные summary. Сырые источники, распакованные архивы, runtime-логи и временные workspaces игнорируются.

## Стадии работы с внешним кодом

### S0. Decision / цель

До работы нужно понимать, зачем источник нужен:

- inventory архитектуры;
- поиск функций;
- извлечение документации;
- тестирование конкретной команды;
- сравнение вариантов;
- подготовка адаптера/driver.

Если цель доменная, она должна быть оформлена как портал/подтема поверх универсального ядра, по `D-016`.

### S1. Intake

Источник регистрируется в `sandbox/inbox/` через manifest. Нельзя сразу смешивать его с `code/`, `tools/`, `drivers/` или основным corpus.

Минимальная карточка источника:

- source id;
- тип источника;
- откуда взят;
- кто разрешил использовать;
- license/usage note;
- содержит ли секреты или персональные данные;
- ожидаемый режим: read-only или future execute candidate;
- какие вопросы надо проверить.

Шаблон: `sandbox/templates/external-source-manifest.template.json`.

### S2. Quarantine / sources

Сырые архивы, клоны или копии внешнего кода размещаются в `sandbox/sources/<source-id>/` или остаются вне репозитория с указанием абсолютного read-only пути в manifest.

Правило: источник считается недоверенным, пока не прошёл inventory. Не запускать скрипты, install, tests, hooks, binaries.

### S3. Read-only inventory

Первый технический шаг всегда read-only:

- список файлов;
- размеры;
- языки/типы;
- признаки секретов;
- package manifests;
- build/test scripts;
- license files;
- network/process/file-system sensitive code;
- entrypoints;
- документация.

Результат должен быть Markdown report. Для стабильного обсуждения лучше писать очищенный итог в `sandbox/reports/` или общий `reports/`.

### S4. Workspaces

Если нужно готовить эксперимент, создаётся disposable workspace:

```text
sandbox/workspaces/<source-id>/<run-id>/
```

Это копия или checkout для анализа. Она не должна быть canonical source и не должна попадать в Git.

### S5. Execute candidate

Запуск кода запрещён по умолчанию. Чтобы источник стал execute candidate, должны быть закрыты gates из `docs/execute-sandbox-preflight.md`:

- accepted decision;
- источник уже прошёл inventory;
- изолированная среда;
- нет секретов и широких host mount;
- сеть по умолчанию выключена;
- лимиты CPU/RAM/PIDs/disk/timeout;
- audit/log/report;
- rollback;
- явное подтверждение человека для first-run.

### S6. Run plan

Перед каждым разрешённым запуском создаётся run plan. Шаблон:

```text
sandbox/templates/sandbox-run-plan.template.json
```

Run plan фиксирует источник, команду, image/VM, mounts, network, limits, timeout, expected output и rollback.

### S7. Reports and promotion

Сырые логи остаются в `sandbox/runs/` и не версионируются. В Git попадает только очищенный summary:

- что проверяли;
- какая команда/среда;
- что получилось;
- какие риски найдены;
- можно ли переносить что-то в `docs/`, `drivers/`, `tools/` или tasks.

Любой перенос из sandbox в основной проект должен быть отдельной задачей, а не автоматическим merge.

## Как это решает старый долг T-020 / svend4

Старый `T-020` не должен быть специальной дырой в правилах. Правильная модель:

1. Если Stefan даёт read-only путь/архив/snapshot `svend4`, он регистрируется как обычный source id, например `svend4-profile-YYYYMMDD`.
2. Сначала выполняется read-only inventory.
3. Итог обсуждается в report.
4. Только после этого решается, нужен ли connector, driver, portal или execute sandbox.
5. Никакой код `svend4` не запускается на host Windows без отдельного accepted decision.

Если `svend4` недоступен, та же песочница может быть проверена на другом внешнем тестовом репозитории. Это важно: инфраструктура должна быть универсальной, а не зависеть от одного профиля.

## Что не является целью этой папки

- Не хранить чужие репозитории в Git.
- Не делать автоматический `git clone` без review.
- Не запускать `pip install`, `npm install`, тесты или build scripts по факту наличия репозитория.
- Не обходить `execute-sandbox-preflight`.
- Не смешивать sandbox output с чистовыми docs без summary/review.

## Мнение Codex

Такой слой нужен как "середина между read-only анализом и execute". Сейчас проект уже умеет хорошо описывать и индексировать информацию, но старые долги вроде `T-020` показывают следующий разрыв: внешний код нельзя просто подключить, но и держать его вечным blocked тоже плохо.

Универсальная `sandbox/` папка закрывает этот разрыв организационно:

- внешний код получает понятный вход;
- агенты видят, где quarantined source, где workspace, где reports;
- один источник не получает особых прав;
- будущий sandbox runner можно будет добавить позже, не ломая текущую структуру;
- спор `svend4` превращается из персонального блокера в общий процесс external-source intake.

Технически это пока не песочница выполнения. Это **sandbox workspace contract**. Настоящий execute runner должен появиться отдельной задачей после preflight и решения.
