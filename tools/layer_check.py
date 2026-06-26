"""
# ==========================================
# [FILE ID CARD]
# ID: tools.layer_check
# TYPE: active-script
# DOMAIN: core
# DEPTH_LEVEL: 1
# SUMMARY: Скрипт layer_check.py. Описание сгенерировано автоматически.
# ==========================================
"""
"""layer_check.py — контракт пирамиды L1-L4 (lane A layered-pyramid) — folder/layer checks.

Из cauldron lane A «layered-pyramid» (9/10 docs): после ратификации L1/L2/L3/L4-контракта — машинные
folder/layer проверки. Верифицирует инварианты пирамиды (D-016): каждый портал несёт контракт,
core содержит манифест, sandbox остаётся read-only (D-014), а front-matter `level:` не противоречит
физическому слою. Дополняет dir_health (числа папок) проверкой СЛОЁВ.

CLI:
    python tools/layer_check.py            # отчёт (exit 1 если контракт нарушен)
    python tools/layer_check.py --json
"""
import os
import sys
import json
import glob

os.environ.setdefault("PYTHONUTF8", "1")
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from _ioutil import configure_output
from _cli import help_guard
from _canon import parse_front_matter

configure_output()

LAYER_BY_DIR = {"core": "L1", "portals": "L2", "sandbox": "L4"}
L3_DIRS = {"tasks", "decisions", "questions", "streams", "topics", "collab"}


def layer_of(rel):
    top = rel.replace("\\", "/").split("/", 1)[0]
    if top in LAYER_BY_DIR:
        return LAYER_BY_DIR[top]
    return "L3" if top in L3_DIRS else None


def _fm(path):
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            return parse_front_matter(f.read())
    except OSError:
        return {}


def check():
    f = []

    def add(level, kind, where, msg):
        f.append({"level": level, "kind": kind, "where": where, "msg": msg})

    # 1) портал-контракт: каждый portals/<id>/ несёт portal.md с id + level:L2 + l1_basis
    for pd in sorted(glob.glob(os.path.join(ROOT, "portals", "*"))):
        if not os.path.isdir(pd):
            continue
        pid = os.path.basename(pd)
        pm = os.path.join(pd, "portal.md")
        rel = "portals/%s" % pid
        if not os.path.isfile(pm):
            add("FAIL", "portal-contract", rel, "нет portal.md")
            continue
        fm = _fm(pm)
        if not fm.get("id"):
            add("FAIL", "portal-contract", rel + "/portal.md", "нет id во front-matter")
        if str(fm.get("level", "")).upper() != "L2":
            add("WARN", "portal-contract", rel + "/portal.md", "level != L2 (%s)" % fm.get("level"))
        if not fm.get("l1_basis"):
            add("WARN", "portal-contract", rel + "/portal.md", "нет l1_basis (опора на ядро)")

    # 2) core-контракт: есть engine-manifest.md
    if not os.path.isfile(os.path.join(ROOT, "core", "engine-manifest.md")):
        add("FAIL", "core-contract", "core/", "нет engine-manifest.md (L1-манифест)")

    # 3) sandbox read-only: ни один файл sandbox/ не несёт mode: execute (D-014)
    for p in glob.glob(os.path.join(ROOT, "sandbox", "**", "*.md"), recursive=True):
        fm = _fm(p)
        if str(fm.get("mode", "")).lower() == "execute":
            add("FAIL", "sandbox-readonly", os.path.relpath(p, ROOT).replace("\\", "/"),
                "mode: execute в sandbox без accepted-решения (D-014)")

    # 4) согласованность level: front-matter vs физический слой (advisory)
    for pat in ("topics/*.md", "docs/*.md", "core/*.md", "portals/*/*.md"):
        for p in glob.glob(os.path.join(ROOT, pat)):
            fm = _fm(p)
            declared = str(fm.get("level", "")).upper()
            if not declared:
                continue
            rel = os.path.relpath(p, ROOT).replace("\\", "/")
            phys = layer_of(rel)
            if phys and declared != phys:
                add("WARN", "level-mismatch", rel,
                    "front-matter level:%s, но физически %s (%s)" % (declared, phys, rel.split('/')[0]))
    return f


def main(argv):
    help_guard(__doc__, argv)
    as_json = "--json" in argv
    f = check()
    fails = [x for x in f if x["level"] == "FAIL"]
    warns = [x for x in f if x["level"] == "WARN"]
    if as_json:
        print(json.dumps({"fail": len(fails), "warn": len(warns), "findings": f},
                         ensure_ascii=False, indent=2))
        return 1 if fails else 0
    print("=== КОНТРАКТ ПИРАМИДЫ L1-L4 (lane A layered-pyramid) ===")
    print("  FAIL: %d   WARN: %d" % (len(fails), len(warns)))
    for x in fails + warns:
        print("  [%-4s] %-16s %-44s %s" % (x["level"], x["kind"], x["where"], x["msg"]))
    if not f:
        print("  OK: контракт пирамиды соблюдён (порталы/core/sandbox/level-согласованность)")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
