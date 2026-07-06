"""
# ==========================================
# [FILE ID CARD]
# ID: tools.code_pyramid
# TYPE: active-script
# DOMAIN: core
# DEPTH_LEVEL: 1
# SUMMARY: Скрипт code_pyramid.py. Описание сгенерировано автоматически.
# ==========================================
"""
"""code_pyramid.py — линт «3 слоёв» внутри .py (ответ на §3.3 вопросника триадности).

Markdown имеет 3-уровневую пирамиду (визитка→среднее→детальное); код — нет. Этот линт переносит
принцип НА КОД: слой 1 = ВИЗИТКА (module docstring), слой 2 = МЕНЮ (публичный API — top-level
функции/классы без `_` + main), слой 3 = ТЕЛО (приватные `_helpers` — реализация). Измеряет
пирамидальность: узкая верхушка (мало публичного) над широким телом (реализация). Триада
частный·средний·глобальный, применённая ВНУТРЬ файла (фрактал — вопросник §3.3.1/3.3.4).

Python это позволяет: имена резолвятся при ВЫЗОВЕ, не при def → публичный API можно ставить сверху.

CLI:
  python tools/code_pyramid.py <file.py>   # пирамида одного файла
  python tools/code_pyramid.py --board     # сводка по всем tools/*.py
  python tools/code_pyramid.py --json
"""
import os
from _ioutil import configure_output
from _cli import help_guard
import sys
import ast
import glob

configure_output()
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.environ.get("COLLAB_ROOT") or os.path.dirname(HERE)


def analyze(path):
    """3 слоя файла: визитка(docstring) · меню(публичный API) · тело(приватные _helpers)."""
    try:
        src = open(path, encoding="utf-8", errors="replace").read()
        mod = ast.parse(src)
    except (OSError, SyntaxError) as e:
        return {"file": path, "error": str(e)[:60]}
    # слой 1 — визитка: первый РЕАЛЬНЫЙ docstring (не FILE-ID-CARD)
    doc = ast.get_docstring(mod) or ""
    real_doc = doc if "[FILE ID CARD]" not in doc else ""
    if not real_doc:
        for node in mod.body:
            if (isinstance(node, ast.Expr) and isinstance(getattr(node, "value", None), ast.Constant)
                    and isinstance(node.value.value, str) and "[FILE ID CARD]" not in node.value.value):
                real_doc = node.value.value
                break
    # слои 2/3 — публичные(меню) vs приватные(тело) top-level def/class
    public, private = [], []
    for node in mod.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            (private if node.name.startswith("_") else public).append(node.name)
    has_main = "main" in public
    menu = [p for p in public if p != "main"]  # «меню» = публичное БЕЗ служебного main
    # документировано ли меню (публичные имена упомянуты в визитке)
    documented = sum(1 for m in menu if m in real_doc)
    return {
        "file": os.path.relpath(path, ROOT).replace("\\", "/"),
        "visitka": bool(real_doc.strip()),
        "menu": menu, "menu_n": len(menu), "body_n": len(private),
        "has_main": has_main, "documented_menu": documented,
        "flags": _flags(bool(real_doc.strip()), menu, private, has_main, documented),
    }


def _flags(visitka, menu, private, has_main, documented):
    f = []
    if not visitka:
        f.append("нет-визитки (нет реального docstring)")
    if not menu and not has_main:
        f.append("нет-меню (нет публичного API)")
    # «плоский»: много публичного, мало тела → нет инкапсуляции/слоёв
    if len(menu) >= 5 and len(private) == 0:
        f.append("плоский (нет тела/приватных _helpers — слои не разделены)")
    if menu and documented == 0:
        f.append("меню не документировано (публичные не упомянуты в визитке)")
    return f


def _pyramid_glyph(menu_n, body_n):
    """Узкая верхушка над широким телом = хорошая пирамида."""
    if menu_n == 0 and body_n == 0:
        return "—"
    if body_n >= menu_n:
        return "▲ пирамида (узкий верх, широкое тело)"
    return "▽ перевёрнута (публичного больше тела)"


def main(argv):
    help_guard(__doc__, argv)
    import json
    as_json = "--json" in argv
    args = [a for a in argv if not a.startswith("--")]
    if "--board" in argv or not args:
        rows = [analyze(p) for p in sorted(glob.glob(os.path.join(HERE, "*.py")))
                if not os.path.basename(p).startswith("test_")]
        rows = [r for r in rows if "error" not in r]
        if as_json:
            print(json.dumps(rows, ensure_ascii=False, indent=2)); return 0
        flagged = [r for r in rows if r["flags"]]
        with_v = sum(1 for r in rows if r["visitka"])
        pyr = sum(1 for r in rows if r["body_n"] >= r["menu_n"] and (r["menu_n"] or r["body_n"]))
        print("=== ПИРАМИДА КОДА — 3 слоя в .py (визитка·меню·тело), §3.3 вопросника ===")
        print("  тулов: %d · с визиткой: %d · пирамидальных (тело≥меню): %d · с флагами: %d" % (
            len(rows), with_v, pyr, len(flagged)))
        for r in sorted(flagged, key=lambda x: -len(x["flags"]))[:15]:
            print("    %-26s меню %d / тело %d  — %s" % (
                os.path.basename(r["file"]), r["menu_n"], r["body_n"], "; ".join(r["flags"])))
        return 0
    r = analyze(os.path.join(ROOT, args[0]) if not os.path.isabs(args[0]) else args[0])
    if as_json:
        print(json.dumps(r, ensure_ascii=False, indent=2)); return 0
    if "error" in r:
        print("code_pyramid: %s" % r["error"]); return 2
    print("=== ПИРАМИДА КОДА: %s ===" % r["file"])
    print("  Слой 1 — ВИЗИТКА (docstring): %s" % ("✓ есть" if r["visitka"] else "✗ нет"))
    print("  Слой 2 — МЕНЮ (публичный API): %d  [%s%s]" % (
        r["menu_n"], ", ".join(r["menu"][:8]), " …" if r["menu_n"] > 8 else ""))
    print("  Слой 3 — ТЕЛО (приватные _helpers): %d" % r["body_n"])
    print("  Форма: %s · меню документировано: %d/%d" % (
        _pyramid_glyph(r["menu_n"], r["body_n"]), r["documented_menu"], r["menu_n"]))
    if r["flags"]:
        print("  ⚠ " + " · ".join(r["flags"]))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
