"""Тест git_reconcile.py — merge-driver интерфейс (base/ours/theirs → field-merge в ours, exit-код)."""
import os
import sys
import tempfile

os.environ.setdefault("PYTHONUTF8", "1")
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import git_reconcile as gr

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass


def _w(d, name, related, status, body):
    p = os.path.join(d, name)
    open(p, "w", encoding="utf-8", newline="\n").write(
        "---\nid: x\nstatus: %s\nrelated: [%s]\n---\n%s\n" % (status, ", ".join(related), body))
    return p


def main():
    fails = []
    with tempfile.TemporaryDirectory() as d:
        # чистый случай: ours добавил c, theirs добавил d, тело тронул только theirs
        base = _w(d, "base.md", ["a", "b"], "proposed", "базовое тело")
        ours = _w(d, "ours.md", ["a", "b", "c"], "accepted", "базовое тело")
        theirs = _w(d, "theirs.md", ["a", "b", "d"], "proposed", "тело theirs")
        conflicts = gr.reconcile_files(base, ours, theirs)
        if conflicts:
            fails.append("чистый случай не должен дать конфликтов: %s" % conflicts)
        merged = open(ours, encoding="utf-8").read()
        if not ("c" in merged and "d" in merged):
            fails.append("related должно слиться union {a,b,c,d} в ours: %s" % merged[:80])
        if "accepted" not in merged:
            fails.append("status accepted (ours) должен сохраниться")
        if "тело theirs" not in merged:
            fails.append("тело theirs (только theirs тронул) должно попасть")
        if gr.main([base, ours, theirs]) != 0:
            fails.append("exit-код чистого слияния должен быть 0")

        # конфликт тела: оба тронули по-разному → exit 1 + маркеры
        base2 = _w(d, "b2.md", ["a"], "proposed", "база")
        o2 = _w(d, "o2.md", ["a"], "proposed", "версия ours")
        t2 = _w(d, "t2.md", ["a"], "proposed", "версия theirs")
        rc = gr.main([base2, o2, t2])
        if rc != 1:
            fails.append("конфликт тела должен дать exit 1: %s" % rc)
        m2 = open(o2, encoding="utf-8").read()
        if "версия ours" not in m2 or "версия theirs" not in m2 or "<<<<<<<" not in m2:
            fails.append("обе версии тела + маркеры должны быть в ours (не потеряно): %s" % m2[:90])

    if fails:
        print("FAIL test_git_reconcile:")
        for f in fails:
            print("  -", f)
        sys.exit(1)
    print("OK test_git_reconcile: чистый field-merge→exit0 · related-union · конфликт-тела→exit1+маркеры(без потерь)")


if __name__ == "__main__":
    main()
