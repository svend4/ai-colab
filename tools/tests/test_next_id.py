#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ==========================================
# [FILE ID CARD]
# ID: tools.tests.test_next_id
# TYPE: test
# DOMAIN: core.coordination
# DEPTH_LEVEL: 2
# SUMMARY: Проверяет next_id: монотонность, reservation_token, check/fill fencing.
# ==========================================
"""Hermetic-тест next_id: монотонная выдача id + reservation fencing.

Работает на временном дереве через COLLAB_ROOT (реальный канон tasks/decisions/
questions НЕ трогается). COLLAB_ROOT выставляется ДО import next_id, поэтому
next_id.ROOT указывает на фикстуру. Переиспользует drivers/test_tmp.make_temp_dir
и _canon.parse_front_matter для проверки, что стаб проходит как валидный front-matter.
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

HERE = _TOOLS_DIR  # tools/ — тест перенесён в tools/tests/ (C14)
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


def _fm(path):
    with open(path, encoding="utf-8") as f:
        return parse_front_matter(f.read())


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

        # 3) стаб валиден для validate.py: парсится front-matter с id/title/status + reservation
        fm1 = _fm(path1)
        assert fm1.get("id") == "T-008", fm1
        assert fm1.get("status") == "todo", fm1
        assert fm1.get("title"), "у стаба должен быть title (зарезервировано): %s" % fm1
        assert fm1.get("owner") == "tester", fm1  # --agent проброшен в стаб
        token1 = fm1.get("reservation_token")
        assert fm1.get("reserved_by") == "tester", fm1
        assert token1 and len(token1) == 12, fm1

        # 4) reservation check: верный агент+токен проходит, чужие данные отклоняются
        sys.argv = ["next_id.py", "check", "T-008", "--agent", "tester", "--token", token1]
        assert ni.main() == 0, "check с верным reservation_token должен проходить"
        sys.argv = ["next_id.py", "check", "T-008", "--agent", "other", "--token", token1]
        assert ni.main() == 1, "check с чужим agent должен отклоняться"
        sys.argv = ["next_id.py", "check", "T-008", "--agent", "tester", "--token", "badbadbad000"]
        assert ni.main() == 1, "check с чужим token должен отклоняться"

        # 5) fill: корректный token атомарно заменяет placeholder, id в source обязан совпадать
        fill_path = os.path.join(tmp, "fill-task.md")
        with open(fill_path, "w", encoding="utf-8", newline="\n") as f:
            f.write("---\nid: T-008\ntype: task\ntitle: Filled task\nstatus: todo\nowner: tester\n"
                    "priority: normal\nrisk: low\ndepends_on: []\nnext: filled via next_id.py fill\n---\n\n# T-008\n")
        sys.argv = ["next_id.py", "fill", "T-008", "--agent", "tester", "--token", token1, "--from", "fill-task.md"]
        assert ni.main() == 0, "fill с верным token должен проходить"
        assert _fm(path1).get("title") == "Filled task", _fm(path1)

        bad_fill_path = os.path.join(tmp, "bad-fill.md")
        token2 = _fm(path2).get("reservation_token")
        with open(bad_fill_path, "w", encoding="utf-8", newline="\n") as f:
            f.write("---\nid: T-999\ntype: task\ntitle: Wrong id\nstatus: todo\n---\n\n# wrong\n")
        sys.argv = ["next_id.py", "fill", "T-009", "--agent", "tester", "--token", token2, "--from", "bad-fill.md"]
        assert ni.main() == 1, "fill с несовпадающим id должен отклоняться"
        assert _fm(path2).get("title") == "(зарезервировано — заполните)", _fm(path2)

        # 6) другой тип (decision) тоже выдаётся и не конфликтует с пустого каталога -> D-001
        fnd, pathd = _issue(ni, "decision")
        assert fnd == "D-001.md", "decision с нуля должен быть D-001, получено %s" % fnd
        fmd = _fm(pathd)
        assert fmd.get("id") == "D-001" and fmd.get("type") == "decision", fmd
        assert fmd.get("reserved_by") == "tester" and fmd.get("reservation_token"), fmd

        # 7) псевдоним 't' эквивалентен 'task' и продолжает монотонную последовательность
        sys.argv = ["next_id.py", "t", "--agent", "tester"]
        before = set(os.listdir(tasks_dir))
        assert ni.main() == 0
        new = sorted(set(os.listdir(tasks_dir)) - before)
        assert new == ["T-010.md"], "псевдоним t должен дать T-010, получено %s" % new

        print("TESTS OK next_id: max+1/monotonic, reservation_token check/fill fencing, "
              "decision с нуля -> D-001, псевдоним t == task")
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