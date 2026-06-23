#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Тест cohort (tools/cohort.py) — вершинная панель параллельной работы + самохостинг.

Read-only против реального репо; проверяет: board/self/plan дают валидный --json;
side-effect команды (turn/ship) БЕЗ --run только печатают план (ничего не меняют)."""
import os
import sys
import json
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)


def configure_output():
    for name in ("stdout", "stderr"):
        s = getattr(sys, name, None)
        if s is not None and hasattr(s, "reconfigure"):
            s.reconfigure(encoding="utf-8", errors="replace")


configure_output()


def _run(*args):
    p = subprocess.run([sys.executable, os.path.join(HERE, "cohort.py"), *args],
                       cwd=ROOT, capture_output=True, text=True,
                       encoding="utf-8", errors="replace", stdin=subprocess.DEVNULL)
    return p.returncode, (p.stdout or "") + (p.stderr or "")


def run():
    ok = True
    try:
        # board --json: валидный JSON с ключами котла
        _, out = _run("board", "--json")
        d = json.loads(out)
        for k in ("in_work", "ready", "blocked", "active_claims", "drift"):
            assert k in d, "board json без %r" % k

        # self --json: список проверок + backlog
        _, out = _run("self", "--json")
        d = json.loads(out)
        assert "checks" in d and isinstance(d["checks"], list) and d["checks"], "self checks"
        assert "todo" in d, "self todo"

        # plan --json: раздача по агентам
        _, out = _run("plan", "3", "--json")
        d = json.loads(out)
        assert "assignment" in d and isinstance(d["assignment"], dict), "plan assignment"

        # guard --json: триггеры Уровня-1
        _, out = _run("guard", "--json")
        d = json.loads(out)
        assert "level1_recommended" in d and "triggers" in d, "guard json без триггеров"
        assert isinstance(d["triggers"], list), "guard triggers должен быть списком"

        # guard --strict --json: surfaces strict/blocked/mandatory keys; на чистом репо НЕ блокирует
        _, out = _run("guard", "--json", "--strict")
        d = json.loads(out)
        for k in ("strict", "blocked", "mandatory"):
            assert k in d, "guard --strict json без %r" % k
        assert d["strict"] is True, "guard --strict должен ставить strict=true"
        # на репо без обязательных триггеров blocked=false и rc=0 (default-safe инвариант)
        rc, _ = _run("guard", "--strict")
        if not d["mandatory"]:
            assert rc == 0, "guard --strict без обязательных триггеров не должен блокировать"

        # turn БЕЗ --run: только печать плана, ничего не делает
        _, out = _run("turn", "claude")
        assert "печать" in out, "turn должен быть dry без --run"

        # ship БЕЗ --run: dry-план включает commit_lock + selective-add + regenerate
        _, out = _run("ship", "claude", "tools/cohort.py")
        assert "печать" in out, "ship должен быть dry без --run"
        assert "generate" in out, "ship-план должен включать regenerate (чтобы hook не падал)"
        # ship --message не утекает в список файлов (dry)
        _, out = _run("ship", "claude", "tools/cohort.py", "--message", "test msg")
        assert "печать" in out and "test msg" in out, "ship --message должен попасть в план коммита"
        # ship без файлов — подсказка
        _, out = _run("ship", "claude")
        assert "укажи файлы" in out, "ship без файлов — подсказка"

        # ship --strict без файлов всё ещё даёт подсказку (флаг не ломает empty-guard)
        _, out = _run("ship", "claude", "--strict")
        assert "укажи файлы" in out, "ship --strict без файлов — подсказка"
        # ship --strict не блокирует на ЧИСТОМ пути (не foreign, не same-file) — dry-план печатается
        rc, out = _run("ship", "claude", "tools/cohort.py", "--strict")
        # либо обычный dry-план (rc 0), либо ОТКАЗ если tools/cohort.py реально foreign/same-file в этот момент
        assert ("печать" in out) or ("ОТКАЗ" in out), "ship --strict: либо план, либо явный отказ"

        print("TESTS OK cohort: board/self/plan --json валидны; turn/ship dry-by-default")
    except (AssertionError, ValueError) as e:
        ok = False
        print("TEST FAIL:", e)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(run())
