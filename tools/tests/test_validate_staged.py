# ast: allow-subprocess
#!/usr/bin/env python3
# [FILE ID CARD]
# id: tools/tests/test_validate_staged.py
# purpose: Тест быстрой staged-валидации — ловит битый front-matter/статус/ссылку,
#          пропускает валидные; fail-open при отсутствии git.
# mode: test (временный git-репо в системном temp, канон не трогает)
# related: tools/validate_staged.py
"""Самопроверка validate_staged.check() на fixture-репозитории."""
import importlib.util
import os
import subprocess
import sys
import tempfile

_TOOLS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_spec = importlib.util.spec_from_file_location("validate_staged",
                                               os.path.join(_TOOLS, "validate_staged.py"))
vs = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(vs)


def _git(cwd, *a):
    return subprocess.run(["git", *a], cwd=cwd, capture_output=True, text=True,
                          encoding="utf-8", errors="replace")


def _w(root, rel, text):
    p = os.path.join(root, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def _mkrepo():
    d = tempfile.mkdtemp(prefix="validate_staged_test_")  # системный temp, вне канона
    _git(d, "init", "-q")
    _git(d, "config", "user.email", "t@t")
    _git(d, "config", "user.name", "t")
    return d


def _check_staged(root, *rels):
    _git(root, "add", "--", *rels)
    cwd = os.getcwd()
    try:
        os.chdir(root)
        return vs.check(root)
    finally:
        os.chdir(cwd)


def test_valid_passes():
    d = _mkrepo()
    _w(d, "decisions/D-100.md", "---\nid: D-100\ntype: decision\nstatus: accepted\n---\n# D-100\n")
    _w(d, "tasks/T-100.md", "---\nid: T-100\ntype: task\nstatus: todo\n---\n# T-100\n")
    rc, errs = _check_staged(d, "decisions/D-100.md", "tasks/T-100.md")
    assert rc == 0, "валидные staged-файлы должны пройти: %s" % errs
    print("  OK: валидные проходят")


def test_bad_id_mismatch():
    d = _mkrepo()
    _w(d, "tasks/T-101.md", "---\nid: T-999\ntype: task\nstatus: todo\n---\n# x\n")
    rc, errs = _check_staged(d, "tasks/T-101.md")
    assert rc == 1 and any("id" in e for e in errs), "id != имя файла должно флажиться: %s" % errs
    print("  OK: id != имя файла отвергнут")


def test_bad_status():
    d = _mkrepo()
    _w(d, "decisions/D-102.md", "---\nid: D-102\ntype: decision\nstatus: mumbo\n---\n# x\n")
    rc, errs = _check_staged(d, "decisions/D-102.md")
    assert rc == 1 and any("статус" in e for e in errs), "плохой статус должен флажиться: %s" % errs
    print("  OK: недопустимый статус отвергнут")


def test_dangling_ref():
    d = _mkrepo()
    _w(d, "tasks/T-103.md", "---\nid: T-103\ntype: task\nstatus: todo\ndepends_on: [T-777]\n---\n# x\n")
    rc, errs = _check_staged(d, "tasks/T-103.md")
    assert rc == 1 and any("T-777" in e for e in errs), "битая ссылка должна флажиться: %s" % errs
    print("  OK: битая depends_on-ссылка отвергнута")


def test_no_staged_ok():
    d = _mkrepo()
    _w(d, "readme.txt", "not canon\n")
    _git(d, "add", "readme.txt")
    cwd = os.getcwd()
    try:
        os.chdir(d)
        rc, errs = vs.check(d)
    finally:
        os.chdir(cwd)
    assert rc == 0, "нет staged канон-файлов → OK: %s" % errs
    print("  OK: без staged канон-файлов — чисто")


def run():
    test_valid_passes()
    test_bad_id_mismatch()
    test_bad_status()
    test_dangling_ref()
    test_no_staged_ok()
    print("TESTS OK validate_staged: valid + id-mismatch + bad-status + dangling-ref + no-staged")


if __name__ == "__main__":
    run()
