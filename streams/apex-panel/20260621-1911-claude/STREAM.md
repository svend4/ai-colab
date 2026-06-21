---
id: 20260621-1911-claude
topic: apex-panel
agent: claude
status: proposed
created: 2026-06-21
---

# Stream: 20260621-1911-claude

## Причина форка

cohort.py (parallel+self-host) fork to synthesize with top.py panel

## Вариант

Запрос Stefan: сделать вершину пирамиды удобной — обёртки/группы команд («одна кнопка») для людей
И агентов, с упором на **одновременную/параллельную** работу и на **работу системы над собой**.

Это форк-синтез (D-017) поверх уже принятого `tools/top.py` (Codex, T-138 — committed `5f96436`).

### Две вершинные панели — комплементарны, не дубли

| Аспект | `top.py` (Codex) | `cohort.py` (Claude, этот форк) |
|---|---|---|
| Фокус | кнопки для человека и ОДИНОЧНОГО агента | ПАРАЛЛЕЛЬНАЯ много-агентная работа + самохостинг |
| Команды | buttons/status/health/agent-start/take/snapshot/knowledge | board/plan/turn/gate/ship/self |
| Параллель | `take` берёт одну задачу | `plan` раздаёт РАЗНЫЕ задачи N агентам без коллизий; `board` — общий дашборд |
| Коммит | называет commit как side-effect | `ship` = commit_lock + selective-add (политика Ур.0 встроена) |
| Гейт | `health` (validate/generate/caps) | `gate` = `merge_gate.py` (validate+generate --check+permissions) |
| Само-улучшение | — | `self` — движок прогоняет свою quality-автоматику и выдаёт backlog «что чинить» |
| Аудитория | человек + агент | человек (таблицы) + агент (`--json`), side-effects dry-by-default (`--run`) |

### Нижние инструменты этого форка (отдельные коммиты, ноль контенции)

- `tools/variants.py` — реестр форк-вариантов (где все форки по теме) — вход для синтеза.
- `tools/stream.py` — жизненный цикл Level-2 пакетов (этот файл создан им же).
- `tools/merge_gate.py` — merge-гейт как переиспользуемый callable (основа Уровня-1 T-136).
- `tools/promote.py` + `docs/promotion-rules.md` — продвижение по пирамиде L4→L3→L2→L1 (ответ на Q5).
- `tools/sandbox_intake_demo.py` — сквозной S1→S3→S7 демо на `data/fixtures` (прогресс T-020 без svend4).

### Предложение синтеза (на коллективную ратификацию, не соло)

1. **Оставить ОДНУ вершину** для пользователя: `top.py` как имя/вход, влить в неё группы `cohort`:
   `top.py board` (дашборд), `top.py plan` (раздача), `top.py self` (самохостинг), `top.py ship`
   (commit под локом). Либо `top.py` делегирует в `cohort.py` для параллельных сценариев.
2. **Граница безопасности общая** (как у top.py): нет execute; side-effects явные/`--run`; коммит только
   через `commit_lock`+selective-add; внешний код — через sandbox.
3. **Связь с T-136**: `stream.py`+`merge_gate.py` — это Level-1-tooling БЕЗ принятия governance-решения
   (worktree-на-агента и роль merge-gate остаются в котле).

### Перепроверка (D-018)

- **Техническая:** все 7 инструментов протестированы (hermetic, зелёные), read-only/dry-by-default,
  построены и состязательно проверены через workflow; ноль пересечений с горячими файлами Codex.
- **Гуманитарная:** снижает порог входа для людей (одна кнопка вместо 25 команд) и для новых агентов
  (единый дашборд + самохостинг-backlog), не повышая поверхность риска — execute закрыт, коммит под политикой.

## Adoption

Перенос в mainline — только после review и явного `adopt` (governance-решение остаётся в котле, D-018).
