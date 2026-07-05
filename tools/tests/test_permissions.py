#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
# ==========================================
# [FILE ID CARD]
# ID: tools.tests.test_permissions
# TYPE: active-script
# DOMAIN: core
# DEPTH_LEVEL: 1
# SUMMARY: Скрипт test_permissions.py. Описание сгенерировано автоматически.
# ==========================================
"""
"""Тест permissions (tools/permissions.py) — glob-правила доступа match() + контракт main() rc."""
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
import json
import shutil

HERE = _TOOLS_DIR  # tools/ — тест перенесён в tools/tests/ (C14)
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, "drivers"))

from test_tmp import make_temp_dir  # noqa: E402


def configure_output():
    for name in ("stdout", "stderr"):
        s = getattr(sys, name, None)
        if s is not None and hasattr(s, "reconfigure"):
            s.reconfigure(encoding="utf-8", errors="replace")


configure_output()


def run():
    ok = True
    base = make_temp_dir("permissions_")
    # COLLAB_ROOT должен быть установлен ДО импорта модуля (читается на уровне модуля)
    os.environ["COLLAB_ROOT"] = base
    try:
        os.makedirs(os.path.join(base, "tools"), exist_ok=True)
        policy = {
            "claude": ["**"],
            "mavis": ["tasks/**", "docs/**", "*.md", "index.json"],
        }
        with open(os.path.join(base, "tools", "permissions.json"), "w", encoding="utf-8", newline="\n") as f:
            json.dump(policy, f)

        import permissions as p
        # ROOT в модуле должен указывать на наш temp (берётся из COLLAB_ROOT)
        assert p.ROOT == base, (p.ROOT, base)

        m = p.match
        # "**" разрешает всё
        assert m("anything/deep/x.py", "**") is True
        # "dir/**" — только внутри dir/
        assert m("tasks/T-1.md", "tasks/**") is True
        assert m("docs/x/y.md", "docs/**") is True
        assert m("tasksX/T-1.md", "tasks/**") is False, "префикс tasks/ обязателен с слэшем"
        assert m("other/T-1.md", "tasks/**") is False
        # "*.ext" — суффикс по расширению
        assert m("README.md", "*.md") is True
        assert m("a/b/c.md", "*.md") is True
        assert m("README.txt", "*.md") is False
        # точный путь
        assert m("index.json", "index.json") is True
        assert m("sub/index.json", "index.json") is False
        # нормализация backslash → forward slash (Windows-пути)
        assert m("tasks\\T-1.md", "tasks/**") is True, "backslash должен нормализоваться"

        # load_policy читает наш файл
        loaded = p.load_policy()
        assert loaded == policy, loaded

        # КОНТРАКТ main(): читает sys.argv[1:], возвращает int rc, печатает зону
        def call(*argv):
            saved = sys.argv
            sys.argv = ["permissions.py", *argv]
            try:
                return p.main()
            finally:
                sys.argv = saved

        # mavis пишет в разрешённую зону → rc 0
        rc = call("mavis", "tasks/T-1.md", "docs/a.md", "README.md", "index.json")
        assert rc == 0, "разрешённые пути → rc 0"
        # mavis пишет вне зоны (tools/x.py не покрыт) → rc 1
        rc = call("mavis", "tools/secret.py")
        assert rc == 1, "путь вне зоны → rc 1"
        # claude с "**" — всё разрешено
        rc = call("claude", "tools/secret.py", "whatever/x")
        assert rc == 0, "claude (**) → rc 0"
        # неизвестный агент → rc 1
        rc = call("ghost", "x.md")
        assert rc == 1, "агент не в политике → rc 1"
        # нет аргументов → usage rc 2
        rc = call()
        assert rc == 2, "пустые args → rc 2"

        print("TESTS OK permissions: match(** / dir/** / *.ext / exact + backslash-норм) + main rc(0 в зоне / 1 вне зоны / 1 неизв.агент / 2 usage)")
    except AssertionError as e:
        ok = False
        print("TEST FAIL:", e)
    except Exception as e:  # noqa: BLE001
        ok = False
        print("TEST ERROR:", repr(e))
    finally:
        os.environ.pop("COLLAB_ROOT", None)
        shutil.rmtree(base, ignore_errors=True)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(run())
