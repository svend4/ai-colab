#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
# ==========================================
# [FILE ID CARD]
# ID: tools.code_activation
# TYPE: active-script
# DOMAIN: core.activation
# DEPTH_LEVEL: 1
# SUMMARY: Read-only activation plan for code artifacts; no execute.
# ==========================================
"""
"""
Code activation plan.

This tool integrates the existing no-execute draft-code lane, D-014 execute gate,
D-033 autonomy discipline, and execute-sandbox preflight components into one
read-only activation card. It never runs target code, installs dependencies,
imports target modules, mutates decisions, or grants execute permission.

Commands:
    python tools/code_activation.py plan <target> [--driver-id <id>] [--json]
    python tools/code_activation.py plan <target> [--json] --command docker run ...

The optional --command is checked statically for D-014-style isolation/limits. The
command is not executed and backend probes are not run by this tool.
"""
import argparse
import glob
import json
import os
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = Path(os.environ.get("COLLAB_ROOT", str(HERE.parent))).resolve()
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from _cli import help_guard
from _ioutil import configure_output

configure_output()

SCHEMA = "code_activation_plan.v1"


def _repo_path(path):
    raw = Path(path)
    return raw if raw.is_absolute() else ROOT / raw


def _inside_repo(path):
    try:
        Path(path).resolve().relative_to(ROOT)
        return True
    except ValueError:
        return False


def _rel(path):
    try:
        return Path(path).resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return str(path).replace("\\", "/")


def _read_text(path):
    try:
        return Path(path).read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def _parse_front_matter(text):
    fm = {}
    if not text.startswith("---"):
        return fm
    end = text.find("\n---", 3)
    if end < 0:
        return fm
    for line in text[3:end].splitlines():
        m = re.match(r"^([A-Za-z0-9_-]+):\s*(.*)$", line)
        if m:
            fm[m.group(1)] = m.group(2).strip()
    return fm


def _decision_status(decision_id):
    path = ROOT / "decisions" / (decision_id + ".md")
    fm = _parse_front_matter(_read_text(path))
    return {"id": decision_id, "path": _rel(path), "exists": path.exists(), "status": fm.get("status")}


def _scan_execute_drivers():
    hits = []
    for path in sorted(glob.glob(str(ROOT / "drivers" / "*.md"))):
        text = _read_text(path)
        if re.search(r"(?m)^mode:\s*execute\s*$", text):
            hits.append(_rel(path))
    return hits


def _approval_status(driver_id):
    path = ROOT / "sandbox" / "approvals" / (driver_id + "_approval.md")
    fm = _parse_front_matter(_read_text(path))
    return {
        "driver_id": driver_id,
        "path": _rel(path),
        "exists": path.exists(),
        "status": fm.get("status") if fm else None,
        "approved": fm.get("status") == "approved" if fm else False,
    }


def _target_kind(relpath, full):
    if relpath.startswith("sandbox/drafts/"):
        return "draft-code"
    if relpath.startswith("sandbox/"):
        return "sandbox-artifact"
    if relpath.startswith("tools/") and full.suffix == ".py":
        return "repo-tool"
    if relpath.startswith("drivers/"):
        return "driver"
    if full.suffix == ".py":
        return "python-code"
    return "repo-artifact"


def _target_info(target):
    full = _repo_path(target).resolve()
    inside = _inside_repo(full)
    relpath = _rel(full) if inside else str(target)
    exists = full.exists() if inside else False
    kind = _target_kind(relpath, full) if inside else "outside-repo"
    manifest = None
    if exists and full.is_dir() and (full / "manifest.json").exists():
        try:
            manifest = json.loads((full / "manifest.json").read_text(encoding="utf-8"))
        except Exception as exc:
            manifest = {"error": str(exc)}
    elif exists and full.is_file() and full.name == "manifest.json":
        try:
            manifest = json.loads(full.read_text(encoding="utf-8"))
        except Exception as exc:
            manifest = {"error": str(exc)}
    return {"input": target, "path": relpath, "exists": exists, "inside_repo": inside, "kind": kind, "manifest": manifest}


def _autonomy_summary(require):
    try:
        import autonomy_guard
        rows = autonomy_guard.scan(require=require)
        flags = [r for r in rows if r.get("verdict") == "flag"]
        warns = [r for r in rows if r.get("verdict") == "warn"]
        verdict = "flag" if flags else ("warn" if warns else "ok")
        return {"available": True, "verdict": verdict, "total": len(rows), "flags": len(flags), "warns": len(warns)}
    except Exception as exc:
        return {"available": False, "verdict": "unknown", "error": str(exc), "total": 0, "flags": 0, "warns": 0}


def _static_command_check(command):
    if not command:
        return {"provided": False, "verdict": "not-checked", "issues": []}
    issues = []
    try:
        import execute_preflight
        ok_iso, msg_iso = execute_preflight.check_sandbox_isolation(command)
        ok_lim, msg_lim = execute_preflight.check_sandbox_limits(command)
        if not ok_iso:
            issues.append(msg_iso)
        if not ok_lim:
            issues.append(msg_lim)
        return {"provided": True, "verdict": "ok" if not issues else "blocked", "issues": issues,
                "notes": [msg_iso, msg_lim], "executed": False}
    except Exception as exc:
        return {"provided": True, "verdict": "unknown", "issues": [str(exc)], "executed": False}


def _gate(gate_id, status, required, note):
    return {"id": gate_id, "status": status, "required": required, "note": note}


def activation_plan(target, driver_id="code-activation", require_confirmations=2, command=None):
    target_info = _target_info(target)
    d014 = _decision_status("D-014")
    execute_drivers = _scan_execute_drivers()
    approval = _approval_status(driver_id)
    autonomy = _autonomy_summary(require_confirmations)
    static_cmd = _static_command_check(command or [])

    gates = []
    gates.append(_gate("D-014-policy", "ok" if d014.get("status") == "accepted" else "blocked", True,
                       "generic execute-off policy must be accepted"))
    gates.append(_gate("target-inside-repo", "ok" if target_info["inside_repo"] else "blocked", True,
                       "activation target must stay inside workspace"))
    gates.append(_gate("target-exists", "ok" if target_info["exists"] else "blocked", True,
                       "target must exist before activation review"))
    gates.append(_gate("active-execute-drivers", "ok" if not execute_drivers else "blocked", True,
                       "no driver manifest may already be mode: execute"))
    gates.append(_gate("specific-accepted-run-decision", "open", True,
                       "D-014 requires a separate accepted decision for the concrete execute scenario"))
    gates.append(_gate("human-first-run", "ok" if approval["approved"] else "open", True,
                       "Gate 10 requires explicit human first-run approval"))
    gates.append(_gate("autonomy-guard", autonomy["verdict"] if autonomy["available"] else "unknown", False,
                       "D-033 advisory detector for autonomous accepted decisions"))
    gates.append(_gate("static-command-preflight", static_cmd["verdict"], bool(command),
                       "optional command is checked statically only; no backend probe and no execution"))

    blockers = []
    for gate in gates:
        if gate["required"] and gate["status"] in ("blocked", "open", "unknown"):
            blockers.append("%s: %s" % (gate["id"], gate["note"]))
    if static_cmd.get("verdict") == "blocked":
        blockers.extend("static command: %s" % issue for issue in static_cmd.get("issues", []))

    next_commands = []
    if target_info["kind"] == "draft-code":
        next_commands.append("python tools\\draft_code.py check %s --json" % target_info["path"])
        next_commands.append("python tools\\draft_code.py review %s --json" % target_info["path"])
    elif target_info["path"].endswith(".py") and target_info["inside_repo"] and target_info["exists"]:
        next_commands.append("python -X utf8 -m py_compile %s" % target_info["path"].replace("/", "\\"))
    next_commands.append("python tools\\autonomy_guard.py --json")
    next_commands.append("python tools\\validate.py")
    next_commands.append("python tools\\generate.py --check")
    if not approval["approved"]:
        next_commands.append("python tools\\execute_human_gate.py request %s \"<reviewed command pattern>\"" % driver_id)
    if command:
        next_commands.append("python tools\\execute_preflight.py check-command %s" % " ".join(command))

    state = "ready-for-static-review" if not blockers[:3] else "blocked"
    if blockers:
        state = "blocked"

    return {
        "schema": SCHEMA,
        "mutates": False,
        "mode": "read-only-preflight",
        "target": target_info,
        "driver_id": driver_id,
        "state": state,
        "execution_allowed": False,
        "execution_reason": "D-014 keeps execute OFF until a concrete accepted run decision and all gates are closed",
        "d014": d014,
        "approval": approval,
        "autonomy_guard": autonomy,
        "execute_drivers": execute_drivers,
        "static_command": static_cmd,
        "gates": gates,
        "blockers": blockers,
        "next_commands": next_commands,
    }


def print_text(payload):
    print("# Code activation plan")
    print("")
    print("target: `%s`" % payload["target"]["path"])
    print("state: `%s`" % payload["state"])
    print("execution_allowed: `false`")
    print("")
    print("## Gates")
    for gate in payload["gates"]:
        print("- `%s`: `%s` - %s" % (gate["id"], gate["status"], gate["note"]))
    if payload["blockers"]:
        print("")
        print("## Blockers")
        for item in payload["blockers"]:
            print("- %s" % item)
    print("")
    print("## Next commands")
    print("")
    print("```powershell")
    for cmd in payload["next_commands"]:
        print(cmd)
    print("```")


def build_parser():
    parser = argparse.ArgumentParser(description="Read-only code activation planning; no execute.")
    sub = parser.add_subparsers(dest="cmd")
    p = sub.add_parser("plan", help="build activation/preflight card for a code artifact")
    p.add_argument("target")
    p.add_argument("--driver-id", default="code-activation")
    p.add_argument("--require-confirmations", type=int, default=2)
    p.add_argument("--json", action="store_true")
    p.add_argument("--command", nargs=argparse.REMAINDER, help="optional command to statically preflight; never executed")
    p.set_defaults(func=cmd_plan)
    return parser


def cmd_plan(args):
    payload = activation_plan(args.target, driver_id=args.driver_id,
                              require_confirmations=args.require_confirmations,
                              command=args.command or [])
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print_text(payload)
    return 0 if payload["target"]["inside_repo"] else 2


def main(argv=None):
    help_guard(__doc__, argv)
    parser = build_parser()
    args = parser.parse_args(argv)
    if not hasattr(args, "func"):
        parser.print_help()
        return 2
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
