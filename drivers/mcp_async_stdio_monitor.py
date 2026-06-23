#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Advisory monitor for the Windows async MCP stdio blocker (T-174).

The regular acceptance path for this repository is synchronous
`drivers/mcp_sync_acceptance.py`. This helper exists only to periodically check
whether the official async stdio path is still blocked by the local
Windows/Python runtime.

Default mode is advisory: the command exits 0 after it classifies the state.
Use `--strict` when a caller wants a non-zero exit for anything except async OK.
"""
import argparse
import asyncio
import datetime as _dt
import json
import os
import subprocess
import sys


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def configure_output():
    for name in ("stdout", "stderr"):
        stream = getattr(sys, name, None)
        if stream is not None and hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")


configure_output()


async def _async_pipe_probe(timeout):
    proc = await asyncio.create_subprocess_exec(
        sys.executable,
        "-c",
        "print(123)",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    out, err = await asyncio.wait_for(proc.communicate(), timeout=timeout)
    return proc.returncode, out.decode("utf-8", "replace"), err.decode("utf-8", "replace")


def async_pipe_probe(timeout):
    started = _dt.datetime.now(_dt.timezone.utc)
    try:
        rc, out, err = asyncio.run(_async_pipe_probe(timeout))
        status = "ok" if rc == 0 and "123" in out else "fail"
        detail = "returncode=%s stdout=%r stderr=%r" % (rc, out.strip(), err.strip())
    except asyncio.TimeoutError:
        status = "timeout"
        detail = "asyncio.create_subprocess_exec pipe probe timed out after %ss" % timeout
    except Exception as exc:  # noqa: BLE001 - diagnostic tool must report raw runtime failures
        status = "winerror-5" if "WinError 5" in str(exc) or isinstance(exc, PermissionError) else "fail"
        detail = "%s: %s" % (type(exc).__name__, str(exc))
    return {
        "name": "async-pipe-probe",
        "status": status,
        "detail": detail,
        "started_utc": started.isoformat(),
    }


def _command(server, sync=False):
    if sync:
        cmd = [sys.executable, os.path.join(ROOT, "drivers", "mcp_sync_acceptance.py")]
        if server != "all":
            cmd.append(server)
        return cmd
    cmd = [sys.executable, os.path.join(ROOT, "drivers", "mcp_acceptance_test.py")]
    if server != "all":
        cmd.append(server)
    return cmd


def run_acceptance(server, timeout, sync=False):
    cmd = _command(server, sync=sync)
    started = _dt.datetime.now(_dt.timezone.utc)
    try:
        proc = subprocess.run(
            cmd,
            cwd=ROOT,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
        )
        output = (proc.stdout or "") + (proc.stderr or "")
        if proc.returncode == 0:
            status = "ok"
        elif "WinError 5" in output or "PermissionError" in output:
            status = "winerror-5"
        else:
            status = "fail"
        detail = output[-4000:]
        rc = proc.returncode
    except subprocess.TimeoutExpired as exc:
        status = "timeout"
        detail = ((exc.stdout or "") + (exc.stderr or ""))[-4000:]
        if not detail:
            detail = "timeout after %ss" % timeout
        rc = None
    return {
        "name": "sync-acceptance" if sync else "async-acceptance",
        "server": server,
        "status": status,
        "returncode": rc,
        "command": " ".join(cmd),
        "started_utc": started.isoformat(),
        "detail": detail.strip(),
    }


def classify(probe, async_result, sync_result):
    if async_result and async_result["status"] == "ok":
        async_state = "async-ok"
    elif probe["status"] in ("winerror-5", "timeout"):
        async_state = "blocked-before-mcp"
    elif async_result:
        async_state = "blocked-in-acceptance" if async_result["status"] != "ok" else "async-ok"
    else:
        async_state = "not-run"

    sync_state = "not-run"
    if sync_result:
        sync_state = "sync-ok" if sync_result["status"] == "ok" else "sync-failed"

    if async_state == "async-ok":
        recommendation = "Official async stdio acceptance is available; update T-174/gateway docs."
    elif sync_state == "sync-ok":
        recommendation = "Keep sync acceptance as the regular gate; retest async after Python/Windows/mcp runtime changes."
    else:
        recommendation = "Investigate runtime and sync acceptance before changing driver status."
    return {"async_state": async_state, "sync_state": sync_state, "recommendation": recommendation}


def build_report(payload):
    cls = payload["classification"]
    lines = [
        "---",
        "type: report",
        "tool: drivers/mcp_async_stdio_monitor.py",
        "date: %s" % payload["date"],
        "server: %s" % payload["server"],
        "---",
        "",
        "# MCP async stdio monitor",
        "",
        "## Verdict",
        "",
        "- async_state: `%s`" % cls["async_state"],
        "- sync_state: `%s`" % cls["sync_state"],
        "- recommendation: %s" % cls["recommendation"],
        "",
        "## Probe",
        "",
        "```text",
        "%s: %s" % (payload["probe"]["status"], payload["probe"]["detail"]),
        "```",
        "",
    ]
    for key in ("async_acceptance", "sync_acceptance"):
        item = payload.get(key)
        if not item:
            continue
        lines.extend([
            "## %s" % item["name"],
            "",
            "- command: `%s`" % item["command"],
            "- status: `%s`" % item["status"],
            "- returncode: `%s`" % item["returncode"],
            "",
            "```text",
            item["detail"] or "(no output)",
            "```",
            "",
        ])
    return "\n".join(lines)


def write_report(path, payload):
    out = path if os.path.isabs(path) else os.path.join(ROOT, path)
    parent = os.path.dirname(out)
    if parent:
        os.makedirs(parent, exist_ok=True)
    with open(out, "w", encoding="utf-8", newline="\n") as f:
        f.write(build_report(payload))
        f.write("\n")


def run(args):
    probe = async_pipe_probe(args.probe_timeout)
    async_result = None
    if args.force_acceptance or probe["status"] == "ok":
        async_result = run_acceptance(args.server, args.acceptance_timeout, sync=False)
    sync_result = None
    if not args.no_sync:
        sync_result = run_acceptance(args.server, args.sync_timeout, sync=True)
    payload = {
        "date": _dt.datetime.now(_dt.timezone.utc).date().isoformat(),
        "server": args.server,
        "probe": probe,
        "async_acceptance": async_result,
        "sync_acceptance": sync_result,
    }
    payload["classification"] = classify(probe, async_result, sync_result)
    if args.out:
        write_report(args.out, payload)
        payload["out"] = args.out
    return payload


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("server", nargs="?", default="gateway",
                        help="MCP server id, or 'all' for the legacy full async batch")
    parser.add_argument("--probe-timeout", type=int, default=10)
    parser.add_argument("--acceptance-timeout", type=int, default=60)
    parser.add_argument("--sync-timeout", type=int, default=90)
    parser.add_argument("--force-acceptance", action="store_true",
                        help="run async acceptance even when the pipe probe already failed")
    parser.add_argument("--no-sync", action="store_true", help="skip sync acceptance comparison")
    parser.add_argument("--out", help="write a Markdown report")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--strict", action="store_true",
                        help="exit 1 unless async_state is async-ok and sync_state is not sync-failed")
    args = parser.parse_args(argv)

    payload = run(args)
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        cls = payload["classification"]
        print("ASYNC_STATE %s" % cls["async_state"])
        print("SYNC_STATE %s" % cls["sync_state"])
        print("RECOMMENDATION %s" % cls["recommendation"])
        if payload.get("out"):
            print("REPORT %s" % payload["out"])
    if args.strict:
        ok = cls["async_state"] == "async-ok" and cls["sync_state"] != "sync-failed"
        return 0 if ok else 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
