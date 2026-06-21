---
id: architecture-docs-recheck-2026-06-21
title: Architecture docs recheck — ранняя концепция и текущая стадия
status: done
owner: Codex
related: tasks/T-120.md, темы/ai-os-bridge.md, docs/ai_middle_layer_architecture_ru.md, docs/agent-layer-design.md, docs/mvp-roadmap.md, docs/layers-coverage.md, docs/bridge-usage.md
---

# Architecture docs recheck — ранняя концепция и текущая стадия

Дата: 2026-06-21.

## Где зафиксирована исходная подробная концепция

Ключевые ранние документы:

| Файл | Роль |
|---|---|
| `темы/ai-os-bridge.md` | Главная полилог-тема: проблема вершина/основание пирамиды, цель middleware, терминология Treiber/driver, выбор варианта B + MCP, первые задачи T-022..T-024. |
| `темы/information-drivers.md` | Архивная ранняя ветка Mavis с вариантами A-E, аналогиями про тропы/дорожки и каталогом информационных драйверов. |
| `docs/ai_middle_layer_architecture_ru.md` | Самый большой импортированный архитектурный документ: Information Workbench Layer, уровни 0-8, конкретный план, варианты A-E, MVP, риски, svend4. |
| `docs/agent-layer-design.md` | Технический разбор среднего слоя: MCP как драйверы/Treiber, lazy activation, каталог драйверов, варианты уровней, риски и фазы. |
| `docs/middle-layer-guide.md` | Человеческий гайд по среднему слою: соответствие метафор реальным технологиям, практический план Windows + Codex + сервер. |
| `docs/mvp-roadmap.md` | Ранний практический roadmap: стадия "локальный workbench", плюсы/минусы, первые драйверы, SQLite memory, safety checks. |
| `decisions/D-010.md` | Accepted-решение: стартовать с `drivers/`, вариант B -> E, read-only L2 PoC, svend4 без execute до песочницы. |
| `decisions/D-013.md` | Accepted driver schema v1: обязательные поля, timeout, max output, audit, source verification. |
| `decisions/D-015.md` | Accepted gate `draft -> ready`: код работает + перепроверка минимум двумя агентами, без обязательной подписи человека. |

Актуальные документы текущего состояния:

| Файл | Роль |
|---|---|
| `docs/layers-coverage.md` | Каноническая карта L0-L7 и текущая стадия реализации. |
| `docs/bridge-usage.md` | Операционный quick-start: что работает и какие команды запускать. |
| `drivers/CATALOG.md` / `drivers/index.json` | Машинный и Markdown-каталог драйверов. |
| `docs/execute-sandbox-preflight.md` | Safety gate до любого execute/svend4 запуска. |
| `docs/skills-usage.md` | Как использовать и переносить project skills, не называя их plugin. |

## Сверка исходной идеи с текущей реализацией

Исходная идея была: заполнить "пустую середину" между тонким AI-клиентом и большой ОС через слои drivers/MCP, skills, agents, память, правила и безопасность. По текущему состоянию это уже не только концепция.

Реализовано:

- file-native governance: `AGENTS.md`, `PROTOCOL.md`, `TASKS.md`, `QUESTIONS.md`, `DECISIONS.md`, темы, queues;
- динамический pipeline: atomic task ids, claims, done markers, `PIPELINE.md`, heartbeat/live;
- driver registry: `drivers/`, schema validation, generated catalog;
- read-only L2 drivers: `files`, `repo-runner`, `data`, `codex-local`, `gateway`, `git-log`, `sqlite`, плюс workbench/file-inventory контур;
- sync MCP acceptance: полный батч `27/27`;
- L6 memory/workflow: SQLite workbench, `tools/knowledge.py`, FTS5 search, `report --out`, `reports/`, safe corpus, regression-тест write-path safety;
- L3 project skills: `driver-acceptance`, `pipeline-operator`, `repo-review`, usage guide;
- safety: redaction, allowed-root, audit, mode/sandbox validate guard, execute preflight.

Не реализовано:

- execute/sandbox runner для непроверенного кода;
- реальное подключение svend4-репозиториев как read-only corpus/remote source;
- L5 plugin packaging/install lifecycle;
- vector/RAG слой поверх большого корпуса;
- официальный async MCP stdio path в проблемных Windows-средах.

## Текущая стадия

Концептуально: стадия перешла от "идея/обсуждение" к согласованной архитектуре с accepted-решениями. Базовая стратегия стабильна: file-native workbench, drivers/MCP, skills, read-only-first, execute только через песочницу.

Технически: это рабочий read-only прототип среднего слоя. Он уже умеет принимать задачи, вести полилог, проверять себя, подключать локальные драйверы, строить отчёты и индексировать знания. Это ещё не AI-OS, не серверная платформа и не система запуска чужого кода.

## Плюсы

- Выбран правильный масштаб: не "операционная система для ИИ", а управляемый слой возможностей.
- Markdown/front-matter удобны людям и агентам, а генераторы дают машинную навигацию.
- Read-only-first снижает риск при работе с чужими репозиториями и большими папками.
- Driver schema + validation + D-015 дают честный путь `draft -> ready`.
- Sync MCP acceptance обошёл Windows async stdio blocker и сделал приёмку воспроизводимой.
- L6 workflow уже создаёт проверяемые artifacts в `reports/`.

## Минусы и риски

- Проект легко уходит в meta-work: отчёты о системе начинают конкурировать с обработкой реальных данных.
- `T-020` остаётся orphan/blocker: без read-only доступа к svend4 или решения закрыть/переформулировать задачу эта ветка не двигается.
- Документация быстро дрейфует после технических коммитов; T-120 уже нашёл stale-строки про T-119.
- Нет настоящей execute-песочницы; это хорошо как запрет, но ограничивает следующий уровень.
- L6 пока проверен на маленьком synthetic corpus, не на большой реальной базе.
- Plugin/L5 пока только кандидат: переносимость skills описана, но install/update lifecycle отсутствует.

## Предложения по развитию

1. **P0: решить T-020.** Либо дать read-only путь к одному svend4/local repo, либо перевести T-020 в явный `blocked`/переформулировать в generic local repo inventory.
2. **P0: держать docs refresh после каждого крупного шага.** `docs/layers-coverage.md` и `docs/bridge-usage.md` должны быть коротким актуальным входом, а не историей.
3. **P1: расширить L6 на безопасный корпус 50-200 файлов.** Не vector/RAG сразу, а reports + FTS + сравнение результатов между запусками.
4. **P1: добавить driver drift check.** Проверять старый `source_last_verified` и расхождение `tools:` с MCP-сервером уже есть частично; стоит усилить alerts.
5. **P1: подготовить sandbox runner design отдельно от repo-runner.** Не расширять read-only driver до execute по привычке.
6. **P2: L5 plugin только после повторного использования.** Пока skills лучше держать project-local Markdown-процедурами.
7. **P2: async MCP compatibility оставить вторичным.** Sync acceptance работает; официальный async path нужен только если конкретный клиент требует его в этой Windows-среде.

## Мнение Codex

Текущая инфраструктура развивалась в правильном направлении. Самое ценное достижение — не отдельный драйвер, а дисциплина: задачи, claims, manifests, validation, acceptance и отчёты стали единым циклом. Но следующий прирост ценности должен идти не от новых мета-документов, а от реальных источников данных: один большой безопасный corpus, один read-only внешний репозиторий, один воспроизводимый отчёт с вопросами/ответами.

Главная граница остаётся прежней: пока нет песочницы, execute не открывать. Главный практический блокер: `T-020` нужно либо снабдить данными, либо честно снять с активной доски как orphan.
