#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Тест risk_gate (tools/risk_gate.py) — тиринг low/medium/high + human-gate D-006 + контракт main()."""
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


def _entity(root, sub, eid, **fields):
    d = os.path.join(root, sub)
    os.makedirs(d, exist_ok=True)
    lines = ["---", "id: %s" % eid]
    for k, v in fields.items():
        lines.append("%s: %s" % (k, v))
    lines += ["---", "", "тело %s" % eid, ""]
    with open(os.path.join(d, eid + ".md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def run():
    ok = True
    base = make_temp_dir("risk_gate_")
    os.environ["COLLAB_ROOT"] = base
    try:
        # фикстуры: задачи/решения с разными risk через front-matter (_canon)
        _entity(base, "tasks", "T-300", risk="low", status="todo")
        _entity(base, "tasks", "T-301", risk="medium", status="todo")
        _entity(base, "tasks", "T-302", risk="high", status="todo")
        _entity(base, "tasks", "T-303", status="todo")  # risk не указан
        _entity(base, "decisions", "D-006", risk="high", status="accepted")

        # проверим, что фикстуры действительно парсятся каноном (контракт фикстур)
        with open(os.path.join(base, "tasks", "T-302.md"), encoding="utf-8") as f:
            assert parse_front_matter(f.read()).get("risk") == "high"

        import risk_gate as rg
        assert rg.ROOT == base, (rg.ROOT, base)

        # find_entity ищет в tasks/decisions/questions
        assert rg.find_entity("T-300").get("risk") == "low"
        assert rg.find_entity("D-006").get("risk") == "high"
        assert rg.find_entity("T-404-нет") is None, "несуществующий → None"

        # КЛЮЧЕВОЕ: тиринг текст содержит правильный вердикт автономии
        assert rg.TIER["low"].startswith("AUTO"), rg.TIER["low"]
        assert rg.TIER["medium"].startswith("REVIEW"), rg.TIER["medium"]
        assert rg.TIER["high"].startswith("HUMAN"), rg.TIER["high"]
        # human-gate именно для high и отсылает к D-006
        assert "D-006" in rg.TIER["high"], "high → human-gate D-006"
        # пустой risk → REVIEW по умолчанию
        assert rg.TIER[""].startswith("REVIEW"), rg.TIER[""]

        def call(*argv):
            saved = sys.argv
            sys.argv = ["risk_gate.py", *argv]
            buf = io.StringIO()
            try:
                with redirect_stdout(buf):
                    rc = rg.main()
            finally:
                sys.argv = saved
            return rc, buf.getvalue()

        # low → AUTO в выводе
        rc, out = call("T-300")
        assert rc == 0 and "AUTO" in out and "risk=low" in out, out
        # medium → REVIEW
        rc, out = call("T-301")
        assert rc == 0 and "REVIEW" in out, out
        # high → HUMAN + D-006 (human-gate)
        rc, out = call("T-302")
        assert rc == 0 and "HUMAN" in out and "D-006" in out, out
        # risk не указан → дефолтный REVIEW
        rc, out = call("T-303")
        assert rc == 0 and "REVIEW" in out, out
        # D-006 как сущность (решение) тоже резолвится, тир high
        rc, out = call("D-006")
        assert rc == 0 and "HUMAN" in out, out
        # policy → печатает все три тира, rc 0
        rc, out = call("policy")
        assert rc == 0 and "AUTO" in out and "REVIEW" in out and "HUMAN" in out, out
        # несуществующий id → rc 1
        rc, out = call("T-999")
        assert rc == 1 and "ERROR" in out, out
        # нет аргументов → usage rc 2
        rc, out = call()
        assert rc == 2, out

        print("TESTS OK risk_gate: тиринг low→AUTO / medium→REVIEW / high→HUMAN(D-006) / пусто→REVIEW + find_entity + main rc(0/1/2)")
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
