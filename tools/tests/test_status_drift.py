#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
# ==========================================
# [FILE ID CARD]
# ID: tools.tests.test_status_drift
# TYPE: active-script
# DOMAIN: core
# DEPTH_LEVEL: 1
# SUMMARY: Тест status_drift.py — детектор рассинхрона ручного STATUS.md с фактами канона (C17).
# ==========================================
"""
"""Тест status_drift.py (C17): сверка ручных утверждений STATUS.md с машинной реальностью.

Двухступенчатый канон (conftest / test_all.py): файл СОБИРАЕТСЯ pytest (module-level test_*),
и запускается как самозапускающийся скрипт (run() + __main__) для tools/test_all.py.

Гермётичен: строит ИЗОЛИРОВАННЫЙ temp-репо (tempfile.mkdtemp) с fixture STATUS.md, decisions/D-*.md
и tasks/T-*.md, мутирует ROOT модуля на temp-репо, утверждает на ТОЧНЫЕ находки, восстанавливает ROOT.
"""
# --- бутстрап путей (C14): тест в tools/tests/, инструмент — в tools/. Вставка ДО локальных импортов.
import os as _os
import sys as _sys
_TOOLS_DIR = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
if _TOOLS_DIR not in _sys.path:
    _sys.path.insert(0, _TOOLS_DIR)
# --- конец бутстрапа ---

import os
import sys
import tempfile
import shutil

HERE = _TOOLS_DIR  # tools/
sys.path.insert(0, HERE)
from _ioutil import configure_output  # UTF-8 stdout на Windows
configure_output()
import status_drift as sd


def _w(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def _decision(root, did, status):
    _w(os.path.join(root, "decisions", "%s.md" % did),
       "---\nid: %s\ntype: decision\nstatus: %s\n---\n\n# %s\n" % (did, status, did))


def _task(root, tid, status):
    _w(os.path.join(root, "tasks", "%s.md" % tid),
       "---\nid: %s\ntype: task\nstatus: %s\n---\n\n# %s\n" % (tid, status, tid))


def build_fixture(root):
    """Fixture-репо, воспроизводящий C17: STATUS.md с ручными утверждениями + канон-факты.

    Канон: 2 решения (D-024 accepted, D-033 proposed → нератифицировано ровно 1);
    задачи T-100 (done) и T-200 (open). index.json объявляет счётчики (3 задач и т.п.).
    STATUS.md ручной текст УМЫШЛЕННО расходится: строка «7 нератифицированных: D-024, D-033»
    (реально 1), «Задач: 5» в фокусе (реально 3), «текущий фокус … T-100» (задача done),
    плюс GEN-блок с ВЕРНЫМ счётчиком (не должен флажиться) и историческая строка «отстали на
    99 задач» (delta-повествование — не должно флажиться).
    """
    # решения: 1 accepted, 1 proposed → нератифицированных ровно 1
    _decision(root, "D-024", "accepted")
    _decision(root, "D-033", "proposed")
    # задачи
    _task(root, "T-100", "done")
    _task(root, "T-200", "open")
    # index.json (авторитетный источник счётчиков)
    _w(os.path.join(root, "index.json"),
       '{"tasks":[1,2,3],"decisions":[1,2],"questions":[1,2,3,4],"topics":[1,2],"drivers":[1]}')
    # STATUS.md — генерируемо-ручной гибрид
    _w(os.path.join(root, "STATUS.md"),
       "# Статус\n"
       "\n"
       "## Текущий фокус\n"
       "\n"
       "<!-- GEN:counters START -->\n"
       "Задач: 3 · решений: 2 (верный GEN-счётчик, не флажить).\n"
       "<!-- GEN:counters END -->\n"
       "\n"
       "- Всего в работе 5 задач сейчас.\n"                       # (a) 5 != 3 → находка
       "- разбор очереди: 7 нератифицированных: D-024, D-033.\n"  # (b) 7 != 1 и D-024 accepted → 2 находки
       "- текущий фокус: закрыть T-100 и T-200.\n"               # (c) T-100 done → находка; T-200 open ок
       "- C17-заметка: ручные числа отстали на 99 задач (delta, не флажить).\n"  # historical → пропуск
       "\n"
       "## Что изменилось недавно\n"
       "\n"
       "| 2026-06-19 | Novax | заморозка: 42 задач тогда | ref |\n")  # changelog вне фокуса → пропуск


# ----- fixture-хук conftest: даёт `root` через build_fixture (имя make_canon для совместимости) -----
make_canon = build_fixture


def _findings_by_kind(findings):
    by = {}
    for f in findings:
        by.setdefault(f["kind"], []).append(f)
    return by


def _run_on_fixture():
    """Построить fixture, прогнать sd.run на temp-ROOT, вернуть находки. Восстанавливает ROOT."""
    root = tempfile.mkdtemp(prefix="status_drift_test_")
    saved = sd.ROOT
    try:
        build_fixture(root)
        sd.ROOT = root
        return sd.run(root), root
    finally:
        sd.ROOT = saved
        shutil.rmtree(root, ignore_errors=True)


# ===== pytest-ступень (module-level test_*) =====

def test_detects_c17_and_scopes_out_noise():
    findings, _ = _run_on_fixture()
    by = _findings_by_kind(findings)

    # (b) статус: D-024 указан как нератифицированный, но accepted — ядро находки C17
    assert "decision-status" in by, "должна быть находка decision-status (C17): %s" % findings
    wrong = by["decision-status"][0]["wrong"]
    assert wrong == ["D-024"], "wrong должно быть РОВНО [D-024]: %s" % wrong

    # (b) число: заявлено 7, реально нератифицированных в списке 1
    dc = [f for f in by.get("decision-count", []) if f["claimed"] == 7]
    assert dc and dc[0]["actual"] == 1, "decision-count 7→1 ожидается: %s" % by.get("decision-count")

    # (a) числовое: «5 задач» != 3, и НЕ должно быть находки на «99 задач» (delta) или «42 задач» (changelog)
    numeric = by.get("numeric", [])
    claimed = sorted(f["claimed"] for f in numeric if f["noun"] == "tasks")
    assert claimed == [5], "числовая находка задач должна быть РОВНО [5] (99/42 отфильтрованы): %s" % claimed

    # (c) focus-task: T-100 (done) во «текущем фокусе» — находка; T-200 (open) — нет
    focus = by.get("focus-task-done", [])
    tasks = {f["task"] for f in focus}
    assert tasks == {"T-100"}, "focus-task-done должно быть РОВНО {T-100}: %s" % tasks


def test_clean_status_no_findings():
    """Согласованный STATUS.md (ручные утверждения = факты) → находок нет."""
    root = tempfile.mkdtemp(prefix="status_drift_clean_")
    saved = sd.ROOT
    try:
        _decision(root, "D-001", "accepted")
        _decision(root, "D-002", "proposed")
        _task(root, "T-001", "open")
        _w(os.path.join(root, "index.json"),
           '{"tasks":[1],"decisions":[1,2],"questions":[],"topics":[],"drivers":[]}')
        _w(os.path.join(root, "STATUS.md"),
           "# Статус\n\n## Текущий фокус\n\n"
           "- В работе 1 задач.\n"                              # 1 == 1 ок
           "- очередь: 1 нератифицированных: D-002.\n"          # 1 == 1 и D-002 proposed ок
           "- фокус: доделать T-001.\n")                        # T-001 open ок
        sd.ROOT = root
        findings = sd.run(root)
        assert findings == [], "чистый STATUS.md не должен давать находок: %s" % findings
    finally:
        sd.ROOT = saved
        shutil.rmtree(root, ignore_errors=True)


def test_no_false_positive_on_ratification_and_done_marker():
    """Регрессия: НЕ флажить строку, описывающую ПРИНЯТИЕ решений, и T-id с пометкой «(done)».

    Два ложных срабатывания (найдены при фиксе STATUS 2026-07-06):
    (b) «приняты 6 (D-024, D-026 → accepted)» — слово «proposed»/список D-id рядом, но текст
        УТВЕРЖДАЕТ принятие, а не претензию «нератифицировано» → находки быть НЕ должно;
    (c) «T-050 (done)» в фокусе — явная пометка завершённости как контекст → не дрейф.
    """
    root = tempfile.mkdtemp(prefix="status_drift_fp_")
    saved = sd.ROOT
    try:
        _decision(root, "D-024", "accepted")
        _decision(root, "D-026", "accepted")
        _decision(root, "D-033", "proposed")
        _task(root, "T-050", "done")
        _task(root, "T-060", "open")
        _w(os.path.join(root, "index.json"),
           '{"tasks":[1,2],"decisions":[1,2,3],"questions":[],"topics":[],"drivers":[]}')
        _w(os.path.join(root, "STATUS.md"),
           "# Статус\n\n## Текущий фокус\n\n"
           "- governance: из 7 proposed-решений приняты 6 (D-024, D-026 → accepted); остаётся D-033.\n"
           "- фокус: T-050 (done) — контекст; активна T-060.\n")
        sd.ROOT = root
        by = _findings_by_kind(sd.run(root))
        assert "decision-status" not in by, \
            "(b) строка о принятии решений НЕ должна давать decision-status: %s" % by.get("decision-status")
        assert "decision-count" not in by, \
            "(b) строка о принятии не должна давать decision-count: %s" % by.get("decision-count")
        ftd = {f["task"] for f in by.get("focus-task-done", [])}
        assert "T-050" not in ftd, "(c) T-050 (done) с явной пометкой не должна флажиться: %s" % ftd
    finally:
        sd.ROOT = saved
        shutil.rmtree(root, ignore_errors=True)


def test_strip_gen_blocks_excludes_generated():
    """Содержимое GEN-блока не считается ручной прозой (сравниваем только ручной текст)."""
    text = ("ручная строка A\n"
            "<!-- GEN:counters START -->\n"
            "генерируемое: 999 задач\n"
            "<!-- GEN:counters END -->\n"
            "ручная строка B\n")
    manual = "\n".join(t for _n, t in sd.manual_lines(text))
    assert "ручная строка A" in manual and "ручная строка B" in manual
    assert "999" not in manual, "число из GEN-блока не должно попадать в ручную прозу"


# ===== self-running ступень (test_all.py) =====

def run():
    ok = True
    for fn in (test_detects_c17_and_scopes_out_noise,
               test_clean_status_no_findings,
               test_no_false_positive_on_ratification_and_done_marker,
               test_strip_gen_blocks_excludes_generated):
        try:
            fn()
        except AssertionError as exc:
            ok = False
            print("TEST FAIL [%s]: %s" % (fn.__name__, exc))
    if ok:
        print("TESTS OK status_drift: C17 decision-status + count + numeric(scoped) + "
              "focus-task-done + clean-noop + gen-strip")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(run())
