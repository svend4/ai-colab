---
id: razbor-consensus-2026-06-24
type: topic
title: Разбор полётов — КОНСЕНСУС (общие пункты C-01..C-18 из мульти-документного синтеза)
status: proposed
level: L3
owner: semantic-consensus-synthesizer
last_verified: 2026-06-24
source_docs:
  - topics/architecture-fundamentals-2026-06-24.md
  - topics/optimal-information-architecture-2026-06-24.md
  - topics/build-plans-overview-2026-06-23.md
  - topics/perspective-backlog-2026-06-23.md
  - topics/session-state-2026-06-23.md
  - topics/scaling-design.md
  - topics/fleet-designs-2026-06-23.md
  - topics/new-problems-2026-06-23.md
  - topics/governance-proposals-2026-06-23.md
  - topics/orchestration-architecture-2026-06-23.md
divergence_ref: topics/razbor-divergence-2026-06-24.md
method: semantic merge (по смыслу, не лексически), 3 слоя по D-017
---

# Разбор полётов — консенсус группы (семантический merge)

Это коллективный синтез 205 утверждений из 10 вариант-документов 6 рабочих групп.
Группировка СЕМАНТИЧЕСКАЯ: одна мысль = один merged-пункт, даже если доки выразили
её разными словами или с разным акцентом. Лексический Jaccard здесь бессилен (D-023:
307 units / 0 consensus при thr 0.3-0.4 против ≥7 реальных согласий) — поэтому слияние
сделано смысловым проходом.

## §0. Счётчики

- **docs (источники):** 10 вариант-документов (6 групп: architecture-fundamentals×2,
  планы-развития×4, scaling-design×3, governance+оркестрация×2, new-problems включён
  в scaling-группу).
- **claims (всего утверждений):** 205.
- **по kind:** principle 58, rule 52, proposal 44, critique 28, metric 14, answer 6, question 3.
- **questions (явные открытые вопросы):** 3 (целевой масштаб флота; пакет открытых
  разногласий streams/architecture-core; блокированные decision-кандидаты D-014/svend4).
- **proposals (предложения к постройке):** 44.
- **answers (зафиксированный консенсус/закрытие):** 6.
- **mainline-кандидатов из §1 (где ≥2 дока согласны):** 18 merged-узлов.
- **near-consensus из §2 («золотой голос»):** 9 узлов.
- **вынесено в divergence (§3):** 21 кластер.

---

## §1. ОБЩЕЕ — merged-кандидаты в mainline (смысл подтверждён ≥2 доками)

Каждый пункт — ОДИН смысл, собранный из нескольких доков. В скобках — кто подтвердил.

### C-01. Front-matter = единственный источник правды; агрегаты генерируются, не правятся руками
Атомарный файл несёт машинную шапку (id/status/layer/owner), а TASKS.md / index.json /
STATUS.md / board.md / PIPELINE.md — детерминированные производные. Ручная правка агрегата
запрещена; индекс пересобирается генератором и проверяется hook/CI.
(architecture-fundamentals §1.1.2/§2.1.5; optimal-IA §02.01; scaling-design Codex
§128-153 + §325 + §74; session-state «generated indexes не коммитить слепо D-023».)

### C-02. Один файл = одна единица знания — снимает write-write конфликты
Задача/решение/вопрос/сообщение живут как отдельный атомарный Markdown (D-002).
Это базовое свойство параллелизма: шардинг записи уже заложен.
(architecture-fundamentals §1.1.1; scaling-design §31/§32; governance D-002.)

### C-03. Канон принуждается машинно, а не доверием к дисциплине агентов
validate.py ERROR валит коммит, pre-commit hook, generate.py --check ловит дрейф.
Повторяемое правило надо превращать в активный контракт (validator/guard/gate),
а не оставлять пассивным текстом.
(architecture-fundamentals §1.1.4-5; optimal-IA §02.01/§16; scaling-design CI-as-gate §75.)

### C-04. Шардинг горячих реестров — приоритет №1 масштабирования
TASKS/QUESTIONS/DECISIONS/STATUS/board — точка сериализации записи; разнести по файлу
на сущность (T-XXX.md/D-XXX.md/Q-XXX.md), агрегаты сделать генерируемыми. Шардить по
диапазонам immutable-ID, а не по семантике (иммутабельный ID не двигает файл при смене темы).
(architecture-fundamentals §3.2.2; scaling-design §47-49/§73/§308-310 «полный консенсус
Claude+Codex»; optimal-IA подразумевает через generated split.)

### C-05. Слоистая пирамида L1 core → L2 portals → L3 collab/история → L4 sandbox
Ось чистоты/доверия; из L4 ничего не поднимается выше автоматически; нужна явная
promotion-механика с тестом на границе (medallion bronze/silver/gold).
(architecture-fundamentals §1.1.7/§8.1.7; optimal-IA §00/§05.03; модель Википедии D-016.)

### C-06. Портал — тематический plugin (universal core + manifest + corpus + workflows + local checks), не папка с текстами
Порталы строятся на универсальные ТЕМЫ (canon/safety/drivers), а не на разные ДАННЫЕ;
без workflows и машинного l1_basis это просто папка документов. tools/ кластеризуются
в ~6 порталов по реальным импортам.
(architecture-fundamentals §5.1.1-3; optimal-IA §02.04/§05.01; fleet-designs bridge-knowledge
/repo-inventory как доказательство обобщения L2.)

### C-07. Каждый значимый файл несёт визитку card→middle→base; нет файла без карточки
Единый словарь полей, два носителя (YAML для md, docstring/sidecar .meta.md для прочего).
base-уровень = ССЫЛКИ (detail_ref/spec/tests/decisions), не дублирование детали
(дублирование = гарантированный дрейф).
(architecture-fundamentals §2.1.1-2/§2.1.8; optimal-IA §03.02/§06.01.)

### C-08. Знание существует в ДВУХ формах: короткая машинная + расширенная человеческая
Машинная (ID/статус/слой/связи/команды) и человеческая (объяснение/обоснование/история).
Только одна форма — ошибка. Три глубины чтения (semantic elevator): 30 сек карточка →
5 мин карта → 30 мин evidence.
(optimal-IA §06.01/§06.02; architecture-fundamentals §3.2.9 машинный vs человеческий оптимум.)

### C-09. Машинный и человеческий оптимум организации РАЗНЫЕ
Проблема не в ФС (компьютер читает тысячи файлов), а в КОГНИТИВНОЙ навигации.
Физическая раскладка под машину (плоско+шарды), виды под человека (board.md,
фасетные by-status/by-owner, README/index у больших папок).
(architecture-fundamentals §3.2.9; optimal-IA §08.02; библиотечная shelfmark vs каталог.)

### C-10. Health-gate каталога с порогами (структура как код)
files_per_dir>200 FAIL / >100 WARN, file>50KB WARN, index.json>200KB WARN, root_dirs>15 WARN;
правило больших папок >20→README, >50→подпапки/generated catalog, >100→machine-facing.
(architecture-fundamentals §3.2.10; optimal-IA §08.01/§08.03 — эвристики, не закон.)

### C-11. Длинный файл — дерево с head→body→tail и абсолютной нумерацией для крупных доков
Трёхфазный закон (метаданные/ToC → тело → хвост, BLUF/перевёрнутая пирамида), dotted-decimal
нумерация для доков выше порога (~300 строк / status architecture|policy), section card
(claim/status/evidence/next) извлекаема без чтения всего текста, нужен heading-lint.
(architecture-fundamentals §4.1.1/§4.1.3; optimal-IA §07.01/§07.02.)

### C-12. Задача закрывается не «done», а done + evidence + tests + links
Если evidence восстанавливается задним числом — pipeline недостаточно строг. Proof ladder:
idea→note→task→proposed doc→evidence→test→accepted; пропуск ступени assurance.py показывает gap.
(optimal-IA §02.05/§12/§14.02; architecture-fundamentals §6.4.1 — Q-016 ровно об этом разрыве.)

### C-13. Узкое место — не число агентов, а полоса коммита/обработки одного оркестратора
Производство дёшево и параллельно; интеграция в одну git-историю серийна, но дёшева.
Реальный предел — processing band top-слоя, а не технический фан-аут.
(optimal-IA §11.01; session-state §126/§132-133; orchestration-architecture §14/§88/§174.)

### C-14. Конвейер — это STREAM, не BATCH
Anti-pattern «один батч из N» (launch→process→empty→stall) тратит wall-clock. Пополнять
ЗАРАНЕЕ (запускать следующий узел в момент начала обработки текущего), never drain to zero,
target N≈2-4, граница потока = COMMIT-bandwidth.
(session-state §102-108; orchestration-architecture §47/§50-52.)

### C-15. Нужен внешний read-mostly надзиратель conveyor.py — дисциплины мало
Оркестратор — один контекст, может уйти в foreground-стройку и осушить конвейер. Watchdog
сигналит REFILL/PROCESS/IDLE с exit-кодом из hook/CI/wakeup, но САМ не запускает workflows
(паттерн «friction.py сигналит, cohort.py исполняет»).
(session-state §112/§115/§122; orchestration-architecture §56/§68-79.)

### C-16. Серийная интеграция защищена и удешевлена: cohort guard → ship | worktree+merge_gate + TTL-lock
Когортный коммит (selective-add, НЕ git add -A) минимизирует index.lock-churn; commit_lock.py —
атомарный O_EXCL захват с lease_epoch и stale-takeover. Worktree для конкурентных build,
shared tree только для мелких правок.
(session-state §145; orchestration-architecture §44-45; optimal-IA §03.05 worktree-стандарт;
scaling-design claim-с-TTL+fencing §76.)

### C-17. Никто не утверждается соло — ратификация через котёл (D-017 fork-synthesize + D-018), человек промоутит спорное (D-006)
Все доки держат status:proposed; перевод в accepted — коллективным синтезом, не одним агентом;
двойная перепроверка (техническая ≥2 агента по D-015 + гуманитарная). permissions.py =
signal-not-block.
(build-plans-overview §22-26; session-state §149; orchestration-architecture §166/§176/§178;
governance §12/§30; new-problems §94-96.)

### C-18. Новые data-порталы НЕ обнуляют orphan-L1 механически — это честное наблюдение, а не баг
12 orphans — kernel coordination primitives (commit_lock/merge_gate), которые data-корпус
законно не цитирует. Ретайрит их split files:/candidates: + doc/manifest-cross-ref, а не
принуждение порталов цитировать примитивы. Принцип «честная нерешённость»: показывать
orphan-L1 открыто, а не фабриковать reused_in.
(build-plans-overview §92-97/§142-146; fleet-designs §54-59.)

---

## §2. СЕРЕДИНА — near-consensus «золотой голос» (та же мысль разными словами/акцентом)

Здесь смысл совпадает, но формулировки/фокус расходятся — объединённый «золотой голос»
ещё не структурирован как один mainline-пункт, требует доводки на котле.

### M-01. Ядро = маленький скучный control-plane, а не склад функций
«8 плоскостей» (optimal-IA §04.01-02) vs «6 порталов по импортам» (architecture-fundamentals
§5.1.3) vs «8 слоёв file-native platform» (scaling-design Codex §189-198) — одна мысль о
тонком универсальном ядре, разная декомпозиция. Золотой голос: ядро знает только общие
операции (канон/индексы/выдача задач/claims/ownership/worktree/evidence/gate), домен — через портал.

### M-02. Один верхний фасад вместо россыпи команд
top.py (start/status/next/guard/verify/synthesize/friction/portal) у optimal-IA §03.03 =
«командные группы как кнопки» §11.02 = единая точка делегирования. Золотой голос: сначала
CLI-контракт top.py, позже GUI/MCP/web.

### M-03. L1-критерий = переносимость без истории полилога
«взять файл в пустой проект, прочитать карточку, запустить тесты» (optimal-IA §02.03) =
«L1 пока контракт, а не экспортируемый продукт» (architecture-fundamentals §7.1.3). Один
критерий зрелости L1, выраженный позитивно и как критика.

### M-04. Семантический docmerge (Q-017) — opt-in слой над лексическим дефолтом, без внешнего ML
build-plans-overview §37-66 (--semantic над doc_consensus.py, high-thr pre-cluster, residue+reps,
GROUPS/DIVERGENCES JSON) = architecture-fundamentals §6.4.2 (Q-017 ~40%, движок не построен) =
perspective-backlog §19-24 (Q-017 закрыт в T-176). Расхождение по статусу закрытия (см. §3),
но единый дизайн: stdlib+subprocess-агент, лексика остаётся no-cost дефолтом, regression-fixture
«одна идея — разные слова».

### M-05. БРИГАДА {N producers + 1 integrator} = самодостаточная ячейка produce→integrate
orchestration-architecture §100-159 (бригада выдаёт durable-триплет doc_path/doc_content/commit_msg,
обе фазы параллелятся, не делает только git-запись) = session-state §132-133 (COMPOSITION
параллельна / INTEGRATION серийна). Одна модель, разный словарь (бригада/cell/pod).

### M-06. last_verified / source_last_verified — единая freshness-конвенция со SLA
governance §35-47 (ISO last_verified на accepted/policy, штамп СЕГОДНЯ never back-date, SLA
90д governance / 30д drivers, лестница warn→block) = architecture-fundamentals §6 (нужен второй
флаг зрелости decided/implemented/verified). Одна идея «у канона есть срок годности», разный
охват (решения vs все Q-карточки).

### M-07. Расхождение реестров статусов/SLA-дефолтов — чинить единым enum/конфигом
architecture-fundamentals §7.1.1 (validate.py vs generate.py STATUS_RANK) = governance §44-45
(assurance.py:361 --max-age=180 vs driver-safety-policy.md:14 =30). Один класс бага: дублированные
реестры констант без единого источника.

### M-08. Бэклог — живой источник будущих заданий, а не архив диагнозов
perspective-backlog §12-13/§72-73 (refresh: closed→shipped, blocked→decision, next→«Готовы к запуску»)
= session-state §107 (backlog-scanner, out-degree максимален, сортируется первым) =
orchestration-architecture §47/§79 (самокормление, next из «Готовы к запуску»). Одна функция,
разный фокус (гигиена vs топология vs дозалив).

### M-09. Связь должна быть first-class машинным объектом / навигация = проекция графа
architecture-fundamentals §8.1.1-2/§8.1.5 (typed-edges, две ортогональные оси containment vs граф,
board как проекция) = new-problems §113-156 (base↛apex: три namespace без общего ключа, surfaces-ключ
+ tracer + key-join). Одна корневая мысль: ручная навигация при росте = тихая ложь; нужен общий
ключ/ребро для машинного обхода.

---

## §3. Указатель на разногласия

Полный разбор пунктов, встречающихся лишь в одном доке ИЛИ конфликтующих между доками,
вынесен в **topics/razbor-divergence-2026-06-24.md** (21 кластер). Самые важные:

- **Статус Q-017 / top.py-wiring / orphan-L1:** session-state и perspective-backlog говорят
  SHIPPED/closed, build-plans-overview и architecture-fundamentals — ещё buildable/недозакрыто
  (снимки разошлись по времени — прямой конфликт фактов).
- **Физическая судьба L3/collab:** мигрировать tasks/questions/decisions в collab/ или оставить
  логическим слоем (architecture-fundamentals §7.1.2 vs optimal-IA §13.02 open).
- **Потолок файловой модели:** «отлично до десятков агентов, дальше БД+очередь+API»
  (scaling-design §82-84) vs «scaling-design тема закрыта полностью» (§5-6) — конфликт.
- **Отдельная indexes/, ручная vs генерируемая нумерация, portal-local tools, file-cards для всех
  vs только L1/L2/policy** — пакет open-вопросов streams/architecture-core (optimal-IA §13.02).
- **Идентичность/аутентификация/enforced-права** — только scaling-design §51-53; нигде не
  подтверждено вторым доком.

---

## §4. Разбор полётов — что группа вывела коллективно

1. **Главный сдвиг — не «+10 документов», а превращение правил в активные контракты.**
   Сквозная мысль ≥4 групп (optimal-IA §16, architecture-fundamentals §2.1, scaling-design,
   governance): следующий скачок зрелости — file-cards + indexes + top-команды + gates, делающие
   каталог самоописывающимся и самопроверяющимся. Навигация — самая слабая ось (концепция ~760,
   навигация ~480).

2. **Параллелизм решён на входе, но не на выходе.** Группа единодушна: запись шардирована (D-002),
   производство масштабируется свободно — а узкое место переехало в полосу обработки/коммита одного
   оркестратора. Отсюда вся надстройка: STREAM-конвейер, watchdog conveyor.py, бригада
   {N+1}, когортный коммит под TTL-локом. Это единая дуга от architecture к orchestration.

3. **Честность вместо фабрикации — новый осознанный принцип.** Сразу две группы (build-plans,
   fleet-designs) независимо пришли к «честной нерешённости»: показывать orphan-L1 и битые
   указатели открыто, а не подделывать reused_in/самодекларацию. Это методологический сдвиг от
   self-declaration к scan-derived доказательству.

4. **Разрыв «существование ≠ применение» — главный незакрытый класс.** Q-016 (pipeline done не
   зовёт check_report), F-020 (cohort указывает на несуществующий recipe), base↛apex (три namespace
   без ключа), reused_in (ноль писателей поля) — все об одном: артефакт объявлен, но связь в живом
   репозитории не держится. Группа сформулировала это как осознанный фокус следующей волны.

5. **Управляемая автономия с человеком на спорном.** Консенсус по границе: бригада/агент выдаёт
   proposed, accepted даёт котёл (D-017+D-018), человек промоутит governance (D-006); auto-merge
   только для low-risk технического, проходящего validator/tests. Никто не оспорил этот контур.

6. **Главный нерешённый мета-вопрос — целевой масштаб.** scaling-design прямо ставит: от ответа
   «сколько агентов/людей/задач одновременно» зависит, сколько из предложений вообще нужно строить
   (риск over-engineering). Это единственный вопрос, блокирующий приоритизацию остального.
