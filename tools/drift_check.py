#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ==========================================
# [FILE ID CARD]
# ID: tools.drift_check
# TYPE: active-script
# DOMAIN: core.drift
# DEPTH_LEVEL: 1
# SUMMARY: Проверяет дрейф между документацией, generated-файлами, capabilities, drivers и validate.
# ==========================================
"""
Drift detector (C2, консенсус Claude+Codex) — один инструмент «не разошлось ли docs↔факт».

Агрегирует существующие проверки свежести (generate/drivers_catalog/capabilities `--check` +
validate) и добавляет текстовые проверки дрейфа документации: нумерация `L0-L8` вместо канона
`L0-L7` (находка J), legacy `queue.py` во входных инструкциях (актуально `pipeline.py`), orphan
`doing without active claim`. Печатает сводку дрейфа; exit 1 если есть дрейф, 0 если чисто.

    python tools/drift_check.py
"""
import os
import sys
from _ioutil import configure_output
import re
import glob
import json
import subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


configure_output()


def _run(script, *args):
    p = subprocess.run([sys.executable, os.path.join(ROOT, "tools", script), *args],
                       cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace")
    return p.returncode, (p.stdout or "") + (p.stderr or "")


# Маркеры строки, которая лишь *объясняет* дрейф L0-L8 (а не использует его как канон).
_LAYER_META = ("L0-L7", "L0–L7", "канон", "вместо", "находк", "расход", "9 уровн", "9 levels")
# Датированный отчёт/снимок — историческая запись, не живой канон; нумерацию слоёв в нём не сканируем.
_DATED = re.compile(r"\d{4}-\d{2}-\d{2}")


def scan_layer_drift(docs_dir):
    """Живые docs/*.md, использующие L0-L8 как нумерацию слоёв (канон — L0-L7, ревью T-078 находка J).

    Пропускаем: (1) датированные архивные отчёты (имя файла со YYYY-MM-DD); (2) строки, которые лишь
    упоминают L0-L8, объясняя сам дрейф (есть L0-L7/канон/вместо/находка/«9 уровней») — чтобы онбординг
    и манифесты, перечисляющие дрейф как пример, не давали ложных срабатываний (см. заметку T-130)."""
    out = []
    for f in sorted(glob.glob(os.path.join(docs_dir, "*.md"))):
        base = os.path.basename(f)
        if _DATED.search(base):
            continue
        try:
            txt = open(f, encoding="utf-8", errors="replace").read()
        except OSError:
            continue
        for line in txt.splitlines():
            if re.search(r"L0[-–]L8", line) and not any(m in line for m in _LAYER_META):
                out.append(base)
                break
    return out


def _assurance_currency_drift(out):
    """HIGH-находки секции currency из `assurance.py currency --json` как строки дрейфа.

    Только HIGH (битые СТРУКТУРНЫЕ ссылки + ссылки на superseded-решения) — это настоящий
    content-дрейф docs↔факт. Info-нудж «без last_verified» и структурные orphan-L1/flow сюда НЕ идут
    (это не дрейф, а известное состояние) — чтобы drift_check не шумел. Никогда не падает.
    """
    drift = []
    try:
        data = json.loads(out or "")
    except ValueError:
        return drift
    for s in data.get("sections", []):
        for f in s.get("findings", []):
            if f.get("level") == "high":
                drift.append("assurance currency: %s" % (f.get("msg") or ""))
    return drift


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

    # 2b. content-дрейф ссылок (assurance currency: битые структурные / superseded)
    rc, out = _run("assurance.py", "currency", "--json")
    drift.extend(_assurance_currency_drift(out))

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
