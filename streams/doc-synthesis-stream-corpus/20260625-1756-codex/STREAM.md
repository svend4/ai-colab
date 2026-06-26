---
id: 20260625-1756-codex
topic: doc-synthesis-stream-corpus
agent: codex
status: ready-for-synthesis
created: 2026-06-25
variant_policy: independent-first
synthesis_ready: true
task: T-255
status_note: variant completed, ready for synthesis
---

# Stream: doc-synthesis-stream-corpus / codex

## 00. Причина независимого варианта

T-255 закрывает практический разрыв в новой политике independent-first variants. После `top.py variant-start` агент уже создаёт личный `STREAM.md`, но observer/synthesizer всё ещё должен был помнить точный путь stream-файла и передавать его в `doc_synthesis.py scan` вручную. Это тормозит верхний слой и снова возвращает работу к ручной навигации.

## 01. Условия применимости

Вариант верен при таких условиях:

1. Тема уже имеет один или несколько stream-пакетов в `streams/<topic>/<stream-id>/STREAM.md`.
2. Агент или observer хочет выполнить proposed synthesis по topic, а не по заранее собранному списку обычных `docs/*.md`.
3. Нужно сохранить независимость вариантов: stream-пакеты остаются в своих деревьях, а synthesis только читает их как corpus.
4. Нельзя ломать старый shortcut `architecture-core`, потому он уже используется как preset по историческому набору документов.

## 02. Независимый ответ агента

Решение: добавить в `tools/doc_synthesis.py` маленький слой автоматического выбора corpus:

1. Если пользователь явно передал files, использовать эти files.
2. Если topic равен `architecture-core`, использовать исторический preset `ARCHITECTURE_CORE_FILES`.
3. Если topic custom и files не переданы, найти `STREAM.md` внутри `streams/<topic>/...`.
4. Если такие stream-файлы есть, сканировать их как обычный corpus.
5. Если stream-файлов нет, падать с понятной подсказкой: нужен file list или `streams/<topic>/*/STREAM.md`.

Это сохраняет старые команды и добавляет новый верхний сценарий:

```powershell
python tools\top.py variant-start codex doc-synthesis-stream-corpus --task T-255
python tools\stream.py mark 20260625-1756-codex ready-for-synthesis "variant completed"
python tools\top.py synthesize-docs doc-synthesis-stream-corpus --json
```

## 03. Потенциал, который нужно раскрыть до синтеза

- новые под-вопросы: нужно ли позже добавить явный флаг `--stream-corpus` для preset-тем вроде `architecture-core`;
- edge cases: topic с несколькими stream-пакетами разного статуса сейчас читается целиком, без фильтра `ready-only`;
- альтернативные реализации: связать `doc_synthesis.py` с `stream.py list --ready-only`, но это сильнее сцепляет инструменты;
- риски и ограничения: текущая версия делает read-only corpus selection, но не принимает adoption/governance решений.

## 04. Сравнение с известными вариантами

- Похожие пункты: `tools/synthesis_helper.py report <topic>` уже работает со stream-подходом, но решает другой, более старый формат fork-сводки.
- Отличия: `doc_synthesis.py` строит richer synthesis по keyword buckets, refs, lanes и JSON, поэтому должен сам уметь читать stream corpus.
- Что этот вариант добавляет сверх уже написанного: убирает ручной список файлов между `variant-start` и `synthesize-docs`.
- Что может оказаться настоящим шумовым дублем после синтеза: если будущий `variants.py` полностью заменит эту функцию и даст более точный semantic/ready-only corpus.

## 05. Evidence / проверки

Файлы изменения:

- `tools/doc_synthesis.py` — добавлен `stream_topic_files(topic)` и новый порядок `resolve_files()`.
- `tools/test_doc_synthesis.py` — добавлен тест временного stream topic corpus.
- `docs/document-synthesis-mechanism-2026-06-24.md` — описан T-255 workflow.
- `docs/independent-variant-stream-policy.md` — пункт 12.3 переведён в DONE.
- `docs/top-layer-command-groups.md` — верхняя команда описана как полный цикл.

Проверки на момент заполнения stream:

```powershell
python -m py_compile tools\doc_synthesis.py tools\test_doc_synthesis.py
python tools\test_doc_synthesis.py
```

Результат: `test_doc_synthesis.py` прошёл 3 теста, синтаксис зелёный.

## 06. Вопросы другим агентам и людям

- Нужно ли `doc_synthesis.py scan architecture-core` когда-нибудь переключать на stream corpus, или исторический preset должен оставаться постоянным shortcut?
- Нужно ли читать только `ready-for-synthesis` stream-пакеты, или proposed/developing тоже полезны для раннего обзора?
- Нужен ли отдельный observer-command: `python tools\top.py synthesize-streams <topic> --ready-only`?

## 07. Synthesis contract

- consensus candidates: custom topic без files должен читать `streams/<topic>/*/STREAM.md`; synthesis остаётся proposed; explicit files имеют приоритет.
- divergence candidates: поведение preset-тем; фильтрация по ready status; связь с `variants.py` и semantic synthesis.
- adoption target: `tools/doc_synthesis.py`, `tools/test_doc_synthesis.py`, `docs/document-synthesis-mechanism-2026-06-24.md`, `docs/top-layer-command-groups.md`, `docs/independent-variant-stream-policy.md`.
- reject/supersede condition: можно заменить, если появится единый `variants/doc_synthesis` corpus provider с tests и stream-status filtering.

## 08. Adoption

Этот stream не принимает governance-решение. Он описывает реализованный вариант T-255 и готов к synthesis/review. Перенос в accepted policy остаётся за человеком или назначенным integrator по D-018.