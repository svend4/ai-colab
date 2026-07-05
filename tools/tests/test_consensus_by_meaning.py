"""Тест consensus_by_meaning.py — вес по свидетелям, не по счёту (денежный кадр)."""
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
import consensus_by_meaning as cm

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass


def _v(d, name, model, lens, bullets):
    body = "".join("- %s\n" % b for b in bullets)
    txt = "---\nmodel: %s\nlens: %s\nsealed: blind\n---\n%s" % (model, lens, body)
    p = os.path.join(d, name)
    open(p, "w", encoding="utf-8", newline="\n").write(txt)
    return p


def main():
    fails = []
    with tempfile.TemporaryDirectory() as d:
        # v1,v2 — КЛОНЫ (m1/L1), оба заявляют «alpha shared claim»
        v1 = _v(d, "v1.md", "m1", "L1", ["alpha shared claim here", "beta unique one here"])
        v2 = _v(d, "v2.md", "m1", "L1", ["alpha shared claim here", "gamma unique two here"])
        # v3,v4 — НЕЗАВИСИМЫ (m2/L2, m3/L3), оба заявляют «delta core principle»
        v3 = _v(d, "v3.md", "m2", "L2", ["delta core principle here", "omega specific three here"])
        v4 = _v(d, "v4.md", "m3", "L3", ["delta core principle here", "sigma different four here"])

        r = cm.consensus([v1, v2, v3, v4])
        core_txt = " || ".join(c["text"] for c in r["core"])
        minor_txt = {c["text"]: c for c in r["minor"]}

        # ЯДРО: «delta core principle» — 2 независимых свидетеля
        delta = [c for c in r["core"] if "delta core principle" in c["text"]]
        if not delta or delta[0]["witnesses"] != 2:
            fails.append("delta должен быть в ЯДРЕ с 2 свидетелями: core=%s" % core_txt)

        # МИНОР + ДЕНЕЖНЫЙ КАДР: «alpha shared claim» — 2 ВХОЖДЕНИЯ, но 1 СВИДЕТЕЛЬ (клоны)
        alpha = [c for c in r["minor"] if "alpha shared claim" in c["text"]]
        if not alpha:
            fails.append("alpha должен быть в МИНОРЕ (клоны=1 свидетель), а не в ядре")
        elif not (alpha[0]["witnesses"] == 1 and alpha[0]["occurrences"] == 2):
            fails.append("alpha: ожидается свидетель=1, вхождений=2 (денежный кадр): %s" % alpha[0])

        # alpha НЕ должен попасть в ядро несмотря на 2 вхождения (отличие от счётчика!)
        if "alpha shared claim" in core_txt:
            fails.append("alpha попал в ЯДРО по счёту — провал замены счётчика")

        # уникальные claim — минор, 1 свидетель, сохранены
        if not any("beta unique one" in c["text"] for c in r["minor"]):
            fails.append("уникальный beta должен быть СОХРАНЁН в миноре")

    if fails:
        print("FAIL test_consensus_by_meaning:")
        for f in fails:
            print("  -", f)
        sys.exit(1)
    print("OK test_consensus_by_meaning: ядро=2-независимых · alpha 2-вхожд/1-свидетель→минор (не ядро) · минор сохранён")


if __name__ == "__main__":
    main()
