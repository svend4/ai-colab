"""
# ==========================================
# [FILE ID CARD]
# ID: tools.tests.test_header
# TYPE: active-script
# DOMAIN: core
# DEPTH_LEVEL: 1
# SUMMARY: Скрипт test_header.py. Описание сгенерировано автоматически.
# ==========================================
"""
"""Тест header.py — визитка-шапка файла (извлечение md/py, lint, board, покрытие)."""
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
import header

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

MD_FM = "---\nid: X-1\ntype: doc\ntitle: Заголовок\nstatus: proposed\ngist: краткая суть\n---\n\nтело\n"
MD_NOFM = "# Просто заголовок\n\nпервая строка прозы — суть\n"
MD_BAD = "просто текст без заголовка\n"
PY_DOC = '"""mytool.py — суть инструмента.\n\nподробно.\n"""\nimport os\n'
PY_NODOC = "import os\nx = 1\n"


def main():
    fails = []
    with tempfile.TemporaryDirectory() as d:
        def w(name, txt):
            p = os.path.join(d, name)
            open(p, "w", encoding="utf-8", newline="\n").write(txt)
            return p

        # md с front-matter → полная визитка
        c = header.card_of(w("a.md", MD_FM))
        if not c["ok"] or c["title"] != "Заголовок" or c["gist"] != "краткая суть":
            fails.append("md+fm: визитка неполная %s" % c)
        if c["id"] != "X-1" or c["type"] != "doc":
            fails.append("md+fm: id/type не извлечены")

        # md без front-matter → title из #, gist из прозы
        c2 = header.card_of(w("b.md", MD_NOFM))
        if not c2["ok"] or "заголовок" not in c2["title"].lower():
            fails.append("md-nofm: title не из # (%s)" % c2)
        if "суть" not in c2["gist"]:
            fails.append("md-nofm: gist не из прозы")

        # md без заголовка → неполная
        c3 = header.card_of(w("c.md", MD_BAD))
        if c3["ok"]:
            fails.append("md-bad: должна быть неполная визитка")

        # py с docstring → title — gist
        c4 = header.card_of(w("t.py", PY_DOC))
        if not c4["ok"] or c4["title"] != "mytool.py" or "суть" not in c4["gist"]:
            fails.append("py-doc: визитка из docstring неверна (%s)" % c4)
        if c4["type"] != "script":
            fails.append("py: type != script")

        # py без docstring → неполная
        c5 = header.card_of(w("n.py", PY_NODOC))
        if c5["ok"]:
            fails.append("py-nodoc: должна быть неполная")

        # lint возвращает только неполные
        bad = header.lint([w("ok.md", MD_FM), w("bad2.md", MD_BAD)])
        if len(bad) != 1:
            fails.append("lint: ожидал 1 неполную, факт %d" % len(bad))

    if fails:
        print("FAIL test_header:")
        for f in fails:
            print("  -", f)
        sys.exit(1)
    print("OK test_header: визитка md(fm/#)/py(docstring) + lint + поля + неполные")


if __name__ == "__main__":
    main()
