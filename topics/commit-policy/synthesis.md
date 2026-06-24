---
id: synthesis-commit-policy
topic: commit-policy
type: synthesis-scaffold
status: proposed
agents: codex
variants: 3
---

# Синтез (скелет): commit-policy

> **proposed** — материал для котла (D-018). Скелет собран автоматически из форк-вариантов;
> консенсус/расхождения/решение заполняет коллектив с двойной перепроверкой. Инструмент
> ничего не решает и не помечает accepted.

## Консенсус

Legacy alias: см. следующую секцию "## 1. Общие пункты (Сверху / Консенсус)"; этот блок добавлен для нового synthesis-validator и не меняет смысл старого skeleton.

## 1. Общие пункты (Сверху / Консенсус)
> ЗАПОЛНИТЬ: Выделите сухой остаток, с которым согласны все варианты.
- [ ] ...

## 2. Исходные документы (Середина / Золотой голос)
> Ниже представлены оригинальные варианты от разных агентов.

| Агент | Статус | Тип | Файл |
|---|---|---|---|
| codex | adopted | stream | `streams/commit-policy/2026-06-21-codex-streams-policy/STREAM.md` |
| codex | ready-for-review | stream | `streams/commit-policy/2026-06-21-codex-t136-synthesis/STREAM.md` |
| codex | proposed | stream | `streams/commit-policy/20260622-0555-codex/STREAM.md` |

### codex — [streams/commit-policy/2026-06-21-codex-streams-policy/STREAM.md](file:///C:/Users/stefan/Documents/New project ai colab/streams/commit-policy/2026-06-21-codex-streams-policy/STREAM.md)
- **Проблема** — При параллельной работе агентов Git commit может случайно забрать чужие half-done файлы. С другой ст
- **Вариант** — Добавить `streams/` как промежуточный слой:
- **Почему это может быть лучше** — Так сохраняются альтернативные технические варианты, но mainline остаётся чистой. Это отвечает замеч
- **Риски** — - появится ещё одна папка и ещё один слой процесса;
- **Проверка** — Через несколько задач проверить:
- **Что нужно для adoption** — Минимальная adoption уже сделана: `docs/commit-stream-policy.md` и `streams/README.md`.

### codex — [streams/commit-policy/2026-06-21-codex-t136-synthesis/STREAM.md](file:///C:/Users/stefan/Documents/New project ai colab/streams/commit-policy/2026-06-21-codex-t136-synthesis/STREAM.md)
- **Problem** — The current shared worktree works for small sequential edits, but it becomes fragile when several ag
- **Evidence** — The T-133 case is useful because it happened live:
- **Codex Position** — 1. **Use Level 0 now.** It is cheap, tested, and already fits the repository policy.
- **Proposed Architecture** — ```text
- **Why not a separate Markdown changeset system** — A Markdown changeset is useful as evidence inside `streams/`, but not as a second VCS. Once code cha
- **What Stefan Needs To Decide** — - Are per-agent/per-task worktrees allowed on this machine/project?
- **Recommendation** — Accept Level 0 immediately. Approve Level 1 as the target for multi-agent parallelism. Keep `streams

### codex — [streams/commit-policy/20260622-0555-codex/STREAM.md](file:///C:/Users/stefan/Documents/New project ai colab/streams/commit-policy/20260622-0555-codex/STREAM.md)
- **Причина форка** — Этот stream создан по T-146 как структурированный “ручеёк” для продолжения темы, которая уже обсужда
- **Наблюдение** — Level 0 (`commit_lock` + selective-add) достаточен для малых одиночных правок, но не достаточен при 
- **Вариант** — Принять правило: Level 1 worktree обязателен, если есть хотя бы один триггер:
- **Почему это может быть лучше** — Это превращает “ждать чужой commit” из нормального режима в исключение. Агент продолжает работу в св
- **Риски** — - Больше worktree/branch объектов, которые надо чистить.
- **Проверка** — В T-146 dry-run уже показывает, что текущий фасад понимает проблему:
- **Что нужно для adoption** — 1. Ответить на `Q-015`.

## Разногласия

Legacy alias: см. следующую секцию "## 3. Разногласия и Детализация (Вынесено)"; этот блок добавлен для нового synthesis-validator и не принимает решение.

## 3. Разногласия и Детализация (Вынесено)
> ЗАПОЛНИТЬ: Пункты спора, вынесенные в отдельные документы для глубокой проработки.
- [ ] пункт спора · варианты сторон · доказательная база

### Файлы для детальных разногласий (Streams)
- [codex: streams/commit-policy/codex-divergence.md](file:///C:/Users/stefan/Documents/New project ai colab/streams/commit-policy/codex-divergence.md)

## Двойная перепроверка (D-018)
- **Техническая:** [ ] корректность · [ ] тесты · [ ] нет новой поверхности риска
- **Гуманитарная:** [ ] польза людям/пользователям · [ ] понятность · [ ] последствия

## 4. Предложение синтеза (proposed, не решение)
- ...
