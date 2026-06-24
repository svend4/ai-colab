---
id: razbor-divergence-status-2026-06-24
type: topic
title: Lane B — статус 21 разногласия после churn-reconcile (что разрешено / открыто / в котёл)
gist: Из 21 разногласия ~9 разрешены этой сессией (мигрируют в консенсус), ~4 tracked/partial, ~8 остаются открытым design-фронтиром (typed-ссылки, две оси, decay, security, зрелость)
status: proposed
owner: stefan
date: 2026-06-24
level: L3
related: [razbor-divergence-2026-06-24, cauldron-two-lane-board-2026-06-24, navigation-vs-sharding-2026-06-24]
---

# 0. Визитка
> Lane B (divergence-detail) после **churn-reconcile**: многие разногласия из `razbor-divergence`
> разрешены работой этой сессии. Здесь — статус каждого: разрешено (evidence→консенсус) /
> tracked / открытый design / конфликт→котёл. Lane-B-workflow умер на компактации — собрано вручную
> с прямой проверкой кода/канона.

## 0.1. Счётчики (из 21)
- **Разрешено за сессию → мигрируют в консенсус:** 9
- **Tracked / частично:** 4
- **Открытый design-фронтир:** 7
- **Не-конфликт (позиционирование):** 1

---

# 1. РАЗРЕШЕНО за сессию (evidence) → мигрируют в lane A консенсус

| DIV | Было разногласие | Разрешено чем (проверено) |
|---|---|---|
| **DIV-01** | статус Q-017 (docmerge) | `questions/Q-017.md` = **answered**; `doc_consensus --semantic` + `--divergence-out` построены |
| **DIV-03** | статус orphan-L1 | `assurance coverage` = **orphan-L1: 0** (derive_reuse + порталы) |
| **DIV-04** | потолок файлов / шардинг | **`navigation-vs-sharding-2026-06-24`**: шардинг отклонён, навигация-метаданными (`folder_index`+`indexes/`) |
| **DIV-09** | indexes/ как явный слой | **построен** `indexes/{tasks,…}.md` + `tools/folder_index.py` |
| **DIV-10** | reconcile_state (dry-run/derived) | **построен** `cmd_fix` (94c3c35) |
| **DIV-12** | F-020 gate-poison | **построен** `friction.check_gate_poison` (67fa8b5) |
| **DIV-13** | derive_reuse / gate L2→L1 | **построен** `promote.derive_reuse` (6ede574); P12 verification-гейт (Codex) |
| **DIV-14** | svend4 / Q-009 / T-020 | **D-020 §4 accepted** (svend4 = generic intake) |
| **DIV-15** | D-014 execute-OFF | **D-014 accepted** (10-гейтовый preflight) |

→ Эти 9 — не «разногласия», а уже-сделанное. Снять с lane B, отметить в консенсусе.

# 2. TRACKED / частично (нужен один шаг)

- **DIV-02** top.py-wiring (S1/assurance в апексе) — top.py assurance-кнопка построена; остаточный doc-status конфликт → пометить shipped.
- **DIV-11** gateway async stdio WinError-5 — sync-acceptance зелёная; async env-зависим → **T-174** (трекер). Остаётся.
- **DIV-18** section-tree крупных файлов в index.json — `heading_check.py` детектит структуру; полный section-tree-в-index — открыт (build).
- **DIV-19** 5 фунд-Q Stefan не заведены как Q-карточки — **actionable**: завести Q-карточки (архитектура/визитка/статистика/нумерация/портабельность). Простой build.

# 3. ОТКРЫТЫЙ design-фронтир (2-й голос / дизайн) — реальный остаток

| DIV | Суть | 2-й голос / маршрут |
|---|---|---|
| ~~DIV-07~~ | typed/directed ссылка как first-class объект | ✅ **ПОСТРОЕНО** `tools/edges.py` — 6 типов рёбер из front-matter, граф запрашиваем. `typed-link-graph-2026-06-24`. |
| ~~DIV-08~~ | две ортогональные оси физически (дерево↔граф) | ✅ **ПОСТРОЕНО** `edges.py neighbors` — обе оси (containment ⟂ typed-edges) над одними атомами, хранилище не тронуто. |
| ~~DIV-06~~ | decay/температура узлов (cold→архив) | ✅ **ПОСТРОЕНО** `tools/decay.py` — третья ось (время): git-возраст→hot/warm/cold + stale-активные. В блоке improve. `time-axis-decay-2026-06-24`. |
| **DIV-05** | identity/auth/enforced-права + prompt-injection | Security-design. Codex **T-219 «Redaction»** уже касается. Координировать. |
| **DIV-17** | многоуровневая автономия + риск-рубрикатор (серьёзность×вероятность) | `risk_gate.py` тиринг — частично. Расширить рубрикатор. Med. |
| **DIV-20** | наивный front-matter парсер (_canon split(':',1), не YAML) | **Реальный код-долг**: ломается на сложном YAML. Fix `_canon` (core, осторожно) или принять ограничение. |
| **DIV-21** | зрелость TRL по осям / промилле | Идея Stefan (% выполнения). Build: maturity-скоринг (как §6 реестра вопросов). Med. |

# 4. Не-конфликт
- **DIV-16** Codex 8-слойная платформа / этапы A-F / queue→agent_queue — позиционирование Codex, не противоречие. Информационно.

---

# 5. Итог двухтрекового цикла
- **Lane A (консенсус→построено):** ✅ структурно-навигационный консенсус закрыт (5 чекеров + indexes + блоки).
- **Lane B (разногласия):** **9/21 разрешены сессией**, 4 tracked, **DIV-19 + DIV-07/08 построены** этой сессией → открытый design сократился до 5 (DIV-05/06/17/20/21), + 1 позиционирование.
- **Реальный остаток для работы:** DIV-05 security · DIV-06 decay · DIV-17 автономия-рубрикатор · DIV-20 YAML-парсер (код-долг) · DIV-21 зрелость-промилле. Крупные концептуальные слои (typed-ссылки/две-оси) — **закрыты** через `edges.py`.

**Вывод:** разногласий «горит» меньше, чем казалось — построение по консенсусу попутно разрешило ~половину. Остаток — осознанный design-фронтир, не хаос.
