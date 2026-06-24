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
import sys
import tempfile

os.environ.setdefault("PYTHONUTF8", "1")
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import dir_health as dh

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass


def main():
    fails = []
    with tempfile.TemporaryDirectory() as root:
        # понизить пороги для быстрого теста
        dh.ROOT = root
        dh.FILES_FAIL = 5
        dh.FILES_WARN = 3
        dh.FILE_KB_WARN = 1
        dh.ROOT_DIRS_WARN = 2

        def mkfiles(d, n, size=0):
            os.makedirs(os.path.join(root, d), exist_ok=True)
            for i in range(n):
                with open(os.path.join(root, d, "f%d.md" % i), "w", encoding="utf-8") as f:
                    f.write("x" * size)

        mkfiles("big", 6)          # >5 → FAIL files-per-dir
        mkfiles("medium", 4)       # >3,<=5 → WARN files-per-dir
        mkfiles("small", 2)        # ок
        # большой файл (>1КБ)
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
        # root-dirs: 3 папки (big/medium/small) > порог 2 → WARN
        if not any(x["kind"] == "root-dirs" for x in f):
            fails.append("root-dirs (3>2) не флагнут")

    if fails:
        print("FAIL test_dir_health:")
        for x in fails:
            print("  -", x)
        sys.exit(1)
    print("OK test_dir_health: files-per-dir FAIL/WARN + file-size + root-dirs (пороги как код)")


if __name__ == "__main__":
    main()
