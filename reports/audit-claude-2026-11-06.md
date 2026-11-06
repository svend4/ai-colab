# Полный аудит репозитория — 2026-11-06 (Claude)

- **Объект:** svend4/ai-colab, ветка `claude/youthful-ramanujan-m7gyjy`, HEAD `543da97` (коммит «Create LICENSE», 2026-11-02).
- **Состояние дерева:** `git status` пуст до и после аудита. Единственные изменения коммита — этот отчёт и запись в `queues/outbox/`. Игнорируемые `tools/__pycache__/*.pyc`, созданные во время аудита, удалены (раздел 9).
- **Метод:** 7 независимых линз (статический разбор и read-only проверки), затем адверсариальная верификация: 124 утверждения, 142 вердикта (97 CONFIRMED, 45 PARTIAL, 0 REFUTED), 48 адверсариальных проверок (воспроизведение, опровержение и оценка воздействия). Раздел 2.
- **Ключевые границы:** клон shallow (61 коммит, самый ранний `25600ab` от 2026-07-06); настройки GitHub недоступны; живые хуки не активны в клоне. Раздел 10.

## 1. Резюме

Исполнение в порядке, защиты — декларативны.

**Исправлено и подтверждено:**
- Тесты зелёные: pytest 8.2.2 — 188 passed на Python 3.11 и 3.13; `tools/test_all.py` — 147 из 147 скриптов.
- На `main` для `543da97` проходят `Canon Check` (smoke на 3.11 и 3.13), `Bulk-Deletion Guard` и `Nightly Tests` (проверено через GitHub).
- `dir_health` без FAIL (было 2). Навигация покрывает 84 из 84 тем.
- Fail-open в `immune.py` устранён: сбой git даёт код 2 (для проверенных классов сбоя).
- Takeover протухших claim выровнен с `pipeline.py` (O_EXCL, перепроверка, `os.replace`). Формы `-v`, `--volume=`, `--mount`, `--net host` в `execute_preflight` дают ERROR.

**Не исправлено — главное:**
1. **Защиты декларативны.** Права агентов принуждает только совещательный `permissions.py`, который не вызывают ни хуки, ни CI (NF-03). Гейт «человек подтвердил» — обычный файл, который может создать агент (M-20). Локальные гейты в типичном клоне не работают: хук не исполняемый (100644), `core.hooksPath` не задан, установщика нет (NF-04). Блокировку слияния подтвердить нельзя: API GitHub вернул 403.
2. **Защита от массового удаления обходится.** Токен в сообщении коммита снимает проверку (NF-01). Переименования не считаются удалениями (NF-02). Пороги CI и `bulk_guard` расходятся в обе стороны.
3. **Инцидент outbox-mass-strip.** Срок 2026-07-13 просрочен на 116 дней, закрытия нет. T-269 в статусе `doing` с протухшим claim, который закоммичен в git (NF-27, NF-28).
4. **Правила частично нечитаемы.** В `AGENTS.md` раздел D-027 и в `tools/README.md` раздел D-032 записаны в UTF-16LE с нулевыми байтами. Ни один валидатор этого не проверяет (NF-30). Полный текст D-027 сохранён в `decisions/D-027.md`.
5. **Управление.** D-025 принят без следа человека (NF-16). D-033 засчитан 1 из 2 (NF-14). Ратификации D-034…D-039 записаны пересказами агентов (NF-15). D-018 допускает принятие по консенсусу агентов (NF-17).
6. **Документы расходятся с фактом.** `STATUS.md:13` утверждает «все задачи закрыты, validate без ERROR» — неверно (M-6, high): 287 из 294 задач `done`, validate даёт ERROR=2.
7. **Тесты.** Тесты драйверов не входят в CI (NF-06). `generate.py` при `COLLAB_ROOT` перезаписывает шесть индексов в корне (NF-09). `test_volatile.py` пишет в живое дерево (NF-38).

**Регрессий** относительно аудита 2026-07-02 не найдено.

**Понижены после верификации:** N-SEC-1 — с high до medium (NF-03); N-GOV-1 — с high до low (NF-30). Остальные изменения серьёзности — в разделе 5.

## 2. Метод и границы

**Линзы (этап 1).** Семь агентов. Только чтение; запуски — только в копиях или в отдельных scratch-репозиториях.
- H-статусы (H-1…H-12).
- M-статусы (M-1…M-14 и M-15…M-28).
- L-1…L-15, I-1…I-3 и раздел 5 прошлого аудита.
- Безопасность, CI, лицензия, гигиена git.
- Тесты, код и новые модули.
- Канон и управление: решения, задачи, драйверы, очереди.

**Верификация (этап 2).** Каждое утверждение проверялось независимым агентом.
- Воспроизведение по цитате: ~94 проверки в шести пакетах.
- Опровержение (поиск контраргументов) и оценка воздействия: 48 проверок, для статусов «ИСПРАВЛЕНО», спорных и medium-находок.
- Исходные оценки серьёзности агентов пересматривались по результатам проверки (раздел 5).

**Уровни доверия** в таблицах:
- **V2** — воспроизведение плюс опровержение (и воздействие).
- **V1** — независимое воспроизведение.
- **—** — только утверждение агента либо собственный прогон; указано явно.

**Итоги верификации:** 124 утверждения, 142 вердикта — 97 CONFIRMED, 45 PARTIAL, 0 REFUTED. PARTIAL означает, что ядро утверждения верно, а часть формулировки, цифр или механизма — нет. Поправки приведены в разделе 5. Одна цитата в N-A4-6 оказалась неверной, и пункт получил PARTIAL.

**Границы:**
- Клон shallow: 61 коммит, самый ранний `25600ab` (2026-07-06). Всё, что опирается на историю до этой границы, помечено «история не проверена».
- Настройки GitHub (branch protection, required checks, default branch, права токена) недоступны: API вернул 403. Барьеры слияния не подтверждены.
- Живые хуки в клоне не активны (`core.hooksPath` не задан, в `.git/hooks` нет активных скриптов). Хуки проверены по коду и в scratch-репозиториях.
- pytest 8.2.2 (из `requirements.txt`) установлен в отдельный venv. Драйверы не запускались: пакет `mcp` не установлен и не объявлен.
- CI проверен через GitHub-инструменты, не через `gh`.
- `git fetch` и `ls-remote` не выполнялись; доступность `origin` не проверялась.

## 3. Статусы прошлых находок (аудит 2026-07-02)

Всего 70 пунктов: 58 находок (H-1…H-12, M-1…M-28, L-1…L-15, I-1…I-3) и 12 пунктов раздела 5.

| Статус | H | M | L | I | Раздел 5 | Итого |
|---|---|---|---|---|---|---|
| ИСПРАВЛЕНО | 3 | 13 | 5 | 0 | 8 | **29** |
| ЧАСТИЧНО | 9 | 15 | 7 | 0 | 3 | **34** |
| ОТКРЫТО | 0 | 0 | 0 | 1 | 1 | **2** |
| НЕАКТУАЛЬНО (в клоне) | 0 | 0 | 1 | 0 | 0 | **1** |
| НЕ ПРОВЕРЕНО | 0 | 0 | 2 | 2 | 0 | **4** |
| РЕГРЕСС | 0 | 0 | 0 | 0 | 0 | **0** |

### 3.1. H — высокий приоритет (H-1…H-12)

| ID | Статус | Проверка | Что сейчас |
|---|---|---|---|
| H-1 | ИСПРАВЛЕНО (с оговорками) | V2: воспроизведение CONFIRMED low, опровержение PARTIAL low, воздействие CONFIRMED low | При сбое git (OSError, таймаут, ненулевой код) `immune.py` выходит с кодом 2. Советник: блоков на нём нет. Литеральная команда из отчёта даёт код 127 (нет `python` при временном PATH). Путь exit 0 при двух пустых выводах git вне классификации. |
| H-2 | ЧАСТИЧНО | V2: PARTIAL medium / medium / low | HEAD согласован (`generate.py --check` OK). Но `indexes/docs.md` отстаёт на один файл, а folder-индексы не проверяет ни один гейт (NF-39). |
| H-3 | ИСПРАВЛЕНО | V2: CONFIRMED info | `blocks.py scan` заменён на `blocks.py pyramid` в обоих quickstart. |
| H-4 | ЧАСТИЧНО | V1: CONFIRMED low | Инвентарь закрыт (GEN:tools-index содержит все 146 не-тестовых скриптов). `repo_hygiene.py` и `workflow_recover.py` кодом не вызываются (NF-40). NUL в `tools/README.md` (NF-30). |
| H-5 | ЧАСТИЧНО | V2: CONFIRMED low; V1: CONFIRMED medium | Владелец (Stefan) и срок 2026-07-13 назначены. Срок просрочен на 116 дней, закрытия нет. Резерв 2026-07-05 — метаданные ID; действующего claim нет (NF-27). |
| H-6 | ЧАСТИЧНО (ратифицировано; enforcement не активен) | V2: PARTIAL high; V1: PARTIAL medium | D-026 accepted. Хук вызывает `bulk_guard --hook`. Но файл хука не исполняемый, `core.hooksPath` не задан, установщика нет. Ветка bulk-проверки в `commit.py` мёртвая (NF-04). Блокировку слияния не проверить (403). |
| H-7 | ЧАСТИЧНО | V2: CONFIRMED medium; V1: CONFIRMED high | Deny-список работает для трёх путей (exit 1). Не охвачены код гейтов и workflows (NF-03). |
| H-8 | ЧАСТИЧНО | V2: PARTIAL medium; V1: CONFIRMED low | Gate 1 есть, но обходится: `execute_decision` не ограничен `decisions/`; `mode: "execute"` в кавычках пропускает Gate 1 и проверку sandbox; `sandbox_runner` манифест не читает (NF-23). |
| H-9 | ЧАСТИЧНО | V2: PARTIAL medium; V1: CONFIRMED info | Формы `-v`, `--volume=`, `--mount`, `--net host` дают ERROR. Склеенные короткие флаги (`-dv`, `-itv`) не распознаются (NF-24). Путь пока недостижим: execute выключен. |
| H-10 | ИСПРАВЛЕНО (с остатком) | V2: PARTIAL low; V1: CONFIRMED low | Takeover идентичен `pipeline.py`. Остаток: при битом front-matter claim `agent_queue` уходит в бесконечную гонку (NF-61). |
| H-11 | ЧАСТИЧНО | V2: CONFIRMED medium; V1: CONFIRMED medium | `acquire` не удаляет лок вслепую. Но `release()` из CLI без токена снимает свежий лок того же agent-id и возвращает 0 (NF-25). |
| H-12 | ЧАСТИЧНО | V2: CONFIRMED medium; V1: CONFIRMED medium | `atomic_write` (tmp + `os.replace`) есть. Цикл read → check → write без блокировки: молчаливая потеря чужой записи (NF-26). |

### 3.2. M — статусы (M-1…M-28)

| ID | Статус | Проверка | Что сейчас |
|---|---|---|---|
| M-1 | ИСПРАВЛЕНО | V1: CONFIRMED info; CI nightly — success (GitHub) | `conftest.py` с фикстурой `root` есть; тесты `tools/tests` зелёные в CI. |
| M-2 | ЧАСТИЧНО | V1: CONFIRMED low | Полный вход есть: `test_all.py` — 147/147. pytest собирает 188 тестов в 39 из 147 файлов. `PROTOCOL.md` о тестах молчит. |
| M-3 | ИСПРАВЛЕНО | Прогон: `dir_health.py` → FAIL 0, WARN 25 | Пороги соблюдены. |
| M-4 | ЧАСТИЧНО | V1: PARTIAL low | `orphans = 0` держится на упоминаниях в `docs/` (`dcard_index.md` и др.), а не на подключении. `repo_hygiene.py` и `workflow_recover.py` — только в docs (NF-56). |
| M-5 | ИСПРАВЛЕНО | V1: CONFIRMED info | Строки T-196/T-197 зачёркнуты или перенесены в Shipped. |
| M-6 | ЧАСТИЧНО | V1: CONFIRMED high | Счётчики в `STATUS.md` сгенерированы верно (294/39/24/84). Нарратив `STATUS.md:13` неверен: «все задачи закрыты (done), ready-пул пуст, validate без ERROR». Фактически 287 из 294 done, validate ERROR=2. Срок 2026-07-13 в `STATUS.md:14` указан как действующий. |
| M-7 | ИСПРАВЛЕНО | V1: CONFIRMED low (детали — PARTIAL) | index.json: 84 из 84 тем. Validate проверяет title (`check_topics`). Уточнение: generate берёт title из front matter, заголовок `#` — только фоллбэк. |
| M-8 | ЧАСТИЧНО | V1: CONFIRMED low | D-029 принят (accepted, 2026-07-05), но `docs/independent-consensus-overview.md:58, :63` всё ещё пишут «D-029 proposed». |
| M-9 | ЧАСТИЧНО | V1: PARTIAL low | D-033 — 1 из 2 подтверждений (подтверждено). Утверждение «нет срока для proposed» неверно: C29 (порог 5 дней) есть, но ссылка из заблокированной T-280 глушит предупреждение (NF-14). |
| M-10 | ЧАСТИЧНО | V1: PARTIAL low | Указатели `next` у agent-pipeline и ai-os-bridge — на done-задачи T-274 и T-273; у meta-sanation и triadic — на несуществующую T-284. Счётчик «активных» тем: 8 в тексте, 9 в сгенерированной навигации. |
| M-11 | ИСПРАВЛЕНО (с побочным эффектом) | V1: CONFIRMED low | Автоочистка heartbeat по done-задачам есть. Но `cmd_status` её выполняет, то есть статус не чисто читающий (NF-33). |
| M-12 | ИСПРАВЛЕНО | V1: CONFIRMED none | `AGENTS.md:15`: захват через `pipeline.py next`; `queues/claimed/` — legacy. Но pipeline использует этот каталог как хранилище lease (NF-28). |
| M-13 | ИСПРАВЛЕНО | V1: CONFIRMED low | README: индексы не править вручную; `generate --check` в pre-commit — WARN, блокирует CI. |
| M-14 | ЧАСТИЧНО | V2: CONFIRMED medium (NF-18) | В PROTOCOL §10 запрет `git add -A` есть. Но `docs/agent-onboarding.md:158-159` всё ещё рекомендует его. |
| M-15 | ЧАСТИЧНО | V1: PARTIAL low | `board.md` и `STATUS.md` названы каноническими; `board.py` генератором не назван. Но фраза «board.py не существует» осталась как отрицание в строке 89. |
| M-16 | ИСПРАВЛЕНО | V1: CONFIRMED low | Glossary: срез 2026-07-05, счётчики не дублируются, «D-001..D-009» отсутствует. |
| M-17 | ЧАСТИЧНО | V1: CONFIRMED low | PROTOCOL §10 и AGENTS.md описывают commit_queue и D-022. `docs/protocol-machine-layer.md` не упоминает commit_queue, worktree, D-031, D-022, cohort. |
| M-18 | ЧАСТИЧНО | V1: CONFIRMED low | Pipeline (в копии): готовы 4, в работе 0, заблокированы 3 (T-269 и T-293 — протухший claim; T-280 — blocked). Условие «ready=0» снято. |
| M-19 | ИСПРАВЛЕНО (с поправкой) | V1: PARTIAL low | `queues/inbox/` содержит только README. Дамп перенесён в `queues/done/` (status historical; covered_by T-067, T-068, T-077). Поправка: в дампе один GEN-блок, а не три. |
| M-20 | ЧАСТИЧНО | V1: CONFIRMED medium | Gate 10: подтверждение — обычный файл; проверка — regex `status: approved` без автора (`execute_human_gate.py:33-38, :80-91`). Deny работает только при указании агента. `sandbox/approvals/` отсутствует. `pre-commit` permissions не вызывает (NF-03). |
| M-21 | ЧАСТИЧНО | V1: CONFIRMED medium | `_canon.py:47, :51, :55` согласован с AGENTS.md:22-25. Но summarizer, reviewer и researcher (AGENTS.md:34-36) отсутствуют в `_canon`, `permissions.json` и `participants/`. `antigravity` сохраняет ключ в permissions.json. Зоны mavis, novax и antigravity шире таблицы. Регистр «Mavis» и «mavis» расходится (`permissions.py:101`). |
| M-22 | ЧАСТИЧНО | V1: PARTIAL medium | Из 146 не-тестовых скриптов 50 пишут файлы (`open` с w/a/x). `safe_write` используют 7 файлов (в отчёте было 3). `set_status` переведён на `atomic_write`. `atomic_write` не защищает от урезания содержимого. Сырые записи остались: `generate.py:480, :498`. |
| M-23 | ИСПРАВЛЕНО | V1: CONFIRMED medium | `action_tracker.py` импортирует только `parse_fm`; `dump_fm` локальный. |
| M-24 | ИСПРАВЛЕНО | V1: PARTIAL low | Claim-механика вынесена в `_claims.py`. `pipeline.py` и `agent_queue.py` делегируют; `queue.py` — shim. Остатки: NF-61 (livelock) и claim-файлы в git (NF-28). |
| M-25 | ЧАСТИЧНО | V1: CONFIRMED low | `ownership.py`, `cohort.py`, `variants.py` берут ростер из `_canon`. `genetic_router.py:10` — свой список (NF-34). |
| M-26 | ЧАСТИЧНО | V1: PARTIAL medium | Три места исправлены: `commit_queue` (карантин), `pipeline.py --ratio` (ошибка, rc 2), `conveyor.py` (WARN). Но `conveyor.load()` молча подменяет повреждённый леджер пустым, а `_staged_diff()` молча возвращает пустую строку. Утверждение «молчаливых проглатываний нет» неверно. |
| M-27 | ИСПРАВЛЕНО | V1: CONFIRMED info | Ветки `main` и `origin/main` существуют, обе на `543da97`. Предпосылка «remote не настроен» устарела. Доступность `origin` не проверялась. |
| M-28 | ИСПРАВЛЕНО | V1: CONFIRMED info | `logs/` не в git; `.gitignore:18` исключает `logs/heartbeat/`. |

### 3.3. L — статусы (L-1…L-15)

| ID | Статус | Проверка | Что сейчас |
|---|---|---|---|
| L-1 | ЧАСТИЧНО | V1: PARTIAL low | `dangling = 11` подтверждено. Маркер `[planned]` есть на 11 строках в 6 файлах (не на 10). Непомеченные ссылки: разбивка 7/3/1 подтверждена. |
| L-2 | ЧАСТИЧНО | V1: CONFIRMED medium | `stream.py check`: 11 потоков в статусе ready-for-synthesis от 2026-06-25 — правило P-11 нарушено (из пяти исходных: 3 adopted, 2 archived). |
| L-3 | НЕАКТУАЛЬНО (в клоне) | — | `z` в клоне отсутствует. На машине автора не проверено. |
| L-4 | ИСПРАВЛЕНО (документировано) | V1: PARTIAL low | Файл содержит пометку «тело отчёта утеряно» и итог проверки бэкапа (2026-07-05). Утверждение «`25600ab` дописал» не проверяется из-за границы shallow. |
| L-5 | ЧАСТИЧНО | V1: CONFIRMED medium | Хук в шапке «ЧЕРНОВИК»; пропуск логируется в `logs/friction.jsonl`; `permissions.py` не вызывается; `core.hooksPath` не задан (NF-04). |
| L-6 | ИСПРАВЛЕНО | V1: CONFIRMED low | `drivers/files.md:21` = `files_driver.py:40` (1048576). |
| L-7 | ЧАСТИЧНО | V1: PARTIAL low | 47 файлов с `C:\Users\stefan` подтверждены строгим шаблоном. Метод в цитате неточен; число 37 не проверяется. Остаток по каталогам: topics 14, reports 9, docs 8, queues 6, tasks 2, sandbox 2, tools 2, фикстуры 4. |
| L-8 | ИСПРАВЛЕНО | V1: CONFIRMED info | `dcard_indexer.py` без голых except и без импорта yaml. `requirements.txt` = `pytest==8.2.2`. |
| L-9 | ИСПРАВЛЕНО (с остатком) | V1: PARTIAL low | Неизвестный первый аргумент даёт сообщение и exit 2. Аргументы после ROOT молча игнорируются. |
| L-10 | ЧАСТИЧНО | V1: CONFIRMED low | `atomic_write` используется в `pipeline.py`. Остались `except Exception: continue` (600–601) и запись через «w» в `_marker` (270). |
| L-11 | ИСПРАВЛЕНО | V1: CONFIRMED low | `retrieval_bench.py`: `finally` с `shutil.rmtree`; фикстуры через `with`. |
| L-12 | ЧАСТИЧНО | V1: PARTIAL medium | `ls-files --eol`: w/lf 1643, w/crlf 0 — подтверждено. Но счётчик не покрывает 6 файлов (4 бинарные по git, 2 пустых). Остаточные CR есть в трёх отслеживаемых файлах. |
| L-13 | НЕ ПРОВЕРЕНО | — | Ветки `agent/codex/T-162` и worktree — только на машине автора. |
| L-14 | ЧАСТИЧНО | V1: PARTIAL low | `janitor.py`: dry-run по умолчанию, `--delete` выключен. Не подключён к хукам и CI (вызывается вручную). |
| L-15 | НЕ ПРОВЕРЕНО | — | В клоне loose-объектов 0 (in-pack 2317, 3.82 MiB), поэтому цифра 12780 неприменима. На машине автора не проверено. |

### 3.4. I — статусы (I-1…I-3)

| ID | Статус | Проверка | Что сейчас |
|---|---|---|---|
| I-1 | НЕ ПРОВЕРЕНО | — | `indexes/canon.db` в клоне отсутствует (gitignored). |
| I-2 | ОТКРЫТО | V1: CONFIRMED low | `dialog.md`: 167264 байт, 1559 строк; архива нет. Крупнейший tracked-файл — `reports/audit-claude-2026-07-02.json` (343771 байт). |
| I-3 | НЕ ПРОВЕРЕНО | — | Положительные наблюдения по указанию не перепроверялись. |

### 3.5. Раздел 5 прошлого аудита (carry-over)

| ID | Статус | Проверка | Что сейчас |
|---|---|---|---|
| B-01 | ИСПРАВЛЕНО | V1: CONFIRMED info | `test_instruction_trace` проходит; D-001 вынесен из surfaces. |
| B-02 | ИСПРАВЛЕНО | V1: CONFIRMED info | `test_synthesis_helper` проходит; заголовки «## Варианты», «## Расхождения» на месте. |
| B-03 | ИСПРАВЛЕНО | V1: CONFIRMED info | `test_info_draft` использует `mkdtemp`. |
| B-04 | ИСПРАВЛЕНО | V1: CONFIRMED info | Bare CR в `reconcile_state.py` и `dispatch.py` отсутствуют. |
| E-03 | ИСПРАВЛЕНО | V1: CONFIRMED low | `test_guard.md` в корне отсутствует; `.gitignore:38`. |
| D-04 | ИСПРАВЛЕНО | V1: CONFIRMED low | В D-027, D-028, D-030 полей `reserved_*` нет. Но в 48 файлах они остались (NF-50). |
| F-04 | ИСПРАВЛЕНО | V1: CONFIRMED low | README перечисляет каталоги `tasks/`, `questions/`, `decisions/`, `indexes/`, `drivers/`, `logs/`. |
| F-05 | ИСПРАВЛЕНО | V1: CONFIRMED info | PROTOCOL.md: нет `agent-codex` и `agent-reviewer`. |
| Codex 4.2.3 / P1.3 | ЧАСТИЧНО | V1: CONFIRMED low | `gap_scan dcard`: 13 из 147 `tools/*.py` без блока (было 74 из 242). |
| Gap-inventory f (CANON_DIRS) | ЧАСТИЧНО | V1: CONFIRMED medium | Дублирование: `validate_staged.py:37` держит свою копию без «docs» (NF-20). |
| G2 (D-022) | ЧАСТИЧНО | V1: PARTIAL medium | D-015 и D-023 проверяются в validate (WARN), но диапазон строк в цитате неточен. Cohort guard в хук не входит. Хук не подключён (NF-04). |
| B-07 | ОТКРЫТО | V1: CONFIRMED low | `tools/portal.py` (8118 байт) и `tools/portals.py` (5842 байта): разное назначение, похожие имена. |

## 4. Новые верифицированные находки

Нумерация NF-xx — в этом отчёте. В скобках — ID исходной находки агента.

### 4.1. Medium (27)

| ID | Проверка | Где | Что (исправленная формулировка) | Рекомендация |
|---|---|---|---|---|
| NF-01 (N-A1-4) | V2, medium | `.github/workflows/bulk-guard.yml:50, :54-55` | Токен `bulk-approved`, `allow-mass-delete` или `D-026 accepted:` в сообщении любого коммита диапазона снимает проверку массового удаления. Одобрение не сверяется с решением и человеком. Пороги не совпадают: CI блокирует 21 мелкий файл, который `bulk_guard` не считает массовым; CI пропускает усечение 10 файлов на 400 строк, которое `bulk_guard` считает STOP; CI пропускает ровно 500 удалённых строк, которые `bulk_guard` (правило «≥500») считает массовыми. | Принимать токен только с ID решения `accepted` в `decisions/`; якорить в начале строки; выровнять пороги. |
| NF-02 (N-SEC-3) | V2, medium | `bulk-guard.yml:46-47` | Rename-детект: 40 файлов `canon/` → `archive/` с правкой одной строки дают R=40 и D=0; с `--no-renames` — D=40 и BLOCK. Порог 500 строк не срабатывает ни в одном варианте. Обходится порог числа файлов (>20). | Считать `git diff --no-renames`; учитывать R-записи, выходящие из каталогов канона. |
| NF-03 (N-SEC-1, N-A1-3, M-20) | V2, medium (+ V1 для M-20) | `tools/permissions.json:3-5`, `tools/permissions.py:17, :112-116`, `tools/execute_human_gate.py:33-38, :80-91`, `tools/merge_gate.py:66` | Права агентов принуждает только совещательный `permissions.py`. Хуки, `commit.py`, `validate.py` и CI его не вызывают. Стадия permissions в `merge_gate` запускается по запросу и видит только незакоммиченное. Стандартный путь `cohort ship` (`cohort.py:290-294`) гейт не вызывает. Deny-список закрывает хук и подтверждения, но не код гейтов (`bulk_guard`, `staged_check`, `validate`, `_canon`, `permissions`, workflows, `.gitignore`). Deny задуман как закрытие gate-10 и C31, но не принуждается. Гейт человека — файл с `status: approved`, который может создать агент. | Вызывать `permissions.py` в pre-commit и в CI; расширить deny на код гейтов и workflows; подтверждение человека — вне зоны агентов (защищённый каталог с CODEOWNERS или внешний канал). |
| NF-04 (N-SEC-4, N-SEC-6, N-A4-5, N-A4-6; H-6) | V2, medium | `tools/githooks/pre-commit:2, :43-49`, `tools/githooks/post-commit`, `tools/commit.py:171-177`, `.git/hooks/` | Локальные гейты в клоне не работают: `core.hooksPath` не задан, установщика нет. Файл хука в индексе — 100644: git пропускает неисполняемый хук при заданном `hooksPath` (подсказка выводится по умолчанию; при 755 хук запускается). Хук помечен «ЧЕРНОВИК», `validate_staged` работает в WARN-режиме: полный validate при коммите не запускается. Ветка bulk-проверки в `commit.py` мёртвая: отказ только по подстроке ERROR, которой нет в выводе STOP (эксперимент). Post-commit: троттлинг 90 с, фон только при активации и +x. Барьер CI на push не отклоняет push; блокировка слияния требует branch protection (не подтверждено, API 403). Цитата в `pre-commit.full.bak:6` неверна: там команда активации, инструкция замены — в proposal §5. | Сделать хуки исполняемыми в индексе (`git update-index --chmod=+x`); установщик `core.hooksPath` и WARN в validate при пустом `hooksPath`; исправить условие bulk-проверки в `commit.py` (искать STOP); решить, какой барьер реальный (CI и branch protection) и задокументировать. |
| NF-05 (N-A3-5, N-A3-6) | V1, medium | `.gitattributes:7-10`, `docs/agent-quickstart.md:80`, `docs/glossary.md:16`, `docs/HUMAN-DECISIONS-OPEN.md:82` | `merge=crdt` задан, драйвер не настроен (`git config --get merge.crdt.driver` → 1); docs говорят об автоматическом запуске. Запись B1 в HUMAN-DECISIONS-OPEN описывает push на GitHub как нерешённый вопрос, хотя `origin` настроен. | Скрипт установки драйвера; исправить docs; статус удалённого репозитория — подтвердить человеку. |
| NF-06 (N-SEC-7, N-CODE-7) | V2, medium | `.github/workflows/*.yml`, `tools/test_all.py`, `drivers/**/test_*.py` (15 файлов), `requirements.txt` | Тесты драйверов не входят ни в один CI-шаг. `pytest drivers` не собирается: одинаковые basename `test_inventory.py` без `__init__.py`. Три скриптовых теста падают на `mcp` (в requirements его нет). | Добавить `pytest drivers` в nightly с уникальными именами или `--import-mode=importlib`; объявить `mcp` с версией. |
| NF-07 (N-SEC-8) | V1, medium | `.github/workflows/*.yml`, `smoke.py:36-37`, `bulk-guard.yml:78` | Нет блока `permissions:` (токен по умолчанию). Actions подключены тегами (`@v4`, `@v5`), не SHA. Checkout сохраняет токен в `.git/config`. `smoke.py` пропускает критический тест, если файла нет (fail-open). Ошибки `pip` глушатся. | `permissions: contents: read`; SHA-пины; `persist-credentials: false`; fail-closed в smoke. |
| NF-08 (N-SEC-11) | V2, medium (PARTIAL) | `tools/flow.py:222`, `tools/permissions.json:46`, `tools/githooks/` | `flow.py finish` делает checkout `master`; ветки `master` нет (есть `main` и `claude/…`). `antigravity` исключён в `_canon`, но остался в permissions.json. В трекинге дубли хуков (`pre-commit.full.bak`, `pre-commit.fast`). Личный путь в фикстуре — подтверждается не полностью. | Исправить ветку; убрать дубли; заменить личный путь. |
| NF-09 (N-CODE-1) | V2, medium | `tools/generate.py:506-510`, `tools/folder_index.py:29, :71`, `tools/tests/test_generate.py:106`, `tools/tests/test_generate_tools_index.py:92` | При `COLLAB_ROOT` `generate.py` (без `--check`) пишет индексы в корень, из которого запущен: `folder_index.ROOT` берётся из `__file__`. Перезаписываются все шесть BIG-индексов (tasks, decisions, questions, docs, topics, drivers), а не только `docs.md`. Тесты передают `COLLAB_ROOT` и попадают в этот путь. | Передавать root в `folder_index`; тесты — с подменой ROOT. |
| NF-10 (N-CODE-5) | V2, medium | `tools/work_admission.py`, `tools/worktree_gate.py:44, :136`, `decisions/D-039.md` | Гейт B (D-039) не подключён: вызовов `acquire` и `release` нет ни в одном хуке, в `commit.py`, `commit_queue.py`, `pipeline.py`, `top.py`, `cohort.py`, `flow.py` и workflows. Есть только текст подсказки. | Подключить в коммит-путь или пометить нереализованным (T-297); интеграционный тест. |
| NF-11 (N-CODE-8) | V2, medium | `tools/ast_sandbox.py:23-24, :60, :72`, `tools/validate.py:849` | Guard D-036 без теста (MATURITY помечает test=❌). Маркер `# ast: allow-subprocess` (88 файлов) освобождает любой subprocess, включая `shell=True` (проба rc=0). Правил на `shell=True`, `pickle`, `yaml.load`, `extractall` нет. `drivers/` не сканируется. | Тест guard; отдельный маркер для shell-вызовов; сканировать `drivers/`. |
| NF-12 (N-GOV-5) | V2, medium | `tools/validate.py:652-654, :719`; `topics/agent-pipeline.md`, `topics/ai-os-bridge.md`, `topics/repo-review-2026-06-21.md` | У трёх тем нет date и created. Возраст берётся из mtime, а mtime совпадает со временем checkout — возраст 0, C29 печатает OK. Открытых задач, ссылающихся на эти темы, нет. | Возраст из front matter или `git log`; отсутствие даты — WARN. |
| NF-13 (N-GOV-6) | V2, medium | `tasks/T-278.md:11`; `tools/validate.py:210-218` | Задача T-278 (done) опирается на отсутствующий `reports/governance-batch-results-2026-07-06.md`. Отчёта нет ни в дереве, ни в видимой истории. Validate проверяет только колонку «Тема», не тело и поле next. Утверждение «6 из 7 accepted, D-033 proposed» сохранено в `tools/status_drift.py:16`. | Восстановить отчёт или переоткрыть T-278; проверять ссылки в теле задачи. |
| NF-14 (N-GOV-8) | V2, medium (PARTIAL) | `decisions/D-033.md:9, :31, :207`; `tasks/T-290.md:20-21` | Единица «1 из 2» засчитана за котёл-день доработку. Доработка — не подтверждение: по собственным правилам D-033 доработка должна сбрасывать счётчик в 0 — этого не сделано. Единица существовала в `25600ab` (до котёл-дня), то есть каузальная связь неверна. Подлинность «1» подтверждается только текстом агента и противоречит 0/2 в human-actions-plan того же дня. | Пересчитать до 0/2 или зафиксировать подтверждение человека дословной цитатой. |
| NF-15 (N-GOV-9) | V2, medium | `docs/HUMAN-DECISIONS-OPEN.md:29, :36, :90`; `reports/human-actions-plan-2026-07-06.md:110, :164`; `decisions/D-034.md:13`; `decisions/D-035.md:13` | Провенанс D-034…D-039 — пересказ агента без цитаты реплики. D-035 §3 предписывает это писарю, но проверить провенанс не с чем: реплика в репо не хранится. Метка C1 означает разное; одна реплика «C1(b)» засчитана обоим пунктам. Метка E3 в сводке «ПРИМЕНЕНО» отсутствует, хотя D-035 и T-270 считают её принятой тем же ответом. | Журнал дословных реплик с датами; развести метки. |
| NF-16 (N-GOV-10) | V2, medium (PARTIAL) | `decisions/D-025.md:1-6`; `docs/HUMAN-DECISIONS-OPEN.md:90`; `reports/` (статус-доклад 2026-06-24) | D-025 — accepted без следа человека: нет записи в файле, dialog.md, QUESTIONS.md, HUMAN-DECISIONS-OPEN; партия «по ответу A3 / волна 3» его не включает. Статус-доклад 2026-06-24 показывает D-025 как proposed, ждущий человека. Утверждение «без даты» опровергнуто: шапка содержит created и last_verified; пустое поле в `DECISIONS.md:34` — потому что генератор читает только ключ `date` (`generate.py:214`). | Подтвердить с записью или вернуть в proposed; гигиена ключа даты — low. |
| NF-17 (N-GOV-11) | V2, medium | `decisions/D-018.md:30`, `decisions/D-006.md:14`, `decisions/D-014.md:17`, `.agents/skills/cauldron-synthesis/SKILL.md:23`, `AGENTS.md:14` | Буквальное чтение D-018 и SKILL.md допускает accepted при консенсусе агентов. D-006 и AGENTS.md требуют человека или назначенного сборщика. Практика 2026-07-06 — ратификации за человеком; двухагентного консенсуса по D-014 в репо нет. Правило неоднозначно. | Отдельное решение о правиле для accepted. |
| NF-18 (N-A2-7) | V2, medium | `docs/agent-onboarding.md:158-159`; `PROTOCOL.md:190-191`; `docs/commit-safety-standard.md:26` | Онбординг рекомендует `git add -A` как работающую команду — против PROTOCOL §10 и стандарта коммита. Оговорки для параллельной работы нет. | Заменить на явный список путей или `commit.py`. |
| NF-19 (N-A2-10) | V1, medium | `topics/*.md` | 57 из 84 тем в `status: proposed` (52 датированы; возраст 133–138 дней). Жизненный цикл тем не замыкается. | Срок для proposed-тем или архивация. |
| NF-20 (GAP-F) | V1, medium | `tools/validate_staged.py:37`, `tools/_canon.py:39` | `CANON_DIRS` продублирован; копия в `validate_staged` без `docs`. | Импорт из `_canon`. |
| NF-21 (N-A1-2) | V2, medium | `tools/githooks/pre-commit:52, :91-94`, `tools/staged_check.py:65-80, :97-98`, `tools/tests/test_staged_check.py` (случай b) | Навигация застейджена раньше, источник меняется и стейджится отдельно: `unstaged_generated` пуст, блока нет. `staged_check.verdict(['topics/x-2026.md','STATUS.md','index.json'], [])` → blocked False. Тест фиксирует это как ожидаемое. Proposal §4 утверждает обратное — неверно. CI (`bulk-guard.yml:81-88`) поймает после push. | Сверять застейдженные генераты с застейдженными источниками. |
| NF-22 (N-A1-5) | V2, medium | `tools/execute_preflight.py:229-288`, `tools/code_activation.py:163-178` | `check-command docker run --pid host --ipc host --cap-add=SYS_ADMIN --security-opt seccomp=unconfined …` даёт OK. `--memory-swap 1g` проходит Gate 6 подстрочной проверкой. Ложный OK переиспользуется в `code_activation.py`, но его state захардкожен как blocked. Execute выключен; ни один драйвер не `mode: execute`; approval-файла нет. | Разбирать флаги токенами; запрещать `*=host`, `--cap-add`, `--security-opt`, `--device`. |
| NF-23 (H-8) | V2, medium (PARTIAL) | `tools/validate.py:533-541, :542`, `tools/execute_preflight.py:59-60, :65`, `tools/_canon.py:164-175`, `tools/sandbox_runner.py` | Gate 1 обходится: `execute_decision` не ограничен каталогом `decisions/` (путь наружу, например `../docs/...` со status accepted); `mode: "execute"` в кавычках пропускает Gate 1 и проверку sandbox; `sandbox_runner` и `execute_audit` манифест не читают, поэтому драйвер с `mode: read-only` запускает docker без решения. | Нормализовать YAML-скаляры; ограничить путь `decisions/`; читать манифест в `sandbox_runner`. |
| NF-24 (H-9) | V2, medium (PARTIAL) | `tools/execute_preflight.py:150-189`, `tools/sandbox_runner.py:41-73` | Склеенные короткие флаги (`-dv`, `-itv`, `-dv=`) не распознаются, а docker разбирает `-dv X` как `-d -v X`. При `image='-dv'` проверка изоляции проходит (симуляция). Путь не достижим для выполнения, пока execute выключен. Gate 10 привязан к драйверу, а не к маунтам. | Токенизировать docker-команду; тесты на склеенные флаги. |
| NF-25 (H-11) | V2, medium | `tools/commit_lock.py:175-191` | `release()` из CLI без `--token` снимает свежий лок того же agent-id и возвращает 0 (для другого имени — rc 1). Проверка токена на CLI-пути не выполняется; докстринг обещает сверку. | Требовать токен или эпоху в CLI. |
| NF-26 (H-12) | V2, medium | `tools/_ioutil.py:122, :142` | `safe_write`: окно между проверкой (142) и `os.replace` (122) даёт молчаливую потерю чужой записи. Остаток H-12: truncate закрыт, race — нет. Явного принятия риска не найдено; в handoff C11 отмечен исправленным без упоминания TOCTOU. | Блокировка или CAS на read-check-write; либо явное решение о принятии риска. |
| NF-27 (N-A1-6, H-5) | V1, medium | `topics/incident-outbox-mass-strip-2026-06-24.md:6, :82-83`, `board.md:24`, `STATUS.md:14`, `tasks/T-269.md:5, :12` | Срок 2026-07-13 просрочен на 116 дней; инцидент `open`; записи о закрытии нет; `STATUS.md:14` подаёт срок как действующий. Резерв `2026-07-05` — метаданные ID (`next_id.py`), не активный claim. | Решение человека (раздел 7). |

### 4.2. Low и info (34)

| ID | Проверка | Где | Суть |
|---|---|---|---|
| NF-28 (N-A3-2) | V2, low | `queues/claimed/T-269.claim.md:5`, `queues/claimed/T-293.claim.md:3,5`, `.gitignore` | Claim-файлы закоммичены (`747ba0b`, `fcf9df2`), протухли 2026-07-06. Имена агентов сравниваются регистрозависимо: `novax` не может завершить T-293 под claim `Novax`. Validate расхождение не видит. Документы противоречат: PROTOCOL.md:93 — legacy, `pipeline-operator-guide.md:55` — источник правды. |
| NF-29 (E-root) | V2, low (PARTIAL) | `tools/validate.py:481-510, :901`, `decisions/D-011.md`, `.github/workflows/canon-check.yml` | ERROR на свежем клоне — намеренная presence-проверка по D-011 (принятый bootstrap, Q-022). CI проходит, потому что snapshot идёт до smoke. Узкое расхождение с D-022 п.3 (не валить гейт на волатильных) и сообщение без команды bootstrap. |
| NF-30 (N-A1-1, N-A4-1, N-A4-2, N-SEC-5, N-GOV-1, N-A2-1, N-A2-2) | V2, low | `AGENTS.md:47-50` (86 NUL), `tools/README.md:638-644` (156 NUL), `queues/done/2026-06-21-driver-acceptance-output.txt` | Блоки UTF-16LE (588 и 734 байта). Файл очереди — сырой дамп по замыслу (T-265). Полный текст D-027 — в `decisions/D-027.md` (58 строк, NUL=0); `docs/agent-approval-matrix.md` (327 строк) — тоже чистый. Enforcement от текста не зависит. Git считает файлы бинарными; `grep` обрывает на NUL. Проверки кодировки нет. Серьёзность — low (исходно high). |
| NF-31 (N-A1-7) | V1, low | `tools/immune.py:23, :60-73, :181-189` | На репозитории без коммитов `git log` → код 128 → «сбой git» и exit 2, хотя докстринг обещает 0 для короткой истории. |
| NF-32 (N-A1-8) | V1, low (PARTIAL) | `AGENTS.md` (D-027), `tools/githooks/pre-commit:2`, `tools/blocks.py:74`, `tools/bulk_guard.py:18` | Документы расходятся с кодом: D-027 говорит о блокировке зон на pre-commit, но хук и CI не вызывают `permissions.py`; шапка «не активен»; комментарии «WARN до ратификации» и «D-026 proposed» устарели; реестр AGENTS.md уже, чем permissions.json (mavis, novax, antigravity); `tools/` нигде не разрешён, хотя реестр говорит «помощь с tools/». |
| NF-33 (N-A3-3, N-A2-4) | V1, low | `tools/pipeline.py:548-550, :586-617, :610` | `cmd_status` вызывает `collect_heartbeats`, который удаляет `logs/heartbeat/<agent>.json` по закрытым задачам (`os.remove`). Статус не чисто читающий. В клоне файлов нет, эффект не проявился. |
| NF-34 (N-A3-4) | V1, low | `tools/genetic_router.py:10` | Список агентов (summarizer, reviewer) вне `_canon` и `AGENTS_ROSTER`; импортёров нет. |
| NF-35 (N-A4-3) | V1, low (PARTIAL) | `queues/done/2026-06-21-driver-acceptance-output.txt`, `reports/audit-infrastructure-changes-2026-07-06.md:17` | Файл: BOM и ASCII с CRLF, далее UTF-16LE с байта 40. «38 одиночных CR» — ошибка подсчёта: это CRLF-пары. Одиночный CR есть в отчёте (строка 1). |
| NF-36 (N-A4-7) | V1, low (PARTIAL) | `docs/`, `decisions/`, `queues/done/`, `dialog.md`, `TASKS.md` | Ссылки на `tools/test_*.py`, перенесённые в `tools/tests/`: по репозиторию 98 уникальных путей; 94 в `tools/tests/`, 1 в корне (`test_all.py`), 3 не существуют: `test_race_test.py` (план `git mv` в T-190), `test_specific_file.py`, `test_X.py`. Цифры агента (95/91) неверны. |
| NF-37 (N-A4-8) | V1, low | `tools/stream.py:431, :451`, `docs/parallel-work-policy.md:224`, `tools/friction.py:805` | Дефолт `check`/`archive` — 14 дней; политика и friction — 7 дней. Сейчас эффекта нет. |
| NF-38 (N-CODE-2, N-CODE-3) | V2 / V1, low | `tools/tests/test_volatile.py:44, :71`; `tools/execute_audit.py:35`; `tools/test_all.py:112` | `test_volatile` запускает `snapshot` с cwd=ROOT и перезаписывает четыре gitignored-файла в дереве, где лежит. Изоляции по умолчанию нет. Тесты пишут `reports/audit_*`, `.pytest_cache/`. Запускать тесты в копии (как в этом аудите). |
| NF-39 (N-CODE-4) | V2, low | `indexes/docs.md`; `tools/folder_index.py`; `tools/generate.py:506`; `smoke.py`; `bulk-guard.yml` | Файл на один документ отстаёт (`additive-enrichment-shortlist`). Числа агента («146 строк при 148») завышены: файл — 155 строк, README исключён по дизайну. Folder-индексы не проверяет ни один гейт, включая `generate --check`. |
| NF-40 (N-CODE-9) | V2, low | `tools/chrono_guard.py`, `holo_distiller`, `quantum_merge`, `entropy_monitor`, `genetic_router`, `memoize`, `ast_healer`, `butterfly_cron`, `butterfly_sleep`, `friction_advisor` | Добавлены 2026-07-06..07, без тестов и без вызовов (упоминания — только README и MATURITY). |
| NF-41 (N-CODE-10) | V1, low (PARTIAL) | `tools/friction_advisor.py:27, :54` | Голые except. Нечитаемая тема тихо выпадает через статус read-error; тестов нет. |
| NF-42 (N-CODE-11) | V1, low | `drivers/test_tmp.py:17, :46`, `tools/tests/test_assurance.py:30` | Helper из `drivers/` импортируют тесты `tools/tests`; temp-каталог пишется в реальный `tmp-work/`. |
| NF-43 (N-CODE-13) | V1, low | `tools/githooks/pre-commit.full.bak`, `drivers/codex-local/test_codex_local.py:14-31` | Резервная копия хука в трекинге; тест codex-local проверяет только тип, ключ и whitelist. |
| NF-44 (N-GOV-3) | V2, low (PARTIAL) | `tools/validate.py:508-510`, `:496-509` | Строка «OK: … присутствуют» печатается безусловно рядом с ERROR в том же прогоне; счётчик OK завышен на 1. Presence-проверка — задуманный дизайн. |
| NF-45 (N-GOV-4) | V2, low | `tools/drift_check.py:145`; `tools/pipeline.py:398` | Drift ищет подстроку «без claim», а pipeline пишет «с протухшим claim». T-269 и T-293 вне дрейфа. `drift_check` в копии даёт exit 1 по ERROR=2. |
| NF-46 (N-GOV-7) | V2, low | `tasks/T-296.md:5`; коммиты `8279a89`, `f443a49`, merge `15a59ff` | Задача в статусе todo, хотя результат смержен. Состояние устарело после слияния. |
| NF-47 (N-GOV-12) | V2, low | `decisions/D-038.md:14`, `decisions/D-015.md:26`, `tools/validate.py:744-745` | D-038 дополняет и сужает D-015 без обратной ссылки; validate считает записи в verified_by, а не агентов (проверено синтетическим прогоном). |
| NF-48 (N-GOV-13) | V2, low (PARTIAL) | `reports/fix-wave2-plan-2026-07-02.md:670`; `tools/status_drift.py` | 29 вариантов Q-W2-* (19 номеров) отсутствуют в QUESTIONS.md. `status_drift` исключает их из счёта по замыслу; D-035 не требует записи. Часть номеров имеет явный провенанс, остальные — «ответ котла». Нужен реестр вопросов котла. |
| NF-49 (N-GOV-14, N-A2-3) | V2, low (PARTIAL) | `topics/meta-sanation-questions-2026-06-24.md:7, :215, :221`; `STATUS.md:83-84`; `index.json:15, :22`; `tools/validate.py:608` | T-283, T-284, T-289 отсутствуют. C19-c сканирует только `docs/` (задокументировано в тесте). Шлюз `HUMAN-DECISIONS-OPEN` Q8 назван, но отмечен как применённый (freeze, `a7faf92`) — живого открытого пункта нет. |
| NF-50 (N-GOV-15) | V2, low (PARTIAL) | `decisions/D-039.md:7-9`; `tasks/`, `questions/` | Поля `reserved_*` остались в 48 файлах (не 46). Ручное снятие есть (`c2d6bf6`), автоматического нет. |
| NF-51 (N-GOV-16) | V2, low (PARTIAL) | коммит `7f12e10`; `docs/commit-safety-standard.md:29` | Сообщение коммита документирует `--no-verify` и `validate OK=17 WARN=5 ERROR=0`. Утверждение «против D-031» неверно: запрет `--no-verify` появился позже (`435985f`). |
| NF-52 (N-GOV-17) | V2, low (PARTIAL) | `queues/outbox/` (193 файла), `queues/done/` (240) | 182 датированных файла outbox (старше 2026-10-07) ≈ 595 КБ; вся папка ≈ 690 КБ (с 11 недатированными). `du` даёт 1.1M на каждую папку. В done 230 файлов без даты. Крупнейший — 69 КБ. |
| NF-53 (N-GOV-18) | V1, low | `tasks/T-295.md:9`; `tools/dispatch.py` | `depends_on` T-295 указывает на решения; dispatch их игнорирует. Название совпадает с `tools/cauldron_task_materializer.py`. |
| NF-54 (N-GOV-19) | V1, low | `drivers/SCHEMA.md`; `decisions/D-013.md`; `code/README.md:10` | SCHEMA остаётся draft при accepted D-013. Ссылка на несуществующий `topics/api-design.md`. |
| NF-55 (N-A2-8) | V2, low (PARTIAL) | `drivers/*.md` (9); `decisions/D-015.md:26`; `tasks/T-293.md:15` | Четыре ready-драйвера имеют одну запись в verified_by при требовании D-015 ≥2 (подтверждено). Утверждение «не пересверялись 136–139 дней» неверно: 8 из 9 имеют след сверки от 2026-07-06, но `source_last_verified` не обновлён. T-293 заявляет verified_by 0 — по факту 1. |
| NF-56 (N-A2-11) | V2, low (PARTIAL) | `tools/gap_scan.py:101-115, :118-144` | G1 засчитывает упоминание в любом `docs/**/*.md`; orphans = 0 держится на `dcard_index.md` и `three-paths-strategy`. Шаблон `\bfold\b` совпадает с английским словом. G5 не видит ссылки на планы без `[planned]`. |
| NF-57 (N-A2-12) | V1, low | `index.json` (193822 байта), `queues/outbox/` (193 файла) | Близко к порогам FAIL (200 KiB и 200 файлов): запас ~11 КиБ и 7 файлов. |
| NF-58 (N-A2-13) | V1, info (PARTIAL) | `tasks/T-061.md:4-5`; `tools/pipeline.py:149-159` | Заглушка-title в done-задаче. Механизм неверен: `is_placeholder_task` вызывается только для todo-задач. Косметика. |
| NF-59 (N-SEC-10) | V1, low | коммит `543da97`; `README.md`; `DECISIONS.md` | LICENSE (AGPL-3.0) добавлен без записи решения и без раздела о лицензии в README. |
| NF-60 (N-CODE-6) | V2, low (PARTIAL) | `tools/test_all.py:21, :75`; `docs/agent-quickstart.md:137-138`; `.github/workflows/canon-check.yml` | «Полный» прогон охватывает самозапускающиеся скрипты; PR-гейт гоняет 5 из 147 файлов (smoke); остальные 142 — только в nightly. Путь `flow.py finish` → `merge_gate` без тестов (флаг выключен). Регрессия в одном из 142 файлов может попасть в main. Потери покрытия из-за обёрток нет. |
| NF-61 (H-10) | V2, low (PARTIAL) | `tools/agent_queue.py` (`write_claim`), `tools/_canon.py:164-175`, `tools/_claims.py:79-80` | Если front matter claim не разбирается, `parse_front_matter` возвращает `{}`. `write_claim` не считает `{}` перехватываемым: `create_claim` падает на O_EXCL, гонка повторяется бесконечно. `pipeline` берёт тот же файл. Противоречит намерению: битый claim не должен вечно блокировать задачу. |

## 5. Поправки к утверждениям агентов

Проверка уточнила или опровергла часть утверждений исходных агентов. Формулировки в разделах 3–4 — уже исправленные.

| Утверждение (ID) | Что верно по проверке |
|---|---|
| N-SEC-1: серьёзность high | Medium. Факт верен; deny задуман как закрытие gate-10, но не принуждается. |
| N-SEC-3: «0 удалённых строк» | Только для чистого переноса или дописывания строки. При замене строки D=40 с `--no-renames`. Порог строк не срабатывает; обходится порог файлов (NF-02). |
| N-SEC-6: post-commit «на каждом коммите» | Завышено: троттлинг 90 с, фон только при активации и +x. Пишет только в gitignored-пути. Низкий риск. |
| N-SEC-11: «в репозитории только main» | Неверно: есть ветка `claude/youthful-ramanujan-m7gyjy`. Ссылка `flow.py:222` на `master` подтверждена. |
| N-CODE-1: индексы «docs.md» | Перезаписываются все шесть BIG-индексов (NF-09). |
| N-CODE-2: серьёзность medium | Low: файлы gitignored и регенерируются. |
| N-CODE-4: «146 строк против 148» | Завышено вдвое: файл 155 строк, README исключён по дизайну. Реальный пропуск — один файл (NF-39). |
| N-CODE-6: «только в nightly» | Буквально неверно для 5 файлов (PR и push в main). Для 142 файлов nightly — единственный автоматический прогон (NF-60). |
| N-CODE-9: серьёзность medium | Low. Даты и отсутствие тестов подтверждены. |
| N-GOV-3: «безусловно» | Верно относительно артефактов. OK-строка печатается в том же прогоне, что и ERROR, — счётчик завышен на 1 (NF-44). |
| N-GOV-4: серьёзность medium | Low. Механизм подтверждён: подстрока не совпадает с формулировкой pipeline. |
| N-GOV-8: «счётчик держится на доработке» | Каузальная часть неверна: «1» существовала до котёл-дня. Подлинность и внутреннее противоречие D-033 — подтверждены (NF-14). |
| N-GOV-10: «без даты» | Опровергнуто: даты в шапке есть, генератор читает только `date`. Человеческий след — подтверждён (NF-16). |
| N-GOV-13: серьёзность medium | Low. Q-W2 исключены из канона по замыслу `status_drift`; часть провенанса явная. |
| N-GOV-14: «шлюз Q8 не назван» | Опровергнуто: Q8 назван в тех же строках. Остаток — статус «применено» без живого пункта (NF-49). |
| N-GOV-15: «46 файлов», «снятия нет» | 48 файлов; ручное снятие есть (`c2d6bf6`). |
| N-GOV-16: «против D-031» | Неверно: запрет `--no-verify` появился позже (`435985f`). Текст коммита подтверждён. |
| N-GOV-17: «690 КБ» | 182 датированных файла — ≈ 595 КБ; 690 КБ — вся папка. |
| N-A2-8: «не пересверялись 136–139 дней» | Неверно: 8 из 9 имеют след сверки от 2026-07-06, но `source_last_verified` не обновлён. Четыре ready с одной верификацией — верно. |
| N-A2-13: «скрыта через is_placeholder_task» | Неверно: функция не применяется к done-задачам. Косметика. |
| N-A4-3: «38 одиночных CR» | Неверно: это CRLF-пары. Смешанная кодировка — верно. |
| N-A4-5: «молча не работают» | Частично: git печатает подсказку по умолчанию (`advice.ignoredHook`). Молчание — в `commit.py` и при отключённых подсказках. Эффект латентен до активации (NF-04). |
| N-A4-6: цитата `pre-commit.full.bak:6` | Неверно: строка 6 — команда активации. Инструкция замены — в proposal §5. |
| N-A4-7: «95 путей, 91 перенесён» | Неверно: 98 уникальных, 94 перенесено. Три отсутствующих — верно (NF-36). |
| N-A3-2: серьёзность medium | Low: блокирует только T-269. Регистровая регрессия подтверждена. |
| N-A1-1: серьёзность medium | Low. Полный текст D-027 есть в `decisions/D-027.md` (58 строк). |
| H-1: «fail-open устранён» | Для заявленных классов сбоя — да. Литеральная команда даёт код 127, не 2. Блоков на immune нет. |
| H-2: «навигация самосогласована» | Неверно для `indexes/docs.md` и folder-индексов (NF-39). |
| H-5: «резерв от 2026-07-05» | Метаданные ID, не активный резерв. «C29 зелёный» — не ложный зелёный: проверка утверждает только наличие открытой задачи. |
| H-6: «ратифицирован и подключён» | Ратифицирован и подключён в коде; enforcement не активен в клоне; ветка bulk в `commit.py` мёртвая (NF-04). |
| H-8: «Gate 1 обеспечивает» | Машинная проверка есть, обходится тремя способами (NF-23). |
| H-9: «-v разбирается» | Верно для отдельного `-v`; склеенные флаги не распознаются (NF-24). |
| H-10: «как в pipeline.py» | Верно для валидных claim; при битом front matter — гонка (NF-61). |
| H-11: «acquire не удаляет вслепую» | Верно. Но `release()` из CLI без токена снимает чужой свежий лок (NF-25). |
| M-6: «все задачи закрыты» | Неверно (high): 287 из 294 done. |
| M-9: «нет срока для proposed» | Неверно: C29 есть, но глушится ссылкой из заблокированной задачи. |
| M-10: «8 активных тем» | 8 в тексте, 9 в сгенерированной навигации. |
| M-19: «три GEN-маркера» | Один GEN-блок. |
| M-22: «safe_write в 3 файлах из ~35» | Пишущих файлов 50, safe_write — в 7. Вывод «большинство без гварда» верен. |
| M-26: «молчаливых проглатываний нет» | Неверно: `conveyor.load()` и `_staged_diff()` молчат. |
| L-1: «10 строк с [planned]» | 11 строк в 6 файлах. |
| L-7: «37 файлов» | 47 подтверждено строгим шаблоном; 37 не проверяется. |
| L-9: «неизвестный аргумент — exit 2» | Верно для первого аргумента; остальные игнорируются молча. |
| L-12: «весь eol покрыт» | 6 файлов не учтены; остаточные CR в трёх файлах. |

## 6. Механические прогоны

Воспроизводимо: команды выполнены из корня репозитория; `git status` не менялся, кроме игнорируемых артефактов аудита (раздел 9).

- `python tools/validate.py` (локально, без snapshot): exit 1, `OK=18 WARN=15 ERROR=2`. ERROR: D-011 — нет `PIPELINE.md` и `logs/pipeline.json` (оба gitignored). В CI шаг «Снимок конвейера» идёт до smoke, поэтому ошибка там не возникает (проверено по логам CI). WARN: T-280 ссылается на отсутствующий бриф; 9 драйверов с возрастом источника 136–139 дней; 4 ready-драйвера с одной верификацией; antigravity вне ростера.
- `python tools/generate.py --check`: OK; тем в навигации 84.
- `python tools/dir_health.py`: `FAIL: 0 WARN: 25` (в 2026-07-02 было FAIL 2).
- `python tools/permissions.py claude tools/permissions.json tools/githooks/pre-commit sandbox/approvals/x.md`: три «ВНЕ ЗОНЫ (deny)», exit 1. `mavis` на `tools/permissions.json` — тоже отказ.
- pytest 8.2.2 на Python 3.11 (копия дерева): 188 passed в 39 файлах; на 3.13 — 188 passed (по данным агента N1). На GitHub CI проверены smoke-шаги на 3.11 и 3.13.
- `pytest drivers`: ошибки сбора (коллизия basename, нет `__init__.py`); три скриптовых теста падают на `mcp` (NF-06).
- `python tools/test_all.py`: 147 из 147 скриптов OK (в CI — nightly success).
- `smoke.py`: rc=0 на 3.11 и 3.13 (копия и CI).
- Синтаксис: `ast.parse` для 345 `.py` (tools, drivers, sandbox, core, portals, code) — без ошибок.
- Pipeline (в копии, без записи в живое дерево): готовы 4 (T-285, T-295, T-296, T-297), в работе 0, заблокированы 3 (T-269, T-293 — протухший claim; T-280 — blocked).
- Счётчики: решения 39 (37 accepted, 1 proposed — D-033, 1 superseded — D-019); задачи 294 (287 done, 2 doing, 1 blocked, 4 todo); вопросы 24; темы 84 (57 в proposed); драйверы 9.
- CI на GitHub для `543da97` (`main`): Canon Check (run 41486154533) — success, smoke 3.11 и 3.13; Bulk-Deletion Guard (run 41486154878) — success; Nightly Tests (run 42154509041) — success, шаг «Run all tests» — success.
- NUL-байты: `AGENTS.md` (86), `tools/README.md` (156). Блоки: 588 и 734 байта (проверено по смещениям).

## 7. Решения, которые нужны от человека

Аудит не принимает решения за человека. Ниже — то, что требует решения Stefan.

1. **Инцидент outbox-mass-strip и T-269** (NF-27, H-5). Закрыть с организационными выводами или продлить с новой датой. Снять протухшие claim (NF-28).
2. **D-033** (NF-14). Пересчитать до 0/2 или подтвердить второе подтверждение дословной цитатой.
3. **D-025** (NF-16). Подтвердить с записью или вернуть в proposed.
4. **Правило для accepted** (NF-17). Может ли решение становиться accepted по консенсусу агентов (D-018) или только по решению человека (D-006, AGENTS.md)?
5. **Ратификации D-034…D-039** (NF-15). Журнал дословных реплик с датами или переоформление.
6. **Политика bulk-guard** (NF-01, NF-02). Отменить токен в сообщении коммита или привязать его к решению `accepted`. Как учитывать переименования.
7. **Гейт человека** (NF-03). Механизм подтверждения, который отличает человека от агента.
8. **Барьер слияния** (NF-04, H-6). Включить branch protection и required checks на GitHub — проверить настройки вне клона (сейчас 403).
9. **Лицензия AGPL-3.0** (NF-59). Оформить решение и раздел в README.
10. **T-283, T-284, T-289** (NF-49). Восстановить шлюз или перенаправить на HUMAN-DECISIONS-OPEN Q8.

## 8. Рекомендуемый порядок работ

**P0 — малые исправления с большим эффектом:**
1. Вернуть UTF-8 в `AGENTS.md` (раздел D-027 — из `decisions/D-027.md`) и перегенерировать `tools/README.md`; добавить проверку NUL-байтов в validate для канон-файлов (NF-30).
2. Исправить нарратив `STATUS.md:13–14` (M-6).
3. Сделать хуки исполняемыми в индексе (`git update-index --chmod=+x`); установщик `core.hooksPath`; WARN в validate при пустом `hooksPath` (NF-04).
4. Исправить ветку bulk-проверки в `commit.py` (искать STOP, NF-04).
5. Сделать validate понятным на свежем клоне: сообщение с командой bootstrap; строку OK печатать только при наличии артефактов (NF-29, NF-44).
6. CLI `commit_lock release` — требовать токен или эпоху; `safe_write` — блокировку или CAS (NF-25, NF-26).

**P1 — защиты и тесты:**
7. Вызывать `permissions.py` в pre-commit и в CI; расширить deny на код гейтов и workflows (NF-03).
8. Bulk-guard: токен только с ID решения `accepted`; `git diff --no-renames`; единые пороги (NF-01, NF-02).
9. Gate 1 и sandbox: нормализация YAML-скаляров, ограничение `execute_decision` каталогом `decisions/`, чтение манифеста в `sandbox_runner`; токенизация docker-флагов и запрет host-namespaces, `--cap-add`, `--security-opt`, `--device` (NF-22, NF-23, NF-24).
10. Тесты: `pytest drivers` в nightly с уникальными именами; `mcp` — объявить (NF-06); `test_all` по умолчанию с pytest; тесты и generate при `COLLAB_ROOT` — в копиях (NF-38, NF-09, NF-60).
11. Workflows: `permissions: contents: read`; SHA-пины; `persist-credentials: false`; fail-closed в smoke (NF-07).
12. Гейт B (`work_admission`) — подключить или пометить нереализованным (NF-10). `ast_sandbox`: маркер без освобождения от shell, тест (NF-11).
13. Governance-инструменты: возраст тем из front matter или git (NF-12); drift по reason (NF-45); ссылки на deliverables в теле задачи (NF-13).

**P2 — документация и гигиена:**
14. `docs/agent-onboarding.md`: убрать `git add -A` (NF-18). `docs/independent-consensus-overview.md`: D-029 (M-8). `docs/protocol-machine-layer.md` (M-17). README: раздел о лицензии (NF-59). HUMAN-DECISIONS-OPEN B1 (NF-05). Stream default 7 дней (NF-37).
15. Непривязанные модули: `repo_hygiene`, `workflow_recover`, `genetic_router`, десять модулей NF-40 — подключить или архивировать. Ростер в `genetic_router` — импорт из `_canon` (NF-34).
16. Гигиена данных: ротация `dialog.md` (I-2); outbox и done (NF-52); `indexes/docs.md` и folder-индексы в `generate --check` (NF-39); claim-файлы в `.gitignore` после решения человека (NF-28).

## 9. Побочные эффекты аудита и уборка

- **`tools/__pycache__/`.** Шесть `.pyc` созданы во время аудита (20:22:39–20:30:09): ранними командами без `PYTHONDONTWRITEBYTECODE` и запусками агентов. Каталог игнорируется git. Удалён после финального прогона (шаг уборки в конце коммита).
- **Scratchpad сессии.** Копии дерева, venv, журналы верификации — вне репозитория.
- **Параллельная работа.** Во время аудита в scratchpad появлялись файлы, созданные другими процессами (по данным агентов). `HEAD` и дерево при этом не менялись.
- **Перезапуски контейнера.** Три перезапуска. Журналы верификации сохранены; недостающие проверки перезапущены. Ни один результат не потерян.
- **Процесс.** Один агент использовал `gh` для чтения CI, хотя `gh` разрешён только для поиска. Результаты CI перепроверены через GitHub-инструменты.
- **Запись в живое дерево.** Тесты и `generate` запускались только в копиях. В живом дереве — только read-only режимы (`validate`, `generate --check`, `dir_health`, `permissions`).

## 10. Ограничения и непроверенное

- **История.** Клон shallow: всё до `25600ab` (2026-07-06) недоступно. Отдельные выводы о более ранних коммитах (например, `92917d5`, тег `backup-outbox-*`, ветки `agent/codex/*`) не проверены.
- **GitHub-настройки.** Branch protection, required checks, default branch, права токена — не проверены (API 403). Блокировка слияния не подтверждена.
- **Живые хуки.** В клоне `core.hooksPath` не задан. Поведение в авторской среде не проверено.
- **Драйверы.** Не запускались: пакет `mcp` не установлен и не объявлен. Их тесты — только сбор pytest и статический разбор.
- **Гипотеза N-SEC-9** (force-push и `github.event.before`) — не проверялась; в отчёт не включена.
- **Только на машине автора:** L-3, L-13, L-15 (ветки, worktree, `z`, loose-объекты).
- **Не перепроверялось по указанию:** I-3 (положительные наблюдения).
- **Файл отсутствует в клоне:** I-1 (`indexes/canon.db`, gitignored).
- **Сила тестов.** Мутационное тестирование не выполнялось.
- **`adoption.py`** не запускался: dormant-статус инструментов установлен по grep.
- **`validate.py` после snapshot** не запускался в живом дереве (только в копии).
- **Нагрузка и производительность** не измерялись.
