#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
# ==========================================
# [FILE ID CARD]
# ID: tools.test_merge_gate
# TYPE: active-script
# DOMAIN: core
# DEPTH_LEVEL: 1
# SUMMARY: Скрипт test_merge_gate.py. Описание сгенерировано автоматически.
# ==========================================
"""
"""Тест merge-gate (tools/merge_gate.py) — оркестратор гейта green/red.

Гермётичен и НЕ зависит от реального состояния репо (его churn'ит Codex): stage-runner
инъектируется контролируемой фикстурой. PASS/FAIL утверждается на фикстуре, не на репо.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import merge_gate as mg


def make_runner(fail_script=None):
    """Фейковый runner: всё зелёное, кроме fail_script.

    Для generate.py имитируем 'drift' через STALE в выводе при rc==0 — проверяем,
    что _is_green ловит маркер дрейфа, а не только ненулевой код."""
    def runner(script, *args):
        if script == fail_script:
            if script == "generate.py":
                return 0, "STALE: индексы устарели\n"
            return 1, "%s провалился\n" % script
        return 0, "OK %s\n" % script
    return runner


def run():
    ok = True
    try:
        # Состав стадий: без agent — две стадии; с agent — три (добавляется permissions).
        st = mg.gate_stages()
        labels = [s[0] for s in st]
        assert labels == ["validate", "generate --check"], labels
        st_a = mg.gate_stages(agent="claude")
        assert st_a[-1][1] == "permissions.py", st_a
        assert st_a[-1][2] == ("claude",), st_a

        # --with-tests добавляет хотя бы один tools/test_*.py (включая нас самих).
        st_t = mg.gate_stages(with_tests=True)
        assert any(lbl.startswith("test:") for lbl, _, _ in st_t), st_t

        # Все зелёные -> all_green True, exit 0.
        green, results = mg.gate(agent="claude", runner=make_runner())
        assert green is True, results
        assert all(g for _, g, _, _ in results), results

        # generate --check репортит drift (STALE при rc=0) -> red, exit 1.
        red, results = mg.gate(agent="claude", runner=make_runner(fail_script="generate.py"))
        assert red is False, results
        bad = [lbl for lbl, g, _, _ in results if not g]
        assert bad == ["generate --check"], bad

        # validate провалился ненулевым кодом -> тоже red.
        red2, _ = mg.gate(runner=make_runner(fail_script="validate.py"))
        assert red2 is False

        # main(): зелёный фейковый прогон -> 0, красный -> 1 (через monkeypatch _run).
        orig = mg._run
        sys.argv = ["merge_gate.py", "check", "claude", "T-999"]
        try:
            mg._run = make_runner()
            assert mg.main() == 0
            mg._run = make_runner(fail_script="generate.py")
            assert mg.main() == 1
            # неизвестная команда -> 2 (help)
            sys.argv = ["merge_gate.py", "bogus"]
            assert mg.main() == 2
        finally:
            mg._run = orig

        print("TESTS OK merge_gate: stages + green/red + drift-detect + main exit-codes")
    except AssertionError as e:
        ok = False
        print("TEST FAIL:", e)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(run())
