# ast: allow-subprocess
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
# ==========================================
# [FILE ID CARD]
# ID: tools.tests.test_validate
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

HERE = _TOOLS_DIR  # tools/ — тест перенесён в tools/tests/ (C14)
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


def _driver_fm(mode="read-only", status="draft", extra=""):
    """Полный driver-манифест (все required-поля check_drivers) для fixture-корня."""
    return (
        "---\nid: fx-driver\ntype: driver\ntitle: fixture driver\nstatus: %s\nlevel: L1\n"
        "mode: %s\nowner: test\nrisk: low\nactivation: manual\ninterfaces: [cli]\n"
        "inputs: [x]\noutputs: [y]\nsandbox: docker\nsecrets: none\n"
        "source_last_verified: 2099-01-01\ntimeout_seconds: 10\nmax_output_bytes: 1000\n"
        "audit: true\nrelated: [T-001]\n%s---\n# fixture driver\n" % (status, mode, extra)
    )


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


def _run_validate_argv(args):
    """Прогон validate.py с произвольным argv и БЕЗ COLLAB_ROOT (C48: разбор argv[1]).

    Возвращает (returncode, stdout, stderr): die() пишет в stderr, stdout чистый.
    """
    env = dict(os.environ)
    env.pop("COLLAB_ROOT", None)
    env["PYTHONUTF8"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"
    proc = subprocess.run(
        [sys.executable, os.path.join(HERE, "validate.py"), *args],
        env=env, capture_output=True, text=True, encoding="utf-8",
    )
    return proc.returncode, proc.stdout, proc.stderr


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

    # D-037 (волна 3): чистая логика case_collisions
    assert v.case_collisions(["a/Foo.md", "a/foo.md", "b.md"]) == [["a/Foo.md", "a/foo.md"]]
    assert v.case_collisions(["Docs/x.md", "docs/y.md"]) == [["Docs", "docs"]]
    assert v.case_collisions(["Docs/x.md", "docs/x.md"]) == [["Docs", "docs"]]
    assert v.case_collisions(["a.md", "b/a.md"]) == []

    # P10-b (волна 2): чистая логика D-023 (ownership индексов) — без git
    f1 = v.d023_findings(["tasks/T-001.md"])  # source без индекса
    assert len(f1) == 1 and "D-023" in f1[0] and "source" in f1[0], f1
    f2 = v.d023_findings(["index.json"])  # индекс без source
    assert len(f2) == 1 and "D-023" in f2[0], f2
    assert v.d023_findings(["tasks/T-001.md", "index.json"]) == []  # оба — согласовано
    assert v.d023_findings(["tools/x.py", "docs/y.md"]) == []  # не наш класс
    assert v.d023_findings([]) == []

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

    # WARN-кейс (C18): тема без front-matter title → WARN (не валит), тема названа в выводе
    with temp_dir("validate_warn_topic_") as root:
        _build_valid_root(root)
        _write(root, "topics/no-title.md", "# Тема без title\n\nтекст\n")
        rc, out = _run_validate(root)
        ok, warn, err = _counters(out)
        assert rc == 0, "тема без title не должна валить канон (rc=%d):\n%s" % (rc, out)
        assert err == 0, "тема без title должна давать WARN, не ERROR:\n%s" % out
        assert warn >= 1 and "topics/no-title.md" in out, \
            "ожидался WARN про topics/no-title.md:\n%s" % out

    # --- Волна 2: C7-a — D-014 execute_decision (ERROR-контур) ---
    # (A) mode: execute БЕЗ execute_decision → ERROR
    with temp_dir("validate_d014_nofield_") as root:
        _build_valid_root(root)
        _write(root, "drivers/fx-driver.md", _driver_fm(mode="execute"))
        rc, out = _run_validate(root)
        assert rc == 1, "execute без execute_decision должен валить:\n%s" % out
        assert "execute_decision" in out and "D-014" in out, out

    # (B) execute_decision указывает на proposed-решение → ERROR
    with temp_dir("validate_d014_proposed_") as root:
        _build_valid_root(root)
        _seed_source(root, "decisions", "D-050", "proposed")
        _write(root, "drivers/fx-driver.md", _driver_fm(mode="execute", extra="execute_decision: D-050\n"))
        rc, out = _run_validate(root)
        assert rc == 1, "execute_decision→proposed должен валить:\n%s" % out
        assert "D-050" in out and "accepted" in out, out

    # (C) execute_decision указывает на accepted → ОК; sandbox_runner.py кладём в fixture-tools
    # (presence проверяется относительно COLLAB_ROOT).
    with temp_dir("validate_d014_accepted_") as root:
        _build_valid_root(root)
        _seed_source(root, "decisions", "D-050", "accepted")
        os.makedirs(os.path.join(root, "tools"), exist_ok=True)
        _write(root, "tools/sandbox_runner.py", "# fixture runner\n")
        _write(root, "drivers/fx-driver.md", _driver_fm(mode="execute", extra="execute_decision: D-050\n"))
        rc, out = _run_validate(root)
        ok, warn, err = _counters(out)
        assert err == 0 and rc == 0, "accepted execute_decision не должен давать ERROR:\n%s" % out

    # --- Волна 2: C19-c — ссылка на несуществующий id в docs → WARN (не ERROR) ---
    with temp_dir("validate_docs_refs_") as root:
        _build_valid_root(root)
        _write(root, "docs/bad-ref.md", "# doc\nСм. D-999 и D-001; T-000 — плейсхолдер, не ловим.\n")
        rc, out = _run_validate(root)
        ok, warn, err = _counters(out)
        assert rc == 0 and err == 0, "битая ссылка в docs — WARN, не ERROR:\n%s" % out
        assert "D-999" in out and warn >= 1, "ожидался WARN про D-999:\n%s" % out
        assert "T-000" not in out, "плейсхолдер T-000 не должен флажиться:\n%s" % out

    # --- Волна 2: C29-b — proposed старше N дней без открытой задачи → WARN; с задачей → тишина ---
    with temp_dir("validate_untasked_") as root:
        _build_valid_root(root)
        _seed_source(root, "decisions", "D-777", "proposed", extra="date: 2020-01-01\n")
        rc, out = _run_validate(root)
        ok, warn, err = _counters(out)
        assert rc == 0 and err == 0, "stale proposed — WARN, не ERROR:\n%s" % out
        assert "D-777" in out and "без открытой задачи" in out, out
    with temp_dir("validate_tasked_") as root:
        _build_valid_root(root)
        _seed_source(root, "decisions", "D-777", "proposed", extra="date: 2020-01-01\n")
        _write(root, "tasks/T-002.md",
               "---\nid: T-002\ntype: task\ntitle: ratify\nstatus: todo\n---\n# Ратифицировать D-777\n")
        rc, out = _run_validate(root)
        assert "без открытой задачи" not in out, "связанная открытая задача должна гасить WARN:\n%s" % out

    # --- Волна 2: P10-b — D-015 driver-ready без verified_by ≥2 → WARN (не ERROR) ---
    with temp_dir("validate_d015_") as root:
        _build_valid_root(root)
        _write(root, "drivers/fx-driver.md", _driver_fm(status="ready"))
        rc, out = _run_validate(root)
        ok, warn, err = _counters(out)
        assert rc == 0 and err == 0, "D-015 нарушение — WARN, не ERROR:\n%s" % out
        assert "D-015" in out and "verified_by" in out, out
    with temp_dir("validate_d015_ok_") as root:
        _build_valid_root(root)
        _write(root, "drivers/fx-driver.md",
               _driver_fm(status="ready", extra="verified_by: [claude, codex]\n"))
        rc, out = _run_validate(root)
        assert "verified_by содержит" not in out, "verified_by ≥2 не должен давать WARN:\n%s" % out

    # C48-кейс A: мусорный флаг НЕ трактуется как ROOT — die() вместо ложного «канон сломан»
    rc, out, errout = _run_validate_argv(["--json"])
    assert rc == 2, "мусорный флаг должен давать exit 2 (die), получили rc=%d:\n%s\n%s" % (rc, out, errout)
    assert "отсутствует" not in out, "ложный «канон отсутствует» на мусорном флаге:\n%s" % out
    assert "--json" in errout, "в stderr нет внятной подсказки про аргумент:\n%r" % errout

    # C48-кейс B: несуществующий каталог как ROOT — тоже die(), а не ложные ERROR
    rc, out, errout = _run_validate_argv(["no-such-dir-xyz"])
    assert rc == 2, "несуществующий каталог должен давать exit 2:\n%s\n%s" % (out, errout)
    assert "no-such-dir-xyz" in errout, errout

    # C48-кейс C: позиционный ROOT (существующий каталог) по-прежнему принимается
    with temp_dir("validate_root_arg_") as root:
        _build_valid_root(root)
        rc, out, _ = _run_validate_argv([root])
        assert rc == 0, "валидный позиционный ROOT должен работать (rc=%d):\n%s" % (rc, out)

    # C48-кейс D: --help не задет проверкой argv (help_guard печатает docstring, exit 0)
    rc, out, _ = _run_validate_argv(["--help"])
    assert rc == 0 and "Валидатор" in out, "--help сломан (rc=%d):\n%s" % (rc, out)

    # D-037: Прогон на case-sensitive FS с case collisions
    with temp_dir("validate_case_") as root:
        _build_valid_root(root)
        fs_supports_case = True
        try:
            _write(root, "testCase", "a")
            _write(root, "testcase", "b")
            with open(os.path.join(root, "testCase")) as f:
                if f.read() == "b":
                    fs_supports_case = False
        except Exception:
            fs_supports_case = False

        if fs_supports_case:
            _write(root, "topics/Case.md", "---\nid: Case\ntype: topic\ntitle: Case\nstatus: open\n---\n")
            _write(root, "topics/case.md", "---\nid: case\ntype: topic\ntitle: case\nstatus: open\n---\n")
            rc, out = _run_validate(root)
            ok, warn, err = _counters(out)
            assert rc == 0, "Конфликт регистра должен давать WARN, не ERROR:\n%s" % out
            assert "Имена различаются только регистром" in out, "Ожидался WARN про регистр:\n%s" % out
            assert "topics/Case.md ↔ topics/case.md" in out or "topics/case.md ↔ topics/Case.md" in out, "Ожидались имена конфликтующих файлов в выводе:\n%s" % out

    print("TESTS OK validate: helpers (table_rows/md_paths/inline-list/fences/case_collisions) + "
          "main() контракт OK/WARN/ERROR (valid→0, 3 ERROR-кейса→1) + "
          "C18 WARN тема-без-title + C48 argv (флаг/битый ROOT→die 2, каталог→ok, --help→0) + "
          "волна2: C7 D-014 execute_decision (нет поля/proposed→ERROR, accepted→0) + "
          "C19-c docs-id WARN + C29-b stale-без-задачи WARN/с задачей тишина + "
          "P10-b D-015 verified_by WARN + D-023 d023_findings (чистая логика)")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(run())
    except AssertionError as exc:
        print("TEST FAIL:", exc)
        sys.exit(1)
