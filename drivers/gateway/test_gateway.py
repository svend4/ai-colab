#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тест gateway-композиции (T-093, покрытие находки M ревью T-078).

Тестирует gateway IN-PROCESS — импортирует модуль сервера и вызывает tool-функции
напрямую, БЕЗ поднятия stdio MCP-сервера. Поэтому тест:
- проверяет реальную композицию (files/repo-runner/workbench движки + проброс base_dir),
  redaction секретов, allowed-root confinement и аудит вызовов;
- не зависит от async stdio runtime (обходит Windows WinError 5) → переносим между средами.
"""
import os
import sys
import json
import tempfile
import shutil

HERE = os.path.dirname(os.path.abspath(__file__))


def run():
    base = tempfile.mkdtemp(prefix="gw_test_")
    audit_log = os.path.join(base, "audit.jsonl")
    os.environ["GATEWAY_BASE"] = base
    os.environ["DRIVER_AUDIT_LOG"] = audit_log
    sys.path.insert(0, HERE)
    ok = True
    try:
        import mcp_server as g  # загружает движки + регистрирует tools (без stdio-сервера)

        # фикстуры внутри allowed-root
        with open(os.path.join(base, "a.txt"), "w", encoding="utf-8") as f:
            f.write("hello world\napi_key=SUPERSECRETVALUE\nAKIA1234567890ABCD12\n")
        os.makedirs(os.path.join(base, "repo"))
        with open(os.path.join(base, "repo", "m.py"), "w", encoding="utf-8") as f:
            f.write("print('x')\n")

        # files_list
        lst = g.files_list(base)
        assert "a.txt" in lst, lst

        # files_read с redaction (секреты не должны утечь через композицию)
        rd = json.dumps(g.files_read("a.txt"), ensure_ascii=False)
        assert "SUPERSECRETVALUE" not in rd and "AKIA1234567890ABCD12" not in rd, "секрет не замаскирован"
        assert "***" in rd, "нет маркера маскировки"

        # files_search
        hits = g.files_search("hello", base)
        assert any(h.get("path") == "a.txt" for h in hits), hits

        # repo_inspect (read-only inventory)
        rep = g.repo_inspect("repo")
        assert isinstance(rep, dict), rep

        # memory_query на свежей БД (init создаёт схему в allowed-root)
        mem = g.memory_query("mem.db")
        assert isinstance(mem, list), mem

        # confinement: выход за allowed-root → ошибка
        try:
            g.files_read("../escape.txt")
            raise AssertionError("confinement не сработал (ожидалась PathAccessError)")
        except AssertionError:
            raise
        except Exception as e:
            assert "PathAccess" in type(e).__name__ or "outside" in str(e).lower(), \
                "ожидалась PathAccessError, получено %r" % e

        # аудит: запись по каждому вызову gateway
        lines = [json.loads(l) for l in open(audit_log, encoding="utf-8") if l.strip()]
        actions = {x["action"] for x in lines if x.get("driver") == "gateway"}
        need = {"files_list", "files_read", "files_search", "repo_inspect", "memory_query"}
        assert need <= actions, "не все вызовы зааудированы: %s" % (need - actions)

        print("TESTS OK gateway: composition+redaction+confinement+audit (audit lines=%d)" % len(lines))
    except AssertionError as e:
        ok = False
        print("TEST FAIL:", e)
    finally:
        os.environ.pop("GATEWAY_BASE", None)
        os.environ.pop("DRIVER_AUDIT_LOG", None)
        shutil.rmtree(base, ignore_errors=True)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(run())
