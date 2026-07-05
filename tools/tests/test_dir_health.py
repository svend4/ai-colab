"""
# ==========================================
# [FILE ID CARD]
# ID: tools.tests.test_dir_health
# TYPE: active-script
# DOMAIN: core
# DEPTH_LEVEL: 1
# SUMMARY: Скрипт test_dir_health.py. Описание сгенерировано автоматически.
# ==========================================
"""
"""Тест dir_health.py — health-gate каталога. Пороги понижены + ROOT на temp (hermetic)."""
# --- бутстрап путей (C14, аудит 2026-07-02): тест живёт в tools/tests/, инструменты — в tools/.
# Вставка ДО локальных импортов, чтобы standalone-запуск работал из нового места.
import os as _os
import sys as _sys
_TOOLS_DIR = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
if _TOOLS_DIR not in _sys.path:
    _sys.path.insert(0, _TOOLS_DIR)
# --- конец бутстрапа ---

import os
import shutil
import subprocess
import sys
import time

os.environ.setdefault("PYTHONUTF8", "1")
HERE = _TOOLS_DIR  # tools/ — тест перенесён в tools/tests/ (C14)
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
        with open(os.path.join(root, d, "f%d.md" % i), "w", encoding="utf-8", newline="\n") as f:
            f.write("x" * size)


def main():
    fails = []

    root = make_temp_dir("dir_health_")
    orig_gitignored = dh._gitignored
    try:
        # понизить пороги для быстрого теста
        dh.ROOT = root
        dh.FILES_FAIL = 5
        dh.FILES_WARN = 3
        dh.FILE_KB_WARN = 1
        dh.ROOT_DIRS_WARN = 2
        # temp-каталог лежит в tmp-work/ (gitignored в основном репо) — заглушаем C55-c-исключение,
        # чтобы подтест порога размера остался герметичным; gitignore-ветка проверяется отдельно ниже
        dh._gitignored = lambda base, relpaths: set()

        _mkfiles(root, "big", 6)          # >5 -> FAIL files-per-dir
        _mkfiles(root, "medium", 4)       # >3,<=5 -> WARN files-per-dir
        _mkfiles(root, "small", 2)        # ок
        with open(os.path.join(root, "small", "huge.md"), "w", encoding="utf-8", newline="\n") as f:
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
        dh._gitignored = orig_gitignored
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

    # --- inbox-ttl (C30-b): свежий вход — тишина, старый — WARN, README.md — исключён ---
    root = make_temp_dir("dir_health_ttl_")
    try:
        dh.ROOT = root
        inbox = os.path.join(root, "queues", "inbox")
        os.makedirs(inbox)
        for name in ("README.md", "fresh.md", "old.md"):
            with open(os.path.join(inbox, name), "w", encoding="utf-8", newline="\n") as f:
                f.write("x")
        stale = time.time() - (dh.INBOX_TTL_WARN_DAYS + 3) * 86400
        os.utime(os.path.join(inbox, "old.md"), (stale, stale))
        os.utime(os.path.join(inbox, "README.md"), (stale, stale))   # README старый, но не вход
        ttl = {x["where"]: x["level"] for x in dh.scan() if x["kind"] == "inbox-ttl"}
        if ttl.get("queues/inbox/old.md") != "WARN":
            fails.append("inbox-ttl: старый вход (TTL+3д) не WARN")
        if "queues/inbox/fresh.md" in ttl:
            fails.append("inbox-ttl: свежий вход ложно флагнут")
        if "queues/inbox/README.md" in ttl:
            fails.append("inbox-ttl: README.md не должен считаться входом")
    finally:
        shutil.rmtree(root, ignore_errors=True)

    # --- file-size + gitignore (C55-c): gitignored сверх порога — тишина, tracked — WARN ---
    if shutil.which("git"):
        root = make_temp_dir("dir_health_gitignore_")
        try:
            dh.ROOT = root
            dh.FILE_KB_WARN = 1
            rc = subprocess.run(["git", "init", "-q", root], capture_output=True)
            if rc.returncode != 0:
                fails.append("gitignore: git init не отработал в temp-каталоге")
            else:
                with open(os.path.join(root, ".gitignore"), "w", encoding="utf-8", newline="\n") as f:
                    f.write("ignored.db\n")
                for name in ("ignored.db", "tracked.md"):
                    with open(os.path.join(root, name), "w", encoding="utf-8", newline="\n") as f:
                        f.write("z" * 2048)
                sizes = {x["where"] for x in dh.scan() if x["kind"] == "file-size"}
                if "ignored.db" in sizes:
                    fails.append("gitignore: gitignored-файл сверх порога ложно флагнут")
                if "tracked.md" not in sizes:
                    fails.append("gitignore: tracked-файл сверх порога не флагнут")
        finally:
            shutil.rmtree(root, ignore_errors=True)
    else:
        print("SKIP: git не найден — подтест gitignore-исключения пропущен")

    if fails:
        print("FAIL test_dir_health:")
        for x in fails:
            print("  -", x)
        sys.exit(1)
    print("OK test_dir_health: files-per-dir FAIL/WARN + file-size + root-dirs + CLI root + inbox-ttl + gitignore-искл.")


if __name__ == "__main__":
    main()