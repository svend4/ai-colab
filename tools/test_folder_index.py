"""
# ==========================================
# [FILE ID CARD]
# ID: tools.test_folder_index
# TYPE: active-script
# DOMAIN: core
# DEPTH_LEVEL: 1
# SUMMARY: Скрипт test_folder_index.py. Описание сгенерировано автоматически.
# ==========================================
"""
"""Тест folder_index.py — папка-индекс из визиток (build/write/check, навигация-не-шардинг)."""
import os
import sys
import tempfile

os.environ.setdefault("PYTHONUTF8", "1")
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import folder_index as fi

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

A = "---\nid: A-1\ntype: task\nstatus: done\ngist: суть А\n---\nтело\n"
B = "---\nid: B-2\ntype: task\nstatus: todo\ngist: суть Б\n---\nтело\n"


def main():
    fails = []
    with tempfile.TemporaryDirectory() as root:
        fi.ROOT = root
        fi.INDEXES = os.path.join(root, "indexes")
        d = os.path.join(root, "myfolder")
        os.makedirs(os.path.join(d, "sub"))
        open(os.path.join(d, "a.md"), "w", encoding="utf-8").write(A)
        open(os.path.join(d, "b.md"), "w", encoding="utf-8").write(B)

        content = fi.build(d)
        for n in ("a.md", "b.md", "суть А", "суть Б", "Подпапки", "sub", "227" if False else "2 файлов"):
            if n not in content:
                fails.append("build без %r" % n)

        if fi.write("myfolder") != 0:
            fails.append("write вернул не 0")
        if not os.path.isfile(os.path.join(fi.INDEXES, "myfolder.md")):
            fails.append("indexes/myfolder.md не создан")
        if fi.check("myfolder") != 0:
            fails.append("check сразу после write не OK (не идемпотентен)")

        # изменить файл → check STALE
        open(os.path.join(d, "a.md"), "w", encoding="utf-8").write(A.replace("суть А", "суть НОВАЯ"))
        if fi.check("myfolder") == 0:
            fails.append("check после правки не поймал STALE")

    if fails:
        print("FAIL test_folder_index:")
        for f in fails:
            print("  -", f)
        sys.exit(1)
    print("OK test_folder_index: build(визитки+подпапки) + write + check(идемпотент+STALE)")


if __name__ == "__main__":
    main()
