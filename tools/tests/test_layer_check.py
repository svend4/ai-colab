"""
# ==========================================
# [FILE ID CARD]
# ID: tools.tests.test_layer_check
# TYPE: active-script
# DOMAIN: core
# DEPTH_LEVEL: 1
# SUMMARY: Скрипт test_layer_check.py. Описание сгенерировано автоматически.
# ==========================================
"""
"""Тест layer_check.py — контракт пирамиды (portal/core/sandbox/level) на temp-пирамиде."""
# --- бутстрап путей (C14, аудит 2026-07-02): тест живёт в tools/tests/, инструменты — в tools/.
# Вставка ДО локальных импортов, чтобы standalone-запуск работал из нового места.
import os as _os
import sys as _sys
_TOOLS_DIR = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
if _TOOLS_DIR not in _sys.path:
    _sys.path.insert(0, _TOOLS_DIR)
# --- конец бутстрапа ---

import os
import sys
import tempfile

os.environ.setdefault("PYTHONUTF8", "1")
HERE = _TOOLS_DIR  # tools/ — тест перенесён в tools/tests/ (C14)
sys.path.insert(0, HERE)
import layer_check as lc

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass


def _w(root, rel, txt):
    p = os.path.join(root, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8", newline="\n") as f:
        f.write(txt)


def main():
    fails = []
    with tempfile.TemporaryDirectory() as root:
        lc.ROOT = root
        # хороший портал
        _w(root, "portals/good/portal.md", "---\nid: portal-good\nlevel: L2\nl1_basis: [tools/x.py]\n---\nok\n")
        # плохой портал (нет portal.md)
        _w(root, "portals/bad/current-state.md", "no portal.md\n")
        # core-манифест есть
        _w(root, "core/engine-manifest.md", "---\nid: m\n---\nmanifest\n")
        # topic с level:L2 (mismatch, физически L3)
        _w(root, "topics/x.md", "---\nid: x\nlevel: L2\n---\nтело\n")
        # sandbox с mode:execute (FAIL D-014)
        _w(root, "sandbox/bad.md", "---\nid: s\nmode: execute\n---\nopasno\n")

        f = lc.check()
        kinds = {(x["kind"], x["level"]) for x in x_iter(f)}
        wheres = {x["where"]: x for x in f}

        if not any(x["kind"] == "portal-contract" and x["level"] == "FAIL"
                   and "bad" in x["where"] for x in f):
            fails.append("плохой портал (нет portal.md) не FAIL")
        if any(x["kind"] == "portal-contract" and x["level"] == "FAIL"
               and "good" in x["where"] for x in f):
            fails.append("хороший портал ложно FAIL")
        if not any(x["kind"] == "sandbox-readonly" and x["level"] == "FAIL" for x in f):
            fails.append("sandbox mode:execute не FAIL (D-014)")
        if not any(x["kind"] == "level-mismatch" for x in f):
            fails.append("level-mismatch (topic L2) не WARN")
        # core есть → нет core-contract FAIL
        if any(x["kind"] == "core-contract" for x in f):
            fails.append("core-contract ложно (манифест есть)")
        _ = (kinds, wheres)

    if fails:
        print("FAIL test_layer_check:")
        for x in fails:
            print("  -", x)
        sys.exit(1)
    print("OK test_layer_check: portal-contract + sandbox-readonly + level-mismatch + core-contract")


def x_iter(f):
    return f


if __name__ == "__main__":
    main()
