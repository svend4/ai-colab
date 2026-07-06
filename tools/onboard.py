# ast: allow-subprocess
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
# ==========================================
# [FILE ID CARD]
# ID: tools.onboard
# TYPE: active-script
# DOMAIN: core
# DEPTH_LEVEL: 1
# SUMMARY: Скрипт onboard.py. Описание сгенерировано автоматически.
# ==========================================
"""
"""
Onboard (C3, консенсус Claude+Codex) — одна команда входа вместо чтения 10 файлов.

Агрегирует для подключающегося агента/человека: capability manifest (C1), состояние конвейера,
дрейф (C2), указатели на онбординг-доки и (если передан агент) его активные задачи.

    python tools/onboard.py [agent]
"""
import os
import sys
from _ioutil import configure_output
from _cli import help_guard
import json
import subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CAPS = os.path.join(ROOT, "system-capabilities.json")

configure_output()

def _run(script, *args):
    p = subprocess.run([sys.executable, os.path.join(ROOT, "tools", script), *args],
                       cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace")
    return p.returncode, (p.stdout or "") + (p.stderr or "")

def _caps():
    try:
        with open(CAPS, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return None

def onboard(agent=None):
    line = "=" * 60
    print(line)
    print("AI-OS Bridge — onboard" + (" (%s)" % agent if agent else ""))
    print(line)

    c = _caps()
    if c:
        print("\nСтадия: %s" % c.get("stage", "?"))
        print("Драйверов: %s (ready %s)" % (c.get("drivers_total"), c.get("drivers_ready")))
        print("Политика execute: %s" % c.get("execute_policy", "?"))
        print("\nКлючевые команды:")
        for cmd in (c.get("commands") or [])[:5]:
            print("  %-46s — %s" % (cmd.get("cmd", ""), cmd.get("does", "")))
    else:
        print("\n(нет system-capabilities.json — запусти `python tools/capabilities.py snapshot`)")

    print("\nСейчас в конвейере:")
    _, out = _run("pipeline.py", "status")
    for lbl in ("В РАБОТЕ", "ГОТОВЫ К ВЗЯТИЮ", "ЗАБЛОКИРОВАН"):
        for ln in out.splitlines():
            if lbl in ln:
                print("  " + ln.strip())
                break

    print("\nДрейф (drift_check):")
    _, out = _run("drift_check.py")
    print("  " + (out.strip().splitlines() or ["?"])[0])

    print("\nЧитать:")
    print("  docs/agent-onboarding.md          — понять систему (человеку)")
    print("  docs/top-agent-operating-manual.md — команды/микро-инструкции (агенту)")
    print("  docs/bridge-usage.md              — как пользоваться слоем")
    print("  AGENTS.md / PROTOCOL.md           — правила и роли")

    if agent:
        print("\nТвои активные задачи:")
        _, out = _run("pipeline.py", "mine", agent)
        for ln in out.splitlines()[:8]:
            print("  " + ln.strip())

    print("\nДальше: `python tools/pipeline.py next %s` — взять задачу." % (agent or "<agent>"))
    print(line)
    return 0

def main():
    help_guard(__doc__)
    a = sys.argv[1:]
    agent = a[0] if a and not a[0].startswith("-") else None
    return onboard(agent)

if __name__ == "__main__":
    sys.exit(main())
