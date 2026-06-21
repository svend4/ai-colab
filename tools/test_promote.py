#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Тест promotion gate пирамиды (tools/promote.py) — герметичный, temp-root, реальные артефакты не трогаются."""
import os
import sys
import shutil

HERE = os.path.dirname(os.path.abspath(__file__))
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

        if ok:
            print("TESTS OK promote: list/levels, check fail no-decision-ref, atomic move L4->L3 + stamp, no orphan")
    except AssertionError as e:
        ok = False
        print("TEST FAIL:", e)
    finally:
        shutil.rmtree(root, ignore_errors=True)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(run())
