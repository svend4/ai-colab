---
id: bulk-guard-range-gate-proposal-2026-07-06
type: report
status: proposed
agent: codex
date: 2026-07-06
related: [D-026, tools/bulk_guard.py, tools/commit.py, tools/githooks/pre-commit, reports/no-verify-bulk-guard-review-2026-07-06.md]
---

# Bulk guard range gate proposal

## 1. Ответ на вопрос о недостаточном использовании агентов

Критика справедлива частично. В этой среде у Codex сейчас нет отдельного callable-инструмента для запуска локального subagent/workflow: `tool_search` не выдал agent-runtime, пригодный для запуска `safety-scout`. Поэтому реальное выполнение через отдельного агента я не могу гарантировать из чата напрямую.

Но это не значит, что рой простаивает концептуально. Правильное действие в текущем репозитории: оформить read-only задачу как `subagent-worker/safety-scout` в `queues/outbox/`, чтобы любой доступный агент или человек мог независимо выполнить проверку без права записи. Такое задание добавлено в `queues/outbox/2026-07-06-safety-scout-readonly-assignment-codex.md`.

## 2. Что уже есть в защите от bulk-стирания

1. Принятое решение D-026.
   - `decisions/D-026.md:4` фиксирует тему: запрет несанкционированного bulk-стирания и обязательная страховка.
   - `decisions/D-026.md:5` показывает `status: accepted`.
   - `decisions/D-026.md:27` задаёт порог массовой операции: 10 файлов или 500 строк.
   - `decisions/D-026.md:31` требует страховку до операции.
   - `decisions/D-026.md:42` требует согласие человека на удаление 500+ строк живого содержимого.

2. Протокол D-026.
   - `PROTOCOL.md:306` содержит D-026-раздел.
   - `PROTOCOL.md:308` требует страховку при массовых операциях.
   - `PROTOCOL.md:312` прямо запрещает обход `--no-verify` без обоснования.

3. Локальный pre-commit hook.
   - `tools/githooks/pre-commit:11` перечисляет блокирующие проверки.
   - `tools/githooks/pre-commit:12` включает `bulk_guard --hook`.
   - `tools/githooks/pre-commit:95` реально запускает `tools/bulk_guard.py --hook`.
   - `git config core.hooksPath` сейчас возвращает `tools/githooks`, то есть hook path активен.

4. `bulk_guard.py`.
   - `tools/bulk_guard.py:42` задаёт порог 500 удалённых строк.
   - `tools/bulk_guard.py:43` задаёт порог 10 файлов с крупным урезанием.
   - `tools/bulk_guard.py:47` парсит `git diff --numstat`.
   - `tools/bulk_guard.py:77` читает `backup-*` теги.
   - `tools/bulk_guard.py:80` проверяет теги, указывающие прямо на `HEAD`.
   - `tools/bulk_guard.py:94` анализирует diff.
   - `tools/bulk_guard.py:116` даёт hook exit-code: accepted D-026 + STOP => блок.

5. Тесты.
   - `tools/tests/test_bulk_guard.py:61` проверяет порог 600 удалённых строк.
   - `tools/tests/test_bulk_guard.py:66` проверяет 12 файлов с урезанием.
   - `tools/tests/test_bulk_guard.py:88` проверяет блок accepted D-026 + STOP.
   - `tools/tests/test_bulk_guard.py:94` проверяет, что старый backup-тег не страхует новый diff.
   - `tools/tests/test_bulk_guard.py:97` проверяет, что backup-тег на `HEAD` страхует diff.

6. Безопасная commit-обёртка.
   - `tools/commit.py:4` описывает цель: убрать нужду в `git commit --no-verify`.
   - `tools/commit.py:13` объясняет проблему: `--no-verify` выключает весь pre-commit.
   - `tools/commit.py:20` требует явные пути вместо `git add -A`.
   - `tools/commit.py:23` обещает `git commit` без обхода хуков.
   - `tools/commit.py:46` запрещает pathspec вроде `-A`, `.`, `*`, `:/`.
   - `tools/commit.py:163` запускает `bulk_guard` до коммита.
   - `tools/commit.py:179` делает `git commit` без `--no-verify`.

## 3. Как `--no-verify` обходит защиту

`git commit --no-verify` отключает локальные hooks, включая `pre-commit`. Поэтому не запускаются:

1. `tools/validate.py`.
2. `tools/generate.py --check`.
3. `tools/staged_check.py`.
4. `tools/gap_scan.py drift --strict`.
5. `tools/bulk_guard.py --hook`.

Это видно по архитектуре hook: все проверки находятся внутри `tools/githooks/pre-commit`. Если сам hook не запускается, весь этот слой защиты исчезает.

Отдельная проблема: сам hook сейчас печатает пользователю escape-подсказки:

- `tools/githooks/pre-commit:59` предлагает `git commit --no-verify`.
- `tools/githooks/pre-commit:66` предлагает `git commit --no-verify`.
- `tools/githooks/pre-commit:77` допускает `git commit --no-verify` для исключения D-023.
- `tools/githooks/pre-commit:88` снова предлагает `git commit --no-verify`.

Я не меняю эти строки, потому `tools/githooks/**` находится в deny-зоне для агентов. Но это нужно вынести человеку/интегратору: после D-026 accepted текст hook должен быть жёстче и должен направлять агента в `tools/commit.py` или incident report, а не в обычный `--no-verify`.

## 4. Три меры, которые нельзя обойти локальным `--no-verify`

### 4.1. CI required check

CI проверяет уже созданный commit или PR range:

```powershell
python tools\bulk_guard.py --range origin/main..HEAD --format json --strict
```

Локальный `--no-verify` не влияет на CI. Если PR удаляет 500+ строк или режет 10+ файлов без D-026 insurance, CI краснеет.

### 4.2. Server-side pre-receive hook

На self-hosted Git или сервере можно проверять push:

```sh
while read old new ref; do
  python tools/bulk_guard.py --range "$old..$new" --strict || exit 1
done
```

Локальный пользователь не может обойти server-side hook через `git commit --no-verify`.

### 4.3. Merge-gate / protected branch

Ветка `main/master` не принимает прямой push. Merge-owner или bot запускает:

```powershell
python tools\bulk_guard.py --range main..candidate --strict --require-insurance
python tools\validate.py
python tools\generate.py --check
```

Даже если агент сделал локальный плохой commit, он не попадает в mainline без merge-gate.

## 5. CLI-контракт для `bulk_guard --range`

Предпочтительно расширить существующий `tools/bulk_guard.py`, а не плодить отдельный файл. Так pre-commit, CI и merge-gate используют один policy engine.

Предлагаемый контракт:

```powershell
python tools\bulk_guard.py
python tools\bulk_guard.py --staged
python tools\bulk_guard.py --hook
python tools\bulk_guard.py --range <base>..<head>
python tools\bulk_guard.py --range <base>..<head> --format json
python tools\bulk_guard.py --range <base>..<head> --strict
python tools\bulk_guard.py --range <base>..<head> --require-insurance
python tools\bulk_guard.py --range <base>..<head> --fail-on-live-delete 500
```

Семантика:

- `--range A..B`: анализирует `git diff --numstat A..B`.
- `--staged`: анализирует `git diff --cached --numstat`.
- default: анализирует `git diff --numstat HEAD`.
- `--format json`: печатает машинный результат.
- `--strict`: возвращает `1` при `STOP-uninsured`, если D-026 accepted.
- `--require-insurance`: требует D-026 insurance независимо от локального режима.
- `--fail-on-live-delete N`: отдельный hard-fail при удалении N+ строк живого контента.

Минимальный JSON:

```json
{
  "range": "base..head",
  "deletions": 0,
  "insertions": 0,
  "bulk_files": 0,
  "threshold_lines": 500,
  "threshold_files": 10,
  "is_bulk": false,
  "insured": false,
  "insurance": {
    "backup_tags": [],
    "backup_on_base": [],
    "backup_on_head": []
  },
  "verdict": "ok-not-bulk",
  "top": []
}
```

Для range-режима страховка должна проверяться иначе, чем для локального working tree:

- локальный рабочий diff: backup tag должен указывать на текущий `HEAD`;
- CI/PR range: backup tag должен указывать на `base` или на commit до опасной операции;
- pre-receive: backup tag должен быть достижимым сервером, а не только локальным тегом, иначе это ложная страховка.

Если не хочется усложнять `bulk_guard.py`, допустим отдельный файл:

```powershell
python tools\bulk_range_guard.py <base> <head> --format json --strict
```

Но моё мнение: лучше один `bulk_guard.py` с mode flags, потому иначе логика порогов разъедется.

## 6. Риски ложных срабатываний

1. Легитимная санация или перенос.
   - Большое удаление может быть нормальным, если контент уже перемещён и сохранён.
   - Нужен manifest: source, destination, hash/count строк, подтверждение человека.

2. Generated files.
   - `TASKS.md`, `index.json`, каталоги и снимки могут массово меняться из-за генератора.
   - Для generated files нужен allowlist, но только если source files и генератор консистентны.

3. Rename выглядит как delete+add.
   - `git diff --numstat` может показывать удаление/добавление вместо move.
   - Range guard должен использовать `--find-renames` или дополнительно анализировать `git diff --name-status -M`.

4. Binary/large files.
   - `numstat` для binary может давать `-`.
   - Такие файлы надо считать отдельным risk-class, не игнорировать молча.

5. Cleanup старых build artifacts.
   - Удаление временных артефактов может быть нормальным.
   - Решение: allowlist путей плюс запрет на allowlist для `queues/`, `topics/`, `reports/`, `tasks/`, `decisions/`, `docs/` без явного решения.

6. Submodule/vendor sync.
   - Внешние деревья могут меняться массово.
   - Для них нужен отдельный режим: vendor update report + source hash/tag.

## 7. Рекомендуемый следующий порядок

1. Дождаться независимого read-only отчёта `safety-scout`.
2. Человеку или назначенному интегратору разрешить правку `tools/githooks/pre-commit`, потому это deny-зона.
3. Реализовать `tools/bulk_guard.py --range`.
4. Добавить тесты для `--range`: normal, bulk-uninsured, bulk-insured-on-base, rename, generated allowlist.
5. Подключить `--range` в merge-gate/CI/pre-receive.
6. После обкатки заменить подсказки hook про `--no-verify` на `tools/commit.py` + incident-report route.

## 8. Проверка текущего состояния

Текущий `python tools\bulk_guard.py` показал:

```text
−98 строк · +631 · крупно-урезанных файлов: 0
порог: −500 строк / 10 файлов
вердикт: не массовая операция
```

То есть прямо сейчас D-026 bulk-stop не срабатывает на рабочий diff.
