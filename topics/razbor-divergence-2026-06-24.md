---
id: razbor-divergence-2026-06-24
status: proposed
layer: L3
owner: semantic-consensus-synthesizer
last_verified: 2026-06-24
consensus_ref: topics/razbor-consensus-2026-06-24.md
method: single-doc-only OR cross-doc-conflict (по D-017 sub-points)
---

# Разногласия — для детализации, обоснования и доп-вопросов (D-017)

Пункты, встречающиеся ТОЛЬКО в одном доке (standalone-инсайт, пока не подтверждён вторым
голосом) ИЛИ КОНФЛИКТУЮЩИЕ между доками. Формат каждого: claim / какой агент-док предложил /
почему standalone-или-конфликт / что разрешает (детализация/обоснование/вопрос на котёл).

## A. КОНФЛИКТЫ ФАКТОВ (доки противоречат друг другу — нужен котёл)

### DIV-01. Статус Q-017 (семантический docmerge)
- **build-plans-overview** (§37-75): Q-017 — opt-in --semantic, подробный buildable-дизайн (ещё не построен).
- **architecture-fundamentals** (§6.4.2): Q-017 ~40%, «решение принято, движок не построен».
- **perspective-backlog** (§19-24): «Q-017 semantic doc-merge закрыт в T-176».
- **Конфликт:** закрыт vs недозакрыт vs только-дизайн. **Разрешает:** сверить T-176 факт реализации против build-plans-дизайна; вероятно снимки разной даты (24 vs 23 июня).

### DIV-02. Статус top.py-wiring (S1 / assurance в апексе)
- **session-state** (§76-77): SHIPPED 2026-06-23 (91cd162), mode done.
- **build-plans-overview** (§159-177, §246): S1 всё ещё перечислен как worktree-buildable.
- **Конфликт прямой**, отмечен самим session-state как divergence. **Разрешает:** канонизировать факт по git-логу; обновить build-plans до shipped.

### DIV-03. Статус orphan-L1
- **session-state** (§14): assurance репортит orphan-L1-12 (ATTENTION).
- **perspective-backlog** (§19-24): «orphan-L1 coverage закрыт T-173, orphan-L1: 0».
- **Конфликт:** 12 vs 0. **Разрешает:** перезапустить assurance.py на HEAD; решить какая цифра каноническая.

### DIV-04. Потолок файловой модели / закрытость темы scaling
- **scaling-design** (§82-84): файловая модель отлична до десятков агентов, выше — БД+очередь+API.
- **scaling-design** (§5-6): «тема scaling-design закрыта, roadmap T-008..T-016 реализован полностью».
- **Само-конфликт внутри одного дока:** закрыто, но честный потолок остаётся открытым. **Разрешает:** различить «MVP-roadmap закрыт» от «масштаб >десятков агентов — новая тема».

## B. STANDALONE — только в одном доке (нужен второй голос/обоснование)

### DIV-05. Identity / auth / enforced-права + prompt-injection риск
Только **scaling-design** §51-53/§174-185 (модель доверия с ролями human-owner/maintainer/worker/
reviewer/script/external). Нигде больше не поднято. **Разрешает:** отдельный security-вопрос на котёл — нужна ли enforcement-модель на текущем масштабе или это over-engineering.

### DIV-06. Decay/температура узлов (cold→архив)
Только **architecture-fundamentals** §8.1.8. **Разрешает:** обосновать критерий «N времени без обращений» и кто измеряет обращения.

### DIV-07. typed/directed ссылка как first-class объект (from/to/refines|cites|contradicts|supersedes)
Только **architecture-fundamentals** §8.1.2 (Xanadu/RDF), частично перекликается с base↛apex
(new-problems), но как ОБЩАЯ модель графа — standalone. **Разрешает:** опциональный слой над
детерминированным ядром (D-010, без RAG до спроса) — детализировать схему ребра.

### DIV-08. Две ортогональные оси физически (containment vs typed-edges, дерево vs граф)
Только **architecture-fundamentals** §8.1.1 (Ранганатан PMEST). **Разрешает:** обосновать, что
смешение дерева и графа — корневая причина хаоса; как разделить физически.

### DIV-09. indexes/ как явный слой (files/folders/commands/questions/open-loops/portals/stale.json)
Только **optimal-IA** §06.03. Конфликтует с open-вопросом §13.02 «нужна ли отдельная indexes/».
**Разрешает:** решить генерировать ли набор индексов или один index.json.

### DIV-10. reconcile_state.py (dry-run default, DERIVED vs PRIMARY дрейф, только 4 производных)
Только **fleet-designs** §23-35. **Разрешает:** детализировать список авто-чинимых кодов,
CRLF-дрейф на Windows, default-apply footgun.

### DIV-11. Gateway: async stdio WinError 5 → синхронная transport-independent приёмка
Только **new-problems** §176-202 (+perspective-backlog §45-47 как blocked-кандидат). **Разрешает:**
канонизировать sync tools/call как environment-portable гейт; обосновать почему async stdio
не durable.

### DIV-12. F-020 gate-poison детектор (cohort→friction висячий cross-link)
Только **new-problems** §28-100 (+session-state/perspective упоминают как shipped 67fa8b5).
**Разрешает:** различить read-only детектор (в scope) от структурного per-agent scoping
validate.py (требует D-017/D-018, owned интегратором).

### DIV-13. derive_reuse / _gate_L2_L1 distinct-portal count / section_coverage по files: not candidates:
Только **build-plans-overview** §95-119. **Разрешает:** детализировать механику scan-provenance
штампа reused_in и сужение manifest files: 10→8.

### DIV-14. svend4 / Q-009 / T-020 внешний код blocked
Только **perspective-backlog** §45-47. **Разрешает:** решение человека — ждать source или закрыть как generic.

### DIV-15. D-014 execute-OFF до явного решения человека
Только **perspective-backlog** §45 (+optimal-IA §13.01 «execute выключен до полного gate» — частично
второй голос). **Разрешает:** явное human-решение, не запускать execute-build до acceptance.

### DIV-16. Codex-специфика: 8-слойная file-native platform / этапы A-F / queue.py claim-complete-fail
Только **scaling-design** Codex-секции §189-300. **Разрешает:** соотнести Codex-roadmap A-F с
текущим состоянием (часть уже shipped) — что ещё актуально.

### DIV-17. Многоуровневая автономия с риск-рубрикатором (серьёзность × вероятность)
Только **scaling-design** §59-61. Перекликается с C-17, но риск-матрица как механизм — standalone.
**Разрешает:** обосновать рубрикатор vs текущий человек-гейт D-006.

### DIV-18. Section-tree крупных файлов в index.json (section-id/anchor/level/line)
Только **architecture-fundamentals** §4.1.7 (близко к C-11, но как машинный lookup внутри файла —
отдельная деталь). **Разрешает:** детализировать генератор section-index.

### DIV-19. 5 фундаментальных Q Stefan не заведены как Q-карточки (слепое пятно реестра)
Только **architecture-fundamentals** §6.5. **Разрешает:** завести мета-Q-карточки
(ядро/визитка/статистика/нумерация/портабельность).

### DIV-20. Наивный парсер front-matter (_canon.py split(':',1), не настоящий YAML)
Только **architecture-fundamentals** §7.1.4. **Разрешает:** обосновать переход на YAML-парсер vs
риск хрупкости на многострочных значениях.

### DIV-21. Зрелость TRL по осям / стадии зрелости в промилле
Метрики разными шкалами: **scaling-design** §19-27 (TRL 7-8 малый / 3-4 большой) vs
**optimal-IA** §01.02 (концепт 760 / навигация 480) vs **architecture-fundamentals** §6 (Q-016 55%,
Q-017 40%). Не конфликт, но НЕ сведены в одну шкалу. **Разрешает:** выбрать единую метрику зрелости
для board.
