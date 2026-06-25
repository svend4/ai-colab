---
id: 20260625-2142-codex
topic: independent-first-process-guard
agent: codex
status: ready-for-synthesis
created: 2026-06-25
variant_policy: independent-first
synthesis_ready: true
task: T-262
phase: self-critique-before-repo-comparison
---

# Stream: independent-first-process-guard / Codex self-critique

## 00. Причина независимого варианта

В T-261 я нарушил дух новой политики: перед полным раскрытием собственного решения начал смотреть существующие механизмы (`doc_synthesis`, `result_intake`, `draft_code`). Формально потом был создан stream и вариант, но порядок мышления уже был смещён: старый паттерн “сначала не дублировать” победил новый паттерн “сначала раскрыть потенциал варианта”.

Это не ошибка инструмента и не зависание. Это процессный дефект агента.

## 01. Условия применимости

Guard нужен для любых задач, где пользователь просит:

1. предложить новый метод;
2. разработать новую политику;
3. сделать аналогию с прошлым опытом;
4. сравнить несколько вариантов агентов;
5. работать по independent-first / fork-and-synthesize;
6. строить новый слой между raw input и clean canon.

Если задача только исправляет конкретный известный bug, такой guard может быть advisory. Если задача методологическая или архитектурная, guard должен быть обязательным перед repo-search/comparison.

## 02. Независимый ответ агента

Мой вариант процесса:

```text
0. Stop: no repo search yet.
1. Write own model from general to specific.
2. Write algorithm.
3. Write pseudocode / operational protocol.
4. Name assumptions and risks.
5. Only then compare with existing repo mechanisms.
6. Split result into consensus/divergence.
7. Implement only consensus-smallest useful step.
```

Главная причина нарушения: агент смешал два правильных, но конфликтующих правила:

- “не изобретать заново и уважать существующий код”; 
- “не схлопывать независимый вариант до раскрытия”.

Для обычного coding bug первое правило часто важнее. Для методологической задачи второе правило должно идти раньше.

## 03. Потенциал, который нужно раскрыть до синтеза

### 03.1. Алгоритм

1. Получить вопрос пользователя.
2. Классифицировать вопрос:
   - `implementation-only`;
   - `architecture/methodology`;
   - `variant/synthesis`;
   - `safety/governance`.
3. Если вопрос `architecture/methodology` или `variant/synthesis`, открыть independent-first режим.
4. До `rg`, `repo-search`, чтения чужих stream и прежних отчётов написать:
   - общий принцип;
   - структуру решения;
   - алгоритм;
   - псевдокод;
   - критерии проверки;
   - известные риски.
5. Проверить, что текст не является шаблоном и содержит самостоятельный ответ.
6. После этого делать repo-search и сравнение.
7. Если существующее решение лучше, свой вариант не удалять, а пометить как `superseded with useful deltas`.

### 03.2. Псевдокод

```text
function handle_task(user_request):
    kind = classify(user_request)
    if kind in {architecture, methodology, variant, synthesis}:
        stream = create_stream(no_search=True)
        write_section_01_conditions(stream)
        write_section_02_independent_answer(stream)
        write_section_03_algorithm_and_pseudocode(stream)
        result = independent_first_check(stream)
        if result.status != ok:
            stop("fill independent variant before repo-search")
        existing = repo_search_after_independent_variant()
        comparison = compare(stream, existing)
        implement(consensus_smallest_step(comparison))
    else:
        read_codebase_first_as_normal_engineering()
```

### 03.3. Что должен проверять guard

Минимально:

- есть `STREAM.md`;
- есть секции 01, 02, 03 с точными заголовками;
- секции не пустые и не содержат стандартные placeholder phrases;
- в секции 03 есть слова/маркеры `алгоритм`, `псевдокод`, `algorithm`, `pseudocode`;
- статус `ready-for-synthesis` допустим только если check проходит.

Guard не должен доказывать качество мысли. Он должен ловить грубое нарушение порядка.

## 04. Сравнение с известными вариантами

Эта секция заполняется после собственного варианта. Сначала мой вывод: существующий `variant-start` уже печатает правильную подсказку “fill independent sections before repo-search”, но подсказка не стала gate. Нужно добавить отдельный проверяемый шаг `independent_first.py check` и вставить его в `next_commands` после создания stream.

## 05. Evidence / проверки

Сначала записан этот independent stream без repo-search. После этого можно сверять с `top.py`, `stream.py`, `doc_synthesis.py`, `tools/test_top.py`.

## 06. Вопросы другим агентам и людям

1. Должен ли guard быть strict в `stream.py mark ready-for-synthesis`, или пока достаточно отдельной команды?
2. Нужно ли блокировать `top.py repo-search`, если есть свежий stream по той же теме без passed independent check?
3. Считать ли “кодовые bugfix задачи” исключением из independent-first?
4. Как документировать честное исключение: когда сначала читать код всё-таки правильно?

## 07. Synthesis contract

- consensus candidates: для методологических/вариантных задач нужен guard до repo-search.
- divergence candidates: strict enforcement location — `stream.py`, `top.py`, `advice.py`, или отдельный tool.
- adoption target: `tools/independent_first.py`, tests, top next_commands, docs/capabilities.
- reject/supersede condition: если guard встроят прямо в `stream.py mark`, отдельный tool можно оставить compatibility layer.

## 08. Объяснение пользователю коротко

Почему так произошло: потому что старый инженерный рефлекс “сначала изучить текущую систему” автоматически включился в методологической задаче, где нужно было сначала дать независимый вариант. Это хороший рефлекс для bugfix, но неправильный порядок для fork-and-synthesize. Исправление: сделать independent-first не только текстовой политикой, а проверяемым шагом в workflow.