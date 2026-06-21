#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Drift detector (C2, консенсус Claude+Codex) — один инструмент «не разошлось ли docs↔факт».

Агрегирует существующие проверки свежести (generate/drivers_catalog/capabilities `--check` +
validate) и добавляет текстовые проверки дрейфа документации: нумерация `L0-L8` вместо канона
`L0-L7` (находка J), legacy `queue.py` во входных инструкциях (актуально `pipeline.py`), orphan
`doing without active claim`. Печатает сводку дрейфа; exit 1 если есть дрейф, 0 если чисто.

    python tools/drift_check.py
"""
import os
import re
import sys
import glob
import subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def configure_output():
    for name in ("stdout", "stderr"):
        s = getattr(sys, name, None)
        if s is not None and hasattr(s, "reconfigure"):
            s.reconfigure(encoding="utf-8", errors="replace")


configure_output()


def _run(script, *args):
    p = subprocess.run([sys.executable, os.path.join(ROOT, "tools", script), *args],
                       cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace")
    return p.returncode, (p.stdout or "") + (p.stderr or "")


def scan_layer_drift(docs_dir):
    """Файлы docs/*.md с нумерацией L0-L8 (канон — L0-L7, ревью T-078 находка J)."""
    out = []
    for f in sorted(glob.glob(os.path.join(docs_dir, "*.md"))):
        try:
            txt = open(f, encoding="utf-8", errors="replace").read()
        except OSError:
            continue
        if re.search(r"L0[-–]L8", txt):
            out.append(os.path.basename(f))
    return out


def scan_legacy_queue(files):
    """Входные инструкции, всё ещё ссылающиеся на legacy queue.py (актуально pipeline.py)."""
    out = []
    for rel in files:
        p = os.path.join(ROOT, rel)
        if os.path.exists(p):
            txt = open(p, encoding="utf-8", errors="replace").read()
            if re.search(r"\bqueue\.py\b", txt):
                out.append(rel)
    return out


def run():
    drift = []

    # 1. свежесть генерируемых производных
    for script, label in (("generate.py", "навигация/index"),
                          ("drivers_catalog.py", "каталог драйверов"),
                          ("capabilities.py", "capability manifest")):
        rc, out = _run(script, "--check")
        if rc != 0 or "STALE" in out:
            drift.append("STALE: %s (%s --check)" % (label, script))

    # 2. здоровье канона
    rc, out = _run("validate.py")
    m = re.search(r"ERROR=(\d+)", out)
    if m and int(m.group(1)) > 0:
        drift.append("validate: ERROR=%s" % m.group(1))

    # 3. дрейф нумерации слоёв (J)
    for fn in scan_layer_drift(os.path.join(ROOT, "docs")):
        drift.append("нумерация L0-L8 вместо канона L0-L7: docs/%s" % fn)

    # 4. legacy queue.py во входных инструкциях
    for rel in scan_legacy_queue(["docs/quickstart.md", "docs/agent-quickstart.md", "README.md"]):
        drift.append("legacy queue.py во входной инструкции: %s (актуально pipeline.py)" % rel)

    # 5. orphan doing без claim
    rc, out = _run("pipeline.py", "status")
    for line in out.splitlines():
        if "doing without active claim" in line:
            drift.append("orphan: %s" % line.strip())

    return drift


def main():
    drift = run()
    if not drift:
        print("OK: дрейфа не обнаружено")
        return 0
    print("ДРЕЙФ обнаружен (%d):" % len(drift))
    for d in drift:
        print("  - " + d)
    return 1


if __name__ == "__main__":
    sys.exit(main())
