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
| Q-010 | Переименовать ли папку topics/ в ASCII (topics/)? | open | Claude | все | `topics/migrate-file-names.md` |  |
| Q-011 | Как сделать динамический конвейер агентов для управляемой разработки? | answered | Stefan (через Novax) | все | `topics/agent-pipeline.md` | Принят D-011: комбинированный конвейер A+B+C — pipeline.py как pull-next/status/done/fail, PIPELINE.md для людей, logs/pipeline.json для агентов. |
| Q-012 | Делать ли обязательный heartbeat/live-room для агентов? | answered | Codex | Stefan, Claude, Mavis, Novax | `topics/agent-pipeline.md` | Принят D-012: вариант B — добровольный heartbeat; pipeline.py heartbeat пишет per-agent JSON, LIVE.md и logs/heartbeat.json. |
| Q-013 | Как согласовать спорные пункты onboarding/manual roadmap? | answered | codex | все | `topics/ai-os-bridge.md` | Закрыто через Котёл-синтез (см. streams/q013-divergences/divergence.md) |
| Q-014 | Цель проекта — юридический workbench (домен) или универсальный generic-инструмент? | answered | Claude | Stefan | `topics/opinion-synthesis-2026-06-21.md` | Stefan — универсальное ядро + домен как тематический портал/плагин (модель Википедии). См. D-016. |
| Q-015 | Когда Level 1 worktree должен быть обязательным, а не рекомендацией? | answered | codex | все | `topics/commit-policy-streams-2026-06-21.md` | Принят D-022 — вариант B; Level 1 worktree обязателен по триггерам: чужие source-файлы, stale index не от своей работы, hot files, явная параллельная работа или same-file коллизия. |
| Q-016 | Гарантия применения и актуальности инструкций (existence != applied) + поток знания вверх L4->L1 | answered | stefan | все | `topics/assurance-and-doc-merge-2026-06-22.md` | Утверждено котлом: S0 миграция выполнена (проставлен last_verified на D-001..D-023 и политиках). |
| Q-017 | Автоматизация слияния документации агентов — консенсус с cross-references + структурированные разногласия | answered | stefan | все | `topics/q017-docmerge-semantic-2026-06-23.md` | Утверждено котлом. Создана задача T-191 на реализацию семантического гибрида. |
<!-- GEN:questions END -->
