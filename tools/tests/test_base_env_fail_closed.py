#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Fail-closed для переменных зоны `*_BASE` (docs/files-driver-hardening.md, «Изменение 2026-10-16»).

Без переменной каждая точка входа драйверов отказывает и не берёт рабочую папку процесса.
MCP-серверы проверяют переменную до импорта mcp, поэтому модуль выполняется in-process без FastMCP
и должен поднять SystemExit с именем переменной. CLI проверяются через main(); позитивный прогон
workbench с WORKBENCH_BASE показывает, что штатный путь по-прежнему работает."""
import contextlib
import io
import os
import runpy
import shutil
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, "drivers"))
sys.path.insert(0, os.path.join(ROOT, "drivers", "workbench"))
from test_tmp import make_temp_dir
import ingest as ing
import workbench as wb

MCP_SERVERS = [
    ("drivers/files/mcp_server.py", "FILES_DRIVER_BASE"),
    ("drivers/repo-runner/mcp_server.py", "REPO_RUNNER_BASE"),
    ("drivers/git-log/mcp_server.py", "GIT_LOG_BASE"),
    ("drivers/data/mcp_server.py", "DATA_DRIVER_BASE"),
    ("drivers/sqlite/mcp_server.py", "SQLITE_DRIVER_BASE"),
    ("drivers/gateway/mcp_server.py", "GATEWAY_BASE"),
]


@contextlib.contextmanager
def _environ(**values):
    """Временно задаёт переменные окружения: None — снять, строка — задать. Восстанавливает всё."""
    saved = {k: os.environ.get(k) for k in values}
    try:
        for k, v in values.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        yield
    finally:
        for k, v in saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v


@contextlib.contextmanager
def _argv(*args):
    saved = sys.argv
    sys.argv = list(args)
    try:
        yield
    finally:
        sys.argv = saved


def _load_server(rel):
    return runpy.run_path(os.path.join(ROOT, rel), run_name="base_env_check")


class BaseEnvFailClosedTest(unittest.TestCase):
    def test_mcp_servers_refuse_to_start_without_base(self):
        for rel, name in MCP_SERVERS:
            with self.subTest(server=rel), _environ(**{name: None}):
                with self.assertRaises(SystemExit) as cm:
                    _load_server(rel)
                self.assertIn(name, str(cm.exception.code))

    def test_blank_base_counts_as_unset(self):
        with _environ(FILES_DRIVER_BASE="   "):
            with self.assertRaises(SystemExit) as cm:
                _load_server("drivers/files/mcp_server.py")
        self.assertIn("FILES_DRIVER_BASE", str(cm.exception.code))

    def test_workbench_cli_refuses_without_base(self):
        out = io.StringIO()
        with _environ(WORKBENCH_BASE=None), _argv("workbench.py", "init", "x.db"), \
                contextlib.redirect_stdout(out):
            rc = wb.main()
        self.assertEqual(rc, 2, out.getvalue())
        self.assertIn("WORKBENCH_BASE", out.getvalue())

    def test_ingest_cli_refuses_without_base(self):
        out = io.StringIO()
        with _environ(WORKBENCH_BASE=None, INGEST_SOURCE_BASE=None), \
                _argv("ingest.py", "repo", "x.db", "."), contextlib.redirect_stdout(out):
            rc = ing.main()
        self.assertEqual(rc, 2, out.getvalue())
        self.assertIn("WORKBENCH_BASE", out.getvalue())
        self.assertIn("INGEST_SOURCE_BASE", out.getvalue())

    def test_workbench_cli_works_with_base(self):
        tmp = make_temp_dir("base_env_fail_closed_")
        try:
            out = io.StringIO()
            with _environ(WORKBENCH_BASE=tmp), \
                    _argv("workbench.py", "init", os.path.join(tmp, "wb.db")), \
                    contextlib.redirect_stdout(out):
                rc = wb.main()
            self.assertEqual(rc, 0, out.getvalue())
            self.assertIn('"ok": true', out.getvalue())
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
