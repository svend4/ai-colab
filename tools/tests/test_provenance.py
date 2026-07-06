# ast: allow-subprocess
"""
# ==========================================
# [FILE ID CARD]
# ID: tools.test_provenance
# TYPE: active-script
# DOMAIN: core
# DEPTH_LEVEL: 1
# SUMMARY: Скрипт test_provenance.py. Описание сгенерировано автоматически.
# ==========================================
"""
"""Тест provenance_independence (ripeness_gate) — порядок коммитов = направленная независимость."""
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

V = "---\nid: %s\nsealed: blind\n---\n# Тело %s\nсодержание варианта %s\n"


def _git(args, cwd, when=None):
    env = dict(os.environ)
    if when:
        env["GIT_AUTHOR_DATE"] = when
        env["GIT_COMMITTER_DATE"] = when
    subprocess.run(["git"] + args, cwd=cwd, capture_output=True, text=True,
                   encoding="utf-8", errors="replace", stdin=subprocess.DEVNULL, env=env)


def main():
    fails = []
    with tempfile.TemporaryDirectory() as d:
        _git(["init"], d)
        _git(["config", "user.email", "t@t"], d)
        _git(["config", "user.name", "t"], d)
        vd = os.path.join(d, "variants", "topic")
        os.makedirs(vd, exist_ok=True)
        a = os.path.join(vd, "a.md")
        b = os.path.join(vd, "b.md")

        # A закоммичен РАНЬШЕ B (контролируем даты)
        open(a, "w", encoding="utf-8", newline="\n").write(V % ("a", "a", "a"))
        _git(["add", "-A"], d); _git(["commit", "-m", "a"], d, when="2026-01-01T00:00:00")
        open(b, "w", encoding="utf-8", newline="\n").write(V % ("b", "b", "b"))
        _git(["add", "-A"], d); _git(["commit", "-m", "b"], d, when="2026-02-01T00:00:00")

        r = rg.provenance_independence(a, b, root=d)
        if r["direction"] != "ordered" or r.get("independent") != "a.md" or r.get("suspect") != "b.md":
            fails.append("A раньше B → A независим, B suspect: %s" % r)
        if not r["both_verified"]:
            fails.append("оба незменены → both_verified")
        # симметрия аргументов: тот же вердикт
        r2 = rg.provenance_independence(b, a, root=d)
        if r2.get("independent") != "a.md":
            fails.append("порядок не зависит от порядка аргументов: %s" % r2)

        # два файла в ОДНОМ коммите → взаимная независимость
        c = os.path.join(vd, "c.md"); e = os.path.join(vd, "e.md")
        open(c, "w", encoding="utf-8", newline="\n").write(V % ("c", "c", "c"))
        open(e, "w", encoding="utf-8", newline="\n").write(V % ("e", "e", "e"))
        _git(["add", "-A"], d); _git(["commit", "-m", "ce"], d, when="2026-03-01T00:00:00")
        rm = rg.provenance_independence(c, e, root=d)
        if rm["direction"] != "mutual":
            fails.append("один коммит → mutual (взаимно независимы): %s" % rm)

        # не в git → недоказуемо
        z = os.path.join(vd, "z.md")
        open(z, "w", encoding="utf-8", newline="\n").write(V % ("z", "z", "z"))
        if rg.provenance_independence(a, z, root=d)["direction"] != "unknown":
            fails.append("незакоммиченный → порядок недоказуем (unknown)")

    if fails:
        print("FAIL test_provenance:")
        for f in fails:
            print("  -", f)
        sys.exit(1)
    print("OK test_provenance: A<B→A независим/B suspect · симметрия аргументов · один коммит→mutual · не-в-git→unknown")


if __name__ == "__main__":
    main()
