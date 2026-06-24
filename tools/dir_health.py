"""
# ==========================================
# [FILE ID CARD]
# ID: tools.dir_health
# TYPE: active-script
# DOMAIN: core
# DEPTH_LEVEL: 1
# SUMMARY: Скрипт dir_health.py. Описание сгенерировано автоматически.
# ==========================================
"""
"""dir_health.py — health-gate каталога (C-10 консенсус) — пороги структуры как код.

Из architecture-fundamentals §3.2 + razbor-consensus C-10: организация каталога проверяется ЧИСЛАМИ,
как код (не на глаз). Пороги (консенсус 2+ агентов): файлов в папке >200 FAIL / >100 WARN (цель 7-50);
файл >50КБ WARN; index.json >200КБ WARN; корневых папок >15 WARN; глубина вложенности >3 WARN.
Флагует, где структура вышла за пределы машинной И человеческой навигации (напр. tasks/=222 → FAIL,
прямой повод для C-04 шардинга по диапазонам ID).

CLI:
    python tools/dir_health.py            # отчёт + пороги (exit 1 если есть FAIL)
    python tools/dir_health.py --json
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

configure_output()

FILES_FAIL = 200       # жёсткий потолок файлов в одной папке
FILES_WARN = 100       # мягкий потолок (цель 7-50)
FILE_KB_WARN = 50      # размер одного файла
INDEX_KB_WARN = 200    # центральный index.json
ROOT_DIRS_WARN = 15    # число корневых папок
DEPTH_WARN = 3         # глубина вложенности

SKIP = (".git", "data", "tmp-work", "__pycache__", "node_modules", ".idea", "external", "logs")


def _skip(rel):
    parts = [p for p in rel.replace("\\", "/").split("/") if p and p != "."]
    return any(p in SKIP or p.startswith(".") for p in parts)


def scan():
    findings = []
    # 1) файлов в каждой папке
    for dirpath, dirs, files in os.walk(ROOT):
        rel = os.path.relpath(dirpath, ROOT)
        if rel != "." and _skip(rel):
            dirs[:] = []
            continue
        dirs[:] = [d for d in dirs if not _skip(os.path.join(rel, d))]
        real = [f for f in files if not f.startswith(".")]
        n = len(real)
        relshow = "." if rel == "." else rel.replace("\\", "/")
        if n > FILES_FAIL:
            # navigation-vs-sharding: при наличии папка-индекса (indexes/<name>.md) это не FAIL —
            # навигация решена метаданными, шардинг не требуется (решение 2026-06-24).
            has_index = "/" not in relshow and os.path.isfile(
                os.path.join(ROOT, "indexes", relshow + ".md"))
            findings.append({"kind": "files-per-dir", "level": "WARN" if has_index else "FAIL",
                             "where": relshow + (" (есть папка-индекс)" if has_index else ""),
                             "value": n, "limit": FILES_FAIL})
        elif n > FILES_WARN:
            findings.append({"kind": "files-per-dir", "level": "WARN", "where": relshow,
                             "value": n, "limit": FILES_WARN})
        # 2) большие файлы
        for f in real:
            kb = os.path.getsize(os.path.join(dirpath, f)) // 1024
            if kb > FILE_KB_WARN:
                lvl = "WARN" if f != "index.json" else ("WARN" if kb <= INDEX_KB_WARN else "FAIL")
                lim = INDEX_KB_WARN if f == "index.json" else FILE_KB_WARN
                findings.append({"kind": "file-size", "level": lvl,
                                 "where": ("%s/%s" % (relshow, f)).lstrip("./"), "value": kb, "limit": lim})
    # 3) корневых папок
    root_dirs = [d for d in os.listdir(ROOT)
                 if os.path.isdir(os.path.join(ROOT, d)) and not _skip(d)]
    if len(root_dirs) > ROOT_DIRS_WARN:
        findings.append({"kind": "root-dirs", "level": "WARN", "where": ".",
                         "value": len(root_dirs), "limit": ROOT_DIRS_WARN})
    # 4) глубина
    maxdepth = 0
    for dirpath, dirs, _files in os.walk(ROOT):
        rel = os.path.relpath(dirpath, ROOT)
        if rel != "." and _skip(rel):
            dirs[:] = []
            continue
        depth = 0 if rel == "." else len(rel.replace("\\", "/").split("/"))
        maxdepth = max(maxdepth, depth)
    if maxdepth > DEPTH_WARN:
        findings.append({"kind": "depth", "level": "WARN", "where": ".",
                         "value": maxdepth, "limit": DEPTH_WARN})
    return findings


def main(argv):
    as_json = "--json" in argv
    f = scan()
    fails = [x for x in f if x["level"] == "FAIL"]
    warns = [x for x in f if x["level"] == "WARN"]
    if as_json:
        print(json.dumps({"fail": len(fails), "warn": len(warns), "findings": f},
                         ensure_ascii=False, indent=2))
        return 1 if fails else 0
    print("=== HEALTH-GATE КАТАЛОГА (C-10: структура как код) ===")
    print("  FAIL: %d   WARN: %d   (пороги: файлов/папка >%d FAIL >%d WARN, файл >%dКБ, корней >%d, глубина >%d)"
          % (len(fails), len(warns), FILES_FAIL, FILES_WARN, FILE_KB_WARN, ROOT_DIRS_WARN, DEPTH_WARN))
    for x in fails + warns:
        print("  [%-4s] %-16s %-34s %d (порог %d)" % (x["level"], x["kind"], x["where"], x["value"], x["limit"]))
    if not f:
        print("  OK: структура в пределах порогов")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
