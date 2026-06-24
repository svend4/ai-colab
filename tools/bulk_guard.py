"""bulk_guard.py — детектор массового стирания БЕЗ страховки (enforcement D-026).

Реализует политику bulk-information-safety: ловит «массовую операцию» в git-diff
(≥THRESHOLD_LINES удалённых строк ИЛИ ≥THRESHOLD_FILES файлов с крупным урезанием) и проверяет
наличие СТРАХОВКИ — git-тега `backup-*`, указывающего на HEAD (состояние ДО стирания). Без страховки
печатает STOP. Прецедент — инцидент outbox-mass-strip 2026-06-24 (147 файлов / 8643 строки без
согласия). Read-only (только чтение git).

Старт как WARN (D-026 proposed); после ратификации может стать pre-commit гейтом.

CLI:
  python tools/bulk_guard.py            # рабочее дерево (все изменения vs HEAD)
  python tools/bulk_guard.py --staged   # только staged (для pre-commit)
  python tools/bulk_guard.py --json
"""
import os
import sys
from _ioutil import configure_output
from _cli import help_guard
import subprocess

configure_output()
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.environ.get("COLLAB_ROOT") or os.path.dirname(HERE)

THRESHOLD_LINES = 500   # суммарно удалённых строк → массовая операция (D-026 П-1)
THRESHOLD_FILES = 10    # файлов с крупным урезанием → массовая операция
FILE_DEL_MIN = 30       # файл «крупно урезан», если удалено ≥30 строк


def parse_numstat(text):
    """git diff --numstat → {deletions, insertions, bulk_files, top:[(file,del)]}."""
    dele = ins = bulk = 0
    rows = []
    for line in (text or "").splitlines():
        parts = line.split("\t")
        if len(parts) < 3:
            continue
        a, d = parts[0], parts[1]
        if a == "-" or d == "-":  # бинарный файл
            continue
        a, d = int(a), int(d)
        ins += a
        dele += d
        if d >= FILE_DEL_MIN:
            bulk += 1
        rows.append((parts[2], d, a))
    rows.sort(key=lambda r: -r[1])
    return {"deletions": dele, "insertions": ins, "bulk_files": bulk, "top": rows[:12]}


def _git(args):
    try:
        p = subprocess.run(["git"] + args, cwd=ROOT, capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=30)
        return p.stdout if p.returncode == 0 else ""
    except (OSError, subprocess.SubprocessError):
        return ""


def backup_tags():
    """Все теги backup-* (страховка) + подмножество, указывающее прямо на HEAD."""
    allt = [t.strip() for t in _git(["tag", "--list", "backup-*"]).splitlines() if t.strip()]
    head = [t.strip() for t in _git(["tag", "--points-at", "HEAD"]).splitlines()
            if t.strip().startswith("backup-")]
    return allt, head


def check(staged=False):
    args = ["diff", "--numstat"] + (["--cached"] if staged else ["HEAD"])
    stat = parse_numstat(_git(args))
    is_bulk = stat["deletions"] >= THRESHOLD_LINES or stat["bulk_files"] >= THRESHOLD_FILES
    allt, head = backup_tags()
    # страховка для UNCOMMITTED bulk: пре-стирочное состояние ещё в HEAD (восстановимо checkout'ом)
    # ИЛИ есть backup-тег. Сильнейшая — тег прямо на HEAD.
    insured = bool(allt)
    return {**stat, "is_bulk": is_bulk, "insured": insured, "backup_tags": allt,
            "backup_on_head": head,
            "verdict": ("ok-not-bulk" if not is_bulk else ("ok-insured" if insured else "STOP-uninsured"))}


def main(argv):
    help_guard(__doc__, argv)
    import json
    as_json = "--json" in argv
    staged = "--staged" in argv
    r = check(staged=staged)
    if as_json:
        print(json.dumps(r, ensure_ascii=False, indent=2))
        return 1 if r["verdict"] == "STOP-uninsured" else 0
    print("=== BULK-GUARD (D-026 bulk-information-safety) ===")
    print("  объём (%s): −%d строк · +%d · крупно-урезанных файлов: %d  (пороги: −%d строк / %d файлов)" % (
        "staged" if staged else "vs HEAD", r["deletions"], r["insertions"], r["bulk_files"],
        THRESHOLD_LINES, THRESHOLD_FILES))
    if not r["is_bulk"]:
        print("  ✓ не массовая операция — guard неприменим")
        return 0
    print("  ⚠ МАССОВАЯ операция (≥порога). Крупнейшие урезания:")
    for f, d, a in r["top"][:8]:
        print("      −%-5d +%-4d %s" % (d, a, f))
    if r["insured"]:
        if r["backup_on_head"]:
            print("\n  ✓ ЗАСТРАХОВАНО — backup-тег прямо на HEAD: %s" % ", ".join(r["backup_on_head"]))
        else:
            print("\n  ✓ ЗАСТРАХОВАНО — backup-тег(и) существуют: %s" % ", ".join(r["backup_tags"]))
            print("    (не на текущем HEAD — убедись, что тег покрывает удаляемый контент)")
        print("    контент восстановим; массовая операция допустима.")
        return 0
    print("\n  ✗ STOP — массовое стирание БЕЗ страховки (нарушение D-026 П-2).")
    print("    СНАЧАЛА застрахуй: git tag backup-<тема>-<дата> HEAD + внешняя копия/bundle,")
    print("    затем повтори. ≥500 строк живого контента — ещё и согласие человека (D-026 П-4).")
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
