#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
# ==========================================
# [FILE ID CARD]
# ID: tools.test_action_tracker
# TYPE: active-script
# DOMAIN: core
# DEPTH_LEVEL: 1
# SUMMARY: Тест action_tracker.py — канонический parse_fm из _canon (аудит C34) + dump_fm/replace_fm + status.
# ==========================================
"""
"""Тест action_tracker (tools/action_tracker.py).

Регрессия аудита C34: `from _canon import parse_fm, dump_fm` всегда падал
(dump_fm в _canon нет), поэтому работал локальный фоллбэк-парсер, который
расходился с каноном (front-matter без завершающего перевода строки после
закрывающего `---` давал {} вместо словаря). Проверяем, что parse_fm — это
реально _canon.parse_fm, и что расхождение устранено.
"""
import io
import json
import os
import shutil
import sys
from contextlib import redirect_stdout

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, "drivers"))

from test_tmp import make_temp_dir  # noqa: E402
import _canon  # noqa: E402


def configure_output():
    for name in ("stdout", "stderr"):
        s = getattr(sys, name, None)
        if s is not None and hasattr(s, "reconfigure"):
            s.reconfigure(encoding="utf-8", errors="replace")


configure_output()


def _report(base, name, body):
    d = os.path.join(base, "queues", "outbox")
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, name), "w", encoding="utf-8", newline="\n") as f:
        f.write(body)


def run():
    ok = True
    base = make_temp_dir("action_tracker_")
    os.environ["COLLAB_ROOT"] = base
    try:
        import importlib
        import action_tracker as at
        at = importlib.reload(at)  # ROOT/OUTBOX вычисляются при импорте — перечитываем COLLAB_ROOT

        # КЛЮЧЕВОЕ (C34): парсер — канонический, а не локальная копия.
        assert at.parse_fm is _canon.parse_fm, "parse_fm должен быть _canon.parse_fm (C34)"
        # dump_fm остаётся локальным (в _canon его нет — перенос отложен до C35).
        assert not hasattr(_canon, "dump_fm"), "dump_fm появился в _canon — тест и комментарий C34 устарели"

        # Регрессия C34: фоллбэк-regex требовал `---\n` в конце и давал {}
        # для front-matter без завершающего перевода строки; канон даёт словарь.
        assert at.parse_fm("---\nstatus: active\n---") == {"status": "active"}, \
            "front-matter без завершающего \\n после `---` должен парситься (канон)"
        assert at.parse_fm("---\nstatus: active\n---\nтело\n") == {"status": "active"}
        assert at.parse_fm("просто текст без front-matter") == {}

        # dump_fm/replace_fm: сериализация и замена блока front-matter.
        assert at.dump_fm({"status": "historical", "id": "R-1"}) == "---\nstatus: historical\nid: R-1\n---\n"
        text = "---\nstatus: active\n---\n# Отчёт\n- [ ] пункт\n"
        replaced = at.replace_fm(text, {"status": "historical"})
        assert replaced == "---\nstatus: historical\n---\n# Отчёт\n- [ ] пункт\n", repr(replaced)
        # текст без front-matter: блок добавляется в начало
        assert at.replace_fm("тело\n", {"a": "1"}) == "---\na: 1\n---\nтело\n"
        # раунд-трип: replace_fm → parse_fm возвращает тот же словарь
        assert at.parse_fm(replaced) == {"status": "historical"}

        # parse_file/status: считает чекбоксы, уважает historical и код-блоки.
        assert at.ROOT == base, (at.ROOT, base)
        _report(base, "r-unprocessed.md", "---\nstatus: active\n---\n- [ ] один\n- [ ] два\n")
        _report(base, "r-partial.md", "- [x] готово\n- [ ] нет\n")
        _report(base, "r-shipped.md", "- [x] готово\n")
        _report(base, "r-historical.md", "---\nstatus: historical\n---\n- [ ] игнор\n")
        # чекбокс внутри код-блока не считается
        _report(base, "r-noactions.md", "```\n- [ ] в код-блоке\n```\nтекст\n")

        info = at.parse_file(os.path.join(base, "queues", "outbox", "r-unprocessed.md"))
        assert info["status"] == "unprocessed" and info["unchecked"] == 2, info
        info = at.parse_file(os.path.join(base, "queues", "outbox", "r-historical.md"))
        assert info["status"] == "historical", info
        info = at.parse_file(os.path.join(base, "queues", "outbox", "r-noactions.md"))
        assert info["status"] == "no-actions" and info["total"] == 0, info

        def call(*argv):
            saved = sys.argv
            sys.argv = ["action_tracker.py", *argv]
            buf = io.StringIO()
            try:
                with redirect_stdout(buf):
                    rc = at.main()
            finally:
                sys.argv = saved
            return rc, buf.getvalue()

        # status --json — контракт для conveyor.py/top.py (активный путь C34)
        rc, out = call("status", "--json")
        assert rc == 0, out
        data = {r["file"]: r["status"] for r in json.loads(out)}
        assert data == {
            "r-unprocessed.md": "unprocessed",
            "r-partial.md": "partial",
            "r-shipped.md": "shipped",
            "r-historical.md": "historical",
            "r-noactions.md": "no-actions",
        }, data

        rc, out = call("status")
        assert rc == 0 and "unprocessed: 1" in out and "historical:  1" in out, out

        print("TESTS OK action_tracker: parse_fm is _canon.parse_fm (C34) + регрессия front-matter без \\n + dump_fm/replace_fm + parse_file/status(--json)")
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


def test_action_tracker():
    # обёртка для pytest — сам тест самопроверенный (run)
    assert run() == 0


if __name__ == "__main__":
    sys.exit(run())
