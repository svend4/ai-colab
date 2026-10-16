#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ==========================================
# [FILE ID CARD]
# ID: tools.tests.test_question_tree
# TYPE: active-script
# DOMAIN: core.reflection
# DEPTH_LEVEL: 1
# SUMMARY: Tests for read-only numbered question tree extractor.
# ==========================================
# --- бутстрап путей (C14, аудит 2026-07-02): тест живёт в tools/tests/, инструменты — в tools/.
# Вставка ДО локальных импортов, чтобы standalone-запуск работал из нового места.
import os as _os
import sys as _sys
_TOOLS_DIR = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
if _TOOLS_DIR not in _sys.path:
    _sys.path.insert(0, _TOOLS_DIR)
# --- конец бутстрапа ---

import io
import json
import os
import shutil
import sys
from contextlib import redirect_stdout

HERE = _TOOLS_DIR  # tools/ — тест перенесён в tools/tests/ (C14)
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import question_tree as qt


def prepare_root():
    candidates = [
        os.path.join(ROOT, "tmp-work", "question_tree_test_runtime"),
    ]
    if os.name == "nt":  # C:\tmp только на Windows; на Linux это относительный путь в cwd
        candidates.insert(0, os.path.join(r"C:\tmp", "ai_colab_question_tree_test"))
    last_error = None
    for root in candidates:
        try:
            shutil.rmtree(root, ignore_errors=True)
            os.makedirs(root, exist_ok=True)
            probe = os.path.join(root, ".probe")
            with open(probe, "w", encoding="utf-8", newline="\n") as f:
                f.write("ok")
            os.remove(probe)
            return root
        except OSError as exc:
            last_error = exc
    raise RuntimeError("no writable question_tree test root: %r" % (last_error,))


def run():
    tmp = prepare_root()
    old_root = qt.ROOT
    try:
        text = '''# Demo

## 1. Block

**Вопрос 1.1.1.** Первый вопрос?

**Ответ:** Уже есть частичный ответ.

**Статус:** частично решено.

**Вопрос 1.1.2.** Второй вопрос?

**Ответ:** Нет ответа.

**Статус:** открыто.

**Вопрос 1.1.3.** Третий вопрос?

**Статус:** requires decision.
'''
        path = os.path.join(tmp, "q.md")
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write(text)
        qt.ROOT = tmp
        data = qt.analyze(path)
        assert data["schema"] == "question_tree.v1", data
        assert data["counts"]["questions"] == 3, data
        assert data["counts"]["by_category"]["partial"] == 1, data
        assert data["counts"]["by_category"]["open"] == 1, data
        assert data["counts"]["by_category"]["requires-decision"] == 1, data
        out = qt.text_report(data, category="open")
        assert "Второй вопрос" in out and "Первый вопрос" not in out, out
        plan = qt.build_action_plan(data)
        assert plan["schema"] == "question_tree.action_plan.v1", plan
        assert plan["recommended_sequence"][:2] == ["requires-decision", "open"], plan
        plan_text = qt.action_plan_report(plan)
        assert "QUESTION TREE ACTION PLAN" in plan_text and "decision-lane" in plan_text, plan_text
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = qt.main([path, "--json"])
        payload = json.loads(buf.getvalue())
        assert code == 0, code
        assert payload["counts"]["questions"] == 3, payload
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = qt.main([path, "--action-plan", "--json"])
        plan_payload = json.loads(buf.getvalue())
        assert code == 0, code
        assert plan_payload["schema"] == "question_tree.action_plan.v1", plan_payload
        print("OK test_question_tree: parse/status/json/text/action-plan")
        return 0
    finally:
        qt.ROOT = old_root
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(run())