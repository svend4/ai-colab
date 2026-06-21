#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sandbox intake DEMO — end-to-end S1->S3->S7 over `data/fixtures` (T-020 support).

Доказывает, что полный **read-only** intake-конвейер песочницы работает БЕЗ svend4 и
БЕЗ запуска кода: тема «заблокировано на svend4» превращается в показанный прогресс.

Что делает (всё read-only, execute-путь не вызывается):
  - берёт `data/fixtures` как «внешний источник»;
  - прогоняет его через `tools/sandbox.py` (S1 манифест + S3 read-only inventory через
    `drivers/repo-runner/inventory.py` + S7 markdown-отчёт) — переиспользуя `sandbox.intake`,
    НЕ реимплементируя его;
  - кладёт детерминированный манифест/отчёт `demo-fixtures` в `sandbox/reports/`
    (или в каталог `--out`).

Код фикстур НЕ исполняется. В манифесте `mode: read-only`; никакого `mode: execute` и
никакого вызова run/execute (gate — `docs/execute-sandbox-preflight.md`).

CLI:
    python tools/sandbox_intake_demo.py [--out <dir>]
"""
import os
import sys
import importlib.util

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOLS = os.path.join(ROOT, "tools")
FIXTURES = os.path.join(ROOT, "data", "fixtures")
DEMO_ID = "demo-fixtures"


def configure_output():
    for name in ("stdout", "stderr"):
        s = getattr(sys, name, None)
        if s is not None and hasattr(s, "reconfigure"):
            s.reconfigure(encoding="utf-8", errors="replace")


configure_output()


def _load_sandbox():
    """Load tools/sandbox.py as a module (reuse its S1/S3/S7 functions)."""
    path = os.path.join(TOOLS, "sandbox.py")
    spec = importlib.util.spec_from_file_location("sandbox_intake_demo_sb", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def run_demo(out_dir=None, source=FIXTURES, _sandbox=None):
    """
    Drive sandbox.intake over the fixtures as an external source, writing the
    deterministic `demo-fixtures` manifest + inventory report into `out_dir`
    (defaults to sandbox/reports/ via sandbox.py's own layout).

    STRICTLY read-only: this reuses sandbox.intake, which performs only S3
    read-only inventory (no code execution). The execute path is never enabled.

    `_sandbox` lets callers/tests inject an already-loaded sandbox module (so a
    test can observe the exact driver instance the demo drives); defaults to a
    fresh load of tools/sandbox.py.
    """
    src = os.path.abspath(os.path.expanduser(source))
    if not os.path.isdir(src):
        raise NotADirectoryError("фикстуры не найдены: %s" % src)

    sb = _sandbox if _sandbox is not None else _load_sandbox()

    # Redirect sandbox.py's output dirs to our --out (manifest -> inbox, report
    # -> reports). When --out is given, keep both under it so the demo is hermetic.
    if out_dir is not None:
        out = os.path.abspath(os.path.expanduser(out_dir))
        inbox = os.path.join(out, "inbox")
        reports = os.path.join(out, "reports")
        os.makedirs(inbox, exist_ok=True)
        os.makedirs(reports, exist_ok=True)
        sb.INBOX = inbox
        sb.REPORTS = reports

    note = "demo intake over data/fixtures (read-only, без svend4, без execute) — T-020"
    result = sb.intake(DEMO_ID, src, note=note)

    # Surface which sink was used so callers/tests can locate outputs.
    result["source"] = src
    result["report_dir"] = sb.REPORTS
    result["manifest_dir"] = sb.INBOX

    # sandbox.intake reads summary["files"], but the inventory driver emits
    # "total_files" — so result["files"] may be None upstream. Recompute the
    # read-only count here (same S3 scan_repo, no execution) so the demo
    # reliably proves files were inventoried.
    scan = sb.inv.scan_repo(src, base_dir=src)
    summary = scan.get("summary", {}) if isinstance(scan, dict) else {}
    result["inventoried_files"] = summary.get("total_files")
    result["structure"] = scan.get("structure", []) if isinstance(scan, dict) else []
    return result


def main():
    a = sys.argv[1:]
    if "--help" in a or "-h" in a:
        print(__doc__)
        return 0
    out_dir = None
    if "--out" in a:
        i = a.index("--out")
        if i + 1 >= len(a):
            print("ОШИБКА: --out требует путь")
            return 2
        out_dir = a[i + 1]
    try:
        r = run_demo(out_dir=out_dir)
    except Exception as exc:  # noqa: BLE001 - CLI boundary
        print("ОШИБКА: %s: %s" % (type(exc).__name__, exc))
        return 1
    print("demo-intake %s: файлов=%s рисков=%s (read-only, execute НЕ вызван)"
          % (DEMO_ID, r.get("inventoried_files"), r.get("risks")))
    print("  манифест: %s" % r["manifest"])
    print("  отчёт:    %s" % r["report"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
