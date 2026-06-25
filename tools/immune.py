"""immune.py — иммунная система канона (negative-selection детектор аномалий).

Биологический принцип (полуфантастический прообраз → реальный механизм): иммунитет учит профиль
«СВОЕГО» (median±MAD нормального коммита по истории) и помечает «ЧУЖОЕ» — статистический выброс
(массовое стирание, аномальный коммит). Умнее bulk_guard: порог НЕ фиксированный, а адаптируется к
истории репо. Прецедент: инцидент outbox-strip (147 файлов / 8643 строки) ОБЯЗАН пометиться outlier.
Дополняет D-026/bulk_guard (фикс-правило+страховка) статистическим слоем. Read-only (только git read).

CLI:
  python tools/immune.py              # профиль «своего» + проверка рабочего дерева (vs HEAD)
  python tools/immune.py profile      # только профиль (median±MAD по N коммитам)
  python tools/immune.py --json
"""
import os
from _ioutil import configure_output
from _cli import help_guard
import sys
import json
import subprocess

configure_output()
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.environ.get("COLLAB_ROOT") or os.path.dirname(HERE)

SAMPLE = 200    # коммитов для обучения профиля «своего»
K_MAD = 4.0     # порог: > median + K*MAD = «чужое» (выброс)


def _median(xs):
    if not xs:
        return 0.0
    s = sorted(xs)
    n = len(s)
    return float(s[n // 2]) if n % 2 else (s[n // 2 - 1] + s[n // 2]) / 2.0


def _mad(xs, med):
    """Median Absolute Deviation — робастная мера разброса (устойчива к выбросам, в отличие от std)."""
    if not xs:
        return 0.0
    return _median([abs(x - med) for x in xs])


def _git(args):
    try:
        return subprocess.run(["git"] + args, cwd=ROOT, capture_output=True, text=True,
                              encoding="utf-8", errors="replace", timeout=60).stdout
    except (OSError, subprocess.SubprocessError):
        return ""


def commit_stats(n=SAMPLE):
    """Per-commit статистика по последним n коммитам: {files, deletions, additions}."""
    out = _git(["log", "-%d" % n, "--no-merges", "--numstat", "--format=C%H"])
    stats, cur = [], None
    for line in out.splitlines():
        if line.startswith("C") and len(line) > 10:
            if cur is not None:
                stats.append(cur)
            cur = {"files": 0, "deletions": 0, "additions": 0}
        elif cur is not None and "\t" in line:
            a, d = line.split("\t")[:2]
            if a == "-" or d == "-":
                continue
            cur["files"] += 1
            cur["additions"] += int(a)
            cur["deletions"] += int(d)
    if cur is not None:
        stats.append(cur)
    return stats


# «антитела» (Т-клетки). Аномалия = КВОРУМ (≥QUORUM сигналят), как иммунный ответ требует ко-стимуляции.
# Смешиваем ОТНОСИТЕЛЬНОЕ (адаптивный профиль) и АБСОЛЮТНЫЕ сигнатуры стрипа — чтобы отличить
# массовое СТИРАНИЕ (опасно) от крупной ЛЕГИТИМНОЙ правки (много файлов, но добавление-доминантна).
QUORUM = 2
NET_DELETION_RATIO = 1.0   # del/add > 1 = нетто-ПОТЕРЯ информации (абс. сигнатура стрипа)
LARGE_DELETION = 500       # абс. порог удалений (согласован с D-026)


def profile(stats):
    """Учим относительный профиль «своего» по числу файлов (адаптивно к истории репо)."""
    files = [s["files"] for s in stats]
    fm = _median(files)
    return {"n_commits": len(stats), "files_median": round(fm, 1), "files_mad": round(_mad(files, fm), 1),
            "files_threshold": round(fm + K_MAD * _mad(files, fm), 1)}


def current_diff():
    """Текущее рабочее дерево vs HEAD (включая незакоммиченное)."""
    out = _git(["diff", "HEAD", "--numstat"])
    files = dele = add = 0
    for line in out.splitlines():
        if "\t" not in line:
            continue
        a, d = line.split("\t")[:2]
        if a == "-" or d == "-":
            continue
        files += 1
        add += int(a)
        dele += int(d)
    return {"files": files, "deletions": dele, "additions": add}


MIN_SAMPLE = 10  # меньше — профиль ненадёжен, не выносим вердикт (защита от ложных срабатываний)


def assess(cur, prof):
    if prof["n_commits"] < MIN_SAMPLE:
        return {"anomaly": False, "fired": [], "insufficient": True}
    ratio = cur["deletions"] / max(1, cur["additions"])
    fired = []
    if cur["files"] > prof["files_threshold"]:                       # относит.: необычно много файлов
        fired.append({"dim": "many_files", "label": "файлов %d (порог %.0f, норма ~%.0f)" % (
            cur["files"], prof["files_threshold"], prof["files_median"])})
    if ratio > NET_DELETION_RATIO:                                   # абс.: нетто-потеря (стрип-сигнатура)
        fired.append({"dim": "net_deletion", "label": "удал./добавл. %.1f > 1 (нетто-потеря)" % ratio})
    if cur["deletions"] > LARGE_DELETION:                            # абс.: крупное удаление (D-026)
        fired.append({"dim": "large_deletion", "label": "удалений %d > %d (D-026)" % (cur["deletions"], LARGE_DELETION)})
    # кворум ≥2: «много файлов» само по себе = крупная правка (ок); + нетто-потеря/крупное удаление = стрип.
    return {"anomaly": len(fired) >= QUORUM, "fired": fired, "quorum": QUORUM}


def main(argv):
    help_guard(__doc__, argv)
    as_json = "--json" in argv
    args = [a for a in argv if not a.startswith("--")]
    prof = profile(commit_stats())
    if args and args[0] == "profile":
        if as_json:
            print(json.dumps(prof, ensure_ascii=False, indent=2)); return 0
        print("=== ИММУННЫЙ ПРОФИЛЬ «своего» (по %d коммитам) ===" % prof["n_commits"])
        print("  файлов/коммит: медиана %.0f ± MAD %.0f → относит. порог %.0f" % (
            prof["files_median"], prof["files_mad"], prof["files_threshold"]))
        print("  абс. сигнатуры стрипа: нетто-потеря (del/add>%.0f), крупное удаление (>%d, D-026)" % (
            NET_DELETION_RATIO, LARGE_DELETION))
        print("  кворум аномалии: ≥%d антител разом" % QUORUM)
        return 0
    cur = current_diff()
    a = assess(cur, prof)
    ratio = cur["deletions"] / max(1, cur["additions"])
    if as_json:
        print(json.dumps({"current": cur, "ratio": round(ratio, 2), "profile": prof, **a}, ensure_ascii=False, indent=2))
        return 1 if a["anomaly"] else 0
    if a.get("insufficient"):
        print("=== ИММУННАЯ СИСТЕМА ===\n  недостаточно истории (%d < %d коммитов) — вердикт не выносится" % (
            prof["n_commits"], MIN_SAMPLE))
        return 0
    print("=== ИММУННАЯ СИСТЕМА — рабочее дерево vs профиль «своего» (Т-клетки + кворум) ===")
    print("  текущее: %d файлов, −%d / +%d строк (удал./добавл. %.2f)" % (
        cur["files"], cur["deletions"], cur["additions"], ratio))
    print("  сигналят антител: %d (кворум %d)" % (len(a["fired"]), a["quorum"]))
    for f in a["fired"]:
        print("      ⚠ %s" % f["label"])
    if a["anomaly"]:
        print("\n  🛑 АНОМАЛИЯ («чужое» — кворум): проверь намеренность; массовое стирание → страховка (D-026/bulk_guard).")
        return 1
    print("\n  ✓ в пределах «своего» (кворум не набран — крупная, но легитимная правка или норма)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
