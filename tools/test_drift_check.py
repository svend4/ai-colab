#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Тест drift detector (tools/drift_check.py) — текстовые сканеры дрейфа."""
import os
import sys
import tempfile
import shutil

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import drift_check as dc


def run():
    base = tempfile.mkdtemp(prefix="drift_test_", dir=os.path.join(ROOT, "tmp-work")
                            if os.path.isdir(os.path.join(ROOT, "tmp-work")) else None)
    ok = True
    try:
        docs = os.path.join(base, "docs")
        os.makedirs(docs)
        with open(os.path.join(docs, "bad.md"), "w", encoding="utf-8") as f:
            f.write("# x\nслои L0-L8 тут\n")
        with open(os.path.join(docs, "good.md"), "w", encoding="utf-8") as f:
            f.write("# y\nканон L0-L7\n")

        # scan_layer_drift ловит L0-L8 и не ловит L0-L7
        found = dc.scan_layer_drift(docs)
        assert found == ["bad.md"], found

        # scan_legacy_queue ловит queue.py
        q = os.path.join(base, "qs.md")
        with open(q, "w", encoding="utf-8") as f:
            f.write("запусти python tools/queue.py next\n")
        clean = os.path.join(base, "clean.md")
        with open(clean, "w", encoding="utf-8") as f:
            f.write("запусти python tools/pipeline.py next\n")
        # scan_legacy_queue принимает пути относительно ROOT — проверим через абсолютные имена
        rel_q = os.path.relpath(q, ROOT)
        rel_clean = os.path.relpath(clean, ROOT)
        hits = dc.scan_legacy_queue([rel_q, rel_clean])
        assert hits == [rel_q], hits

        # run() возвращает список (на реальном репо — допустимо непусто)
        d = dc.run()
        assert isinstance(d, list), type(d)

        print("TESTS OK drift_check: layer-scan + queue-scan + run() (реальный дрейф=%d)" % len(d))
    except AssertionError as e:
        ok = False
        print("TEST FAIL:", e)
    finally:
        shutil.rmtree(base, ignore_errors=True)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(run())
