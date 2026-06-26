---
id: 2026-06-25-independent-code-variant-policy
type: report
status: proposed
owner: codex
date: 2026-06-25
related: [T-257, T-238, D-017, D-018, D-028, streams/code-variant-sandbox/20260625-1818-codex/STREAM.md, sandbox/drafts/README.md]
---

# T-257 — independent-first policy for preliminary code variants

## 01. Что исправлено методологически

Предыдущая ошибка Codex: для вопроса о preliminary code я начал с проверки “что уже есть”, а не с раскрытия собственного варианта. Это нарушило новую политику independent-first: содержательный вариант нельзя схлопывать до того, как он полностью раскрыт.

В T-257 порядок исправлен:

1. Сначала создан независимый вариант Codex: `streams/code-variant-sandbox/20260625-1818-codex/STREAM.md`.
2. Только после этого выполнена сверка с `T-238`, `sandbox/drafts/README.md`, manifest template и старыми outbox-отчётами.
3. Результат ниже разделён на consensus и divergence.

## 02. Независимый вариант Codex, кратко

Codex предлагает пятиступенчатую модель:

```text
idea card -> pseudocode variant -> draft code packet -> static review -> promotion task
```

Главное разделение:

| Слой | Роль |
|---|---|
| `streams/<topic>/<stream-id>/STREAM.md` | почему этот вариант существует, условия, risks, synthesis contract |
| `pseudocode.md` | алгоритм без статуса исполняемого кода |
| `sandbox/drafts/<draft-id>/` | черновой code packet как evidence, не implementation |
| `static review` | manifest/schema/path/AST/link/secret checks без запуска |
| `promotion task` | обычная claimed задача на mainline-реализацию после synthesis |

Ключевое правило:

```text
draft code is evidence, not implementation
```

## 03. Сверка с существующим механизмом

Существующий механизм уже есть и оказался сильнее, чем я учёл в первом импульсе:

- `T-238` уже поставил задачу draft-code sandbox lane.
- `sandbox/drafts/README.md` уже описывает no-execute lane.
- `sandbox/templates/draft-code-manifest.template.json` уже задаёт manifest schema.
- `queues/outbox/2026-06-24-t238-draft-code-sandbox.md` уже объясняет pros/cons/promotion flow.
- `tools/sandbox_schema_validator.py` уже понимает `draft-code-proposal.v1`.
- `tools/sandbox_intake_chain.py` уже различает `agent-draft` для `sandbox/drafts/`.

Поэтому мой вариант не должен заменять существующий draft-code lane. Он добавляет недостающую методологическую обвязку перед ним: independent stream + pseudocode + synthesis before promotion.

## 04. Consensus candidates

Эти пункты совпадают между моим вариантом и существующей системой:

1. Черновой код должен жить вне mainline.
2. Execute OFF по умолчанию.
3. Draft code не разрешает автоматический запуск.
4. Нельзя ставить зависимости из draft-кода.
5. Нельзя хранить secrets.
6. Нельзя напрямую promote в `tools/`, `drivers/`, `core/`, `portals/`.
7. Promotion должен быть отдельной claimed задачей.
8. Перед promotion нужен outbox/report и static review.
9. Draft manifest нужен обязательно.
10. Draft code можно использовать как evidence/proposal material.

## 05. Что добавляет вариант Codex

Новые или усиленные пункты:

1. Перед draft code должен быть independent stream-вариант, чтобы агент не останавливался на словах “это уже есть”.
2. Псевдокод выделяется как отдельный уровень между reasoning и draft code.
3. Synthesis должен сравнивать code-варианты не только по файлам, но по conditions/tradeoffs/tests/risks/promotion cost.
4. Draft code не должен копироваться вслепую: promotion task реализует выбранный вариант инженерно, с тестами.
5. Нужно различать `ready-for-synthesis` и возможный будущий `ready-for-static-review`.
6. Нужен top-level сценарий, но только после фиксации политики: `top.py code-variant-start` не должен появляться раньше consensus.

## 06. Divergence / открытые вопросы

Эти вопросы нельзя закрывать агентом в одиночку:

| ID | Вопрос | Варианты |
|---|---|---|
| CVD-001 | Где жить псевдокоду? | рядом со stream / внутри draft packet / оба места с разными ролями |
| CVD-002 | Хранить ли raw draft folders в Git? | ignored by default / tracked selected fixtures / tracked all draft packets |
| CVD-003 | Нужен ли статус `ready-for-static-review`? | да, отдельный maturity stage / нет, достаточно `ready-for-synthesis` |
| CVD-004 | Может ли observer редактировать draft code? | только review notes / может делать patch variant / может создавать свой draft fork |
| CVD-005 | Когда делать `top.py code-variant-start`? | сейчас / после ещё одного agent variant / после human ratification |

## 07. Рекомендация Codex после сверки

Моя рекомендация теперь такая:

1. Не реализовывать сразу `top.py code-variant-start` в этом же шаге.
2. Сначала принять proposed-policy как рабочее уточнение: independent stream обязателен перед draft-code synthesis.
3. Добавить ещё минимум один независимый вариант от другого агента или человека по CVD-001..CVD-005.
4. После этого сделать synthesis и только then завести build-задачу на `top.py code-variant-start` или `tools/draft_code.py`.

Причина: сама ошибка, которую мы исправляем, была в преждевременном переходе к реализации. Поэтому правильное действие сейчас — не кодить wrapper, а закрепить процесс и дать другим агентам возможность раскрыть свои варианты.

## 08. Проверки и evidence

Проверено перед отчётом:

```powershell
python -m py_compile tools\doc_synthesis.py tools\top.py tools\test_doc_synthesis.py tools\test_top.py
python tools\test_doc_synthesis.py
python tools\test_top.py
python tools\validate.py
python tools\stream.py check --max-age-days 7 --json
```

Дополнительная сверка:

```powershell
rg -n "draft-code|draft code|sandbox/drafts|pseudocode|promotion task|static review|no-execute|code variant" docs tasks queues\outbox streams sandbox tools -S
```

## 09. Applied instructions

- `AGENTS.md` / `PROTOCOL.md`: работа оформлена через T-257, stream и outbox; чужие сообщения не удалялись.
- `D-017` / `D-028`: похожее существующее решение не схлопнуло independent variant; вариант сначала раскрыт.
- `D-018` / cauldron-synthesis: consensus/divergence разделены; accepted-решений агентом не принято.
- Self-critique: ошибка прежнего порядка зафиксирована и исправлена процедурно.

## 10. Следующие задачи-кандидаты

1. Создать задачу для второго независимого agent/human варианта по CVD-001..CVD-005.
2. После второго варианта запустить `python tools\top.py synthesize-docs code-variant-sandbox --ready-only --json`.
3. Если consensus устойчивый, создать build-задачу на `top.py code-variant-start` или `tools/draft_code.py create/check/list`.

## Applied instructions

- AGENTS.md: outbox report preserved; no чужие сообщения удалялись.
- PROTOCOL.md: report kept as proposed/done evidence; no accepted decision is created here.
- docs/protocol-machine-layer.md: added explicit machine-readable evidence footer for check-report.

Checks:
- python tools\validate.py -> OK
- python tools\generate.py --check -> OK
- python tools\instructions.py check-report <this-file> -> OK after footer normalization
