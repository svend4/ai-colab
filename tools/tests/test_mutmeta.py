"""
# ==========================================
# [FILE ID CARD]
# ID: tools.test_mutmeta
# TYPE: active-script
# DOMAIN: core
# DEPTH_LEVEL: 1
# SUMMARY: Скрипт test_mutmeta.py. Описание сгенерировано автоматически.
# ==========================================
"""
"""Тест mutmeta.py — gen_mutants(компилируемость) · verdict(co_defective) · интеграция (хороший vs пустой тест)."""
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
import mutmeta as mm

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

SAMP = """def add(a, b):
    return a + b

def is_one(x):
    return x == 1

def flag():
    return True

def count():
    return 3
"""

GOOD_TEST = """import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import samp
assert samp.add(1, 2) == 3
assert samp.is_one(1) is True
assert samp.is_one(2) is False
assert samp.flag() is True
assert samp.count() == 3
print("OK samp")
"""

BAD_TEST = """import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import samp
samp.add(1, 2)        # вызывает, но НИЧЕГО не ассертит
print("OK samp (пусто)")
"""


def main():
    fails = []

    # 1) gen_mutants: компилируемые мутанты, есть известные мутации
    muts = mm.gen_mutants(SAMP, cap=20)
    if len(muts) < 4:
        fails.append("должно быть несколько мутантов: %d" % len(muts))
    if not all(mm._compiles(m) for _l, m in muts):
        fails.append("все мутанты должны компилироваться")
    joined = "\n".join(m for _l, m in muts)
    if "return None" not in joined:
        fails.append("ожидалась мутация return X→None")
    if "x != 1" not in joined:
        fails.append("ожидалась мутация ==→!=")

    # 2) verdict
    if mm.verdict([("a", True), ("b", False)]) != {"valid_mutants": 2, "caught": 1, "mutation_score": 0.5,
                                                   "co_defective": False, "missed": ["b"]}:
        fails.append("verdict 1/2: %s" % mm.verdict([("a", True), ("b", False)]))
    if not mm.verdict([("a", False), ("b", False)])["co_defective"]:
        fails.append("0 пойманных → co_defective")
    if mm.verdict([])["co_defective"]:
        fails.append("нет мутантов → НЕ co_defective (нечего ловить)")

    # 3) интеграция: фикстура tools-dir
    fix = os.path.join(REPO_ROOT, "tmp-work", "mutmeta_fix_%d_%d" % (os.getpid(), time.time_ns()))
    os.makedirs(fix, exist_ok=True)
    try:
        open(os.path.join(fix, "samp.py"), "w", encoding="utf-8", newline="\n").write(SAMP)
        open(os.path.join(fix, "test_samp.py"), "w", encoding="utf-8", newline="\n").write(GOOD_TEST)
        open(os.path.join(fix, "test_sampbad.py"), "w", encoding="utf-8", newline="\n").write(BAD_TEST)

        v_good, _ = mm.run_meta("samp", "test_samp", tools_dir=fix, cap=12)
        if v_good.get("co_defective"):
            fails.append("хороший тест НЕ должен быть co_defective: %s" % v_good)
        if v_good.get("caught", 0) < 1:
            fails.append("хороший тест должен поймать ≥1 мутацию: %s" % v_good)

        v_bad, _ = mm.run_meta("samp", "test_sampbad", tools_dir=fix, cap=12)
        if not v_bad.get("co_defective"):
            fails.append("пустой тест ДОЛЖЕН быть co_defective: %s" % v_bad)
    finally:
        pass

    if fails:
        print("FAIL test_mutmeta:")
        for f in fails:
            print("  -", f)
        sys.exit(1)
    print("OK test_mutmeta: gen_mutants(компилируемы+известные мутации) · verdict(co_defective) · интеграция(хороший≠co · пустой=co)")


if __name__ == "__main__":
    main()
