#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
# ==========================================
# [FILE ID CARD]
# ID: tools.test_dispatch
# TYPE: active-script
# DOMAIN: core
# DEPTH_LEVEL: 1
# SUMMARY: Скрипт test_dispatch.py. Описание сгенерировано автоматически.
# ==========================================
"""
"""Тест dispatch (tools/dispatch.py) — DAG-диспетчер: ready/blocked по depends_on + приоритетный порядок + next."""
import os
import sys
import io
import shutil
from contextlib import redirect_stdout

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, "drivers"))

from test_tmp import make_temp_dir  # noqa: E402
from _canon import parse_front_matter  # noqa: E402


def configure_output():
    for name in ("stdout", "stderr"):
        s = getattr(sys, name, None)
        if s is not None and hasattr(s, "reconfigure"):
            s.reconfigure(encoding="utf-8", errors="replace")


configure_output()


def _task(root, tid, status="todo", priority="", depends_on="", title="t"):
    d = os.path.join(root, "tasks")
    os.makedirs(d, exist_ok=True)
    fm = ["---", "id: %s" % tid, "title: %s" % title, "status: %s" % status]
    if priority:
        fm.append("priority: %s" % priority)
    if depends_on:
        fm.append("depends_on: %s" % depends_on)
    fm += ["---", "", "body", ""]
    with open(os.path.join(d, tid + ".md"), "w", encoding="utf-8") as f:
        f.write("\n".join(fm))


def run():
    ok = True
    base = make_temp_dir("dispatch_")
    os.environ["COLLAB_ROOT"] = base
    try:
        # DAG:
        #   T-400 done (база)
        #   T-401 todo, depends_on T-400(done) → READY, priority high
        #   T-402 todo, depends_on T-400(done) → READY, priority normal
        #   T-403 todo, depends_on T-410(не done) → BLOCKED
        #   T-410 todo (статус не done) — блокирует T-403; сам без deps → READY, low
        #   T-420 done → не попадает ни в ready, ни в blocked (фильтр status==todo)
        _task(base, "T-400", status="done")
        _task(base, "T-401", priority="high", depends_on="T-400")
        _task(base, "T-402", priority="normal", depends_on="T-400")
        _task(base, "T-403", priority="high", depends_on="зависит от T-410 и T-400")
        _task(base, "T-410", priority="low")
        _task(base, "T-420", status="done")

        # контракт фикстур: _canon парсит наш front-matter
        with open(os.path.join(base, "tasks", "T-401.md"), encoding="utf-8") as f:
            assert parse_front_matter(f.read()).get("depends_on") == "T-400"

        import dispatch as d
        assert d.ROOT == base, (d.ROOT, base)

        # регресс (аудит P3/B-04): в исходнике модуля нет bare-CR переводов строк
        # (bare-CR ломает git-диффы: файл считается -text/binary)
        raw = open(os.path.join(HERE, "dispatch.py"), "rb").read()
        assert b"\r" not in raw.replace(b"\r\n", b"\n"), \
            "bare-CR переводы строк в dispatch.py (git видит файл как binary)"

        tasks = d.load_tasks()
        assert set(tasks) == {"T-400", "T-401", "T-402", "T-403", "T-410", "T-420"}, set(tasks)
        # deps извлекаются регуляркой T-\d+ из произвольного текста depends_on
        assert tasks["T-403"]["deps"] == ["T-410", "T-400"], tasks["T-403"]["deps"]
        assert tasks["T-401"]["deps"] == ["T-400"]
        assert tasks["T-410"]["deps"] == []
        # PRIO-карта: high<normal<low<""
        assert d.PRIO["high"] < d.PRIO["normal"] < d.PRIO["low"] < d.PRIO[""]

        def call(*argv):
            saved = sys.argv
            sys.argv = ["dispatch.py", *argv]
            buf = io.StringIO()
            try:
                with redirect_stdout(buf):
                    rc = d.main()
            finally:
                sys.argv = saved
            return rc, buf.getvalue()

        # default-вывод: ГОТОВЫ=3 (401,402,410), ЗАБЛОКИРОВАНЫ=1 (403)
        rc, out = call()
        assert rc == 0, out
        assert "ГОТОВЫ (можно брать), 3:" in out, out
        assert "ЗАБЛОКИРОВАНЫ, 1:" in out, out
        # заблокированный показывает невыполненную зависимость T-410 (а не T-400, который done)
        assert "T-403" in out and "T-410" in out, out
        blk_line = [ln for ln in out.splitlines() if "T-403" in ln][0]
        assert "T-410" in blk_line and "T-400" not in blk_line, blk_line

        # порядок ready по приоритету: T-401(high) раньше T-402(normal) раньше T-410(low)
        ready_section = out.split("ЗАБЛОКИРОВАНЫ")[0]
        i401 = ready_section.index("T-401")
        i402 = ready_section.index("T-402")
        i410 = ready_section.index("T-410")
        assert i401 < i402 < i410, "приоритетный порядок high<normal<low нарушен"

        # КЛЮЧЕВОЕ: next → id самой приоритетной готовой задачи (T-401, high)
        rc, out = call("next")
        assert rc == 0 and out.strip() == "T-401", repr(out)

        # пустой workspace → next пуст, default не падает
        empty = make_temp_dir("dispatch_empty_")
        os.environ["COLLAB_ROOT"] = empty
        import importlib
        importlib.reload(d)
        try:
            assert d.ROOT == empty
            rc, out = call("next")
            assert rc == 0 and out.strip() == "", "нет готовых → next пуст: %r" % out
            rc, out = call()
            assert rc == 0 and "ГОТОВЫ (можно брать), 0:" in out, out
        finally:
            shutil.rmtree(empty, ignore_errors=True)
            os.environ["COLLAB_ROOT"] = base

        print("TESTS OK dispatch: load_tasks(deps regex T-\\d+) + ready/blocked по depends_on + приоритет high<normal<low + next + пустой workspace + нет bare-CR")
    except AssertionError as e:
        ok = False
        print("TEST FAIL:", e)
    except Exception as e:  # noqa: BLE001
        ok = False
        print("TEST ERROR:", repr(e))
    finally:
        os.environ.pop("COLLAB_ROOT", None)
        shutil.rmtree(base, ignore_errors=True)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(run())
