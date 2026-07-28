# ast: allow-subprocess
# ==========================================
# [FILE ID CARD]
# ID: tools.bulk_guard
# TYPE: active-script
# DOMAIN: core.validation
# DEPTH_LEVEL: 1
# SUMMARY: детектор массового стирания БЕЗ страховки (enforcement D-026).
# ==========================================
"""bulk_guard.py — детектор массового стирания БЕЗ страховки (enforcement D-026).

Реализует политику bulk-information-safety: ловит «массовую операцию» в git-diff
(≥THRESHOLD_LINES удалённых строк ИЛИ ≥THRESHOLD_FILES файлов с крупным урезанием) и проверяет
наличие СТРАХОВКИ — git-тега `backup-*`, указывающего на состояние ДО стирания. Старый backup-тег
не считается страховкой для нового bulk-изменения. Без страховки печатает STOP. Прецедент —
инцидент outbox-mass-strip 2026-06-24 (147 файлов / 8643 строки без согласия). Read-only
(только чтение git).

Старт как WARN (D-026 proposed); после ратификации может стать pre-commit гейтом.

Режим `--hook` (C44, волна 2, решение Stefan Q-W2-13c) — УСЛОВНАЯ строгость по машинному
статусу D-026: хук читает `status:` из decisions/D-026.md; при `accepted` нарушение
(STOP-uninsured) блокирует коммит (exit 1), при любом другом статусе — только советник-WARN
(exit 0). Ратификация человеком автоматически «включает» гейт, без правки хука.

Режим `--range BASE..HEAD` нужен для merge-gate/CI: он проверяет aggregate diff, каждый commit
в диапазоне и churn, чтобы сценарий «bulk delete в одном commit, restore в следующем» не выглядел
безопасным только потому, что итоговый diff пустой.

CLI:
  python tools/bulk_guard.py                         # рабочее дерево (все изменения vs HEAD)
  python tools/bulk_guard.py --staged                # только staged (для pre-commit)
  python tools/bulk_guard.py --hook                  # pre-commit: exit 1 при accepted D-026 + STOP
  python tools/bulk_guard.py --json
  python tools/bulk_guard.py --range BASE..HEAD --json
  python tools/bulk_guard.py --range BASE..HEAD --strict
"""
import json
import os
import subprocess
import sys

from _canon import parse_front_matter
from _cli import help_guard
from _ioutil import configure_output

configure_output()
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.environ.get("COLLAB_ROOT") or os.path.dirname(HERE)

THRESHOLD_LINES = 500   # суммарно удалённых строк → массовая операция (D-026 П-1)
THRESHOLD_FILES = 10    # файлов с крупным урезанием → массовая операция
FILE_DEL_MIN = 30       # файл «крупно урезан», если удалено ≥30 строк


class UsageError(ValueError):
    pass


def parse_numstat(text):
    """git diff --numstat → {deletions, insertions, bulk_files, top:[(file,del,ins)]}."""
    dele = ins = bulk = 0
    rows = []
    binary = []
    for line in (text or "").splitlines():
        parts = line.split("\t")
        if len(parts) < 3:
            continue
        a, d = parts[0], parts[1]
        if a == "-" or d == "-":
            binary.append(parts[2])
            continue
        a, d = int(a), int(d)
        ins += a
        dele += d
        if d >= FILE_DEL_MIN:
            bulk += 1
        rows.append((parts[2], d, a))
    rows.sort(key=lambda r: -r[1])
    return {
        "deletions": dele,
        "insertions": ins,
        "bulk_files": bulk,
        "top": rows[:12],
        "binary_files": binary[:12],
        "binary_count": len(binary),
    }


def stat_is_bulk(stat):
    return stat.get("deletions", 0) >= THRESHOLD_LINES or stat.get("bulk_files", 0) >= THRESHOLD_FILES


def mark_stat(stat):
    out = dict(stat)
    out["is_bulk"] = stat_is_bulk(out)
    return out


def _git_proc(args, timeout=30):
    try:
        p = subprocess.run(
            ["git"] + args,
            cwd=ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
        )
        return p.returncode, p.stdout or "", p.stderr or ""
    except (OSError, subprocess.SubprocessError) as exc:
        return 3, "", str(exc)


def _git(args):
    rc, out, _err = _git_proc(args)
    return out if rc == 0 else ""


def backup_tags_pointing_at(ref):
    rc, out, _err = _git_proc(["tag", "--points-at", ref])
    if rc != 0:
        return []
    return [t.strip() for t in out.splitlines() if t.strip().startswith("backup-")]


def backup_tags():
    """Все теги backup-* (страховка) + подмножество, указывающее прямо на HEAD."""
    allt = [t.strip() for t in _git(["tag", "--list", "backup-*"]).splitlines() if t.strip()]
    head = backup_tags_pointing_at("HEAD")
    return allt, head


def classify_verdict(is_bulk, backup_tags=None, backup_on_head=None):
    """Classify a working-tree/staged bulk operation.

    D-026 insurance for local diff requires a backup tag on current HEAD, because HEAD is the
    state before the uncommitted/staged deletion.
    """
    backup_tags = backup_tags or []
    backup_on_head = backup_on_head or []
    insured = bool(backup_on_head)
    verdict = "ok-not-bulk" if not is_bulk else ("ok-insured" if insured else "STOP-uninsured")
    return insured, verdict


def check(staged=False):
    args = ["diff", "--numstat"] + (["--cached"] if staged else ["HEAD"])
    stat = parse_numstat(_git(args))
    is_bulk = stat_is_bulk(stat)
    allt, head = backup_tags()
    # D-026 П-2: страховка должна указывать на состояние ДО стирания, т.е. текущий HEAD.
    insured, verdict = classify_verdict(is_bulk, allt, head)
    return {**stat, "is_bulk": is_bulk, "insured": insured, "backup_tags": allt,
            "backup_on_head": head, "verdict": verdict}


def d026_status(root=None):
    """Машинное чтение статуса решения D-026 из decisions/D-026.md ('' при отсутствии файла)."""
    path = os.path.join(root or ROOT, "decisions", "D-026.md")
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            return (parse_front_matter(f.read()).get("status") or "").strip().lower()
    except OSError:
        return ""


def hook_rc(verdict, status):
    """Чистая логика режима --hook: exit-код по вердикту guard'а и статусу D-026."""
    return 1 if (verdict == "STOP-uninsured" and status == "accepted") else 0


def hook_mode(staged=True):
    """Режим pre-commit: печать краткого вердикта + условный exit-код по статусу D-026."""
    r = check(staged=staged)
    status = d026_status()
    rc = hook_rc(r["verdict"], status)
    if r["verdict"] == "STOP-uninsured":
        if rc:
            print("bulk_guard: БЛОК — массовое стирание без страховки (D-026 accepted, П-2).")
            print("  Сначала: git tag backup-<тема>-<дата> HEAD, затем повтори коммит.")
        else:
            print("bulk_guard WARN: массовое стирание без страховки (−%d строк / %d файлов)."
                  % (r["deletions"], r["bulk_files"]))
            print("  D-026 пока %s — не блокирует; рекомендация: git tag backup-<тема>-<дата> HEAD."
                  % (status or "не найдено"))
    return rc


def parse_range_spec(spec):
    if not spec or spec.count("..") != 1 or "..." in spec:
        raise UsageError("--range expects BASE..HEAD")
    base, head = spec.split("..", 1)
    if not base or not head:
        raise UsageError("--range expects non-empty BASE and HEAD")
    return base, head


def resolve_commit(ref):
    rc, out, err = _git_proc(["rev-parse", "--verify", "%s^{commit}" % ref])
    if rc != 0:
        raise UsageError("cannot resolve commit %r: %s" % (ref, (err or out).strip()))
    return out.strip()


def _numstat_between(left, right):
    rc, out, err = _git_proc(["diff", "--numstat", "--find-renames", "--no-ext-diff", left, right, "--"])
    if rc != 0:
        raise RuntimeError((err or out or "git diff failed").strip())
    return mark_stat(parse_numstat(out))


def _rev_list(base, head):
    rc, out, err = _git_proc(["rev-list", "--reverse", "%s..%s" % (base, head)])
    if rc != 0:
        raise RuntimeError((err or out or "git rev-list failed").strip())
    return [line.strip() for line in out.splitlines() if line.strip()]


def _commit_parent(commit):
    rc, out, err = _git_proc(["rev-parse", "--verify", "%s^1" % commit])
    if rc != 0:
        raise RuntimeError((err or out or "cannot resolve first parent").strip())
    return out.strip()


def _commit_summary(commit):
    rc, out, _err = _git_proc(["log", "-1", "--format=%s", commit])
    return out.strip() if rc == 0 else ""


def check_range(range_spec, strict=False):
    """Check a committed range. Read-only and fail-closed on git/rev errors."""
    result = {
        "mode": "range",
        "range": range_spec,
        "strict": bool(strict),
        "thresholds": {
            "lines": THRESHOLD_LINES,
            "files": THRESHOLD_FILES,
            "file_del_min": FILE_DEL_MIN,
        },
        "base": None,
        "head": None,
        "aggregate": None,
        "churn": None,
        "commits": [],
        "hidden_by_aggregate": False,
        "insurance": {},
        "blocked_by": [],
        "errors": [],
        "verdict": "ERROR",
    }
    try:
        base_ref, head_ref = parse_range_spec(range_spec)
        base = resolve_commit(base_ref)
        head = resolve_commit(head_ref)
        result["base"] = base
        result["head"] = head

        aggregate = _numstat_between(base, head)
        result["aggregate"] = aggregate
        commits = _rev_list(base, head)

        all_backup, _ = backup_tags()
        backup_on_base = backup_tags_pointing_at(base)
        backup_on_head = backup_tags_pointing_at(head)
        result["insurance"] = {
            "backup_tags": all_backup,
            "backup_on_base": backup_on_base,
            "backup_on_head": backup_on_head,
            "policy": "aggregate/churn require backup on base; per-commit bulk requires backup on first parent",
        }

        churn_deletions = 0
        churn_insertions = 0
        churn_bulk_files = 0
        churn_binary_count = 0
        any_commit_bulk = False

        for commit in commits:
            parent = _commit_parent(commit)
            stat = _numstat_between(parent, commit)
            parent_backup = backup_tags_pointing_at(parent)
            is_bulk = stat_is_bulk(stat)
            any_commit_bulk = any_commit_bulk or is_bulk
            insured = bool(parent_backup) if is_bulk else False
            verdict = "ok-not-bulk" if not is_bulk else ("ok-insured" if insured else "STOP-uninsured")
            row = {
                "commit": commit,
                "parent": parent,
                "summary": _commit_summary(commit),
                "stat": stat,
                "backup_on_parent": parent_backup,
                "insured": insured,
                "verdict": verdict,
            }
            if verdict == "STOP-uninsured":
                result["blocked_by"].append({"type": "commit", "commit": commit, "parent": parent})
            result["commits"].append(row)
            churn_deletions += stat.get("deletions", 0)
            churn_insertions += stat.get("insertions", 0)
            churn_bulk_files += stat.get("bulk_files", 0)
            churn_binary_count += stat.get("binary_count", 0)

        churn = mark_stat({
            "deletions": churn_deletions,
            "insertions": churn_insertions,
            "bulk_files": churn_bulk_files,
            "top": [],
            "binary_files": [],
            "binary_count": churn_binary_count,
        })
        result["churn"] = churn

        aggregate_insured = bool(backup_on_base) if aggregate["is_bulk"] else False
        churn_insured = bool(backup_on_base) if churn["is_bulk"] else False
        if aggregate["is_bulk"] and not aggregate_insured:
            result["blocked_by"].append({"type": "aggregate", "base": base, "head": head})
        if churn["is_bulk"] and not churn_insured:
            result["blocked_by"].append({"type": "churn", "base": base, "head": head})

        result["aggregate"]["insured"] = aggregate_insured
        result["aggregate"]["verdict"] = (
            "ok-not-bulk" if not aggregate["is_bulk"] else ("ok-insured" if aggregate_insured else "STOP-uninsured")
        )
        result["churn"]["insured"] = churn_insured
        result["churn"]["verdict"] = (
            "ok-not-bulk" if not churn["is_bulk"] else ("ok-insured" if churn_insured else "STOP-uninsured")
        )
        result["hidden_by_aggregate"] = (not aggregate["is_bulk"]) and (any_commit_bulk or churn["is_bulk"])

        if result["blocked_by"]:
            result["verdict"] = "STOP-uninsured"
        elif aggregate["is_bulk"] or any_commit_bulk or churn["is_bulk"]:
            result["verdict"] = "ok-insured"
        else:
            result["verdict"] = "ok-not-bulk"
    except (UsageError, RuntimeError) as exc:
        result["errors"].append(str(exc))
    return result


def parse_cli(argv):
    opts = {"json": False, "staged": False, "hook": False, "range": None, "strict": False}
    i = 0
    while i < len(argv):
        arg = argv[i]
        if arg == "--json":
            opts["json"] = True
        elif arg == "--staged":
            opts["staged"] = True
        elif arg == "--hook":
            opts["hook"] = True
        elif arg == "--strict":
            opts["strict"] = True
        elif arg == "--range":
            if opts["range"] is not None:
                raise UsageError("--range passed more than once")
            if i + 1 >= len(argv) or argv[i + 1].startswith("--"):
                raise UsageError("--range requires BASE..HEAD")
            opts["range"] = argv[i + 1]
            i += 1
        elif arg == "--format":
            if i + 1 >= len(argv):
                raise UsageError("--format requires json")
            fmt = argv[i + 1]
            if fmt != "json":
                raise UsageError("unsupported --format %r (only json)" % fmt)
            opts["json"] = True
            i += 1
        else:
            raise UsageError("unknown argument: %s" % arg)
        i += 1
    if opts["range"] and (opts["staged"] or opts["hook"]):
        raise UsageError("--range is incompatible with --staged/--hook")
    return opts


def print_range_human(r):
    print("=== BULK-GUARD RANGE (D-026 merge-gate) ===")
    if r.get("errors"):
        print("  ✗ ERROR: %s" % "; ".join(r["errors"]))
        return
    print("  range: %s" % r["range"])
    print("  base:  %s" % r["base"][:12])
    print("  head:  %s" % r["head"][:12])
    a = r["aggregate"]
    c = r["churn"]
    print("  aggregate: −%d строк · +%d · files=%d · %s" % (
        a["deletions"], a["insertions"], a["bulk_files"], a["verdict"]))
    print("  churn:     −%d строк · +%d · files=%d · %s" % (
        c["deletions"], c["insertions"], c["bulk_files"], c["verdict"]))
    if r["hidden_by_aggregate"]:
        print("  ! hidden_by_aggregate: per-commit/churn loss is larger than final diff suggests")
    bad = [row for row in r["commits"] if row["verdict"] == "STOP-uninsured"]
    if bad:
        print("  blocked commits:")
        for row in bad[:8]:
            s = row["stat"]
            print("    %s −%d %s" % (row["commit"][:12], s["deletions"], row.get("summary") or ""))
    print("  verdict: %s" % r["verdict"])


def usage_error(message, as_json=False):
    if as_json:
        print(json.dumps({"mode": "usage", "verdict": "ERROR", "errors": [message]}, ensure_ascii=False, indent=2))
    else:
        print("ОШИБКА: %s" % message)
    return 2


def main(argv):
    help_guard(__doc__, argv)
    try:
        opts = parse_cli(argv)
    except UsageError as exc:
        return usage_error(str(exc), as_json="--json" in argv or "json" in argv)

    if opts["hook"]:
        return hook_mode(staged=True)

    if opts["range"]:
        r = check_range(opts["range"], strict=opts["strict"])
        if opts["json"]:
            print(json.dumps(r, ensure_ascii=False, indent=2))
        else:
            print_range_human(r)
        if r.get("errors"):
            return 2
        return 1 if r["verdict"] == "STOP-uninsured" else 0

    r = check(staged=opts["staged"])
    if opts["json"]:
        print(json.dumps(r, ensure_ascii=False, indent=2))
        return 1 if r["verdict"] == "STOP-uninsured" else 0
    print("=== BULK-GUARD (D-026 bulk-information-safety) ===")
    print("  объём (%s): −%d строк · +%d · крупно-урезанных файлов: %d  (пороги: −%d строк / %d файлов)" % (
        "staged" if opts["staged"] else "vs HEAD", r["deletions"], r["insertions"], r["bulk_files"],
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
            print("\n  ✗ backup-тег(и) существуют, но НЕ на текущем HEAD: %s" % ", ".join(r["backup_tags"]))
            print("    D-026 требует страховку состояния ДО этой операции: tag должен points-at HEAD.")
        print("    контент восстановим; массовая операция допустима.")
        return 0
    if r["backup_tags"] and not r["backup_on_head"]:
        print("\n  ! Найдены backup-теги, но ни один не указывает на текущий HEAD: %s" % ", ".join(r["backup_tags"]))
        print("    Они НЕ страхуют данный bulk-diff. Создай новый backup-тег на HEAD.")
    print("\n  ✗ STOP — массовое стирание БЕЗ страховки (нарушение D-026 П-2).")
    print("    СНАЧАЛА застрахуй: git tag backup-<тема>-<дата> HEAD + внешняя копия/bundle,")
    print("    затем повтори. ≥500 строк живого контента — ещё и согласие человека (D-026 П-4).")
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))