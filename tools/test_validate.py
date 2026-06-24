#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
# ==========================================
# [FILE ID CARD]
# ID: tools.test_validate
# TYPE: active-script
# DOMAIN: core
# DEPTH_LEVEL: 1
# SUMMARY: Скрипт test_validate.py. Описание сгенерировано автоматически.
# ==========================================
"""
"""
Hermetic-тесты валидатора канона (tools/validate.py).

Покрывают два слоя:
  1. Чистые helper-функции (table_rows, md_paths, _parse_inline_list, strip_code_fences)
     — детерминированно, без файловой системы.
  2. main() через subprocess на изолированном COLLAB_ROOT-фикстуре: проверяем
     контракт счётчиков OK/WARN/ERROR и код выхода (0 без ERROR, 1 с ERROR).

main() работает на module-level ROOT (COLLAB_ROOT/argv[1]), поэтому прогон через
subprocess с COLLAB_ROOT во временной папке — единственный способ инвариантного теста
без мутации реального репо (T-006).
"""
import os
import sys
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, "drivers"))
import validate as v
from test_tmp import temp_dir


def configure_output():
    for name in ("stdout", "stderr"):
        s = getattr(sys, name, None)
        if s is not None and hasattr(s, "reconfigure"):
            s.reconfigure(encoding="utf-8", errors="replace")


configure_output()


# ---------- фикстура минимального канона ----------
DECISIONS = """# Решения

<!-- GEN:decisions START -->
| ID | Решение | Статус | Дата | Файл |
|---|---|---|---|---|
| D-001 | Тест-решение | accepted | 2026-01-01 | `decisions/D-001.md` |
<!-- GEN:decisions END -->
"""

QUESTIONS = """# Вопросы

<!-- GEN:questions START -->
| ID | Вопрос | Статус | Кто задал | Кому | Где обсуждается | Итог |
|---|---|---|---|---|---|---|
| Q-001 | Вопрос? | answered | a | b | `questions/Q-001.md` | решено D-001 |
<!-- GEN:questions END -->
"""

TASKS = """# Задачи

<!-- GEN:tasks START -->
| ID | Задача | Статус | Ответственный | Тема | Следующий шаг |
|---|---|---|---|---|---|
| T-001 | Сделать | done | pool | `themes/x.md` | — |
<!-- GEN:tasks END -->
"""

BOARD = "# Доска\n\n| Тема | Файл |\n|---|---|\n| X | `themes/x.md` |\n"
STATUS = "# Статус\n\n| Тема | Где |\n|---|---|\n| X | `themes/x.md` |\n"


def _write(root, rel, text):
    path = os.path.join(root, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def _seed_source(root, dirname, fid, status, extra=""):
    fm = "---\nid: %s\ntype: %s\ntitle: T %s\nstatus: %s\n%s---\n# %s\n" % (
        fid, dirname[:-1], fid, status, extra, fid,
    )
    _write(root, "%s/%s.md" % (dirname, fid), fm)


def _build_valid_root(root):
    """Минимальный канон без ERROR (могут быть OK/WARN)."""
    _write(root, "DECISIONS.md", DECISIONS)
    _write(root, "QUESTIONS.md", QUESTIONS)
    _write(root, "TASKS.md", TASKS)
    _write(root, "board.md", BOARD)
    _write(root, "STATUS.md", STATUS)
    _write(root, "themes/x.md", "# X\n")
    _write(root, "questions/Q-001.md", "---\nid: Q-001\ntitle: q\nstatus: answered\n---\n# q\n")
    _seed_source(root, "decisions", "D-001", "accepted")
    _seed_source(root, "questions", "Q-001", "answered")
    _seed_source(root, "tasks", "T-001", "done")


def _run_validate(root):
    """Прогон validate.py как subprocess на изолированном COLLAB_ROOT.

    Возвращает (returncode, stdout). Парсим строку счётчиков OK=.. WARN=.. ERROR=..
    """
    env = dict(os.environ)
    env["COLLAB_ROOT"] = root
    env["PYTHONUTF8"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"
    proc = subprocess.run(
        [sys.executable, os.path.join(HERE, "validate.py")],
        env=env, capture_output=True, text=True, encoding="utf-8",
    )
    return proc.returncode, proc.stdout


def _counters(stdout):
    for line in stdout.splitlines():
        if line.startswith("OK=") and "ERROR=" in line:
            parts = dict(p.split("=") for p in line.split())
            return int(parts["OK"]), int(parts["WARN"]), int(parts["ERROR"])
    raise AssertionError("нет строки счётчиков в выводе:\n%s" % stdout)


def run():
    # ---- слой 1: чистые helper-функции ----
    rows = v.table_rows(
        "| T-001 | a | done |\n| skip | b | c |\n| T-002 | x | todo |", "T-"
    )
    assert [r[0] for r in rows] == ["T-001", "T-002"], rows
    assert v.md_paths("см `a/b.md` и `c.md`, не `x.txt`") == ["a/b.md", "c.md"]
    assert v._parse_inline_list("[a, b, c]") == ["a", "b", "c"]
    assert v._parse_inline_list("") == []
    assert "real" not in v.strip_code_fences("text ```real``` tail")

    # ---- слой 2: main() через subprocess ----
    with temp_dir("validate_ok_") as root:
        _build_valid_root(root)
        rc, out = _run_validate(root)
        ok, warn, err = _counters(out)
        assert rc == 0, "валидный канон не должен валить (rc=%d):\n%s" % (rc, out)
        assert err == 0, "валидный канон: ERROR=%d, ожидалось 0:\n%s" % (err, out)
        assert ok > 0, "ожидались OK-сообщения: %r" % out

    # ERROR-кейс A: done-задача ссылается на отсутствующий файл темы
    with temp_dir("validate_err_task_") as root:
        _build_valid_root(root)
        os.remove(os.path.join(root, "themes", "x.md"))
        rc, out = _run_validate(root)
        ok, warn, err = _counters(out)
        assert rc == 1, "пропавший deliverable done-задачи должен валить:\n%s" % out
        assert err >= 1, "ожидался хотя бы один ERROR:\n%s" % out

    # ERROR-кейс B: source без front-matter id
    with temp_dir("validate_err_fm_") as root:
        _build_valid_root(root)
        _write(root, "tasks/T-002.md", "# нет front-matter\nпросто текст\n")
        rc, out = _run_validate(root)
        ok, warn, err = _counters(out)
        assert rc == 1, "source без front-matter id должен валить:\n%s" % out
        assert err >= 1, out

    # ERROR-кейс C: answered-вопрос ссылается на несуществующее решение
    with temp_dir("validate_err_dref_") as root:
        _build_valid_root(root)
        q = QUESTIONS.replace("решено D-001", "решено D-999")
        _write(root, "QUESTIONS.md", q)
        rc, out = _run_validate(root)
        ok, warn, err = _counters(out)
        assert rc == 1, "ссылка на несуществующее D-999 должна валить:\n%s" % out
        assert err >= 1, out

    print("TESTS OK validate: helpers (table_rows/md_paths/inline-list/fences) + "
          "main() контракт OK/WARN/ERROR (valid→0, 3 ERROR-кейса→1)")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(run())
    except AssertionError as exc:
        print("TEST FAIL:", exc)
        sys.exit(1)
