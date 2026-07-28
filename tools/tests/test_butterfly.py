#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ==========================================
# [FILE ID CARD]
# ID: tools.tests.test_butterfly
# TYPE: active-script
# DOMAIN: core.synthesis
# DEPTH_LEVEL: 2
# SUMMARY: Tests safe dry-run/apply behavior for butterfly graph and synthesis tools.
# ==========================================
"""Focused tests for butterfly graph/alchemist tools."""
# --- бутстрап путей (C14, аудит 2026-07-02): тест живёт в tools/tests/, инструменты — в tools/.
# Вставка ДО локальных импортов, чтобы standalone-запуск работал из нового места.
import os as _os
import sys as _sys
_TOOLS_DIR = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
if _TOOLS_DIR not in _sys.path:
    _sys.path.insert(0, _TOOLS_DIR)
# --- конец бутстрапа ---


import json
import os
import shutil
import sys


HERE = _TOOLS_DIR  # tools/ — тест перенесён в tools/tests/ (C14)
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "drivers"))
sys.path.insert(0, HERE)

from test_tmp import make_temp_dir

import butterfly_alchemist as alchemist
import butterfly_graph_builder as builder
import butterfly_rationalizer as rationalizer
from semantic_engine import AdvancedAlgorithms


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
        assert all(len(atom["hash"]) == 16 for atom in data), data

        sample_a = alchemist.select_atoms(data, 3, seed="42")
        sample_b = alchemist.select_atoms(data, 3, seed="42")
        assert [x["hash"] for x in sample_a] == [x["hash"] for x in sample_b]
        gap_sample = alchemist.select_atoms_by_gap(data, 3)
        assert len(gap_sample) == 3
        assert len({x["hash"] for x in gap_sample}) == 3
        assert "дополнительные ограничения" in alchemist.build_question(["А", "Б", "В", "Г"])

        contradiction = AdvancedAlgorithms.contradiction_check(
            "Система разрешает запись в общий файл",
            "Система не разрешает запись в общий файл",
        )
        support = AdvancedAlgorithms.contradiction_check(
            "Система разрешает запись в общий файл",
            "Система разрешает запись в общий файл",
        )
        assert contradiction["related"] and contradiction["contradicts"], contradiction
        assert support["related"] and not support["contradicts"], support

        duplicate_graph = [
            {"hash": "a" * 16, "content": "Общий котел сохраняет варианты агентов.", "links": []},
            {"hash": "b" * 16, "content": "Общий котел сохраняет варианты агентов.", "links": []},
            {"hash": "c" * 16, "content": "Независимый отчёт добавляет новый контекст.", "links": []},
        ]
        rationalized = rationalizer.rationalize(duplicate_graph, eps=0.0)
        rational_payload = rationalizer.report_payload(
            rationalized, graph, 0.0, 12, False)
        assert rational_payload["removed"] == 1, rational_payload
        assert rational_payload["info_kept_pct"] == 100.0, rational_payload
        assert rational_payload["mode"] == "dry-run"

        near_base = "alpha beta gamma delta epsilon zeta eta theta iota kappa lambda mu nu xi omicron".split()
        near_graph = []
        for idx in range(8):
            words = near_base[:]
            words[-1] = "variant%s" % idx
            near_graph.append({"hash": str(idx), "content": " ".join(words), "links": []})
        near_result = rationalizer.rationalize(near_graph, eps=1.0, hamming_threshold=64)
        near_ops = [op["hash"] for op in near_result["ops"] if op["op"] == "near"]
        assert len(near_ops) == len(set(near_ops)), near_ops
        assert len(near_ops) == len(near_result["removed"]), near_result

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