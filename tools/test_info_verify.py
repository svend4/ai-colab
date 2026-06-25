"""Тест info_verify.py — verify-контракт (тело-инвариант + верхушка-не-хуже)."""
import os
import sys

os.environ.setdefault("PYTHONUTF8", "1")
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import info_verify as iv

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass


def main():
    fails = []

    # _body: тело = после закрывающего front-matter
    if iv._body("---\nid: X\ntitle: T\n---\nТЕЛО атома\n") != "\nТЕЛО атома\n":
        fails.append("_body не извлёк тело после front-matter")
    if iv._body("без front-matter") != "без front-matter":
        fails.append("_body сломал текст без front-matter")
    # визитка (front-matter) НЕ часть тела → менять её не нарушает body-инвариант
    b1 = iv._body("---\ntitle: A\n---\nОДНО ТЕЛО")
    b2 = iv._body("---\ntitle: B\ngist: добавлен\n---\nОДНО ТЕЛО")
    if b1 != b2:
        fails.append("санация визитки (front-matter) ложно меняет тело")

    # verify: монкипатч snapshot = «текущее состояние»
    orig = iv.snapshot

    # (1) тело b.md изменилось → FAIL
    iv.snapshot = lambda: {"bodies": {"a.md": "h1", "b.md": "hX"}, "maturity_avg": 700, "h_top": 100}
    r = iv.verify({"bodies": {"a.md": "h1", "b.md": "h2"}, "maturity_avg": 700, "h_top": 100})
    if r["verdict"] != "FAIL" or "b.md" not in r["changed_bodies"]:
        fails.append("изменённое тело не дало FAIL: %s" % r["verdict"])

    # (2) тело цело + зрелость↑ + H↓ → PASS (валидный инфо-рефакторинг)
    iv.snapshot = lambda: {"bodies": {"a.md": "h1"}, "maturity_avg": 710, "h_top": 90}
    r2 = iv.verify({"bodies": {"a.md": "h1"}, "maturity_avg": 700, "h_top": 100})
    if r2["verdict"] != "PASS":
        fails.append("валидная санация не дала PASS: %s" % r2)

    # (3) тело цело, но зрелость УПАЛА → FAIL (деградация верхушки)
    iv.snapshot = lambda: {"bodies": {"a.md": "h1"}, "maturity_avg": 600, "h_top": 100}
    r3 = iv.verify({"bodies": {"a.md": "h1"}, "maturity_avg": 700, "h_top": 100})
    if r3["verdict"] != "FAIL":
        fails.append("падение зрелости не дало FAIL")

    # (4) удалённое тело → FAIL
    iv.snapshot = lambda: {"bodies": {}, "maturity_avg": 700, "h_top": 100}
    r4 = iv.verify({"bodies": {"a.md": "h1"}, "maturity_avg": 700, "h_top": 100})
    if r4["verdict"] != "FAIL" or "a.md" not in r4["removed_bodies"]:
        fails.append("удалённое тело не дало FAIL")

    iv.snapshot = orig

    if fails:
        print("FAIL test_info_verify:")
        for f in fails:
            print("  -", f)
        sys.exit(1)
    print("OK test_info_verify: _body + body-инвариант (изменено/удалено=FAIL) + зрелость↑=PASS/↓=FAIL + визитка≠тело")


if __name__ == "__main__":
    main()
