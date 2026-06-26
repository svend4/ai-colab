#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ==========================================
# [FILE ID CARD]
# ID: tools.portability_check
# TYPE: active-script
# DOMAIN: core.portability
# DEPTH_LEVEL: 1
# SUMMARY: Acceptance-тест переносимости: materialize git-tracked HEAD и проверить validate/generate без host paths.
# ==========================================
HELP = """portability_check.py — acceptance-тест портабельности (Q-022 ФУНД-E).

Доказывает clone-and-run ИЛИ находит хост-зависимости. Материализует РОВНО git-tracked дерево HEAD
(`git archive` — точная модель свежего clone: без untracked, без gitignored, без логов/кэшей) в чистый
temp, запускает validate + generate --check ОТТУДА (ROOT вычисляется из нового __file__), плюс ищет
хардкод абсолютных хост-путей в tools/. Зелено + без хардкода → рабочая папка переносима.
Закрывает последний фунд-вопрос ниже 50%.

CLI:
    python tools/portability_check.py            # прогон (exit 1 если не портабельно)
    python tools/portability_check.py --json
"""
import os
import re
import sys
import json
import shutil
import zipfile
import tempfile
import subprocess

os.environ.setdefault("PYTHONUTF8", "1")
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from _ioutil import configure_output
from _cli import help_guard

configure_output()

# fallback-IGNORE (если git недоступен) — менее точная модель
IGNORE = shutil.ignore_patterns(".git", "logs", "data", "tmp-work", "__pycache__",
                                "node_modules", "external", ".idea", "*.pyc", "*.db")
HOST_RE = re.compile(r"""['"](?:[A-Za-z]:[\\/]Users|/home/|/Users/)[^'"]*['"]""")


def _run(pyfile, args, cwd):
    env = dict(os.environ, PYTHONUTF8="1")
    try:
        p = subprocess.run([sys.executable, pyfile] + args, cwd=cwd, env=env,
                           capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=180)
        return p.returncode, (p.stdout or "") + (p.stderr or "")
    except subprocess.TimeoutExpired:
        return 124, "(timeout)"


def _tail(text, n=2):
    return "\n".join(text.strip().splitlines()[-n:])


def _errors(text):
    """Строки-ошибки из вывода validate (для отчёта о конкретных хост-зависимостях)."""
    return [ln.strip() for ln in text.splitlines()
            if ln.strip().startswith("ERROR") or "✗" in ln]


def scan_hardcoded():
    """Хардкод хост-путей в tools/*.py (кроме этого файла + комментариев)."""
    hits = []
    import glob
    for p in glob.glob(os.path.join(HERE, "*.py")):
        b = os.path.basename(p)
        if b == "portability_check.py" or b.startswith("test_"):
            continue  # себя + тесты (host-пути там — фикстуры, не runtime-зависимости)
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


def _materialize_tracked(dest):
    """Ровно git-tracked дерево HEAD → dest (истинный clone). None при отсутствии git."""
    zpath = dest + ".zip"
    try:
        p = subprocess.run(["git", "archive", "--format=zip", "-o", zpath, "HEAD"],
                           cwd=ROOT, capture_output=True, text=True)
    except (OSError, subprocess.SubprocessError):
        return None
    if p.returncode != 0 or not os.path.exists(zpath):
        return None
    os.makedirs(dest, exist_ok=True)
    with zipfile.ZipFile(zpath) as z:
        z.extractall(dest)
    os.remove(zpath)
    return dest


# документированный bootstrap свежего clone (как `npm install`): воссоздать генерируемые снимки
BOOTSTRAP = [("pipeline.py", ["snapshot"])]


def check():
    result = {"hardcoded_paths": scan_hardcoded(), "method": "git-archive-HEAD",
              "raw_rc": None, "raw_findings": [], "bootstrap_needed": False, "runs": []}
    tmp = tempfile.mkdtemp(prefix="portability_")
    dest = os.path.join(tmp, "repo")
    try:
        if _materialize_tracked(dest) is None:
            result["method"] = "copytree-fallback"
            shutil.copytree(ROOT, dest, ignore=IGNORE, symlinks=False)
        # 1) сырой clone — что видит наивный clone-and-run ДО setup
        raw_rc, raw_out = _run(os.path.join(dest, "tools", "validate.py"), [], dest)
        result["raw_rc"] = raw_rc
        result["raw_findings"] = _errors(raw_out)
        result["bootstrap_needed"] = raw_rc != 0
        # 2) документированный bootstrap (воссоздать генерируемые снимки)
        for name, args in BOOTSTRAP:
            _run(os.path.join(dest, "tools", name), args, dest)
        # 3) после bootstrap — истинный вердикт переносимости
        for name, args in (("validate.py", []), ("generate.py", ["--check"])):
            rc, out = _run(os.path.join(dest, "tools", name), args, dest)
            result["runs"].append({"tool": name, "rc": rc, "tail": _tail(out),
                                   "findings": _errors(out) if name == "validate.py" else []})
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    val = next((r for r in result["runs"] if r["tool"] == "validate.py"), {})
    result["portable"] = (val.get("rc") == 0) and not result["hardcoded_paths"]
    return result


def main(argv):
    help_guard(HELP, argv)
    as_json = "--json" in argv
    r = check()
    if as_json:
        print(json.dumps(r, ensure_ascii=False, indent=2))
        return 0 if r["portable"] else 1
    print("=== PORTABILITY ACCEPTANCE (Q-022 ФУНД-E) ===")
    print("  Модель: %s (свежий clone: только tracked, без untracked/gitignored)" % r["method"])
    print("  1) Сырой clone (ДО setup): validate rc=%s%s" % (
        r["raw_rc"], "  → нужен bootstrap" if r["bootstrap_needed"] else ""))
    for f in r["raw_findings"][:10]:
        print("       • %s" % f)
    if r["bootstrap_needed"]:
        print("  2) Bootstrap: %s" % "; ".join("python tools/%s %s" % (n, " ".join(a)) for n, a in BOOTSTRAP))
    print("  3) После bootstrap:")
    for run in r["runs"]:
        print("       %-14s rc=%s  %s" % (run["tool"], run["rc"], (run["tail"] or "").replace("\n", " ")[:60]))
        for f in run.get("findings", [])[:10]:
            print("         • %s" % f)
    print("  %s хардкода хост-путей в tools/" % ("⚠ есть: " + ", ".join(r["hardcoded_paths"][:8])
                                                 if r["hardcoded_paths"] else "✓ нет"))
    verdict = ("ПОРТАБЕЛЬНО — clone + bootstrap → чисто" if r["portable"] and r["bootstrap_needed"]
               else "ПОРТАБЕЛЬНО — clone-and-run сразу чисто" if r["portable"]
               else "НЕ ПОРТАБЕЛЬНО — остаются ошибки после bootstrap")
    print("\n  ВЕРДИКТ: %s" % verdict)
    return 0 if r["portable"] else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
