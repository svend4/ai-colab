# ast: allow-subprocess
# ==========================================
# [FILE ID CARD]
# ID: tools.decay
# TYPE: active-script
# DOMAIN: core
# DEPTH_LEVEL: 1
# SUMMARY: ось ВРЕМЕНИ: температура атомов по git-возрасту (DIV-06).
# ==========================================
"""decay.py — ось ВРЕМЕНИ: температура атомов по git-возрасту (DIV-06).

Третья ось проекта (после дерева=ГДЕ живёт и графа=КАК связан): ВРЕМЯ=насколько СВЕЖ.
git last-commit per file → возраст → температура hot/warm/cold. Главный сигнал: **cold + активный
статус** (todo/doing/open/proposed/blocked) = застывшая незавершёнка → кандидат на ре-оценку/архив.
Терминальные (done/accepted/rejected/answered) холодные — НОРМА (заморожены намеренно).
Read-only (чистое чтение git). Ложится в блок improve.

CLI:
  python tools/decay.py                    # сводка температур + cold-активные кандидаты
  python tools/decay.py --json
  python tools/decay.py --list cold-active # списком: cold-active | cold | warm | hot
  python tools/decay.py --now <epoch>      # зафиксировать «сейчас» (для тестов)
"""
import os
from _ioutil import configure_output
import sys
import json
import glob
import time
import subprocess

configure_output()
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.environ.get("COLLAB_ROOT") or os.path.dirname(HERE)
sys.path.insert(0, HERE)
from _canon import parse_fm
from _cli import help_guard

DIRS = ["tasks", "decisions", "questions", "topics", "docs", "streams"]
HOT_DAYS = 3       # < 3 дней — горячий (активно трогается)
WARM_DAYS = 14     # < 14 — тёплый; >= 14 — холодный
TERMINAL = ("done", "rejected", "superseded", "answered", "accepted", "archived", "archive")
ACTIVE = ("todo", "doing", "open", "proposed", "blocked", "in-progress", "needs-decision", "waiting")
DAY = 86400


def git_mtimes():
    """{relpath: epoch последнего коммита} одним проходом git log (newest-first → первый = свежий)."""
    out = {}
    try:
        p = subprocess.run(["git", "log", "--no-renames", "--format=C%ct", "--name-only"],
                           cwd=ROOT, capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=90)
    except (OSError, subprocess.SubprocessError):
        return out
    if p.returncode != 0:
        return out  # не git-репо → пусто, упадём на fs-mtime
    cur = None
    for line in p.stdout.splitlines():
        if line.startswith("C") and line[1:].isdigit():
            cur = int(line[1:])
        elif line.strip() and cur is not None:
            rel = line.strip().replace("\\", "/")
            if rel not in out:
                out[rel] = cur
    return out


def _age_days(rel, mtimes, now):
    epoch = mtimes.get(rel)
    if epoch is None:
        # не в git (untracked) — пробуем fs mtime
        try:
            epoch = int(os.path.getmtime(os.path.join(ROOT, rel)))
        except OSError:
            return None
    return max(0, (now - epoch) / DAY)


def classify(age_days):
    if age_days is None:
        return "unknown"
    if age_days < HOT_DAYS:
        return "hot"
    if age_days < WARM_DAYS:
        return "warm"
    return "cold"


def collect(now=None):
    now = int(now if now is not None else time.time())
    mtimes = git_mtimes()
    rows = []
    for d in DIRS:
        for p in glob.glob(os.path.join(ROOT, d, "**", "*.md"), recursive=True):
            if os.path.basename(p) == "README.md":
                continue
            rel = os.path.relpath(p, ROOT).replace("\\", "/")
            try:
                fm = parse_fm(open(p, encoding="utf-8", errors="replace").read()) or {}
            except OSError:
                continue
            age = _age_days(rel, mtimes, now)
            temp = classify(age)
            status = (fm.get("status") or "").strip()
            rows.append({"file": rel, "id": fm.get("id", ""), "status": status,
                         "temp": temp, "age_days": None if age is None else round(age, 1),
                         "terminal": status in TERMINAL})
    # stale-активные = активный статус + НЕ горячий (warm/cold) = «открыто, но дольше всего не трогалось».
    # Главный сигнал: работает и в молодом гипер-активном репо (warm), и в старом (cold).
    stale_active = [r for r in rows if r["temp"] in ("warm", "cold") and r["status"] in ACTIVE]
    stale_active.sort(key=lambda r: -(r["age_days"] or 0))
    counts = {}
    for r in rows:
        counts[r["temp"]] = counts.get(r["temp"], 0) + 1
    return {"counts": counts, "total": len(rows), "stale_active": stale_active, "rows": rows}


def main(argv):
    help_guard(__doc__, argv)
    as_json = "--json" in argv
    now = None
    if "--now" in argv:
        i = argv.index("--now")
        if i + 1 < len(argv):
            now = int(argv[i + 1])
    listing = None
    if "--list" in argv:
        i = argv.index("--list")
        if i + 1 < len(argv):
            listing = argv[i + 1]

    data = collect(now)
    if listing:
        sel = (data["stale_active"] if listing in ("stale-active", "cold-active")
               else [r for r in data["rows"] if r["temp"] == listing])
        if as_json:
            print(json.dumps(sel, ensure_ascii=False, indent=2)); return 0
        for r in sel:
            print("  %-5s %5s д  %-9s %s" % (r["temp"], r["age_days"], r["status"] or "—", r["file"]))
        return 0
    if as_json:
        print(json.dumps({k: data[k] for k in ("counts", "total", "stale_active")},
                         ensure_ascii=False, indent=2))
        return 0
    c = data["counts"]
    print("=== ОСЬ ВРЕМЕНИ: температура атомов (DIV-06) ===")
    print("  всего: %d   🔥hot: %d   🌡warm: %d   ❄cold: %d   ?: %d" % (
        data["total"], c.get("hot", 0), c.get("warm", 0), c.get("cold", 0), c.get("unknown", 0)))
    print("  (пороги: hot <%dд · warm <%dд · cold ≥%dд)" % (HOT_DAYS, WARM_DAYS, WARM_DAYS))
    sa = data["stale_active"]
    mark = "•" if sa else "✓"
    print("\n  %s Stale-активные (открыто, но дольше всего не трогалось → ре-оценка/архив): %d" % (mark, len(sa)))
    for r in sa[:20]:
        glyph = "❄" if r["temp"] == "cold" else "🌡"
        print("      %s %5sд  %-9s %s (%s)" % (glyph, r["age_days"], r["status"], r["id"] or r["file"], r["file"]))
    if len(sa) > 20:
        print("      … и ещё %d" % (len(sa) - 20))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
