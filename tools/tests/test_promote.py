#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
# ==========================================
# [FILE ID CARD]
# ID: tools.tests.test_promote
# TYPE: active-script
# DOMAIN: core
# DEPTH_LEVEL: 1
# SUMMARY: Скрипт test_promote.py. Описание сгенерировано автоматически.
# ==========================================
"""
"""Тест promotion gate пирамиды (tools/promote.py) — герметичный, temp-root, реальные артефакты не трогаются."""
# --- бутстрап путей (C14, аудит 2026-07-02): тест живёт в tools/tests/, инструменты — в tools/.
# Вставка ДО локальных импортов, чтобы standalone-запуск работал из нового места.
import os as _os
import sys as _sys
_TOOLS_DIR = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
if _TOOLS_DIR not in _sys.path:
    _sys.path.insert(0, _TOOLS_DIR)
# --- конец бутстрапа ---

import os
import sys
import shutil

HERE = _TOOLS_DIR  # tools/ — тест перенесён в tools/tests/ (C14)
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, "drivers"))
import promote as pr
from test_tmp import make_temp_dir


def _mkpyramid():
    """Временная пирамида: core/ portals/ sandbox/ + L3 dirs."""
    root = make_temp_dir("promote_test_")
    for d in ("core", "portals", "sandbox", "tasks", "decisions"):
        os.makedirs(os.path.join(root, d), exist_ok=True)
    return root


def run():
    ok = True
    root = _mkpyramid()
    try:
        # --- list возвращает уровни ---
        levels = pr.list_levels(root=root)
        names = [lv["level"] for lv in levels]
        assert names == ["L1", "L2", "L3", "L4"], names

        # --- L4-артефакт БЕЗ decision-ref: check должен дать fail ---
        bad = os.path.join(root, "sandbox", "raw-source.md")
        with open(bad, "w", encoding="utf-8", newline="\n") as f:
            f.write("---\nid: raw-source\ntype: external-source\nstatus: quarantine\n---\n\nСырой вход.\n")
        rep_bad = pr.check(bad, frm="L4", to="L3", root=root)
        crit = {c["name"]: c["passed"] for c in rep_bad["criteria"]}
        assert rep_bad["ready"] is False, rep_bad
        assert crit["decision_ref"] is False, crit
        assert crit["read_only_report"] is True, crit

        # --- L4-артефакт С decision-ref: готов к подъёму ---
        good = os.path.join(root, "sandbox", "reviewed-source.md")
        with open(good, "w", encoding="utf-8", newline="\n") as f:
            f.write("---\nid: reviewed-source\ntype: external-source\nstatus: quarantine\n"
                    "decision_ref: D-016\n---\n\nПрошёл review.\n")
        rep_good = pr.check(good, frm="L4", to="L3", root=root)
        assert rep_good["ready"] is True, rep_good

        # --- move L4->L3: атомарный перенос + stamp + NO orphan ---
        r = pr.move(good, "L4", "L3", reviewed_by="tester", decision_ref="D-016", root=root)
        # старый путь исчез
        assert not os.path.exists(good), "orphan: старый путь остался"
        # новый путь существует
        new_path = r["to_path"]
        assert os.path.isfile(new_path), new_path
        # новый путь — в L3 (tasks/)
        assert pr.level_of(new_path, root) == "L3", new_path
        # нет half-move tmp
        assert not os.path.exists(new_path + ".tmp"), "остался .tmp half-move"
        # stamp метаданных записан
        fm = pr._read_fm(new_path)
        for key in ("promoted_from", "promoted_to", "promotion_date",
                    "gate_checks_passed", "reviewed_by", "decision_ref"):
            assert key in fm, ("нет stamp-поля %s" % key, fm)
        assert fm["promoted_from"] == "L4" and fm["promoted_to"] == "L3", fm
        assert fm["reviewed_by"] == "tester", fm
        assert fm["decision_ref"] == "D-016", fm
        # исходное содержимое сохранено
        body = open(new_path, encoding="utf-8").read()
        assert "Прошёл review." in body, body

        # --- gate блокирует подъём неготового артефакта ---
        try:
            pr.move(bad, "L4", "L3", root=root)
            ok = False
            print("TEST FAIL: move неготового артефакта не был заблокирован")
        except ValueError:
            pass
        # неготовый артефакт не сдвинут (нет orphan)
        assert os.path.exists(bad), "неготовый артефакт пропал"

        # --- перескок уровней запрещён ---
        try:
            pr.check(good if os.path.exists(good) else new_path, frm="L4", to="L2", root=root)
            ok = False
            print("TEST FAIL: перескок L4->L2 не отклонён")
        except ValueError:
            pass

        # --- move L2->L1: атомарный перенос + stamp + reuse + verification ---
        l2_root = os.path.join(root, "tools")
        os.makedirs(l2_root, exist_ok=True)
        l2_art = os.path.join(l2_root, "aa.py")
        with open(l2_art, "w", encoding="utf-8", newline="\n") as f:
            f.write("# L2 artifact\n")
        # test-файл для verification (P12)
        l2_test = os.path.join(l2_root, "test_aa.py")
        with open(l2_test, "w", encoding="utf-8", newline="\n") as f:
            f.write("def test_aa(): pass\n")
        # манифест + два портала для reuse_across_portals
        man = os.path.join(root, "core", "engine-manifest.md")
        with open(man, "w", encoding="utf-8", newline="\n") as f:
            f.write("---\nfiles: [tools/aa.py]\n---\n")
        for pid, basis in [("p1", ["tools/aa.py"]), ("p2", ["tools/aa.py"])]:
            pdir = os.path.join(root, "portals", pid)
            os.makedirs(pdir, exist_ok=True)
            with open(os.path.join(pdir, "portal.md"), "w", encoding="utf-8", newline="\n") as f:
                f.write("---\nid: %s\nl1_basis: %s\n---\n" % (pid, basis))
        # проверка гейта
        rep_l2 = pr.check(l2_art, frm="L2", to="L1", root=root)
        assert rep_l2["ready"] is True, rep_l2
        # move
        r2 = pr.move(l2_art, "L2", "L1", reviewed_by="tester", decision_ref="D-TEST", root=root)
        l1_path = r2["to_path"]
        assert os.path.isfile(l1_path), l1_path
        assert pr.level_of(l1_path, root) == "L1", l1_path
        assert not os.path.exists(l2_art), "orphan L2: старый путь остался"
        assert not os.path.exists(l1_path + ".tmp"), "остался .tmp half-move L2->L1"
        fm2 = pr._read_fm(l1_path)
        assert fm2.get("promoted_from") == "L2" and fm2.get("promoted_to") == "L1", fm2
        assert fm2.get("reviewed_by") == "tester", fm2

        if ok:
            print("TESTS OK promote: list/levels, check fail no-decision-ref, atomic move L4->L3 + stamp, no orphan, atomic move L2->L1 + reuse + verification")
    except AssertionError as e:
        ok = False
        print("TEST FAIL:", e)
    finally:
        shutil.rmtree(root, ignore_errors=True)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(run())
