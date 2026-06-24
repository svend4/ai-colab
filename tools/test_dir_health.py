"""
# ==========================================
# [FILE ID CARD]
# ID: tools.test_dir_health
# TYPE: active-script
# DOMAIN: core
# DEPTH_LEVEL: 1
# SUMMARY: Скрипт test_dir_health.py. Описание сгенерировано автоматически.
# ==========================================
"""
"""Тест dir_health.py — health-gate каталога. Пороги понижены + ROOT на temp (hermetic)."""
import os
import shutil
import sys

os.environ.setdefault("PYTHONUTF8", "1")
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "drivers"))
sys.path.insert(0, HERE)
from test_tmp import make_temp_dir
import dir_health as dh

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass


def _mkfiles(root, d, n, size=0):
    os.makedirs(os.path.join(root, d), exist_ok=True)
    for i in range(n):
        with open(os.path.join(root, d, "f%d.md" % i), "w", encoding="utf-8") as f:
            f.write("x" * size)


def main():
    fails = []

    root = make_temp_dir("dir_health_")
    try:
        # понизить пороги для быстрого теста
        dh.ROOT = root
        dh.FILES_FAIL = 5
        dh.FILES_WARN = 3
        dh.FILE_KB_WARN = 1
        dh.ROOT_DIRS_WARN = 2

        _mkfiles(root, "big", 6)          # >5 -> FAIL files-per-dir
        _mkfiles(root, "medium", 4)       # >3,<=5 -> WARN files-per-dir
        _mkfiles(root, "small", 2)        # ок
        with open(os.path.join(root, "small", "huge.md"), "w", encoding="utf-8") as f:
            f.write("y" * 2048)

        f = dh.scan()
        levels = {(x["kind"], x["where"]): x["level"] for x in f}
        if levels.get(("files-per-dir", "big")) != "FAIL":
            fails.append("big (6 файлов) не FAIL")
        if levels.get(("files-per-dir", "medium")) != "WARN":
            fails.append("medium (4 файла) не WARN")
        if ("files-per-dir", "small") in levels:
            fails.append("small (3 файла) ложно флагнут")
        if not any(x["kind"] == "file-size" and x["level"] == "WARN" for x in f):
            fails.append("большой файл (2КБ) не флагнут")
        if not any(x["kind"] == "root-dirs" for x in f):
            fails.append("root-dirs (3>2) не флагнут")
    finally:
        shutil.rmtree(root, ignore_errors=True)

    root = make_temp_dir("dir_health_cli_")
    try:
        custom_root = os.path.join(root, "custom")
        _mkfiles(custom_root, "many", 6)

        old_root = dh.ROOT
        dh.ROOT = os.path.join(root, "unused-default")
        try:
            findings = dh.scan(custom_root)
            if not any(x["kind"] == "files-per-dir" and x["where"] == "many" for x in findings):
                fails.append("scan(custom_root) не анализирует переданный root")
            rc = dh.main([custom_root, "--json"])
            if rc != 1:
                fails.append("main([custom_root, --json]) не использует CLI root / не вернул FAIL")
        finally:
            dh.ROOT = old_root
    finally:
        shutil.rmtree(root, ignore_errors=True)

    if fails:
        print("FAIL test_dir_health:")
        for x in fails:
            print("  -", x)
        sys.exit(1)
    print("OK test_dir_health: files-per-dir FAIL/WARN + file-size + root-dirs + CLI root")


if __name__ == "__main__":
    main()