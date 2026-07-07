# Решения

Полный текст каждого решения — в `decisions/D-XXX.md`. Ниже — **генерируемый индекс** (источник правды — файлы `decisions/*.md`; таблицу вручную не редактировать).

## Индекс решений

<!-- GEN:decisions START — генерируется tools/generate.py из decisions/*.md, не править вручную -->
| ID | Решение | Статус | Дата | Файл |
|---|---|---|---|---|
| D-001 | Markdown как основной формат | accepted | 2026-06-19 | `decisions/D-001.md` |
| D-002 | Для больших тем — отдельный файл на сообщение | accepted | 2026-06-19 | `decisions/D-002.md` |
| D-003 | Правки служебных файлов сопровождаются обоснованием | accepted | 2026-06-19 | `decisions/D-003.md` |
| D-004 | Метод принятия решений по открытым вопросам | accepted | 2026-06-19 | `decisions/D-004.md` |
| D-005 | Имена новых файлов в ASCII | accepted | 2026-06-19 | `decisions/D-005.md` |
| D-006 | Сборщик итогов в больших темах — гибрид | accepted | 2026-06-19 | `decisions/D-006.md` |
| D-007 | Постепенная миграция русских имён к ASCII | accepted | 2026-06-19 | `decisions/D-007.md` |
| D-008 | Границы D-003 — что считать значимой правкой | accepted | 2026-06-19 | `decisions/D-008.md` |
| D-009 | Онбординг агентов — A сейчас, эволюция к C | accepted | 2026-06-19 | `decisions/D-009.md` |
| D-010 | AI-OS Bridge стартует с L1-каталога драйверов и одного L2 PoC | accepted | 2026-06-20 | `decisions/D-010.md` |
| D-011 | Динамический конвейер агентов поверх tasks/queue/index | accepted | 2026-06-20 | `decisions/D-011.md` |
| D-012 | Heartbeat агентов — добровольный live-слой | accepted | 2026-06-20 | `decisions/D-012.md` |
| D-013 | Driver schema v1 — вариант B как proposed | accepted | 2026-06-20 | `decisions/D-013.md` |
| D-014 | Execute OFF по умолчанию — 10-гейтовый preflight перед любым mode:execute | accepted | 2026-06-20 | `decisions/D-014.md` |
| D-015 | Гейт статуса драйверов — многоагентная верификация вместо обязательного human-confirm | accepted | 2026-06-21 | `decisions/D-015.md` |
| D-016 | Универсальное ядро + тематические порталы (домен как плагин, не в коде ядра) | accepted | 2026-06-21 | `decisions/D-016.md` |
| D-017 | Fork-and-synthesize — параллельные варианты вместо чистого dedup для содержательных работ | accepted | 2026-06-21 | `decisions/D-017.md` |
| D-018 | Коллективное принятие решений через котёл — обоснование + двойная перепроверка | accepted | 2026-06-21 | `decisions/D-018.md` |
| D-019 | Commit streams policy — Level 0 now, worktree-streams as proposed Level 1 | superseded | 2026-06-21 | `decisions/D-019.md` |
| D-020 | T-137 consensus proposal — thin automation, streams, sandbox intake, promotion gate | accepted | 2026-06-21 | `decisions/D-020.md` |
| D-021 | Ратификация котёл-пакета — Уровень-1 принят, core-export/apex/D3 по рекомендациям, svend4 BLOCKED | accepted | 2026-06-21 | `decisions/D-021.md` |
| D-022 | Детальная политика параллельной работы — триггеры Level-1, STALE-индекс, волатильные файлы, same-file | accepted | 2026-06-22 | `decisions/D-022.md` |
| D-023 | Ответственность за коммит генерируемых индексов — ownership-aware (commit-your-own / integrator-for-foreign) | accepted | 2026-06-23 | `decisions/D-023.md` |
| D-024 | Формат синтеза с выносом разногласий (Structured Divergences) | accepted | 2026-06-23 | `decisions/D-024.md` |
| D-025 | Стратегии обхода WinError 5 (Async MCP stdio) | accepted |  | `decisions/D-025.md` |
| D-026 | Безопасность массовой информации — запрет несанкционированного bulk-стирания + обязательная страховка | accepted | 2026-06-24 | `decisions/D-026.md` |
| D-027 | Матрица полномочий для людей, AI-агентов, observer/integrator ролей и скриптов | accepted | 2026-06-25 | `decisions/D-027.md` |
| D-028 | Independent-first variants — содержательные дубли раскрываются до синтеза | accepted | 2026-06-25 | `decisions/D-028.md` |
| D-029 | Consensus-by-meaning — merge-инварианты сверки вариантов (по смыслу, не по счёту) | accepted | 2026-07-05 | `decisions/D-029.md` |
| D-030 | Independent-consensus — валидированное ядро после полного адверсариального прогона | accepted | 2026-06-25 | `decisions/D-030.md` |
| D-031 | commit_queue как стандартный путь коммита внутри Уровня 0 (очередь + обратная связь + предсохранение) | accepted | 2026-06-26 | `decisions/D-031.md` |
| D-032 | gap_scan.py + гейт тихого дрейфа деривата — исполняемая рука defect-class-formula | accepted | 2026-06-26 | `decisions/D-032.md` |
| D-033 | "Доработка D-033: уточнённая дисциплина автономных действий + C5 commit_queue + B2" | proposed | 2026-06-26 | `decisions/D-033.md` |
| D-034 | Отдельные пороги dir_health для архивных каталогов (queues/done — FAIL 500 / WARN 400) | accepted | 2026-07-06 | `decisions/D-034.md` |
| D-035 | Батчевая ратификация — «котёл-день» как норма (вопросы копятся, разбираются батчем раз в 3-5 дней) | accepted | 2026-07-06 | `decisions/D-035.md` |
| D-036 | Оркестраторный цикл принят как стандарт работы главных агентов (двухслойная модель + пакеты + повестка + эстафета) | accepted | 2026-07-06 | `decisions/D-036.md` |
| D-037 | Мягкая заморозка мета-развития v2 — новые tools/*.py только из friction-боли или явной потребности человека (advisory) | accepted | 2026-07-06 | `decisions/D-037.md` |
| D-038 | Верификация драйверов по риску — обычные драйверы 2 прохода (можно одна модель), execute/high-risk требуют разные модели/агенты | accepted | 2026-07-06 | `decisions/D-038.md` |
| D-039 | Обязательная worktree-изоляция при N≥3 + потолок одновременности (Гейты A/B) | accepted | 2026-07-07 | `decisions/D-039.md` |
<!-- GEN:decisions END -->
