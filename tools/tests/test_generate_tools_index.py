#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ==========================================
# [FILE ID CARD]
# ID: tools.tests.test_generate_tools_index
# TYPE: active-script
# DOMAIN: core.generation
# DEPTH_LEVEL: 2
# SUMMARY: Тест GEN:tools-index (T-268/C3-a): полный индекс tools/*.py в README, фоллбэки описаний, --check.
# ==========================================
"""Тест автоиндекса инструментов в tools/README.md (T-268, аудит C3-a) — «самопроверено».

Контракты:
  1. collect/render: все не-тестовые tools/*.py попадают в таблицу; test_*.py — нет;
     описание из D-Card SUMMARY, плейсхолдер батч-генератора замещается докстрингом
     (в т.ч. вторым string-литералом после D-Card-докстринга) или HELP-константой;
     `|` в описании экранируется; рендер детерминирован.
  2. main() через subprocess на COLLAB_ROOT-фикстуре: блок заполняется; `--check`
     зелёный на свежем корне и ловит устаревание после правки инструмента (STALE).
  3. Опциональность маркера: корень без tools/README.md → WARN, rc=0 (песочницы
     не ломаются) — как counters (C17-b).

Пишется pytest-collectable (конвенция tools/tests/ по Q-W2-3/C13-c).
"""
# --- бутстрап путей (C14): тест живёт в tools/tests/, инструменты — в tools/.
import os as _os
import sys as _sys
_TOOLS_DIR = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
if _TOOLS_DIR not in _sys.path:
    _sys.path.insert(0, _TOOLS_DIR)
# --- конец бутстрапа ---

import os
import subprocess
import sys

import generate as g

BORDER = "# " + "=" * 42  # граница D-Card — как в реальных файлах/dcard_indexer.DCARD_REGEX


def _gen(marker):
    return "<!-- GEN:%s START -->\nстарое\n<!-- GEN:%s END -->\n" % (marker, marker)


def _write(root, rel, text):
    path = os.path.join(root, rel)
    os.makedirs(os.path.dirname(path) or root, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


# --- фикстурные инструменты: три паттерна описаний из реального tools/ ---
# a.py — настоящий D-Card SUMMARY (комментарий-блок), докстринг не должен использоваться
A_PY = ("#!/usr/bin/env python3\n"
        + BORDER + "\n# [FILE ID CARD]\n# ID: tools.a\n# TYPE: active-script\n"
        "# SUMMARY: Реальное описание A.\n" + BORDER + "\n"
        '"""Докстринг A — НЕ должен попасть в индекс (SUMMARY настоящий)."""\n')
# b.py — плейсхолдер SUMMARY + описание в ведущей HELP-константе (паттерн dispatch/conveyor)
B_PY = ('"""\n' + BORDER + "\n# [FILE ID CARD]\n# ID: tools.b\n"
        "# SUMMARY: Скрипт b.py. Описание сгенерировано автоматически.\n" + BORDER + '\n"""\n'
        'HELP = """b.py — описание из HELP-константы.\n\nдетали ниже.\n"""\n'
        "import os\n")
# c.py — плейсхолдер SUMMARY в D-Card-докстринге + описание во ВТОРОМ string-литерале
#         (паттерн adoption.py); `|` в описании обязан экранироваться в таблице
C_PY = ('"""\n' + BORDER + "\n# [FILE ID CARD]\n# ID: tools.c\n"
        "# SUMMARY: Скрипт c.py. Описание сгенерировано автоматически.\n" + BORDER + '\n"""\n'
        '"""c.py — второй докстринг: low | high.\n\nтело.\n"""\n')
# test_skip.py — тестовый файл: в индекс попадать НЕ должен
TEST_SKIP_PY = '"""Тестовый файл — не инструмент."""\n'


def _build_root(root, with_readme=True):
    """Минимальный COLLAB_ROOT: канон для generate.py + песочный tools/ (фикстура)."""
    _write(root, "STATUS.md", "# Статус\n\n" + _gen("counters") + "\n" + _gen("topics-status"))
    _write(root, "board.md", "# Доска\n\n" + _gen("topics-board"))
    _write(root, "TASKS.md", "# Задачи\n\n" + _gen("tasks"))
    _write(root, "QUESTIONS.md", "# Вопросы\n\n" + _gen("questions"))
    _write(root, "DECISIONS.md", "# Решения\n\n" + _gen("decisions"))
    _write(root, "topics/x.md", "---\nid: x\ntitle: Тема X\nstatus: open\nnext: шаг\n---\n# X\n")
    _write(root, "tools/a.py", A_PY)
    _write(root, "tools/b.py", B_PY)
    _write(root, "tools/c.py", C_PY)
    _write(root, "tools/test_skip.py", TEST_SKIP_PY)
    if with_readme:
        _write(root, "tools/README.md", "# tools\n\n## Полный индекс\n\n" + _gen("tools-index"))


def _run_generate(root, *args):
    env = dict(os.environ)
    env["COLLAB_ROOT"] = root
    env["PYTHONUTF8"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"
    proc = subprocess.run(
        [sys.executable, os.path.join(_TOOLS_DIR, "generate.py"), *args],
        env=env, capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    return proc.returncode, (proc.stdout or "") + (proc.stderr or "")


# ---------- слой 1: чистые функции ----------
def test_tools_doc_line_patterns():
    # обычный докстринг → первая строка
    assert g._tools_doc_line('"""Первая строка.\n\nвторая."""\n') == "Первая строка."
    # D-Card-докстринг ('#'-строки пропускаются) + второй string-литерал
    assert g._tools_doc_line(C_PY) == "c.py — второй докстринг: low | high."
    # HELP-константа после D-Card-докстринга
    assert g._tools_doc_line(B_PY) == "b.py — описание из HELP-константы."
    # нет ведущих строк-описаний / битый синтаксис → пусто (без исключений)
    assert g._tools_doc_line("import os\n") == ""
    assert g._tools_doc_line("def broken(:\n") == ""


def test_render_tools_index_deterministic():
    items = [{"name": "x.py", "summary": "Описание X."}]
    r1 = g.render_tools_index(items)
    assert r1 == g.render_tools_index(items), "недетерминизм render_tools_index"
    assert "| Инструмент | Назначение |" in r1
    assert "| `x.py` | Описание X. |" in r1
    assert "Всего не-тестовых инструментов: 1" in r1
    # маркер объявлен опциональным (корни без tools/README.md не ломаются)
    assert "tools-index" in g.OPTIONAL_MARKERS


# ---------- слой 2: main() через subprocess ----------
def test_tools_index_fill_and_check(tmp_path):
    root = str(tmp_path)
    _build_root(root)

    rc, out = _run_generate(root)
    assert rc == 0, "generate должен пройти (rc=%d):\n%s" % (rc, out)
    with open(os.path.join(root, "tools", "README.md"), encoding="utf-8") as f:
        readme = f.read()
    # охват: все не-тестовые инструменты; test_*.py исключён
    assert "| `a.py` | Реальное описание A. |" in readme, readme
    assert "| `b.py` | b.py — описание из HELP-константы. |" in readme, readme
    # `|` в описании экранирован — таблица не ломается
    assert r"| `c.py` | c.py — второй докстринг: low \| high. |" in readme, readme
    assert "test_skip.py" not in readme, "test_*.py не должен попадать в индекс"
    assert "Всего не-тестовых инструментов: 3" in readme, readme
    assert "Описание сгенерировано автоматически" not in readme, \
        "плейсхолдер должен замещаться докстрингом/HELP"
    assert "старое" not in readme.split("GEN:tools-index START")[1], \
        "плейсхолдер внутри GEN:tools-index не заменён"

    # --check на свежем корне: зелёный
    rc, out = _run_generate(root, "--check")
    assert rc == 0, "--check на свежем корне должен быть rc=0:\n%s" % out
    assert "STALE" not in out, out

    # правка инструмента (новый SUMMARY) → индекс устарел → --check ловит (acceptance T-268)
    _write(root, "tools/a.py", A_PY.replace("Реальное описание A.", "Новое описание A."))
    rc, out = _run_generate(root, "--check")
    assert rc == 1, "--check после правки инструмента должен валить (rc=%d):\n%s" % (rc, out)
    assert "STALE" in out and "tools/README.md" in out, out

    # новый инструмент без записи в индексе — тоже ловится
    _run_generate(root)  # освежить
    _write(root, "tools/d.py", '"""d.py — новый инструмент."""\n')
    rc, out = _run_generate(root, "--check")
    assert rc == 1 and "tools/README.md" in out, \
        "новый инструмент обязан делать индекс STALE:\n%s" % out


def test_tools_index_optional_without_readme(tmp_path):
    # корень без tools/README.md (песочницы/фикстуры): WARN, но не ERROR/rc=1 — как counters
    root = str(tmp_path)
    _build_root(root, with_readme=False)
    rc, out = _run_generate(root)
    assert rc == 0, "generate без tools/README.md должен пройти (rc=%d):\n%s" % (rc, out)
    assert "WARN: нет файла tools/README.md" in out, out
    assert "ERROR" not in out, "опциональная поверхность не должна давать ERROR:\n%s" % out
    rc, out = _run_generate(root, "--check")
    assert rc == 0 and "STALE" not in out, \
        "пропуск опциональной поверхности не должен считаться дрейфом:\n%s" % out


if __name__ == "__main__":
    # standalone-запуск (двухступенчатый канон: этот файл гоняет и test_all.py)
    import tempfile
    import shutil
    failed = 0
    test_tools_doc_line_patterns()
    test_render_tools_index_deterministic()
    for fn in (test_tools_index_fill_and_check, test_tools_index_optional_without_readme):
        tmp = tempfile.mkdtemp(prefix="tools_index_")
        try:
            fn(tmp)
        except AssertionError as e:
            failed += 1
            print("TEST FAIL (%s): %s" % (fn.__name__, e))
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
    if failed:
        sys.exit(1)
    print("TESTS OK generate_tools_index: doc-line фоллбэки (D-Card/второй докстринг/HELP) + "
          "рендер детерминирован + fill/--check (свежий→0, правка→STALE, новый инструмент→STALE) + "
          "опциональный маркер без tools/README.md")
    sys.exit(0)
