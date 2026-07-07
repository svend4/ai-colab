# ast: allow-subprocess
#!/usr/bin/env python3
# [FILE ID CARD]
# id: tools/tests/test_worktree_gate.py
# purpose: Тест Гейта A — вердикт SHARED-BUSY/ISOLATED/OK, hook_rc, счёт активных, ратификация.
# mode: test (временный ROOT в системном temp, git не вызывается — branch монкипатчится)
# related: tools/worktree_gate.py
"""Самопроверка worktree_gate: логика вердикта + условная строгость."""
import importlib.util
import os
import shutil
import tempfile
import time

_TOOLS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_spec = importlib.util.spec_from_file_location("worktree_gate",
                                               os.path.join(_TOOLS, "worktree_gate.py"))
wg = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(wg)


def _tmp_with_claims(n_fresh):
    d = tempfile.mkdtemp(prefix="worktree_gate_test_")
    cd = os.path.join(d, "queues", "claimed")
    os.makedirs(cd, exist_ok=True)
    for i in range(n_fresh):
        p = os.path.join(cd, "T-%03d.claim.md" % i)
        with open(p, "w", encoding="utf-8") as f:
            f.write("claim\n")
        os.utime(p, (time.time(), time.time()))   # свежий
    return d


def test_hook_rc_pure():
    # BLOCK (1) только SHARED-BUSY И ратифицировано; иначе 0
    assert wg.hook_rc("SHARED-BUSY", True) == 1
    assert wg.hook_rc("SHARED-BUSY", False) == 0   # не ратифицировано → advisory
    assert wg.hook_rc("ISOLATED", True) == 0
    assert wg.hook_rc("OK", True) == 0
    print("  OK: hook_rc — блок только SHARED-BUSY + ратифицировано")


def test_active_agents_count():
    d = _tmp_with_claims(4)
    try:
        assert wg.active_agents(d) == 4, "4 свежих claim → 4 активных"
        # протухший claim не считается
        p = os.path.join(d, "queues", "claimed", "T-999.claim.md")
        with open(p, "w", encoding="utf-8") as f:
            f.write("old\n")
        old = time.time() - wg.FRESH_CLAIM_SECONDS - 100
        os.utime(p, (old, old))
        assert wg.active_agents(d) == 4, "протухший claim не увеличивает счёт"
        print("  OK: счёт активных агентов (свежие claim'ы, протухшие игнорятся)")
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_evaluate_shared_busy():
    d = _tmp_with_claims(3)
    saved = wg.current_branch
    try:
        wg.current_branch = lambda: "main"          # монкипатч: на общей ветке
        v, br, n = wg.evaluate(d)
        assert v == "SHARED-BUSY" and n == 3, "main + 3 агента → SHARED-BUSY: %s" % ((v, br, n),)
        print("  OK: общий main + N≥3 → SHARED-BUSY")
    finally:
        wg.current_branch = saved
        shutil.rmtree(d, ignore_errors=True)


def test_evaluate_isolated():
    d = _tmp_with_claims(5)
    saved = wg.current_branch
    try:
        wg.current_branch = lambda: "agent/claude/T-273"   # в worktree-ветке
        v, br, n = wg.evaluate(d)
        assert v == "ISOLATED", "agent-ветка → ISOLATED даже при 5 агентах: %s" % ((v, br, n),)
        print("  OK: agent-ветка (worktree) → ISOLATED (не мешаем)")
    finally:
        wg.current_branch = saved
        shutil.rmtree(d, ignore_errors=True)


def test_readme_not_counted():
    # Регрессия (аудит 2026-07-07): README.md трекается в queues/claimed и на свежем
    # clone/worktree имеет свежий mtime; он НЕ должен считаться агентом — только *.claim.md.
    d = _tmp_with_claims(2)
    try:
        p = os.path.join(d, "queues", "claimed", "README.md")
        with open(p, "w", encoding="utf-8") as f:
            f.write("# очередь claimed\n")
        os.utime(p, (time.time(), time.time()))   # свежий, как на clone
        assert wg.active_agents(d) == 2, "README.md (не claim) не должен раздувать счёт"
        print("  OK: README.md (не *.claim.md) не считается агентом")
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_evaluate_low_concurrency_ok():
    d = _tmp_with_claims(1)
    saved = wg.current_branch
    try:
        wg.current_branch = lambda: "main"
        v, br, n = wg.evaluate(d)
        assert v == "OK", "main + 1 агент < порога → OK (не мешаем): %s" % ((v, br, n),)
        print("  OK: общий main + мало агентов → OK (соразмерность)")
    finally:
        wg.current_branch = saved
        shutil.rmtree(d, ignore_errors=True)


def run():
    test_hook_rc_pure()
    test_active_agents_count()
    test_readme_not_counted()
    test_evaluate_shared_busy()
    test_evaluate_isolated()
    test_evaluate_low_concurrency_ok()
    print("TESTS OK worktree_gate: hook_rc + счёт + README-excl + SHARED-BUSY + ISOLATED + соразмерность")


if __name__ == "__main__":
    run()
