"""Тест code_pyramid.py — линт 3 слоёв в .py (визитка·меню·тело)."""
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
import tempfile

os.environ.setdefault("PYTHONUTF8", "1")
HERE = _TOOLS_DIR  # tools/ — тест перенесён в tools/tests/ (C14)
sys.path.insert(0, HERE)
import code_pyramid as cp

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass


def _w(d, name, txt):
    p = os.path.join(d, name)
    open(p, "w", encoding="utf-8", newline="\n").write(txt)
    return p


def main():
    fails = []
    with tempfile.TemporaryDirectory() as d:
        # хорошая пирамида: визитка + 1 публичная (run) + 2 приватных _helper
        good = _w(d, "good.py", '"""good — делает X. CLI: run."""\n'
                  "def run():\n    return _a() + _b()\n"
                  "def _a():\n    return 1\n"
                  "def _b():\n    return 2\n")
        r = cp.analyze(good)
        if not r["visitka"]:
            fails.append("good: визитка не распознана")
        if r["menu"] != ["run"] or r["body_n"] != 2:
            fails.append("good: меню/тело неверно: menu=%s body=%s" % (r["menu"], r["body_n"]))
        if "run" not in " ".join([str(x) for x in [r]]) or r["documented_menu"] != 1:
            fails.append("good: меню run не документировано (есть в docstring)")
        if r["flags"]:
            fails.append("good: лишние флаги: %s" % r["flags"])

        # плоский: визитка + 6 публичных, 0 приватных → флаг «плоский»
        flat = _w(d, "flat.py", '"""flat."""\n' + "".join("def f%d():\n    pass\n" % i for i in range(6)))
        rf = cp.analyze(flat)
        if not any("плоск" in x for x in rf["flags"]):
            fails.append("flat: «плоский» не помечен: %s" % rf["flags"])

        # нет визитки: только FILE-ID-CARD docstring → флаг «нет-визитки»
        card = _w(d, "card.py", '"""\n# [FILE ID CARD]\n# ID: x\n"""\ndef run():\n    pass\n')
        rc = cp.analyze(card)
        if rc["visitka"]:
            fails.append("card: FILE-ID-CARD ложно засчитан как визитка")
        if not any("визитк" in x for x in rc["flags"]):
            fails.append("card: «нет-визитки» не помечен")

        # реальный docstring ПОСЛЕ FILE-ID-CARD → визитка ✓ (ast-обход второго docstring)
        both = _w(d, "both.py", '"""\n# [FILE ID CARD]\n"""\n"""real — суть. run."""\ndef run():\n    pass\n')
        rb = cp.analyze(both)
        if not rb["visitka"]:
            fails.append("both: реальный docstring после карты не распознан")

    if fails:
        print("FAIL test_code_pyramid:")
        for f in fails:
            print("  -", f)
        sys.exit(1)
    print("OK test_code_pyramid: визитка(real vs FILE-ID-CARD) + меню/тело + флаги(плоский/нет-визитки)")


if __name__ == "__main__":
    main()
