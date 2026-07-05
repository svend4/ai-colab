"""
# ==========================================
# [FILE ID CARD]
# ID: tools.tests.test_folder_index
# TYPE: active-script
# DOMAIN: core
# DEPTH_LEVEL: 1
# SUMMARY: Скрипт test_folder_index.py. Описание сгенерировано автоматически.
# ==========================================
"""
"""Тест folder_index.py — папка-индекс из визиток (build/write/check, навигация-не-шардинг)."""
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
        open(os.path.join(d, "a.md"), "w", encoding="utf-8", newline="\n").write(A)
        open(os.path.join(d, "b.md"), "w", encoding="utf-8", newline="\n").write(B)

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
        open(os.path.join(d, "a.md"), "w", encoding="utf-8", newline="\n").write(A.replace("суть А", "суть НОВАЯ"))
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
