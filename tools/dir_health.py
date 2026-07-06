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
HELP = """dir_health.py — health-gate каталога (C-10 консенсус) — пороги структуры как код.

Из architecture-fundamentals §3.2 + razbor-consensus C-10: организация каталога проверяется ЧИСЛАМИ,
как код (не на глаз). Пороги (консенсус 2+ агентов): файлов в папке >200 FAIL / >100 WARN (цель 7-50);
архивные каталоги (ARCHIVE_DIRS, D-034: архив растёт по определению) >500 FAIL / >400 WARN;
файл >50КБ WARN; index.json >200КБ WARN; корневых папок >15 WARN; глубина вложенности >3 WARN;
элементы queues/inbox/ старше 5д WARN (C30-b аудита 2026-07-02, по аналогии с T-201 для failed;
README.md не считается). Gitignored runtime-артефакты (напр. indexes/canon.db) исключены из порога
размера файла (C55-c: это не канон, а пересобираемый кэш — шум в гейте).
Флагует, где структура вышла за пределы машинной И человеческой навигации (напр. tasks/=222 → FAIL,
прямой повод для C-04 шардинга по диапазонам ID).

CLI:
    python tools/dir_health.py [root]       # отчёт + пороги (exit 1 если есть FAIL)
    python tools/dir_health.py [root] --json
"""
import os
import sys
import json
import glob
import time
import subprocess

os.environ.setdefault("PYTHONUTF8", "1")
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from _ioutil import configure_output
from _cli import help_guard

configure_output()

FILES_FAIL = 200       # жёсткий потолок файлов в одной папке
FILES_WARN = 100       # мягкий потолок (цель 7-50)
# D-034: архивные каталоги растут по определению — отдельные пороги; при достижении WARN (400)
# включается шардирование (done/<YYYY-MM>/) или ротация janitor, а не поднятие порога.
ARCHIVE_DIRS = {"queues/done"}
ARCHIVE_FILES_FAIL = 500
ARCHIVE_FILES_WARN = 400
FILE_KB_WARN = 50      # размер одного файла
INDEX_KB_WARN = 200    # центральный index.json
ROOT_DIRS_WARN = 15    # число корневых папок
DEPTH_WARN = 3         # глубина вложенности
INBOX_TTL_WARN_DAYS = 5  # TTL входов queues/inbox/ (C30-b: семья порогов N=3-5д, как failed/T-201)

SKIP = (".git", "data", "tmp-work", "__pycache__", "node_modules", ".idea", "external", "logs")


def _skip(rel):
    parts = [p for p in rel.replace("\\", "/").split("/") if p and p != "."]
    return any(p in SKIP or p.startswith(".") for p in parts)


def _resolve_root(root=None):
    return os.path.abspath(os.path.expanduser(root or ROOT))


def _gitignored(base, relpaths):
    """Подмножество relpaths (пути с '/', относительно base), игнорируемых git.

    C55-c: gitignored runtime-артефакты (напр. indexes/canon.db 5+МБ) — пересобираемый кэш,
    а не канон; порог размера файла на них ложно шумит в гейте. Один батч-вызов
    `git check-ignore --stdin` на весь скан. Тихая деградация: нет git / base не репозиторий /
    таймаут → пустое множество (поведение порогов как раньше, ничего не исключаем).
    """
    if not relpaths:
        return set()
    try:
        # ВАЖНО: байты, не text=True — текстовый режим на Windows превращает \n в \r\n,
        # и git получает пути с хвостовым \r (ничего не матчится).
        proc = subprocess.run(
            ["git", "-C", base, "check-ignore", "--stdin"],
            input=("\n".join(relpaths) + "\n").encode("utf-8"),
            capture_output=True, timeout=15)
    except (OSError, subprocess.SubprocessError):
        return set()
    if proc.returncode not in (0, 1):    # 0 = есть игнорируемые, 1 = нет; прочее = ошибка git
        return set()
    out = proc.stdout.decode("utf-8", errors="replace")
    return {line.strip() for line in out.splitlines() if line.strip()}


def scan(root=None):
    base = _resolve_root(root)
    findings = []
    oversize = []          # кандидаты file-size: фильтруются по gitignore ОДНИМ батчем после обхода
    # 1) файлов в каждой папке
    for dirpath, dirs, files in os.walk(base):
        rel = os.path.relpath(dirpath, base)
        if rel != "." and _skip(rel):
            dirs[:] = []
            continue
        dirs[:] = [d for d in dirs if not _skip(os.path.join(rel, d))]
        real = [f for f in files if not f.startswith(".")]
        n = len(real)
        relshow = "." if rel == "." else rel.replace("\\", "/")
        # D-034: архивные каталоги (растут по определению) живут по своим порогам 500/400
        is_archive = relshow in ARCHIVE_DIRS
        n_fail = ARCHIVE_FILES_FAIL if is_archive else FILES_FAIL
        n_warn = ARCHIVE_FILES_WARN if is_archive else FILES_WARN
        if n > n_fail:
            # navigation-vs-sharding: при наличии папка-индекса (indexes/<name>.md) это не FAIL —
            # навигация решена метаданными, шардинг не требуется (решение 2026-06-24).
            has_index = "/" not in relshow and os.path.isfile(
                os.path.join(base, "indexes", relshow + ".md"))
            findings.append({"kind": "files-per-dir", "level": "WARN" if has_index else "FAIL",
                             "where": relshow + (" (есть папка-индекс)" if has_index else ""),
                             "value": n, "limit": n_fail})
        elif n > n_warn:
            findings.append({"kind": "files-per-dir", "level": "WARN", "where": relshow,
                             "value": n, "limit": n_warn})
        # 2) большие файлы (кандидаты; gitignored runtime-артефакты исключаются ниже, C55-c)
        for f in real:
            kb = os.path.getsize(os.path.join(dirpath, f)) // 1024
            if kb > FILE_KB_WARN:
                lvl = "WARN" if f != "index.json" else ("WARN" if kb <= INDEX_KB_WARN else "FAIL")
                lim = INDEX_KB_WARN if f == "index.json" else FILE_KB_WARN
                oversize.append({"kind": "file-size", "level": lvl,
                                 "where": ("%s/%s" % (relshow, f)).lstrip("./"), "value": kb, "limit": lim})
    ignored = _gitignored(base, [x["where"] for x in oversize])
    findings.extend(x for x in oversize if x["where"] not in ignored)
    # 3) корневых папок
    root_dirs = [d for d in os.listdir(base)
                 if os.path.isdir(os.path.join(base, d)) and not _skip(d)]
    if len(root_dirs) > ROOT_DIRS_WARN:
        findings.append({"kind": "root-dirs", "level": "WARN", "where": ".",
                         "value": len(root_dirs), "limit": ROOT_DIRS_WARN})
    # 4) глубина
    maxdepth = 0
    for dirpath, dirs, _files in os.walk(base):
        rel = os.path.relpath(dirpath, base)
        if rel != "." and _skip(rel):
            dirs[:] = []
            continue
        depth = 0 if rel == "." else len(rel.replace("\\", "/").split("/"))
        maxdepth = max(maxdepth, depth)
    if maxdepth > DEPTH_WARN:
        findings.append({"kind": "depth", "level": "WARN", "where": ".",
                         "value": maxdepth, "limit": DEPTH_WARN})
    # 5) TTL входов queues/inbox/ (C30-b): вход старше порога = залёживание, никто не взял в работу.
    #    По аналогии с правилом T-201 для failed («не висит без анализа»). README.md — не вход.
    inbox = os.path.join(base, "queues", "inbox")
    if os.path.isdir(inbox):
        now = time.time()
        for f in sorted(os.listdir(inbox)):
            if f == "README.md" or f.startswith("."):
                continue
            p = os.path.join(inbox, f)
            if not os.path.isfile(p):
                continue
            age_days = (now - os.path.getmtime(p)) / 86400.0
            if age_days > INBOX_TTL_WARN_DAYS:
                findings.append({"kind": "inbox-ttl", "level": "WARN",
                                 "where": "queues/inbox/" + f,
                                 "value": int(age_days), "limit": INBOX_TTL_WARN_DAYS})
    return findings


def _parse_args(argv):
    as_json = False
    root = None
    for arg in argv:
        if arg == "--json":
            as_json = True
        elif arg in ("--help", "-h"):
            return as_json, root, True, None
        elif arg.startswith("-"):
            return as_json, root, False, "неизвестный аргумент: %s" % arg
        elif root is None:
            root = arg
        else:
            return as_json, root, False, "ожидался один root-путь, получено лишнее: %s" % arg
    return as_json, root, False, None


def main(argv):
    help_guard(HELP, argv)
    as_json, root, help_requested, error = _parse_args(argv)
    if help_requested:
        print(HELP)
        return 0
    if error:
        print("ОШИБКА: %s" % error)
        return 2
    f = scan(root)
    fails = [x for x in f if x["level"] == "FAIL"]
    warns = [x for x in f if x["level"] == "WARN"]
    if as_json:
        print(json.dumps({"fail": len(fails), "warn": len(warns), "findings": f},
                         ensure_ascii=False, indent=2))
        return 1 if fails else 0
    print("=== HEALTH-GATE КАТАЛОГА (C-10: структура как код) ===")
    print("  FAIL: %d   WARN: %d   (пороги: файлов/папка >%d FAIL >%d WARN (архивные D-034: >%d/>%d), файл >%dКБ (gitignored искл.), корней >%d, глубина >%d, inbox >%dд)"
          % (len(fails), len(warns), FILES_FAIL, FILES_WARN, ARCHIVE_FILES_FAIL, ARCHIVE_FILES_WARN,
             FILE_KB_WARN, ROOT_DIRS_WARN, DEPTH_WARN, INBOX_TTL_WARN_DAYS))
    for x in fails + warns:
        print("  [%-4s] %-16s %-34s %d (порог %d)" % (x["level"], x["kind"], x["where"], x["value"], x["limit"]))
    if not f:
        print("  OK: структура в пределах порогов")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
