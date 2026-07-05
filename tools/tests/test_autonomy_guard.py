"""Тест autonomy_guard.py — матрица случаев classify_decision (proposed/0/1/≥2/autonomous) · scan · read-only."""
# --- бутстрап путей (C14, аудит 2026-07-02): тест живёт в tools/tests/, инструменты — в tools/.
# Вставка ДО локальных импортов, чтобы standalone-запуск работал из нового места.
import os as _os
import sys as _sys
_TOOLS_DIR = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
if _TOOLS_DIR not in _sys.path:
    _sys.path.insert(0, _TOOLS_DIR)
# --- конец бутстрапа ---

import os
import sys
import time

HERE = _TOOLS_DIR  # tools/ — тест перенесён в tools/tests/ (C14)
REPO_ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import autonomy_guard as ag

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass


def v(fm, body=""):
    return ag.classify_decision(fm, body)["verdict"]


def main():
    fails = []

    # Случай 1: proposed → ok (черновик, нет терминального accept)
    if v({"status": "proposed"}) != "ok":
        fails.append("1: proposed → ok")
    # Случай 8: proposed + autonomous:true → ok (помеченный черновик — норм по §0)
    if v({"status": "proposed", "autonomous": "true"}) != "ok":
        fails.append("8: autonomous-черновик proposed → ok")

    # Случай 2: accepted + участник Stefan + проза «ратифицировал» → ≥2 → ok
    if v({"status": "accepted", "participants": "Stefan (ратификация), Claude"}, "Stefan ратифицировал") != "ok":
        fails.append("2: accepted + 2 сигнала → ok")
    # Случай 6: accepted + human_confirmations:2 → ok
    if v({"status": "accepted", "human_confirmations": "2"}) != "ok":
        fails.append("6: accepted + human_confirmations 2 → ok")

    # Случай 3: accepted + только проза «Stefan» (1 сигнал) → warn
    if v({"status": "accepted"}, "по решению Stefan") != "warn":
        fails.append("3: accepted + 1 прозаический сигнал → warn")
    # Случай 7: accepted + только confirmed_by (1 структурный) → warn
    if v({"status": "accepted", "confirmed_by": "Stefan"}) != "warn":
        fails.append("7: accepted + только confirmed_by → warn (нужно ≥2)")

    # Случай 4: accepted + НЕТ человека → flag
    if v({"status": "accepted", "author": "claude"}, "агент свёл итог") != "flag":
        fails.append("4: accepted + 0 сигналов человека → flag")
    # Случай 5: accepted + autonomous:true без подтверждений → flag (самозаявленный)
    if v({"status": "accepted", "autonomous": "true"}, "агент") != "flag":
        fails.append("5: accepted + autonomous:true + 0 → flag")

    # _human_signals считает несколько источников
    if ag._human_signals({"confirmed_by": "Stefan", "human_confirmations": "1"}, "ратифицировал") < 2:
        fails.append("_human_signals должен суммировать источники")

    # scan на временном decisions/
    d = os.path.join(REPO_ROOT, "tmp-work", "autonomy_test_%d_%d" % (os.getpid(), time.time_ns()))
    dd = os.path.join(d, "decisions")
    os.makedirs(dd, exist_ok=True)

    def w(name, fmlines, body=""):
        open(os.path.join(dd, name), "w", encoding="utf-8", newline="\n").write(
            "---\n%s\n---\n%s\n" % ("\n".join(fmlines), body))

    w("D-900.md", ["id: D-900", "status: accepted", "author: claude"], "агент свёл итог")           # flag
    w("D-901.md", ["id: D-901", "status: accepted"], "по решению Stefan")                           # warn
    w("D-902.md", ["id: D-902", "status: accepted", "participants: Stefan, Claude"], "Stefan ратифицировал")  # ok
    w("D-903.md", ["id: D-903", "status: proposed", "autonomous: true"], "черновик")                # ok

    before = open(os.path.join(dd, "D-900.md"), encoding="utf-8").read()
    rows = ag.scan(decisions_dir=dd, require=2)
    by = {r["id"]: r["verdict"] for r in rows}
    if by.get("D-900") != "flag" or by.get("D-901") != "warn" or by.get("D-902") != "ok" or by.get("D-903") != "ok":
        fails.append("scan вердикты: %s" % by)
    # read-only: D-файл НЕ изменён
    if open(os.path.join(dd, "D-900.md"), encoding="utf-8").read() != before:
        fails.append("scan должен быть READ-ONLY (D-файл не изменён)")

    if fails:
        print("FAIL test_autonomy_guard:")
        for f in fails:
            print("  -", f)
        sys.exit(1)
    print("OK test_autonomy_guard: матрица(proposed/0→flag/1→warn/≥2→ok/autonomous) · _human_signals · scan · read-only")


if __name__ == "__main__":
    main()
