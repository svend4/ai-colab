#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ==========================================
# [FILE ID CARD]
# ID: tools.test_butterfly
# TYPE: active-script
# DOMAIN: core.synthesis
# DEPTH_LEVEL: 2
# SUMMARY: Tests safe dry-run/apply behavior for butterfly graph and synthesis tools.
# ==========================================
"""Focused tests for butterfly graph/alchemist tools."""

import json
import os
import shutil
import sys


HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "drivers"))
sys.path.insert(0, HERE)

from test_tmp import make_temp_dir

import butterfly_alchemist as alchemist
import butterfly_graph_builder as builder


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def run():
    base = make_temp_dir("butterfly_")
    try:
        source = os.path.join(base, "outbox")
        graph = os.path.join(base, "indexes", "cauldron_graph.json")
        out = os.path.join(base, "topics", "alchemy.md")
        write(os.path.join(source, "a.md"), """# Report

Первый атом достаточно длинный, чтобы попасть в смысловой граф и стать сырьем.

Второй атом описывает проблему согласования агентов через общий котел и отчеты.

Третий атом предлагает использовать dry-run и apply как управляемую границу записи.
""")

        assert builder.main(["--source-dir", source, "--graph", graph]) == 0
        assert not os.path.exists(graph), "dry-run must not write graph"

        assert builder.main(["--source-dir", source, "--graph", graph, "--apply", "--json"]) == 0
        with open(graph, "r", encoding="utf-8") as f:
            data = json.load(f)
        assert len(data) == 3, data

        sample_a = alchemist.select_atoms(data, 3, seed="42")
        sample_b = alchemist.select_atoms(data, 3, seed="42")
        assert [x["hash"] for x in sample_a] == [x["hash"] for x in sample_b]

        assert alchemist.main([
            "--graph", graph,
            "--out", out,
            "--seed", "42",
            "--created-at", "2026-06-26T00:00:00",
        ]) == 0
        assert not os.path.exists(out), "dry-run must not write synthesis topic"

        assert alchemist.main([
            "--graph", graph,
            "--out", out,
            "--seed", "42",
            "--created-at", "2026-06-26T00:00:00",
            "--apply",
            "--json",
        ]) == 0
        with open(out, "r", encoding="utf-8") as f:
            text = f.read()
        assert "status: proposed" in text, text
        assert "АЛХИМИЧЕСКИЙ СИНТЕЗ" in text, text
        assert "streams/<topic>/<agent>/" in text, text

        print("OK test_butterfly: dry-run/apply + deterministic sample")
        return 0
    finally:
        shutil.rmtree(base, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(run())