#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
codex-local driver — безопасный мост к локальному Codex CLI (read-only detect).

ВАЖНО по безопасности (docs/driver-safety-policy.md, D-010): этот драйвер НЕ
запускает произвольные команды Codex. Разрешён только whitelist безвредных
read-only вызовов (`--version`, `--help`). Реальное делегирование задач Codex —
отдельный high-risk слой, требующий решения и песочницы.

ВНИМАНИЕ: написано без прогона (исполнение было недоступно). Перед использованием
прогнать `python drivers/codex-local/test_codex_local.py`.

CLI:
    python codex_local.py available
    python codex_local.py info
"""
import os
import sys
import json
import shutil
import subprocess

SAFE_FLAGS = {"--version", "--help"}
DEFAULT_TIMEOUT = 10


def configure_output():
    for name in ("stdout", "stderr"):
        s = getattr(sys, name, None)
        if s is not None and hasattr(s, "reconfigure"):
            s.reconfigure(encoding="utf-8", errors="replace")


configure_output()


def available():
    """Есть ли codex в PATH (read-only, ничего не запускает)."""
    return shutil.which("codex") is not None


def _run_safe(flag, timeout=DEFAULT_TIMEOUT):
    if flag not in SAFE_FLAGS:
        raise ValueError("разрешены только безопасные флаги: %s" % sorted(SAFE_FLAGS))
    path = shutil.which("codex")
    if not path:
        return None
    try:
        r = subprocess.run([path, flag], capture_output=True, text=True, timeout=timeout)
        return ((r.stdout or "") + (r.stderr or "")).strip()[:500]
    except Exception as exc:
        return "(не удалось: %s)" % type(exc).__name__


def info():
    """Наличие + версия Codex (через безопасный `codex --version`)."""
    path = shutil.which("codex")
    if not path:
        return {"available": False, "note": "codex не найден в PATH"}
    return {"available": True, "path": path, "version": _run_safe("--version")}


def main():
    a = sys.argv[1:]
    if not a:
        print(__doc__)
        return 2
    if a[0] == "available":
        print(json.dumps({"available": available()}))
        return 0
    if a[0] == "info":
        print(json.dumps(info(), ensure_ascii=False, indent=2))
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main())
