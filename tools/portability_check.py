"""
# ==========================================
# [FILE ID CARD]
# ID: tools.portability_check
# TYPE: active-script
# DOMAIN: core
# DEPTH_LEVEL: 1
# SUMMARY: Скрипт portability_check.py. Описание сгенерировано автоматически.
# ==========================================
"""
"""portability_check.py — acceptance-тест портабельности (Q-022 ФУНД-E).

Доказывает clone-and-run ИЛИ находит хост-зависимости. Копирует канон+инструменты в ЧИСТЫЙ temp,
запускает validate + generate --check ОТТУДА (ROOT вычисляется из нового __file__, не из исходного
места), плюс ищет хардкод абсолютных хост-путей в tools/. Если зелено и без хардкода — рабочая папка
переносима. Закрывает последний фунд-вопрос ниже 50%.

CLI:
    python tools/portability_check.py            # прогон (exit 1 если не портабельно)
    python tools/portability_check.py --json
"""
import os
import re
import sys
import json
import shutil
import tempfile
import subprocess

os.environ.setdefault("PYTHONUTF8", "1")
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from _ioutil import configure_output

configure_output()

# что НЕ копировать (volatile/тяжёлое/хост-специфичное)
IGNORE = shutil.ignore_patterns(".git", "logs", "data", "tmp-work", "__pycache__",
                                "node_modules", "external", ".idea", "*.pyc", "*.db")
# хардкод хост-путей (красный флаг портабельности) — исключаем себя
HOST_RE = re.compile(r"""['"](?:[A-Za-z]:[\\/]Users|/home/|/Users/)[^'"]*['"]""")


def _run(pyfile, args, cwd):
    env = dict(os.environ, PYTHONUTF8="1")
    try:
        p = subprocess.run([sys.executable, pyfile] + args, cwd=cwd, env=env,
                           capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=180)
        tail = "\n".join(((p.stdout or "") + (p.stderr or "")).strip().splitlines()[-2:])
        return p.returncode, tail
    except subprocess.TimeoutExpired:
        return 124, "(timeout)"


def scan_hardcoded():
    """Хардкод хост-путей в tools/*.py (кроме этого файла + комментариев-примеров)."""
    hits = []
    import glob
    for p in glob.glob(os.path.join(HERE, "*.py")):
        if os.path.basename(p) == "portability_check.py":
            continue
        try:
            with open(p, encoding="utf-8", errors="replace") as f:
                for i, line in enumerate(f, 1):
                    if line.lstrip().startswith("#"):
                        continue
                    if HOST_RE.search(line):
                        hits.append("%s:%d" % (os.path.relpath(p, ROOT).replace("\\", "/"), i))
        except OSError:
            pass
    return hits


def check():
    result = {"hardcoded_paths": scan_hardcoded(), "runs": []}
    tmp = tempfile.mkdtemp(prefix="portability_")
    dest = os.path.join(tmp, "repo")
    try:
        shutil.copytree(ROOT, dest, ignore=IGNORE, symlinks=False)
        # запустить ключевые тулы ИЗ КОПИИ (ROOT вычислится = dest)
        for name, args in (("validate.py", []), ("generate.py", ["--check"])):
            rc, tail = _run(os.path.join(dest, "tools", name), args, dest)
            result["runs"].append({"tool": name, "rc": rc, "tail": tail})
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    # validate должен пройти (rc 0); generate --check может быть STALE (rc!=0) — это НЕ хост-зависимость,
    # а просто несвежий индекс в копии; портабельность ломает только импорт-ошибка/абс-путь.
    val = next((r for r in result["runs"] if r["tool"] == "validate.py"), {})
    import_broken = any("Error" in (r.get("tail") or "") and "Traceback" in (r.get("tail") or "")
                        for r in result["runs"])
    result["portable"] = (val.get("rc") == 0) and not result["hardcoded_paths"] and not import_broken
    return result


def main(argv):
    as_json = "--json" in argv
    r = check()
    if as_json:
        print(json.dumps(r, ensure_ascii=False, indent=2))
        return 0 if r["portable"] else 1
    print("=== PORTABILITY ACCEPTANCE (Q-022 ФУНД-E) ===")
    print("  Копия → чистый temp, прогон validate/generate ОТТУДА:")
    for run in r["runs"]:
        print("    %-14s rc=%s  %s" % (run["tool"], run["rc"], (run["tail"] or "").replace("\n", " ")[:70]))
    if r["hardcoded_paths"]:
        print("  ⚠ хардкод хост-путей: %s" % ", ".join(r["hardcoded_paths"][:10]))
    else:
        print("  ✓ хардкода хост-путей в tools/ нет")
    print("\n  ВЕРДИКТ: %s" % ("ПОРТАБЕЛЬНО (clone-and-run работает)" if r["portable"]
                               else "НЕ ПОРТАБЕЛЬНО — см. выше"))
    return 0 if r["portable"] else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
