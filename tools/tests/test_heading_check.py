"""
# ==========================================
# [FILE ID CARD]
# ID: tools.tests.test_heading_check
# TYPE: active-script
# DOMAIN: core
# DEPTH_LEVEL: 1
# SUMMARY: Скрипт test_heading_check.py. Описание сгенерировано автоматически.
# ==========================================
"""
"""Тест heading_check.py — heading-lint (пустые/пропуск уровней/крупный без нумерации)."""
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
import heading_check as hc

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

EMPTY = "# Заголовок\n\n## \n\nтекст\n"                       # пустой ##
SKIP = "# A\n\n#### D\n\nтекст\n"                              # # → #### (пропуск)
FENCE = "# A\n\n```\n## не заголовок в коде\n```\n\n## B\n"    # ## в fence игнор
GOOD = "# A\n\n## 1. Раздел\n\n## 2. Раздел\n"                  # чисто


def main():
    fails = []
    with tempfile.TemporaryDirectory() as d:
        def w(n, t):
            p = os.path.join(d, n)
            open(p, "w", encoding="utf-8", newline="\n").write(t)
            return p

        e = hc.check_file(w("e.md", EMPTY))
        if not any(x["kind"] == "empty-heading" for x in e):
            fails.append("пустой заголовок не пойман")

        s = hc.check_file(w("s.md", SKIP))
        if not any(x["kind"] == "skipped-level" for x in s):
            fails.append("пропуск уровня не пойман")

        # fence: ## внутри code НЕ считается заголовком → только B
        heads = hc._headings(FENCE)
        texts = [t for _l, t, _n in heads]
        if "не заголовок в коде" in texts:
            fails.append("заголовок в code-fence ложно учтён")
        if "B" not in texts:
            fails.append("реальный ## B не учтён")

        g = hc.check_file(w("g.md", GOOD))
        if g:
            fails.append("чистый док дал замечания: %s" % g)

        # крупный без нумерации
        big = "# T\n\n" + "\n".join("## раздел %d\n\nтекст" % i for i in range(40)) + "\n" * 320
        b = hc.check_file(w("big.md", big))
        if not any(x["kind"] == "large-no-numbering" for x in b):
            fails.append("крупный без нумерации не пойман")

    if fails:
        print("FAIL test_heading_check:")
        for x in fails:
            print("  -", x)
        sys.exit(1)
    print("OK test_heading_check: empty + skipped-level + fence-игнор + чистый + large-no-numbering")


if __name__ == "__main__":
    main()
