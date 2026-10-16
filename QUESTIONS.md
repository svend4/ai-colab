# Вопросы

Здесь собираются вопросы и их статусы, чтобы они не терялись в длинных обсуждениях.

## Правила

- Формулируйте вопрос так, чтобы на него можно было ответить.
- Открытые вопросы разбирайте по D-004: варианты → плюсы/минусы → рекомендация → голоса → итог. Шаблон: `templates/decision-options.md`.
- Если вопрос решен, перенесите итог в `DECISIONS.md`.
- Не удаляйте старые вопросы. Меняйте статус на `answered` или `closed`.

## Список вопросов

<!-- GEN:questions START — генерируется tools/generate.py из questions/*.md, не править вручную -->
| ID | Вопрос | Статус | Кто задал | Кому адресован | Где обсуждается | Итог |
|---|---|---|---|---|---|---|
| Q-001 | Какие имена файлов использовать: русские или ASCII? | answered | Codex | все | `topics/organization.md` | ASCII для новых файлов, кириллица в заголовке; существующие имена — Q-004/D-007. См. D-005. |
| Q-002 | Нужен ли отдельный файл для каждого участника в participants/? | answered | Codex | все | `participants.md` | Да, опционально — карточки для активных участников/агентов с ролью; не обязательно на каждого сразу. |
| Q-003 | Кто будет сборщиком итогов в больших темах: человек, главный AI-агент или скрипт? | answered | Codex | все | `topics/organization.md` | Гибрид — агент/скрипт готовит, человек утверждает. См. D-006. |
| Q-004 | Мигрировать ли существующие русские имена файлов к ASCII? | answered | Claude | все | `topics/migrate-file-names.md` | Постепенная (ленивая) миграция: переименовывать при следующей правке файла. См. D-007. |
| Q-005 | Какие правки считать «значимыми» по D-003 (граница обоснования)? | answered | Stefan | все | `topics/d003-scope.md` | Только значимые (структура/правила/решения/задачи/статусы/протокол/права/очереди/шаблоны); мелочи — без. См. D-008. |
| Q-006 | Кто может регистрировать нового агента в реестр (AGENTS/Участники/permissions)? | answered | Claude | все | `topics/q006-agent-onboarding.md` | Принят вариант A (само-регистрация) на текущем этапе; запланирована эволюция к C. См. D-009. |
| Q-007 | Какой первый вариант реализации «информационных драйверов» выбираем? | answered | Mavis | все | `topics/information-drivers.md` | Принят D-010: вариант B с эволюцией к E; каноническая папка drivers/; сначала L1-манифесты, затем один read-only L2/MCP PoC. |
| Q-008 | Расширенная manifest schema для драйверов — какие поля обязательны? | answered | Mavis | Stefan, Codex, Claude, Novax | `topics/ai-os-bridge.md` | Принят вариант B (driver schema v1) — обязательные поля манифеста зафиксированы. См. D-013. |
| Q-009 | Где находятся репозитории svend4 (доступ для T-024)? | answered | Novax | Stefan | `topics/ai-os-bridge.md` | D-020 §4 ратифицирован 2026-06-23 (svend4 = generic external-source intake, не special) — вопрос «где svend4» снят, см. Итог |
| Q-010 | Переименовать ли папку topics/ в ASCII (topics/)? | answered | Claude | все | `topics/migrate-file-names.md` | Выполнена атомарная миграция T-213: папка переименована в topics/, sweep 353 файлов (темы/→topics/), 8 файлов с backslash-путями, правка 7 hardcode в .py. validate.py: 11 OK 0 WARN 0 ERROR. Тесты ядра зелёные. D-007 закрыт. |
| Q-011 | Как сделать динамический конвейер агентов для управляемой разработки? | answered | Stefan (через Novax) | все | `topics/agent-pipeline.md` | Принят D-011: комбинированный конвейер A+B+C — pipeline.py как pull-next/status/done/fail, PIPELINE.md для людей, logs/pipeline.json для агентов. |
| Q-012 | Делать ли обязательный heartbeat/live-room для агентов? | answered | Codex | Stefan, Claude, Mavis, Novax | `topics/agent-pipeline.md` | Принят D-012: вариант B — добровольный heartbeat; pipeline.py heartbeat пишет per-agent JSON, LIVE.md и logs/heartbeat.json. |
| Q-013 | Как согласовать спорные пункты onboarding/manual roadmap? | answered | codex | все | `topics/ai-os-bridge.md` | Закрыто через Котёл-синтез (см. streams/q013-divergences/divergence.md) |
| Q-014 | Цель проекта — юридический workbench (домен) или универсальный generic-инструмент? | answered | Claude | Stefan | `topics/opinion-synthesis-2026-06-21.md` | Stefan — универсальное ядро + домен как тематический портал/плагин (модель Википедии). См. D-016. |
| Q-015 | Когда Level 1 worktree должен быть обязательным, а не рекомендацией? | answered | codex | все | `topics/commit-policy-streams-2026-06-21.md` | Принят D-022 — вариант B; Level 1 worktree обязателен по триггерам: чужие source-файлы, stale index не от своей работы, hot files, явная параллельная работа или same-file коллизия. |
| Q-016 | Гарантия применения и актуальности инструкций (existence != applied) + поток знания вверх L4->L1 | answered | stefan | все | `topics/assurance-and-doc-merge-2026-06-22.md` | Утверждено котлом: S0 миграция выполнена (проставлен last_verified на D-001..D-023 и политиках). |
| Q-017 | Автоматизация слияния документации агентов — консенсус с cross-references + структурированные разногласия | answered | stefan | все | `topics/q017-docmerge-semantic-2026-06-23.md` | Утверждено котлом. Создана задача T-191 на реализацию семантического гибрида. |
| Q-018 | ФУНД-A — Что есть «ядро» проекта и где его граница (L1 vs порталы)? | answered | Stefan | все | `topics/architecture-fundamentals-2026-06-24.md` | Ядро = file-native движок координации (front-matter-правда + generate/validate + hook) поверх пирамиды L1→L4. Граница L1: core-export (engine-manifest 8 tools + candidates), всё доменное — в L2-порталах. Ответ ~65% (граница «что именно L1» уточняется промоушенами L2→L1). |
| Q-019 | ФУНД-B — Машиночитаемая визитка-карточка у каждого файла? | answered | Stefan | все | `topics/architecture-fundamentals-2026-06-24.md` | ДА — стандарт визитки card→middle→base (docs/card-standard.md, §2 свода) + tools/header.py (извлечь/линтить/покрытие). Замер: 213/214 файлов несут визитку (title+gist). Реализовано. |
| Q-020 | ФУНД-C — Авто-статистика папок (числовые пороги структуры)? | answered | Stefan | все | `topics/architecture-fundamentals-2026-06-24.md` | ДА — tools/dir_health.py (§3 свода): пороги files/folder >200 FAIL/>100 WARN (цель 7-50), файл >50КБ, корней >15, глубина >3. + indexes/ навигация. Реализовано. |
| Q-021 | ФУНД-D — Абсолютная нумерация и внутрифайловая навигация (файл-как-дерево)? | answered | Stefan | все | `topics/architecture-fundamentals-2026-06-24.md` | ДА — стандарт «файл-как-дерево» (§4 свода: метаданные→тело→хвост, dotted-decimal 1.2.3) + tools/heading_check.py (пустые заголовки, пропуск уровней, крупные доки без нумерации). Реализовано как линтер. |
| Q-022 | ФУНД-E — Портабельность: переносима ли рабочая папка/ядро целиком? | answered | Stefan | все | `topics/architecture-fundamentals-2026-06-24.md` | ДА, портабельна — доказано acceptance-тестом tools/portability_check.py (git-archive HEAD → чистый temp → validate/generate). Свежий clone требует РОВНО 1 документированный bootstrap `python tools/pipeline.py snapshot` (воссоздаёт 2 генерируемых снимка PIPELINE.md + logs/pipeline.json, gitignored/untracked по дизайну D-011). После bootstrap: validate rc=0, generate rc=0, ноль хардкода хост-путей. |
| Q-023 | Какая матрица полномочий нужна для людей и AI-агентов? | answered | Codex | Stefan, все агенты | `topics/information-refactoring-cycle-3-2026-06-25.md` | answered by D-027 (accepted 2026-07-06) + docs/agent-approval-matrix.md; roster fixed per A4 (antigravity out until incident explanation; subagent-worker = service agent) |
| Q-024 | Что делать с T-285: задача в doing без claim блокирует drift-гейт smoke | answered | claude | Stefan | `tasks/T-285.md, tools/drift_check.py (пункт «orphan: doing без claim»)` | "Выбран вариант A, T-285 возвращена в todo и резерв снят. Решение 2026-10-16 через карточку решения в треде проекта." |
<!-- GEN:questions END -->
