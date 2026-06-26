---
id: offline-headless-workbench-mvp-2026-06-26
type: topic
title: Offline/headless Zed-like workbench — реалистичный MVP (план, подтверждён Goodall)
status: proposed
date: 2026-06-26
author: claude-opus-4-8
related: [repo-as-collaborative-dev-service-2026-06-26, inf-format-cross-pollination-2026-06-26, inf-questionnaire-expanded-2026-06-26]
---

# 0. Визитка
> Goodall подтвердил практический путь: **НЕ копировать Zed как GUI**, а сделать **offline/headless
> Zed-like workbench** — мульти-агентная среда совместной работы без браузера/облака, на локальной модели.
> Это конкретизация «репо как collaborative-dev-service» в исполнимый MVP. 6 компонентов; почти все
> заземлены в том, что у нас УЖЕ есть — новизна только в сборке.

# 1. Принцип (почему headless, а не GUI-клон)
- Zed-сила (мультиплеер-агенты, CRDT-буфер, ACP) ценна, но его коллаборация **облачная** (relay-серверы),
  а GUI на Rust/GPUI — не наш путь (Termux/терминал/файлы).
- Реалистично: взять **модель работы** Zed (агенты = равноправные писатели над общим состоянием), но
  субстрат — наш канон (Markdown+git), а оболочка — **headless** (терминал/файлы), модель — **локальная**.
- Анти-FM-1: workbench собирается из существующих кусков + тонких новых, не как большая новая платформа.

# 2. Шесть компонентов (что · заземление в репо · MVP-форма)
| # | компонент | что | у нас уже есть | MVP-форма / новое |
|---|---|---|---|---|
| 1 | **Локальная модель** | offline LLM, OpenAI-совместимый endpoint | тулы model-agnostic | `llama-server` (llama.cpp) / Ollama; тонкий клиент-указатель на endpoint |
| 2 | **Terminal-thread runner** | процесс на тред: читает Markdown-тред, гоняет агент-цикл, пишет назад | `pipeline.py`/conveyor (pickup+run), queues/ | runner: thread-файл → вызов модели → append+commit; Termux-friendly |
| 3 | **MCP gateway** | один MCP-сервер, к которому подключаются несколько агентов (общие тулы/доступ к канону) | MCP-тулы доступны; канон = файлы | минимальный локальный MCP над каноном (read/search/write-block); **отложить — сначала прямой файловый доступ** |
| 4 | **Markdown-треды** | единица работы = тред-файл (как Zed thread, но file-native): агент/модель/тулы/состояние | канон + queues/ ЭТО уже треды | конвенция thread-файла: front-matter (agent/model/tools/status) + тело = обмен |
| 5 | **SQLite/FTS память** | быстрый full-text поиск по канону + реестр доверия/verify-once | portals/view/edges (граф), seal_verified | индекс канона в SQLite FTS5; запрос → сборка контекста (питает `view.py`) |
| 6 | **Строгая песочница черновиков кода** | код-черновики изолированы; execute OFF by default; human-gate | D-014, `execute_human_gate.py`, `sandbox/`, variants/code-divergence-sandbox | концепт-блоки в `variants/code/`; исполнение за Docker+human-gate |

# 3. Архитектура (как компоненты складываются)
```
СУБСТРАТ (общее состояние):
  канон = Markdown-файлы + git + CRDT-merge (crdt_merge/seq_merge/git_reconcile — конкурентная запись решена)
  + SQLite/FTS индекс (быстрый retrieval) + view/view_html (срезы, progressive disclosure)

РАНТАЙМ (headless):
  N terminal-thread runner'ов (по агенту) → локальная модель (llama-server)
  ↕ доступ к канону: прямой файловый (MVP) → позже MCP gateway (общие тулы)
  оркестрация: claim/lock + synthesis-gate (queues/claimed, observer→integrator) — НЕ нужен GUI

GOVERNANCE (наш слой, которого нет у Zed/infon-board):
  PROTOCOL/decisions · red_team_gate/oracle_quorum (доверие) · seal_verified/provenance (целостность)
  · песочница D-014 (код OFF by default)
```
Человек смотрит не в GUI, а: `view_html` (компиляция среза в `<details>`-HTML) или Rich/Textual в терминале.

# 4. MVP-срез (FM-1: минимум, что доказывает гипотезу)
1. `llama-server` локально (компонент 1).
2. ОДИН terminal-thread runner: читает thread-файл → вызывает модель → append результата → commit (компонент 2+4).
3. SQLite FTS5 индекс канона; runner тянет контекст запросом, не весь репо (компонент 5, питает `view.py`).
4. ДВА агента над общим каноном, конкуренция решается `git_reconcile`/`crdt_merge` (уже построено).
5. Код-черновики = концепт-блоки в `variants/code/`, БЕЗ исполнения (компонент 6 — только sandbox-каркас).
6. **Отложить:** MCP gateway (прямой файловый доступ), оркестратор-доска, real execution.

# 5. Фальсификация (окупается ли workbench)
Реальная задача (срез канона/NormenKG под казус): два offline-агента над общим каноном vs наивное «оба
читают всё, конфликты вручную». Мерить: контекст-токены (FTS+view срез vs полный), merge-конфликты
(git_reconcile vs строчные), число проходов, качество (на локальной модели). Гипотеза верна, если
FTS-retrieval + field/line-merge режут координацию без потери качества (как harness `.inf`-беседы: 76.5%→43%).

# 6. Что переиспользуется (почти всё готово)
- конкурентная запись → `crdt_merge`+`seq_merge`+`git_reconcile` (T-263 решён);
- подача контекста → `view.py`+`view_html` (срезы, меню→детали);
- доверие/валидация → `oracle_quorum`+`red_team_gate`;
- провенанс → `seal_verified`+`provenance_independence`;
- песочница/код → D-014 + `execute_human_gate` + variants/code-divergence-sandbox.
**Новое для MVP:** только (a) terminal-thread runner, (b) SQLite/FTS индекс, (c) thread-файл конвенция,
(d) тонкий клиент к local-model. Четыре куска — не платформа.

# 7. Этапы (roadmap)
1. SQLite/FTS индекс канона + интеграция в `view.py` (retrieval-срез).
2. thread-файл конвенция + одиночный terminal-thread runner на `llama-server`.
3. Два агента + `git_reconcile` как merge-driver (конкуренция вживую).
4. Фальсификация (§5) на реальной задаче.
5. Позже: MCP gateway, оркестратор-доска (`view_html` как поверхность), real execution за human-gate.
