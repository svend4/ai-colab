---
id: doc-consensus-agent-runtime
type: doc
title: DOC_CONSENSUS_AGENT runtime recipe and safe examples
status: draft
owner: codex
related: [T-176, T-196, D-017, D-018, workflow-orchestration-policy]
last_verified: 2026-06-23
---

# DOC_CONSENSUS_AGENT runtime recipe and safe examples

Дата: 2026-06-23.

Назначение: дать безопасный рецепт для `tools/doc_consensus.py report --semantic`, когда лексический Jaccard не видит одну и ту же идею, написанную разными словами.

## Короткая формула

`DOC_CONSENSUS_AGENT` — это opt-in subprocess seam. `doc_consensus.py` сам не вызывает LLM, сеть, Codex, ChatGPT или под-агентов. Он только:

1. извлекает units из markdown-документов;
2. делает механический pre-cluster;
3. если указан `--semantic`, отправляет residuum в команду из переменной окружения `DOC_CONSENSUS_AGENT`;
4. ожидает от команды только JSON;
5. рендерит markdown-отчёт со `status: proposed`.

Это не auto-accept. Принятие результата идёт отдельно через D-017/D-018: review, synthesis, котёл, человек/назначенный интегратор.

## Контракт команды

Команда из `DOC_CONSENSUS_AGENT` должна быть read-only и вести себя как фильтр:

```text
stdin:  prompt + JSON units
stdout: JSON object only or JSON wrapped in harmless prose/fence
stderr: diagnostic noise allowed, но не должен быть источником результата
side effects: none
```

Ожидаемый JSON:

```json
{
  "consensus": [
    {"ids": ["fileA.md:10", "fileB.md:12"], "rationale": "same idea in different words"}
  ],
  "divergences": [
    {
      "id": "fileC.md:20",
      "claim": "unique claim",
      "docs": ["fileC.md"],
      "reason": "why it stands alone",
      "resolves": "what evidence or decision would settle it"
    }
  ]
}
```

Запрещено для команды агента:

- писать в репозиторий;
- делать commit/stage/pipeline done;
- запускать дополнительные fan-out воркфлоу;
- менять `decisions/*.md` или ставить `accepted`;
- читать секреты или внешние источники без отдельного preflight;
- возвращать готовое решение вместо материала для `proposed`-синтеза.

## Безопасный режим по умолчанию

Лексический режим не использует `DOC_CONSENSUS_AGENT`:

```powershell
Remove-Item Env:DOC_CONSENSUS_AGENT -ErrorAction SilentlyContinue
python tools\doc_consensus.py report --files docs\parallel-work-policy.md docs\workflow-orchestration-policy.md --out reports\doc-consensus-lexical.md
```

Свойства:

- no-cost;
- pure stdlib;
- no subprocess agent;
- no network;
- output is a report, not a decision.

## Semantic dry-run без агента

Если `--semantic` включён, но `DOC_CONSENSUS_AGENT` не задан, агентный pass пустой. Механический consensus сохраняется, скрытого вызова нет:

```powershell
Remove-Item Env:DOC_CONSENSUS_AGENT -ErrorAction SilentlyContinue
python tools\doc_consensus.py report --semantic --semantic-budget 1 --files docs\parallel-work-policy.md docs\workflow-orchestration-policy.md --out reports\doc-consensus-semantic-no-agent.md
```

Это полезно как smoke-check: CLI, renderer и `status: proposed` проверяются без LLM.

## Budget guard

`--semantic-budget N` ограничивает число agent-batches. Если units требуют больше batches, команда падает до вызова агента:

```powershell
python tools\doc_consensus.py report --semantic --semantic-budget 0 --files docs\parallel-work-policy.md docs\workflow-orchestration-policy.md
```

Ожидаемое безопасное поведение: exit code `1`, сообщение `semantic budget exceeded`, без agent subprocess call.

Практическое правило:

- `--semantic-budget 0` — preflight: убедиться, что guard работает;
- `--semantic-budget 1` — маленькая пара документов;
- `--semantic-budget 2..3` — средний ручной review;
- больше 3 — только если заранее понятно, кто будет читать результат и как он будет синтезирован.

## Локальный безопасный stub-agent

Для разработки используйте stub, который ничего не принимает как решение. Он читает stdin, парсит units и возвращает все пункты как divergences:

```powershell
$stub = @"
import json, re, sys
raw = sys.stdin.read()
text = raw.split('Units (JSON):', 1)[-1].strip()
try:
    units = json.loads(text) if text else []
except Exception:
    units = []
print(json.dumps({
    "consensus": [],
    "divergences": [
        {
            "id": u.get("id", ""),
            "claim": u.get("text", ""),
            "docs": [u.get("doc", "")],
            "reason": "safe stub: no semantic merge performed",
            "resolves": "replace stub with reviewed read-only agent command"
        }
        for u in units
    ]
}, ensure_ascii=False))
"@
New-Item -ItemType Directory -Force -Path tmp-work | Out-Null
Set-Content -Encoding UTF8 -LiteralPath tmp-work\doc_consensus_agent_stub.py -Value $stub
$env:DOC_CONSENSUS_AGENT = "python tmp-work\doc_consensus_agent_stub.py"
python tools\doc_consensus.py report --semantic --semantic-budget 1 --files docs\parallel-work-policy.md docs\workflow-orchestration-policy.md --out reports\doc-consensus-stub.md
Remove-Item Env:DOC_CONSENSUS_AGENT -ErrorAction SilentlyContinue
```

Смысл примера: проверить runtime seam и формат JSON без реального semantic merge.

## Подключение реального агента

Реальный агент подключается так же, но команда должна быть read-only filter:

```powershell
$env:DOC_CONSENSUS_AGENT = "python path\to\read_only_consensus_agent.py"
python tools\doc_consensus.py report --semantic --semantic-budget 1 --files docs\parallel-work-policy.md docs\workflow-orchestration-policy.md --out reports\doc-consensus-semantic.md
Remove-Item Env:DOC_CONSENSUS_AGENT -ErrorAction SilentlyContinue
```

Перед запуском:

```powershell
python tools\top.py advice codex T-196 --hot-files
python tools\instructions.py preflight codex T-196
python tools\test_doc_consensus.py
```

После запуска:

```powershell
python tools\instructions.py check-report reports\doc-consensus-semantic.md
python tools\validate.py
python tools\generate.py --check
```

`check-report` может показать advisory по отсутствию `Applied instructions`, потому semantic output — это результатный report, а не task closeout. Для task/outbox closeout добавляйте отдельный Applied instructions блок.

## Auto-accept policy

В `doc_consensus.py` auto-accept отсутствует намеренно.

- `render(... semantic ...)` пишет `status: proposed`.
- Текст отчёта содержит: `ничего не auto-accepted — материал для котла (D-017/D-018)`.
- Любой переход в `accepted` делается вне этого инструмента: отдельная review-задача, решение, human/integrator approval.

Если внешний wrapper хочет auto-accept, это уже другой инструмент и он должен пройти отдельное proposed decision + safety gate. Для текущего репозитория правильный режим: semantic consensus помогает увидеть общие идеи, но не принимает решения.

## Быстрый чек-лист перед semantic run

- `--semantic` указан явно.
- `--semantic-budget` указан явно.
- `DOC_CONSENSUS_AGENT` включён только на время команды и потом удалён.
- Output path в `reports/` или `темы/`, не в `decisions/accepted`.
- Результат имеет `status: proposed`.
- Никакой commit/stage/pipeline done не выполняется из agent command.
- Синтез спорных пунктов идёт через D-017/D-018.

## Почему это важно

Без этого рецепта есть два риска:

1. агент запускает дорогой или широкий semantic fan-out скрыто;
2. semantic output ошибочно воспринимают как уже принятое решение.

Правильная модель обратная: semantic pass — это только усиленный reader/synthesizer. Он даёт материал для людей и агентов, но не заменяет governance.