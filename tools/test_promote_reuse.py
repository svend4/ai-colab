"""
# ==========================================
# [FILE ID CARD]
# ID: tools.test_promote_reuse
# TYPE: active-script
# DOMAIN: core
# DEPTH_LEVEL: 1
# SUMMARY: Скрипт test_promote_reuse.py. Описание сгенерировано автоматически.
# ==========================================
"""
"""Тест derive_reuse + _gate_L2_L1 (promote.py): scan-derived переиспользование L1→L2.

Проверяет two-channel grounding (Q-016/pyramid): гейт L2→L1 теперь считает РАЗНЫЕ порталы,
реально ссылающиеся на артефакт (derive_reuse-скан), а не самодекларацию `reused_in`.
Hermetic: строит временную пирамиду (--root), реальный канон не трогает.
"""
import os
import sys
import shutil

os.environ.setdefault("PYTHONUTF8", "1")
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, "drivers"))
import promote
from test_tmp import make_temp_dir

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

MANIFEST = """---
id: core-engine-manifest
type: core-export-manifest
level: L1
files: [tools/aa.py, tools/bb.py]
candidates: [tools/cc.py]
---
inventory
"""

def _portal(pid, basis_tokens, body=""):
    toks = ", ".join(basis_tokens)
    return f"""---
id: {pid}
type: portal
level: L2
l1_basis: [{toks}]
corpus_ref: data/x
---
{body}
"""


def _build(root):
    os.makedirs(os.path.join(root, "core"))
    with open(os.path.join(root, "core", "engine-manifest.md"), "w", encoding="utf-8") as f:
        f.write(MANIFEST)
    # два портала ссылаются на aa.py, один — на bb.py
    for pid, basis in [("portal-p1", ["tools/aa.py"]),
                       ("portal-p2", ["tools/aa.py"]),
                       ("portal-p3", ["tools/bb.py"])]:
        d = os.path.join(root, "portals", pid)
        os.makedirs(d)
        with open(os.path.join(d, "portal.md"), "w", encoding="utf-8") as f:
            f.write(_portal(pid, basis))


def main():
    fails = []
    root = make_temp_dir("promote_reuse_")
    try:
        _build(root)
        reuse = promote.derive_reuse(root)

        # aa.py переиспользуется ДВУМЯ порталами (derived, не задекларировано)
        aa = reuse.get("aa.py", set())
        if aa != {"portal-p1", "portal-p2"}:
            fails.append(f"aa.py reuse ожид {{p1,p2}}, факт {sorted(aa)}")
        # bb.py — одним
        bb = reuse.get("bb.py", set())
        if bb != {"portal-p3"}:
            fails.append(f"bb.py reuse ожид {{p3}}, факт {sorted(bb)}")
        # cc.py — кандидат, теперь входит в L1-инвентарь (candidates включены, D-022/P12)
        if "cc.py" not in reuse:
            fails.append("cc.py должен быть в инвентаре (candidates включены)")
        if reuse.get("cc.py"):
            fails.append("cc.py reuse должен быть пустым (нет порталов, ссылающихся)")

        # gate: aa.py проходит reuse_across_portals (>=2 портала)
        gate_aa = dict((n, ok) for n, ok, _ in
                       promote._gate_L2_L1(os.path.join(root, "tools", "aa.py"), {}, root))
        if not gate_aa.get("reuse_across_portals"):
            fails.append("aa.py: reuse_across_portals должен пройти (2 портала)")
        # bb.py: один портал → НЕ проходит без decision-ref
        gate_bb = dict((n, ok) for n, ok, _ in
                       promote._gate_L2_L1(os.path.join(root, "tools", "bb.py"), {}, root))
        if gate_bb.get("reuse_across_portals"):
            fails.append("bb.py: reuse_across_portals не должен пройти (1 портал, нет decision-ref)")
        # bb.py + decision-ref override → проходит
        gate_bb2 = dict((n, ok) for n, ok, _ in
                        promote._gate_L2_L1(os.path.join(root, "tools", "bb.py"),
                                            {"decision_ref": "D-016"}, root))
        if not gate_bb2.get("reuse_across_portals"):
            fails.append("bb.py + decision-ref: reuse_across_portals должен пройти (override)")
    finally:
        shutil.rmtree(root, ignore_errors=True)

    if fails:
        print("FAIL test_promote_reuse:")
        for f in fails:
            print("  -", f)
        sys.exit(1)
    print("OK test_promote_reuse: derive_reuse + gate L2->L1 (scan-derived) — 5 проверок")


if __name__ == "__main__":
    main()
