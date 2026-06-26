---
id: mmorpg-2d-text-workbench-2026-06-26
type: topic
title: MMORPG reverse engineering into 2D text workbench for humans and agents
status: proposed
owner: codex
date: 2026-06-26
related:
  - text-diffusion-canvas-from-infon-2026-06-26
  - zed-like-headless-workbench-mvp
  - svend4-infon-assessment-2026-06-26
  - T-264
---

# MMORPG -> 2D Text Workbench

## 1. Оценка идеи

Идея сильная: взять не графику MMORPG, а её **организационную механику** и перевести в 2D-текстовую рабочую среду для людей и AI-агентов.

Это можно назвать:

```text
информационный реверсивный инжиниринг MMORPG
```

Не игра переносится в работу, а рабочая координация получает свойства, которые MMORPG давно умеют:

- много участников одновременно;
- разные роли;
- общая карта мира;
- локальные зоны;
- задания/квесты;
- статус участников;
- события во времени;
- инвентарь/артефакты;
- команды/рейды;
- видимые конфликты;
- лог действий;
- миникарта;
- разделение общего мира и инстансов.

Для нашего репозитория это очень подходящая метафора, потому проект уже имеет:

- `tasks/` как квесты;
- `topics/` как зоны мира;
- `streams/` как параллельные варианты/ручейки;
- `sandbox/` как тренировочные и опасные зоны;
- `worktree` как инстанс для отдельной группы;
- `queues/` как почта/биржа заданий;
- `DECISIONS.md` как законы мира;
- `validate.py`/`merge_gate.py` как судьи/охранные ворота;
- `thread.py` как начало долговечных игровых сессий/нитей.

## 2. Главная формула

```text
3D MMORPG world
  -> 2D semantic work map
  -> text cells/cards/events
  -> humans + AI agents as actors
  -> repository as persistent world state
```

В 3D MMORPG участники видят пространство и действуют в нём. В обычном чате участники видят только ленту. Для многоагентной работы лента слишком бедная.

Нужна 2D карта:

```text
горизонталь = участники / роли / стадии / время
вертикаль   = темы / задачи / документы / риски / решения
ячейки      = текстовые блоки, статусы, ссылки, отчёты, конфликты
```

## 3. Таблица соответствий

| MMORPG | 2D text workbench | В нашем репозитории |
|---|---|---|
| Мир | Общее информационное поле | весь repo |
| Локация | Тема / портал / папка | `topics/`, `portals/` |
| Персонаж | Человек / агент / скрипт | `AGENTS.md`, subagents |
| Координаты | Позиция блока на canvas | future `text_cell.v1` |
| Квест | Задача | `tasks/T-*.md` |
| Рейд | Workflow / swarm batch | `workflow`, `conveyor`, subagents |
| Группа | Набор агентов с координатором | 3:1 reduce tree |
| Инстанс | Изолированная ветка/песочница | `worktree`, `sandbox/` |
| Инвентарь | Файлы, отчёты, патчи, evidence | `queues/outbox/`, docs |
| NPC | Tool / driver / script | `tools/`, `drivers/` |
| Миникарта | Dashboard / status card | `top.py`, future `workspace-cell` |
| Чат канала | Thread / topic messages | `thread.py`, `topics/.../messages/` |
| Боевой лог | Append-only event log | future `events/` |
| Туман войны | Непроверенная/непрочитанная область | `unknown`, `needs-review` |
| Бафф/дебафф | Capability/risk flag | `blocked`, `ready`, `unsafe` |
| Лут | Принятый результат | commit, accepted decision |
| Босс | Крупная системная проблема | architecture milestone |
| Респаун | Retry after failure | failed task -> new attempt |
| Правила сервера | Governance | `PROTOCOL.md`, `DECISIONS.md` |

## 4. Почему 2D лучше линейного чата

Линейный чат хорошо работает для двух участников и коротких вопросов. Он плохо работает, когда:

- 5-20 агентов отвечают на одну тему;
- часть ответов совпадает;
- часть ответов конфликтует;
- часть результатов относится к коду;
- часть относится к документации;
- нужно видеть, кто что сделал;
- нужно не потерять minority opinion;
- нужно связать ответы с задачами, файлами и тестами.

2D text workbench решает это пространственно:

```text
             Codex        Agent A      Agent B      Human
Question     Q1           Q1           Q1           comment
Proposal     P1           P2           P1           --
Evidence     file:12      test X       doc Y        source
Risk         low          medium       low          --
Consensus    C1-----------C1-----------C1-----------pending
Conflict     --           X2           --           decide
```

Разногласие становится видимым объектом, а не потерянной фразой в истории.

## 5. Текстовая диффузия

В видео кадр меняется много раз в секунду. В рабочем тексте так часто менять состояние не нужно. Но можно взять принцип:

```text
frame -> diff -> next frame
```

Для текста:

```text
canvas frame -> changed cells -> next semantic frame
```

Пример:

```text
FRAME 001: вопрос поставлен
FRAME 002: три агента дали варианты
FRAME 003: найден consensus
FRAME 004: conflict вынесен в отдельную ячейку
FRAME 005: создана задача
FRAME 006: код ушёл в sandbox/worktree
FRAME 007: тесты прошли
FRAME 008: commit принят
```

Это и есть полудиффузионная модель текста: смысловое поле постепенно уточняется, как изображение в диффузионной модели, но вместо пикселей уточняются утверждения, задачи, риски, связи и доказательства.

## 6. Минимальные сущности

### 6.1. Actor

```json
{
  "schema": "actor.v1",
  "id": "codex",
  "kind": "human|agent|script|tool",
  "role": "builder|reviewer|synthesizer|researcher|integrator",
  "zone": "topics/svend4-infon",
  "status": "idle|working|blocked|reviewing"
}
```

### 6.2. Cell

```json
{
  "schema": "text_cell.v1",
  "id": "cell-001",
  "kind": "question|proposal|evidence|risk|task|decision|summary|patch",
  "owner": "codex",
  "status": "draft|proposed|conflict|accepted",
  "body": "short structured text",
  "links": [
    {"rel": "supports", "target": "cell-000"},
    {"rel": "derived_from", "target": "topics/x.md"}
  ]
}
```

### 6.3. Frame

```json
{
  "schema": "text_frame.v1",
  "canvas": "repo-workbench",
  "frame": 12,
  "changed_cells": ["cell-001", "cell-008"],
  "summary": "new conflict and one consensus candidate"
}
```

### 6.4. Zone

```json
{
  "schema": "zone.v1",
  "id": "zone-svend4-infon",
  "path": "topics/svend4-infon",
  "purpose": "external architecture assessment",
  "rules": ["read-only source", "no code execution", "synthesize before adoption"]
}
```

## 7. Роли как классы персонажей

Не ради игры, а ради разделения труда:

| Role | Аналог MMORPG | Рабочая функция |
|---|---|---|
| Researcher | scout | ищет источники, факты, карту территории |
| Builder | crafter | пишет код/документы/прототипы |
| Reviewer | guard | проверяет риски и ошибки |
| Synthesizer | bard/scribe | сводит варианты и пишет итог |
| Integrator | raid leader | принимает, коммитит, связывает задачи |
| Red-team | rogue | ищет слабые места и противоречия |
| Human maintainer | game master | утверждает спорные решения |

## 8. Как применить к headless Zed-like workbench

Goodall ранее правильно сформулировал практический путь:

```text
offline/headless Zed-like workbench
= local model + terminal-thread runner + MCP gateway + Markdown threads + SQLite/FTS + sandbox
```

MMORPG-слой добавляет к этому не GUI, а **пространственную организацию**:

```text
thread.py         -> сессия / канал
workspace-cell    -> миникарта одного задания
text-canvas       -> карта нескольких заданий и агентов
terminal-thread   -> персонаж/бот в терминальном инстансе
sandbox/worktree  -> инстанс/данжон для опасной работы
MCP/tools         -> NPC/tools
SQLite/FTS        -> память мира / библиотека
```

## 9. Стадии реализации

### Stage 1. Workspace-cell

Одна карточка:

```text
task + thread + stream + worktree + outbox + checks + next action
```

Это минимальная “миникарта”.

### Stage 2. Text-cell schema

Добавить JSON-схему клеток/карточек для одной темы.

### Stage 3. Canvas report

Команда:

```powershell
python tools\text_canvas.py report <topic> --json
python tools\text_canvas.py report <topic>
```

Выводит таблицу/карту.

### Stage 4. Agent lanes

Отдельные колонки по агентам, без смешивания вариантов до synthesis.

### Stage 5. Diff frames

Сохранять не каждый огромный отчёт, а изменения:

```text
new cell
updated status
new conflict
resolved conflict
accepted cell
```

### Stage 6. Brain as proposal generator

Локальная модель или внешний агент может предлагать клетки, но не принимать их.

## 10. Плюсы

- Уходит проблема линейной ленты.
- Видно несколько агентов одновременно.
- Видно, где consensus, где conflict.
- Можно работать оффлайн.
- Можно экспортировать состояние как Markdown/JSON.
- Можно подключать терминальные агенты без GUI.
- Можно сохранять историю кадров/событий.
- Можно переносить темы между репозиториями как bundles.

## 11. Минусы и риски

- Слишком сложная схема может превратиться в бюрократию.
- Красивые карточки не гарантируют правильность.
- Агенты могут начать оптимизировать видимость, а не качество.
- Нужно различать canon и view: canvas не должен подменять источник истины.
- Конфликты нельзя скрывать красивым merge.
- 2D карта требует дисциплины именования и статусов.
- Live/real-time режим опасен без append-only логов.

## 12. Критерий хорошей реализации

Хороший 2D workbench должен отвечать за 10 секунд:

1. Кто сейчас работает?
2. Над чем?
3. Что изменилось?
4. Где конфликт?
5. Что уже проверено?
6. Что можно принять?
7. Что опасно запускать?
8. Где доказательства?
9. Какой следующий шаг?
10. Что надо спросить у человека?

## 13. Multilingual notes

### RU

Суть: сделать из 3D MMORPG не игру, а рабочую 2D карту знаний. Люди и агенты становятся участниками общего информационного мира. Текстовые блоки играют роль клеток карты. Задачи, решения, риски и доказательства видны пространственно, а не теряются в линейном чате.

### EN

Core idea: reverse-engineer the coordination mechanics of a 3D MMORPG into a 2D text workbench. Agents and humans act on a shared semantic map. Text cards replace pixels, quests become tasks, instances become sandboxes/worktrees, and event logs replace combat logs. The goal is not gamification; it is scalable coordination.

### DE

Kernidee: Nicht das Spiel kopieren, sondern die Koordinationslogik eines MMORPG in eine zweidimensionale Text-Arbeitsfläche übertragen. Menschen und Agenten arbeiten auf einer gemeinsamen semantischen Karte. Textkarten ersetzen Pixel, Quests werden Aufgaben, Instanzen werden Sandboxes oder Worktrees, und Ereignislogs ersetzen Chat-Chaos.

### FR

Idée centrale: transformer les mécanismes de coordination d'un MMORPG 3D en espace de travail textuel 2D. Les humains et les agents se déplacent dans une carte sémantique partagée. Les cartes textuelles remplacent les pixels; les quêtes deviennent des tâches; les instances deviennent des sandboxes.

### ES

Idea central: convertir la lógica de coordinación de un MMORPG 3D en un tablero textual 2D para trabajo real. Humanos y agentes colaboran en un mapa semántico compartido. Las tarjetas de texto sustituyen a los píxeles; las misiones se convierten en tareas; las instancias se convierten en sandboxes o worktrees.

## 14. Recommendation

Моя оценка: идея перспективная, но её надо реализовывать снизу вверх.

Правильный порядок:

```text
thread.py -> workspace-cell -> text cells -> canvas report -> agent lanes -> diffusion frames -> brain proposal protocol
```

Неправильный порядок:

```text
сразу делать большой GUI/MMORPG/real-time world
```

Сейчас ближайший полезный шаг: `workspace-cell read-only aggregator`. Он даст первую миникарту без тяжёлой архитектуры.