"""Тест seal_verified (ripeness_gate) — провенанс печати по git (тело==первый коммит)."""
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
import subprocess
import tempfile

os.environ.setdefault("PYTHONUTF8", "1")
HERE = _TOOLS_DIR  # tools/ — тест перенесён в tools/tests/ (C14)
sys.path.insert(0, HERE)
import ripeness_gate as rg

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass


def _git(args, cwd):
    subprocess.run(["git"] + args, cwd=cwd, capture_output=True, text=True,
                   encoding="utf-8", errors="replace", stdin=subprocess.DEVNULL)


VAR = "---\nid: x\nstatus: ready-for-synthesis\nsealed: blind\n---\n# Тело\nисходное содержание варианта\n"


def main():
    fails = []
    with tempfile.TemporaryDirectory() as d:
        _git(["init"], d)
        _git(["config", "user.email", "t@t"], d)
        _git(["config", "user.name", "t"], d)
        os.makedirs(os.path.join(d, "variants", "topic"), exist_ok=True)
        p = os.path.join(d, "variants", "topic", "a.md")
        open(p, "w", encoding="utf-8", newline="\n").write(VAR)
        _git(["add", "-A"], d)
        _git(["commit", "-m", "seal a"], d)

        # сразу после коммита: тело == первый коммит → verified
        v = rg.seal_verified(p, root=d)
        if not v["verified"]:
            fails.append("свежезакоммиченный незменённый → verified: %s" % v)

        # правка тела ПОСЛЕ коммита (без рекоммита) → печать нарушена → НЕ verified
        open(p, "w", encoding="utf-8", newline="\n").write(VAR.replace("исходное содержание", "ПОДДЕЛАННОЕ"))
        v2 = rg.seal_verified(p, root=d)
        if v2["verified"]:
            fails.append("тело изменено после коммита → должно быть НЕ verified (подделка): %s" % v2)
        if "изменено" not in v2.get("why", ""):
            fails.append("причина должна указывать на изменение тела: %s" % v2)

        # незакоммиченный файл → провенанс недоказуем
        q = os.path.join(d, "variants", "topic", "b.md")
        open(q, "w", encoding="utf-8", newline="\n").write(VAR)
        v3 = rg.seal_verified(q, root=d)
        if v3["verified"] or "git" not in v3.get("why", ""):
            fails.append("незакоммиченный → провенанс недоказуем (не в git): %s" % v3)

        # правка ТОЛЬКО front-matter (не тела) — тело то же → печать ЦЕЛА (seal = body-only)
        open(p, "w", encoding="utf-8", newline="\n").write(
            "---\nid: x\nstatus: ready-for-synthesis\nsealed: blind\nmodel: m1\n---\n# Тело\nисходное содержание варианта\n")
        v4 = rg.seal_verified(p, root=d)
        if not v4["verified"]:
            fails.append("правка только front-matter (тело то же) → печать ЦЕЛА (seal по телу): %s" % v4)

    if fails:
        print("FAIL test_seal_verify:")
        for f in fails:
            print("  -", f)
        sys.exit(1)
    print("OK test_seal_verify: verified(тело==коммит) · подделка тела→не verified · не-в-git→недоказуем · front-matter не ломает печать")


if __name__ == "__main__":
    main()
