---
id: skills-usage
title: Project skills usage and packaging
status: draft
owner: Codex
related: tasks/T-113.md, skills/README.md, docs/layers-coverage.md
---

# Project skills usage and packaging

Дата: 2026-06-21.

Назначение: объяснить, как использовать и переносить `skills/*/SKILL.md` в другие среды без преждевременного превращения их в полноценный plugin/marketplace.

## Что это такое

`skills/` в этом репозитории — это L3 project skills:

- переносимые процедуры;
- Markdown-инструкции с front-matter `name` и `description`;
- знания о каноне этого проекта;
- повторяемые workflow для агентов.

Это не L5 plugin:

- нет `.codex-plugin/plugin.json`;
- нет MCP server bundle;
- нет автоматической установки;
- нет marketplace metadata;
- нет гарантии, что другой агент сам загрузит эти skills без явного чтения или настройки своей среды.

## Текущий набор

| Skill | Файл | Назначение |
|---|---|---|
| `driver-acceptance` | `skills/driver-acceptance/SKILL.md` | довести driver до `ready`: unit, MCP sync acceptance, manifest/tools, D-015 |
| `pipeline-operator` | `skills/pipeline-operator/SKILL.md` | брать/закрывать задачи через pipeline, claim, done-marker, validate |
| `repo-review` | `skills/repo-review/SKILL.md` | перепроверка репозитория, дрейф, плюсы/минусы, рекомендации |

## Как применять внутри этого репозитория

1. Определить, что задача совпадает с `description` skill-а.
2. Открыть соответствующий `SKILL.md` полностью.
3. Выполнить шаги из skill-а из корня репозитория.
4. Если команда или файл не существует, не выдумывать поведение: записать отличие в отчёт или создать вопрос/задачу.
5. После результата обновить task/docs/outbox по `PROTOCOL.md`.

Минимальная дисциплина:

```powershell
Get-Content -Encoding UTF8 -LiteralPath .\skills\pipeline-operator\SKILL.md
python tools\pipeline.py status
python tools\validate.py
```

## Как переносить в другой проект

### Вариант A: как project-local folder

Подходит для другого репозитория с похожей дисциплиной.

```powershell
Copy-Item -Recurse -LiteralPath .\skills\pipeline-operator -Destination C:\path\to\other-project\skills\pipeline-operator
Copy-Item -LiteralPath .\skills\README.md -Destination C:\path\to\other-project\skills\README.md
```

После копирования нужно адаптировать ссылки:

- `tools/pipeline.py`;
- `tools/validate.py`;
- `drivers/*`;
- `DECISIONS.md`;
- `PROTOCOL.md`;
- task/status conventions.

Если в новом проекте нет этих файлов, skill переносится как шаблон процедуры, а не как готовая автоматизация.

### Вариант B: как архив для ручной передачи

Подходит для обмена между людьми/агентами без установки.

```powershell
Compress-Archive -LiteralPath .\skills\pipeline-operator -DestinationPath .\tmp-work\pipeline-operator-skill.zip -Force
```

Перед использованием получатель должен распаковать архив, прочитать `SKILL.md` и проверить пути.

### Вариант C: как база для будущего plugin

Использовать только когда skill реально нужен в нескольких проектах и требует автозагрузки, собственных tools или packaged distribution.

Порог перехода к plugin:

- skill используется в 3+ проектах;
- нужны MCP tools/resources;
- нужны versioning/install/update hooks;
- нужны marketplace metadata;
- есть тесты на переносимость;
- есть владелец поддержки.

До этого `skills/*/SKILL.md` дешевле и честнее.

## Чеклист перед переносом

- [ ] `SKILL.md` прочитан полностью.
- [ ] Все относительные пути проверены в новой среде.
- [ ] Команды не требуют отсутствующих Python-пакетов или внешних сервисов.
- [ ] Нет обещания автоматической загрузки, если среда её не поддерживает.
- [ ] Безопасные ограничения сохранены: no secrets, no execute without sandbox, no silent decision changes.
- [ ] В новом проекте есть место для отчётов: `docs/`, `queues/outbox/` или аналог.
- [ ] Понятно, кто утверждает решения: человек, maintainer или policy.

## Рекомендация для агентов

Если агент видит `skills/` в проекте, он должен относиться к ним как к локальной инструкции, а не как к магической возможности среды. Правильный порядок:

1. прочитать `skills/README.md`;
2. выбрать релевантный skill;
3. прочитать `SKILL.md` полностью;
4. проверить, какие команды реально есть в текущем repo;
5. выполнить или честно зафиксировать, что перенос требует адаптации.

## Мнение Codex

Текущая стадия — правильная для L3: skills уже уменьшают повторение и стабилизируют процесс, но ещё не требуют plugin-инфраструктуры. Преждевременный plugin добавит установку, версионирование и поддержку раньше, чем доказана необходимость. Лучший следующий шаг — dogfood: применять эти skills в задачах, уточнять формулировки и только потом решать, какой из них заслуживает L5 packaging.
