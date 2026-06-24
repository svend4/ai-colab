#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
# ==========================================
# [FILE ID CARD]
# ID: tools.test_drift_check
# TYPE: active-script
# DOMAIN: core
# DEPTH_LEVEL: 1
# SUMMARY: Скрипт test_drift_check.py. Описание сгенерировано автоматически.
# ==========================================
"""
"""Тест drift detector (tools/drift_check.py) — текстовые сканеры дрейфа."""
import os
import sys
import shutil

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import drift_check as dc


def prepare_base():
    candidates = [
        os.path.join(r"C:\tmp", "ai_colab_drift_test"),
        os.path.join(ROOT, "tmp-work", "drift_test_runtime"),
    ]
    last_error = None
    for base in candidates:
        try:
            shutil.rmtree(base, ignore_errors=True)
            os.makedirs(base, exist_ok=True)
            probe = os.path.join(base, ".write_probe")
            with open(probe, "w", encoding="utf-8") as f:
                f.write("ok")
            os.remove(probe)
            return base
        except OSError as exc:
            last_error = exc
    raise RuntimeError("no writable drift_check test root: %r" % (last_error,))


def run():
    base = prepare_base()
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
