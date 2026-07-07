# ast: allow-subprocess
#!/usr/bin/env python3
# [FILE ID CARD]
# id: tools/tests/test_commit.py
# purpose: Тест безопасной обёртки commit.py — отказ на массовое удаление и на -A.
# mode: test (создаёт временный git-репозиторий в tmp-work, канон не трогает)
# related: tools/commit.py, D-026
"""Самопроверка tools/commit.py: safe-add дисциплина + D-026 порог удаления."""
import os
import subprocess
import sys
import tempfile

_TOOLS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COMMIT_PY = os.path.join(_TOOLS_DIR, "commit.py")


def _run(args, cwd):
    return subprocess.run(args, cwd=cwd, capture_output=True, text=True,
                          encoding="utf-8", errors="replace")


def _git(cwd, *a):
    return _run(["git", *a], cwd)


def _mkrepo():
    # ВАЖНО: системный temp, НЕ внутри канона — иначе git видит родительский .git
    # и commit.py уходит в реальный validate.py (зависание).
    d = tempfile.mkdtemp(prefix="commit_test_")
    _git(d, "init", "-q")
    _git(d, "config", "user.email", "t@t")
    _git(d, "config", "user.name", "t")
    # начальный коммит с 10 файлами
    for i in range(10):
        with open(os.path.join(d, f"f{i}.md"), "w", encoding="utf-8") as fh:
            fh.write(f"file {i}\n")
    _git(d, "add", "-A")
    _git(d, "commit", "-q", "-m", "init")
    return d


def _commit(cwd, *args):
    return _run([sys.executable, COMMIT_PY, *args], cwd)


def test_forbidden_add_all():
    d = _mkrepo()
    r = _commit(d, "-A", "-m", "bad")
    assert r.returncode == 1, f"ожидался отказ на -A, got {r.returncode}: {r.stdout}{r.stderr}"
    assert "запрещённые pathspec" in (r.stdout + r.stderr) or "ОТКАЗ" in (r.stdout + r.stderr)
    print("  OK: `-A` отвергнут")


def test_no_paths():
    d = _mkrepo()
    r = _commit(d, "-m", "no paths")
    assert r.returncode == 2, f"ожидался usage-отказ без путей, got {r.returncode}"
    print("  OK: пустые пути отвергнуты")


def test_mass_deletion_refused():
    d = _mkrepo()
    # удалить 8 файлов из рабочего дерева
    for i in range(8):
        os.remove(os.path.join(d, f"f{i}.md"))
    # попытаться закоммитить эти удаления явными путями
    paths = [f"f{i}.md" for i in range(8)]
    r = _commit(d, *paths, "-m", "mass delete")
    assert r.returncode == 1, f"ожидался отказ D-026 на 8 удалений, got {r.returncode}: {r.stdout}{r.stderr}"
    assert "D-026" in (r.stdout + r.stderr), "нет ссылки на D-026 в отказе"
    # staged не должен остаться (обёртка снимает)
    st = _git(d, "diff", "--cached", "--name-only").stdout.strip()
    assert st == "", f"staged должен быть снят после отказа, осталось: {st}"
    print("  OK: массовое удаление (8) отвергнуто по D-026, staged снят")


def test_small_deletion_allowed_with_flag():
    d = _mkrepo()
    os.remove(os.path.join(d, "f0.md"))
    r = _commit(d, "f0.md", "-m", "remove one, intentional", "--allow-deletions", "1")
    assert r.returncode == 0, f"ожидался успех при --allow-deletions 1, got {r.returncode}: {r.stdout}{r.stderr}"
    log = _git(d, "log", "--oneline").stdout
    assert "remove one" in log
    print("  OK: одиночное удаление с --allow-deletions 1 прошло")


def test_partial_deletion_cap_respected():
    # Регрессия (аудит 2026-07-07): --allow-deletions 2 при 4 удалениях должен ОТКАЗАТЬ.
    # Было max(N,5) → пропускало до 5 удалений вместо запрошенных N.
    d = _mkrepo()
    for i in range(4):
        os.remove(os.path.join(d, f"f{i}.md"))
    paths = [f"f{i}.md" for i in range(4)]
    r = _commit(d, *paths, "-m", "delete 4", "--allow-deletions", "2")
    assert r.returncode == 1, f"4 удаления при allow=2 → отказ, got {r.returncode}: {r.stdout}{r.stderr}"
    assert "D-026" in (r.stdout + r.stderr), "нет ссылки на D-026"
    print("  OK: --allow-deletions 2 не пропускает 4 удаления (порог = N, не max(N,5))")


def test_magic_pathspec_refused():
    # Регрессия (аудит 2026-07-07): git-магия ':(top)' стейджила всё дерево в обход набора.
    d = _mkrepo()
    with open(os.path.join(d, "sneaky.md"), "w", encoding="utf-8") as fh:
        fh.write("unnamed content\n")
    r = _commit(d, ":(top)", "-m", "broad sneaky stage")
    assert r.returncode == 1, f"':(top)' должен быть отвергнут, got {r.returncode}: {r.stdout}{r.stderr}"
    assert "pathspec" in (r.stdout + r.stderr).lower() or "ОТКАЗ" in (r.stdout + r.stderr)
    assert "broad sneaky" not in _git(d, "log", "--oneline").stdout, "ничего не должно быть закоммичено"
    print("  OK: магический pathspec ':(top)' отвергнут")


def test_normal_add_commits_without_no_verify():
    d = _mkrepo()
    with open(os.path.join(d, "new.md"), "w", encoding="utf-8") as fh:
        fh.write("new content\n")
    r = _commit(d, "new.md", "-m", "add new file")
    assert r.returncode == 0, f"обычный коммит должен пройти, got {r.returncode}: {r.stdout}{r.stderr}"
    assert "new.md" in _git(d, "show", "--name-only", "--format=", "HEAD").stdout
    print("  OK: обычный коммит одного файла прошёл без --no-verify")


def run():
    test_forbidden_add_all()
    test_no_paths()
    test_mass_deletion_refused()
    test_partial_deletion_cap_respected()
    test_magic_pathspec_refused()
    test_small_deletion_allowed_with_flag()
    test_normal_add_commits_without_no_verify()
    print("TESTS OK commit: safe-add + magic-pathspec + D-026 порог(N) + обычный коммит")


if __name__ == "__main__":
    run()
