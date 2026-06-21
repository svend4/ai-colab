#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Тест механизма тематических порталов (tools/portal.py, D-016)."""
import os
import sys
import shutil

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import portal as p


def run():
    name = "_ptest"
    pdir = os.path.join(p.PORTALS, name)
    ok = True
    try:
        # scaffold портала + контент темы
        p.new(name, desc="тест-портал", corpus="corpus", topics=["alpha", "beta", "zeta"])
        cdir = os.path.join(pdir, "corpus")
        with open(os.path.join(cdir, "a.md"), "w", encoding="utf-8") as f:
            f.write("# alpha\nтекст про alpha и немного beta\n")
        with open(os.path.join(cdir, "b.txt"), "w", encoding="utf-8") as f:
            f.write("ещё beta\n")

        # портал виден в списке
        names = [x["name"] for x in p.list_portals()]
        assert name in names, names

        # build заносит документы в свою БД
        n, db, fm = p.build(name)
        assert n == 2, n
        assert fm["_topics"] == ["alpha", "beta", "zeta"], fm["_topics"]

        # report содержит покрытие тем; alpha и beta встречаются, zeta — нет
        rep = p.report(name, query="alpha")
        assert "Покрытие тем портала" in rep, rep[:200]
        assert "Портал **_ptest**" in rep, rep[:120]
        # zeta не встречается → 0; alpha/beta встречаются → >0 (грубая проверка строк таблицы)
        assert "| zeta | 0 |" in rep, "ожидалось zeta=0: %s" % rep[-400:]
        assert ("| alpha | 1 |" in rep or "| alpha | 2 |" in rep), "alpha должно встречаться"

        print("TESTS OK portal: docs=%d topics=%d (build/report/coverage)" % (n, len(fm["_topics"])))
    except AssertionError as e:
        ok = False
        print("TEST FAIL:", e)
    finally:
        shutil.rmtree(pdir, ignore_errors=True)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(run())
