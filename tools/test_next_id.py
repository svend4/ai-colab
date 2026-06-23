#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Hermetic-тест next_id: монотонная выдача id + атомарное создание валидного стаба.

Работает на временном дереве через COLLAB_ROOT (реальный канон tasks/decisions/
questions НЕ трогается). COLLAB_ROOT выставляется ДО import next_id, поэтому
next_id.ROOT указывает на фикстуру. Переиспользует drivers/test_tmp.make_temp_dir
и _canon.parse_front_matter для проверки, что стаб проходит как валидный front-matter.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, "drivers"))


def configure_output():
    for name in ("stdout", "stderr"):
        s = getattr(sys, name, None)
        if s is not None and hasattr(s, "reconfigure"):
            s.reconfigure(encoding="utf-8", errors="replace")


configure_output()

import test_tmp  # drivers/test_tmp.py
from _canon import parse_front_matter


def _issue(ni, kind):
    """Вызвать next_id.main для kind, вернуть выданный id (по факту нового файла в каталоге)."""
    subdir, prefix = ni.TYPES[kind]
    dirpath = os.path.join(ni.ROOT, subdir)
    before = set(os.listdir(dirpath)) if os.path.isdir(dirpath) else set()
    sys.argv = ["next_id.py", kind, "--agent", "tester"]
    rc = ni.main()
    assert rc == 0, "next_id.main(%s) rc=%s" % (kind, rc)
    after = set(os.listdir(dirpath))
    new = sorted(after - before)
    assert len(new) == 1, "ожидался ровно один новый файл, получено: %s" % new
    return new[0], os.path.join(dirpath, new[0])


def run():
    ok = True
    tmp = test_tmp.make_temp_dir("next-id-")
    try:
        # предзаполняем tasks существующими id, чтобы проверить max+1 (а не «с нуля»)
        tasks_dir = os.path.join(tmp, "tasks")
        os.makedirs(tasks_dir, exist_ok=True)
        for n in (3, 7):  # max существующий = T-007
            with open(os.path.join(tasks_dir, "T-%03d.md" % n), "w",
                      encoding="utf-8", newline="\n") as f:
                f.write("---\nid: T-%03d\ntype: task\nstatus: todo\n---\n" % n)

        os.environ["COLLAB_ROOT"] = tmp
        import next_id as ni
        assert ni.ROOT == tmp, "next_id.ROOT не указывает на фикстуру: %s" % ni.ROOT

        # 1) первая выдача = max+1 = T-008
        fn1, path1 = _issue(ni, "task")
        assert fn1 == "T-008.md", "ожидался T-008 (max+1), получено %s" % fn1

        # 2) монотонность: следующая выдача строго больше
        fn2, path2 = _issue(ni, "task")
        assert fn2 == "T-009.md", "ожидался монотонный T-009, получено %s" % fn2

        # 3) стаб валиден для validate.py: парсится front-matter с id/title/status
        with open(path1, encoding="utf-8") as f:
            fm = parse_front_matter(f.read())
        assert fm.get("id") == "T-008", fm
        assert fm.get("status") == "todo", fm
        assert fm.get("title"), "у стаба должен быть title (зарезервировано): %s" % fm
        assert fm.get("owner") == "tester", fm  # --agent проброшен в стаб

        # 4) другой тип (decision) тоже выдаётся и не конфликтует с пустого каталога -> D-001
        fnd, pathd = _issue(ni, "decision")
        assert fnd == "D-001.md", "decision с нуля должен быть D-001, получено %s" % fnd
        with open(pathd, encoding="utf-8") as f:
            fmd = parse_front_matter(f.read())
        assert fmd.get("id") == "D-001" and fmd.get("type") == "decision", fmd

        # 5) псевдоним 't' эквивалентен 'task' и продолжает монотонную последовательность
        sys.argv = ["next_id.py", "t", "--agent", "tester"]
        before = set(os.listdir(tasks_dir))
        assert ni.main() == 0
        new = sorted(set(os.listdir(tasks_dir)) - before)
        assert new == ["T-010.md"], "псевдоним t должен дать T-010, получено %s" % new

        print("TESTS OK next_id: max+1 (T-008) -> монотонно (T-009/T-010), стаб валиден "
              "(id/status/title/owner), decision с нуля -> D-001, псевдоним t == task")
    except AssertionError as e:
        ok = False
        print("TEST FAIL:", e)
    finally:
        import shutil
        os.environ.pop("COLLAB_ROOT", None)
        shutil.rmtree(tmp, ignore_errors=True)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(run())
