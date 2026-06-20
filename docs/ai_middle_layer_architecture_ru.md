# Архитектура промежуточного слоя между Codex, Windows, GitHub/сервером и большой базой информации

Дата: 2026-06-19

## Главная мысль

Codex сам по себе не должен превращаться в операционную систему. Операционная система тоже не должна становиться AI-приложением. Практичная середина - это отдельный "информационный слой" между AI и файлами/программами/сервером.

Этот слой должен делать четыре вещи:

1. Давать AI понятные дорожные карты: где что лежит, какие правила, какие форматы, какие задачи.
2. Давать AI безопасные инструменты: не "делай что хочешь на компьютере", а строго описанные функции.
3. Давать AI память о корпусе: индексы, метаданные, связи, версии, результаты прошлой обработки.
4. Давать человеку контроль: dry-run, журнал действий, подтверждения, копии вместо изменения оригиналов.

Идеальное устройство: Codex наверху как координатор, Windows/сервер/файлы внизу как среда, а между ними - skills, plugins, MCP-серверы, локальные сервисы, индексы, базы данных, адаптеры, агенты и проверочные правила.

## Почему одного Codex мало

Codex хорошо умеет читать код, писать скрипты, запускать команды, анализировать папки, создавать документы и работать как инженерный агент. Но если задача - десятки гигабайт документов, сотни репозиториев, социально-правовые темы, OCR, версии, поиск, шаблоны, доказательства, GitHub, локальные программы и сервер, то одного чата недостаточно.

Проблемы без промежуточного слоя:

- каждый раз надо заново объяснять структуру;
- контекст модели ограничен;
- AI не должен держать в prompt весь архив;
- команды могут быть опасны без ограничений;
- нет стабильного индекса документов;
- нет единых метаданных;
- нет реестра инструментов;
- нет ясной границы между "прочитать", "скопировать", "изменить", "удалить";
- трудно повторить результат через месяц;
- трудно понять, какие агенты за что отвечают.

## Почему полноценная операционная система слишком много

ОС уже умеет хранить файлы, запускать процессы, давать права, работать с сетью, устройствами, пользователями. Переписывать ОС ради AI не нужно.

AI-слой должен использовать ОС, а не заменять её:

- Windows остаётся местом файлов, программ, драйверов, приложений;
- GitHub/сервер остаётся местом кода, версий, CI, удалённых задач;
- локальная база остаётся в папке проекта;
- AI получает не полный хаотический доступ, а структурированные входы и инструменты.

## Правильная середина: Information Workbench Layer

Можно назвать это:

- AI workbench;
- локальная информационная платформа;
- knowledge operating layer;
- документный middleware;
- локальная AI-инфраструктура;
- проектная информационная шина.

По сути это не одна программа, а набор папок, правил, скриптов, индексов, API и навыков.

## Общая схема

```text
                        Человек
                           |
                           v
                        Codex
      ------------------------------------------------
      | AGENTS.md | Skills | Plugins | Custom Agents |
      ------------------------------------------------
                           |
                           v
                 MCP / tools / local APIs
      ------------------------------------------------
      | file driver | OCR driver | GitHub driver     |
      | PDF driver  | DOCX driver| search driver     |
      | DB driver   | web driver | report driver     |
      ------------------------------------------------
                           |
                           v
              Индексы, SQLite, JSONL, Markdown
      ------------------------------------------------
      | documents.db | keyword index | vector index   |
      | entities     | tasks         | audit log      |
      ------------------------------------------------
                           |
                           v
             Windows / GitHub / server / NAS / cloud
      ------------------------------------------------
      | Downloads | Documents | repos | apps | APIs   |
      ------------------------------------------------
```

## Разделение понятий

### 1. Инструкция

Инструкция говорит Codex, как работать.

Примеры:

- `AGENTS.md`
- `README_WORKFLOW.md`
- правила проекта;
- ограничения безопасности;
- названия папок;
- команды проверки.

Когда использовать:

- если это постоянные правила проекта;
- если надо, чтобы Codex всегда помнил: "оригиналы не трогать", "сначала dry-run", "персональные данные отдельно".

### 2. Skill

Skill - это повторяемая процедура. Не просто текст, а инструкция "когда делать, что читать, какие скрипты запускать, какой результат создать".

Примеры skills:

- `sort-social-documents`
- `extract-pdf-docx`
- `build-social-index`
- `analyze-german-social-law`
- `create-objection-draft`
- `merge-case-file`
- `split-large-document`
- `anonymize-sensitive-docs`

Когда использовать:

- если задача повторяется;
- если workflow можно описать пошагово;
- если не нужен отдельный сервер.

### 3. Plugin

Plugin - это упаковка нескольких skills, MCP-конфигурации, assets, hooks и настроек. Skill - это рабочая процедура, plugin - установочный пакет.

Примеры plugins:

- `social-work-knowledge-plugin`
- `local-documents-plugin`
- `svend4-corpus-plugin`
- `legal-templates-plugin`
- `downloads-triage-plugin`

Когда использовать:

- если skills стало много;
- если нужно переносить их между проектами;
- если надо упаковать MCP-сервер и UI/ресурсы;
- если нужна локальная "витрина" инструментов.

### 4. MCP-сервер

MCP-сервер - это мост между AI и внешней системой. Он может давать модели инструменты, ресурсы и prompt-шаблоны.

Три типа возможностей:

- tools: действия, например `search_documents`, `copy_file`, `ocr_scan`, `build_index`;
- resources: данные, например список документов, схема базы, файл, результат поиска;
- prompts: готовые сценарии, например "проанализируй Bescheid", "составь Widerspruch", "сделай доказательственный список".

Когда использовать:

- если нужно, чтобы Codex или другой AI-клиент стабильно вызывал функции;
- если нужна работа с большим корпусом через API, а не через ручной shell;
- если надо подключать не только Codex, но и другие AI-приложения.

### 5. Локальный сервис

Локальный сервис - это программа, которая постоянно или по команде обслуживает базу.

Примеры:

- FastAPI-сервис поиска;
- SQLite API;
- локальный OCR worker;
- watcher для Downloads;
- web-портал;
- queue worker для пакетной обработки.

Когда использовать:

- если операции долгие;
- если нужны несколько клиентов;
- если нужен UI;
- если индексы надо обновлять автоматически.

### 6. Агент

Агент - это не просто prompt. Хороший агент имеет:

- роль;
- ограниченную область;
- доступные инструменты;
- входные данные;
- формат результата;
- критерии остановки;
- правила безопасности.

Примеры агентов:

- `intake_agent`: принимает новые документы и классифицирует;
- `ocr_agent`: ищет сканы и запускает OCR;
- `social_law_agent`: ищет нормы SGB IX/XII и социальные темы;
- `evidence_agent`: собирает доказательства и пропуски;
- `template_agent`: находит шаблоны заявлений;
- `summary_agent`: делает краткое резюме документов;
- `qa_agent`: отвечает на вопросы по локальному корпусу;
- `audit_agent`: проверяет, что не изменены оригиналы.

## Уровни архитектуры от простого к сложному

### Уровень 0. Простая папка проекта

Это самый лёгкий вариант. Нужен уже сейчас.

```text
project/
  AGENTS.md
  README.md
  tools/
  data/
    originals/
    copies/
    text/
    indexes/
    reports/
  docs/
  outputs/
```

Что даёт:

- порядок;
- понятные правила;
- меньше риска испортить Downloads;
- можно работать с Codex без сложного сервера.

Минусы:

- нет настоящего API;
- автоматизация ограничена скриптами;
- сложно подключать другие AI-клиенты.

### Уровень 1. Skills внутри проекта

Добавляется `.agents/skills`.

```text
project/
  .agents/
    skills/
      sort-social-documents/
        SKILL.md
      extract-documents/
        SKILL.md
      build-index/
        SKILL.md
      answer-from-corpus/
        SKILL.md
```

Что даёт:

- Codex сам видит доступные процедуры;
- каждая задача описана отдельно;
- не надо каждый раз писать длинные инструкции;
- можно постепенно наращивать "способности" проекта.

Минусы:

- skill сам по себе не делает магии;
- скрипты всё равно надо писать и тестировать;
- если skills слишком много, их надо хорошо описывать.

### Уровень 2. Локальные Python-скрипты как информационные драйверы

Здесь появляются "драйверы" для типов информации.

```text
tools/
  drivers/
    file_driver.py
    pdf_driver.py
    docx_driver.py
    xlsx_driver.py
    ocr_driver.py
    github_driver.py
    web_driver.py
    search_driver.py
    report_driver.py
```

Примеры функций:

- `scan_folder(path)`
- `extract_text(file)`
- `detect_language(text)`
- `classify_social_topic(text)`
- `copy_to_project(file)`
- `build_keyword_index()`
- `search(query)`
- `merge_documents(list)`
- `split_document(file)`
- `anonymize(file)`

Что даёт:

- детерминированность;
- повторяемость;
- можно тестировать;
- Codex вызывает готовые инструменты, а не каждый раз изобретает команды.

Минусы:

- надо написать и поддерживать код;
- нужна система логирования;
- нужны тестовые документы.

### Уровень 3. SQLite/JSONL как память корпуса

Без базы большой корпус быстро становится хаосом.

Минимальные таблицы:

```text
documents
  id
  source_path
  project_path
  sha256
  file_type
  title
  language
  created_at
  imported_at
  text_path
  category
  confidence
  pii_level
  status

chunks
  id
  document_id
  chunk_no
  heading
  text
  tokens

entities
  id
  document_id
  type
  value
  normalized_value

tasks
  id
  document_id
  task_type
  status
  assigned_agent
  result_path

audit_log
  id
  timestamp
  actor
  action
  target
  result
```

Что даёт:

- можно искать;
- можно обновлять;
- можно отслеживать обработку;
- можно строить отчёты;
- можно не загружать весь корпус в prompt.

Минусы:

- нужно продумать схему;
- нужна миграция при изменениях;
- надо следить за путями и дублями.

### Уровень 4. Индексы

Нужны несколько индексов, потому что один индекс не решает все задачи.

Типы индексов:

- full-text index: быстрый поиск слов;
- keyword index: словарь терминов;
- BM25/passages: поиск релевантных абзацев;
- entity index: люди, учреждения, законы, даты, суммы;
- vector index: смысловой поиск;
- graph index: связи между документами, законами, темами;
- timeline index: события и сроки.

Для социальной темы особенно важны:

- `SGB IX`
- `SGB XII`
- `Persönliches Budget`
- `Eingliederungshilfe`
- `Teilhabe`
- `Pflege`
- `Assistenz`
- `Arbeitgebermodell`
- `ICF`
- `Bedarfsermittlung`
- `Bescheid`
- `Widerspruch`
- `Klage`
- `Frist`

### Уровень 5. Локальный MCP-сервер

MCP-сервер превращает проект в набор понятных инструментов для AI.

Минимальные tools:

```text
list_collections()
scan_downloads()
import_files(dry_run: bool)
extract_text(document_id)
search_documents(query, filters)
get_document(document_id)
get_chunks(document_id)
classify_document(document_id)
find_duplicates()
build_index()
summarize_document(document_id)
make_topic_report(topic)
anonymize_document(document_id, dry_run: bool)
merge_documents(document_ids)
split_document(document_id)
```

Resources:

```text
kb://documents
kb://document/{id}
kb://topic/{name}
kb://schema
kb://audit-log
kb://templates
```

Prompts:

```text
analyze_bescheid
draft_widerspruch
extract_social_law_issues
build_evidence_checklist
summarize_case_file
compare_old_new_document
```

Что даёт:

- Codex видит инструменты как API;
- можно подключать другие клиенты;
- можно ограничить опасные операции;
- проще делать человеческое подтверждение.

Минусы:

- надо писать сервер;
- надо думать про безопасность;
- нужно отдельно тестировать схемы и права.

### Уровень 6. Плагины Codex

Когда skills и MCP стабилизировались, их можно упаковать в plugin.

```text
plugins/
  social-work-knowledge/
    .codex-plugin/
      plugin.json
    skills/
      intake/
        SKILL.md
      social-law-analysis/
        SKILL.md
      evidence-checklist/
        SKILL.md
      report-builder/
        SKILL.md
    mcp/
      server.py
    hooks/
      hooks.json
    assets/
```

Что даёт:

- переносимость;
- установка через marketplace;
- объединение skills + MCP + hooks;
- можно включать/выключать как модуль.

Минусы:

- рано делать plugin, пока workflow не стабилен;
- plugin усложняет отладку;
- нужен контроль версий.

### Уровень 7. Локальные custom agents

Агенты полезны, когда есть независимые роли.

Пример:

```text
.codex/
  agents/
    social-law-reviewer.toml
    document-intake.toml
    ocr-specialist.toml
    evidence-reviewer.toml
    portal-builder.toml
```

Каждый агент должен иметь:

- короткое имя;
- описание, когда его использовать;
- инструкции;
- доступные MCP/tools;
- sandbox/policy;
- формат результата.

Пример роли:

```toml
name = "social-law-reviewer"
description = "Reviews German social-law documents for SGB IX/XII, Eingliederungshilfe, Persönliches Budget, deadlines, evidence gaps, and next-step questions."
developer_instructions = """
Work only from provided project documents and cited official sources.
Do not give final legal advice.
Separate facts, uncertainty, and recommended verification.
Return: summary, relevant norms, missing evidence, deadlines, next actions.
"""
```

Плюсы:

- параллельная работа;
- специализация;
- меньше смешивания задач;
- можно запускать несколько проверок.

Минусы:

- больше расход токенов;
- риск противоречивых результатов;
- нужен главный координатор;
- нельзя давать агентам слишком широкие права.

### Уровень 8. Серверный вариант

Если локально тяжело запускать репозитории, OCR, индексы и веб-портал, можно вынести часть на сервер.

Вариант:

```text
Windows laptop
  Codex app
  project folder
  small local scripts
  encrypted config
        |
        v
Server / VPS / homelab
  Git repos
  Python services
  PostgreSQL / SQLite
  full-text search
  vector DB
  OCR workers
  web portal
  MCP HTTP server
        |
        v
GitHub
  source code
  issues
  actions
  versioned plugins/skills
```

Что локально:

- интерфейс Codex;
- выбранные копии документов;
- приватные ключи;
- ручные проверки;
- маленькие быстрые скрипты.

Что на сервере:

- тяжёлая обработка;
- индексация;
- web UI;
- API;
- расписания;
- фоновая очередь.

Плюсы:

- больше мощности;
- можно запускать долго;
- проще делать портал;
- можно подключать несколько клиентов.

Минусы:

- сложнее безопасность;
- персональные данные нельзя отправлять без продуманной защиты;
- нужен backup;
- нужен контроль доступа;
- сервер надо администрировать.

## Конкретный план для вашего проекта

### Шаг 1. Создать проектную конституцию

Файл:

```text
AGENTS.md
```

Содержание:

- оригиналы не изменять;
- все операции с Downloads сначала dry-run;
- копии хранить в проекте;
- персональные данные помечать;
- удаление запрещено без отдельного подтверждения;
- результат каждой обработки писать в CSV/Markdown/SQLite;
- для социальных тем всегда указывать уверенность и источники.

### Шаг 2. Зафиксировать структуру папок

```text
social_ai_workbench/
  AGENTS.md
  README.md
  .agents/
    skills/
  .codex/
    agents/
    config.toml
  tools/
    drivers/
    pipelines/
    mcp_server/
    tests/
  data/
    00_inbox/
    01_originals/
    02_copies/
    03_text/
    04_chunks/
    05_indexes/
    06_reports/
    07_exports/
    08_audit/
  docs/
    architecture/
    social_taxonomy/
    templates/
  plugins/
```

### Шаг 3. Сделать реестр документов

Сначала простой CSV, потом SQLite.

Минимальные поля:

```text
id, original_path, copy_path, sha256, file_type, size, title,
language, category, score, status, pii_level, notes
```

### Шаг 4. Сделать набор драйверов

Первый набор:

- `file_inventory_driver.py`
- `copy_driver.py`
- `text_extract_driver.py`
- `classification_driver.py`
- `dedupe_driver.py`
- `report_driver.py`

Второй набор:

- `ocr_driver.py`
- `anonymization_driver.py`
- `chunking_driver.py`
- `search_driver.py`
- `github_repo_driver.py`
- `web_source_driver.py`

Третий набор:

- `mcp_tools_driver.py`
- `agent_task_driver.py`
- `portal_export_driver.py`
- `timeline_driver.py`
- `evidence_driver.py`

### Шаг 5. Сделать первые skills

```text
.agents/skills/
  downloads-social-intake/
  document-text-extraction/
  social-law-classification/
  evidence-checklist/
  topic-report-builder/
  local-wiki-export/
```

Каждый skill должен иметь:

- когда запускать;
- какие файлы читать;
- какие скрипты запускать;
- что запрещено;
- какой результат создать.

### Шаг 6. Использовать уже найденные репозитории svend4

Практически:

- `lorenzo`: взять идеи `docs-toolkit`, индексы, Markdown-корпус, RAG, Obsidian/HTML.
- `daten20`: взять document processing, OCR, anonymizer, search, comparator, merger/splitter.
- `data20`: взять структуру knowledge management.
- `data70`: взять архив социальных разговоров и словарь тем.
- `soz140`: взять доменную карту SGB IX, Persönliches Budget, Assistenz.
- `nautilus`: взять принцип портала и адаптеров.
- `universal-file-storage-mcp`: взять идею MCP-доступа к файлам.
- `info1`: взять концепцию домашней информационной системы.
- `info7/info40`: взять агентные роли и оркестрацию позже.

### Шаг 7. Сделать локальный поиск

Сначала без сложной нейросети:

- SQLite FTS;
- keyword index;
- BM25 по абзацам;
- фильтры по категории, языку, типу файла;
- CSV/Markdown отчёты.

Потом:

- embeddings;
- vector search;
- graph search;
- RAG.

Важно: смысловой поиск не заменяет обычный. Для юридических документов точные слова и нормы часто важнее embeddings.

### Шаг 8. Сделать локальную "Википедию"

Самый простой вариант:

- Markdown + Obsidian.

Средний вариант:

- статический HTML.

Сложный вариант:

- web-приложение с поиском, фильтрами, карточками документов, графом и timeline.

Страницы:

```text
Главная
Темы
Документы
Законы
Шаблоны
Доказательства
Сроки
Люди/организации
Вопросы и ответы
Источники
Журнал обработки
```

### Шаг 9. Сделать MCP-сервер

Начать с read-only:

- `search_documents`
- `get_document`
- `get_topic`
- `list_recent_imports`
- `get_audit_log`

Потом добавить safe-write:

- `import_file_copy`
- `write_report`
- `create_index`

Опасные операции:

- delete;
- move originals;
- overwrite;
- send to internet;
- anonymize replacing source.

Их лучше не давать MCP вообще или требовать отдельного подтверждения.

### Шаг 10. Сделать серверный вариант только после локального MVP

Не начинать с Kubernetes, Docker swarm, enterprise dashboard. Сначала локальный MVP:

1. 100 документов.
2. Извлечение текста.
3. Индекс.
4. Поиск.
5. Один отчёт.
6. Один skill.
7. Один read-only MCP tool.

Потом масштабировать.

## Варианты решения

### Вариант A. Минимальный

Только проектная папка, скрипты, Markdown/CSV.

Подходит:

- для первого месяца;
- для проверки идеи;
- если данных не очень много.

Плюсы:

- быстро;
- понятно;
- мало зависимостей;
- легко контролировать.

Минусы:

- нет настоящего API;
- слабая автоматизация;
- сложнее масштабировать.

### Вариант B. Практический локальный workbench

Папка + skills + SQLite + индексы + несколько drivers.

Подходит:

- для реальной работы с Downloads;
- для социальной базы;
- для локальной Википедии.

Плюсы:

- достаточно мощно;
- не слишком сложно;
- всё остаётся локально;
- Codex хорошо с этим работает.

Минусы:

- надо поддерживать код;
- нужны тесты;
- надо продумать backup.

### Вариант C. Локальный MCP + Codex plugin

Workbench + MCP-сервер + plugin.

Подходит:

- если нужно подключать инструменты к Codex системно;
- если skills стало много;
- если хочется переиспользовать в разных проектах.

Плюсы:

- чистая архитектура;
- AI видит tools/resources/prompts;
- можно подключать другие клиенты;
- лучше контроль доступа.

Минусы:

- сложнее разработка;
- надо писать схемы;
- надо тестировать безопасность.

### Вариант D. Серверная платформа

Локальный Codex + сервер с API, индексами, очередями, web UI.

Подходит:

- если данных десятки гигабайт;
- если OCR и индексация тяжёлые;
- если нужно работать с нескольких устройств;
- если проект становится долгосрочным.

Плюсы:

- масштабируемость;
- фоновые задачи;
- web-портал;
- GitHub/CI;
- лучше для больших архивов.

Минусы:

- безопасность сложнее;
- нужны права, backup, обновления;
- выше стоимость времени и администрирования.

### Вариант E. Полная агентная система

Сервер + MCP + plugin + custom agents + очередь задач + evals + observability.

Подходит:

- для исследовательского проекта;
- для команды;
- если надо много автоматических ролей;
- если нужны эксперименты с агентами.

Плюсы:

- гибко;
- расширяемо;
- похоже на настоящую AI-инфраструктуру;
- можно делать сложные workflows.

Минусы:

- легко переусложнить;
- агенты могут ошибаться;
- нужны проверки, логи, evals;
- без чистого корпуса будет хаос.

## Что считать "информационным драйвером"

Информационный драйвер - это маленький модуль, который превращает кусок реальности в понятный для AI объект.

Примеры:

### File driver

Знает:

- где файл;
- какой тип;
- какой hash;
- можно ли читать;
- куда копировать;
- как проверить дубликат.

### PDF driver

Знает:

- как извлечь текст;
- есть ли текстовый слой;
- нужны ли OCR;
- сколько страниц;
- есть ли таблицы.

### Social-law driver

Знает:

- ключевые термины SGB IX/XII;
- категории;
- нормы;
- типы документов;
- шаблоны;
- рискованные места.

### Evidence driver

Знает:

- какие доказательства есть;
- чего не хватает;
- какие документы относятся к какому утверждению;
- какие сроки и адресаты связаны.

### Portal driver

Знает:

- как из базы сделать Markdown/HTML;
- как построить индекс страниц;
- как связать темы.

## Что считать "пассивным агентом"

Пассивный агент - это не постоянно работающая программа. Это подготовленная роль, инструкция и набор инструментов, которые активируются только при задаче.

Пример:

```text
agents/
  intake_agent.md
  social_law_agent.md
  evidence_agent.md
  summary_agent.md
  qa_agent.md
```

Пассивный агент должен отвечать на вопросы:

- когда меня использовать;
- какие документы я читаю;
- какие инструменты мне разрешены;
- какие решения я не имею права принимать;
- какой результат я обязан вернуть.

Это удобно, потому что не надо держать десятки процессов постоянно. Они существуют как структурированная возможность.

## Безопасность

Главные правила:

1. Оригиналы только read-only.
2. Любые изменения - только в проектной копии.
3. Удаление запрещено по умолчанию.
4. Массовые операции сначала dry-run.
5. Интернет-отправка документов запрещена без явного решения.
6. Персональные данные маркировать.
7. Логи сохранять.
8. Все инструменты с write-доступом должны иметь allowlist папок.
9. Каждый dangerous tool должен требовать подтверждения.
10. Юридические выводы отделять от фактов.

## Где хранить что

### В `AGENTS.md`

- общие правила проекта;
- безопасность;
- стиль отчётов;
- какие команды разрешены;
- где лежат данные.

### В `.agents/skills`

- workflows;
- процедуры;
- инструкции для повторяемых задач.

### В `tools/`

- Python-скрипты;
- драйверы;
- тесты;
- CLI.

### В `.codex/agents`

- кастомные роли агентов;
- разные модели/режимы/ограничения;
- специализированные инструкции.

### В `plugins/`

- упакованные skills;
- MCP config;
- hooks;
- assets.

### В `data/`

- копии;
- текст;
- индексы;
- отчёты;
- audit.

### На GitHub

- код;
- skills/plugins;
- документация;
- issues;
- версии;
- CI.

Не хранить на публичном GitHub:

- персональные документы;
- медицинские документы;
- частные письма;
- полные case files;
- ключи и токены.

## Как это соединить с GitHub

GitHub полезен не как место для всех документов, а как место для:

- кода;
- инструментов;
- правил;
- шаблонов;
- документации;
- issues;
- версий архитектуры.

Схема:

```text
GitHub repo
  tools/
  skills/
  plugins/
  docs/
  tests/

Local private data
  documents/
  indexes/
  reports/
  secrets/
```

В GitHub можно хранить:

- `sort_social_downloads.py`
- `mcp_server.py`
- `SKILL.md`
- шаблоны Markdown;
- тестовые обезличенные документы;
- инструкции.

Локально хранить:

- реальные Downloads;
- личные документы;
- медицинские документы;
- OCR-результаты с персональными данными.

## Как это соединить с Windows

Windows-слой:

- PowerShell;
- файловая система;
- Task Scheduler;
- установленные программы;
- локальные Python/Node;
- Tesseract/OCR;
- браузер;
- Office/LibreOffice;
- WSL, если нужен Linux-слой.

AI не должен "бродить" по Windows без карты. Ему надо дать:

- allowlist папок;
- список tools;
- понятные команды;
- read-only scan;
- отдельную папку вывода.

## Что можно сделать из уже созданного результата Downloads

У вас уже есть:

```text
social_downloads_review_final/
  copies/
  index_social_documents.csv
  README_social_documents.md
  SUMMARY_RU.md
```

Это можно сделать seed-корпусом:

1. Перенести в `data/02_copies`.
2. Создать SQLite `documents.db`.
3. Сгенерировать Markdown для каждого документа.
4. Построить keyword/BM25 index.
5. Создать страницы тем.
6. Подключить skill `answer-from-social-corpus`.
7. Затем сделать MCP read-only tool `search_social_documents`.

## Минимальный MVP на 2-3 дня

### День 1

- `AGENTS.md`
- структура папок;
- `documents.db`;
- импорт текущего CSV;
- базовый `search.py`;
- отчёт по темам.

### День 2

- skill `downloads-social-intake`;
- skill `build-social-index`;
- extraction для PDF/DOCX/TXT;
- BM25/keyword search;
- Markdown topic pages.

### День 3

- read-only MCP server;
- tools: search/get/list;
- prompt templates;
- тесты на 10 документов;
- краткий HTML/Obsidian export.

## Дальнейшая дорожная карта

### Версия 0.1

- копии документов;
- CSV/SQLite;
- базовый поиск;
- 2 skills;
- ручные отчёты.

### Версия 0.2

- OCR;
- dedupe;
- классификация;
- entity extraction;
- Obsidian vault.

### Версия 0.3

- MCP read-only;
- topic reports;
- QA по корпусу;
- audit log.

### Версия 0.4

- anonymizer;
- report builder;
- merge/split;
- timeline;
- evidence checklist.

### Версия 0.5

- plugin;
- custom agents;
- local portal;
- background indexing.

### Версия 1.0

- серверный вариант;
- web UI;
- user roles;
- backups;
- scheduled processing;
- evals and guardrails.

## Главные риски

### Риск 1. Переусложнение

Самая частая ошибка - сразу строить агентную платформу. Правильно: сначала чистый корпус и поиск.

### Риск 2. Персональные данные

Социальные и медицинские документы чувствительны. Нельзя бездумно отправлять их в внешние API.

### Риск 3. Галлюцинации

AI может уверенно ошибаться. Поэтому нужны ссылки на документы, цитаты, номера страниц, уровень уверенности.

### Риск 4. Массовые операции

Сортировка, переименование, удаление и перемещение должны быть dry-run-first.

### Риск 5. Непроверенный код из репозиториев

Код svend4 может быть полезным, но его нельзя запускать целиком без аудита. Брать идеи, отдельные скрипты, проверять зависимости и запускать на копиях.

## Моя рекомендация

Лучший путь - не "большая AI-ОС", а локальный AI workbench:

1. Project rules: `AGENTS.md`.
2. Data layer: копии, текст, SQLite, индексы.
3. Tools layer: Python drivers.
4. Workflow layer: skills.
5. API layer: read-only MCP.
6. Distribution layer: plugin.
7. Agent layer: custom agents.
8. Server layer: только когда локальный MVP доказал пользу.

Так Codex остаётся сильным координатором, Windows остаётся надёжной средой, GitHub остаётся хранилищем кода, а между ними появляется управляемая инфраструктура для больших объёмов информации.

## Источники и опорные идеи

- Codex manual: skills, AGENTS.md, plugins, MCP, hooks, custom agents.
- OpenAI Agents SDK: агенты как приложения, которые планируют, вызывают tools, сотрудничают между специалистами и держат состояние.
- Model Context Protocol documentation: client-server architecture, tools, resources, prompts.
- `svend4/lorenzo`: docs-toolkit, Markdown-корпус, RAG, MCP, поиск.
- `svend4/daten20`: document management, OCR, search, anonymization, compare, merge/split.
- `svend4/data20`: knowledge management folder structure.
- `svend4/nautilus`: portal/adapters/compatibility-not-merger.
- `svend4/data70` and `soz140`: социально-правовой доменный корпус.
