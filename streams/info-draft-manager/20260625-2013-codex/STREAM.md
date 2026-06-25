---
id: 20260625-2013-codex
topic: info-draft-manager
agent: codex
status: ready-for-synthesis
created: 2026-06-25
variant_policy: independent-first
synthesis_ready: true
task: T-261
phase: independent-design-before-implementation
---

# Stream: info-draft-manager / Codex variant

## 00. Причина независимого варианта

Пользователь поставил вопрос: если для кода появилась песочница draft packets, как аналогично работать с документацией, информацией и разными видами материалов. Мой независимый ответ: нужен не общий мусорный inbox, а структурированный `info-draft` packet, который сохраняет мысль до synthesis, но не делает её каноном.

## 01. Условия применимости

Этот вариант применяется, когда:

1. Агент или человек хочет предложить документ, раздел, карту вопросов, набор тезисов или источников.
2. Нельзя сразу писать в `docs/`, `topics/`, `core/`, `portals/`, потому неизвестно, является ли текст consensus.
3. Есть несколько вариантов одного документа или разные уровни зрелости информации.
4. Нужно отделить черновик, источники, claims, open questions и synthesis plan.
5. Нужно сохранить independent-first потенциал агента до сравнения с чужими вариантами.

## 02. Независимый ответ агента

Предлагаю слой:

```text
idea / stream -> info draft packet -> structural review -> doc_synthesis -> promotion task
```

`info draft packet` живёт в:

```text
sandbox/info-drafts/<draft-id>/
  manifest.json
  README.md
  brief.md
  outline.md
  claims.md
  sources.md
  open_questions.md
  divergence.md
  notes.md
```

Это не финальный документ. Это evidence packet для дальнейшего synthesis.

## 03. Потенциал, который нужно раскрыть до синтеза

В отличие от `draft_code.py`, здесь не нужен `src/` и `tests/`. Нужны информационные слои:

- `brief.md` — коротко, что пытается сказать draft.
- `outline.md` — структура будущего документа.
- `claims.md` — тезисы, которые можно сравнивать.
- `sources.md` — ссылки/файлы/evidence.
- `open_questions.md` — вопросы, которые нельзя молча решить.
- `divergence.md` — спорные варианты и условия выбора.
- `notes.md` — рабочие заметки автора/reviewer.

## 04. Сравнение с известными вариантами

Существующие механизмы уже закрывают половину задачи:

- `doc_synthesis.py` сравнивает готовые документы/streams.
- `top.py synthesize-docs` делает synthesis доступным наверху.
- `streams/` фиксируют independent-first варианты.
- `queues/outbox/` фиксируют отчёты.
- `sandbox/inbox` принимает хаотический материал.

Но не хватает промежуточного packet manager между хаотическим inbox и synthesis. Поэтому `info_draft.py` должен быть не конкурентом `doc_synthesis.py`, а поставщиком аккуратных входных пакетов.

## 05. Evidence / проверки

Связанные инструменты:

- `tools/draft_code.py` — аналогия реализации.
- `tools/doc_synthesis.py` — следующий synthesis слой.
- `tools/result_intake.py` — классификация landed/outbox результатов.
- `tools/top.py` — верхний proxy.

Проверки для T-261 должны включать:

```powershell
python -m py_compile tools\info_draft.py tools\test_info_draft.py
python tools\test_info_draft.py
python tools\validate.py
python tools\generate.py --check
python tools\stream.py check --max-age-days 7 --json
```

## 06. Вопросы другим агентам и людям

1. Нужно ли хранить selected info drafts в Git или только manifest/report?
2. Должен ли `info_draft.py review` автоматически предлагать `doc_synthesis.py scan` команду?
3. Нужны ли разные типы info draft: `doc`, `question-tree`, `source-map`, `decision-material`, `portal-notes`?
4. Когда info draft можно считать готовым к promotion в `docs/`?

## 07. Synthesis contract

- consensus candidates: info draft packet нужен как средний слой между raw inbox и clean docs.
- divergence candidates: exact draft kinds, Git policy, auto synthesis command, reviewer edit rights.
- adoption target: `tools/info_draft.py`, tests, sandbox/info-drafts contract, top proxy, capabilities/docs.
- reject/supersede condition: если `doc_synthesis.py` станет полноценным packet manager, этот stream можно закрыть как historical design.

## 08. Обоснование правок

Правки повторяют успешную архитектуру T-260, но адаптируют её к документам. Ключевой риск здесь не execute, а преждевременная канонизация. Поэтому инструмент должен создавать и проверять packet, но не принимать решения и не переносить текст в mainline.