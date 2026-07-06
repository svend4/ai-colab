# ast: allow-subprocess
# ast: allow-loops
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Synchronous MCP stdio probe that avoids asyncio subprocess pipes.

The normal Python MCP client uses ``asyncio.create_subprocess_exec``. In the
current Windows runtime that path fails while plain ``subprocess.Popen`` works.
This probe speaks enough MCP JSON-RPC over stdio to initialize a server and list
its tools.

Usage:
    python drivers/mcp_sync_probe.py
    python drivers/mcp_sync_probe.py data codex-local
"""
import argparse
import json
import os
import queue
import subprocess
import sys
import threading
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent

SERVERS = {
    "files": ("drivers/files/mcp_server.py", "FILES_DRIVER_BASE"),
    "repo-runner": ("drivers/repo-runner/mcp_server.py", "REPO_RUNNER_BASE"),
    "data": ("drivers/data/mcp_server.py", "DATA_DRIVER_BASE"),
    "codex-local": ("drivers/codex-local/mcp_server.py", None),
    "gateway": ("drivers/gateway/mcp_server.py", "GATEWAY_BASE"),
    "git-log": ("drivers/git-log/mcp_server.py", "GIT_LOG_BASE"),
    "sqlite": ("drivers/sqlite/mcp_server.py", "SQLITE_DRIVER_BASE"),
}


def configure_output():
    for name in ("stdout", "stderr"):
        stream = getattr(sys, name, None)
        if stream is not None and hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")


configure_output()


def read_message(stream):
    raw = stream.readline()
    if not raw:
        raise EOFError("stdio closed while reading JSON-RPC line")
    return json.loads(raw.decode("utf-8"))


class SyncMcpClient:
    def __init__(self, server, timeout=30):
        if server not in SERVERS:
            raise KeyError("unknown server: %s" % server)
        rel, base_env = SERVERS[server]
        env = dict(os.environ)
        if base_env:
            env[base_env] = str(ROOT)
        self.server = server
        self.timeout = timeout
        self.proc = subprocess.Popen(
            [sys.executable, str(ROOT / rel)],
            cwd=str(ROOT),
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
        )
        self.messages = queue.Queue()
        self.errors = []
        self.reader = threading.Thread(target=self._read_stdout, daemon=True)
        self.err_reader = threading.Thread(target=self._read_stderr, daemon=True)
        self.reader.start()
        self.err_reader.start()
        self.next_id = 1

    def _read_stdout(self):
        try:
            while True:
                self.messages.put(read_message(self.proc.stdout))
        except Exception as exc:
            self.messages.put({"_reader_error": "%s: %s" % (type(exc).__name__, exc)})

    def _read_stderr(self):
        try:
            for raw in iter(self.proc.stderr.readline, b""):
                text = raw.decode("utf-8", errors="replace").rstrip()
                if text:
                    self.errors.append(text)
        except Exception as exc:
            self.errors.append("%s: %s" % (type(exc).__name__, exc))

    def send(self, payload):
        if self.proc.poll() is not None:
            raise RuntimeError("server exited with code %s" % self.proc.returncode)
        body = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        self.proc.stdin.write(body + b"\n")
        self.proc.stdin.flush()

    def request(self, method, params=None):
        ident = self.next_id
        self.next_id += 1
        payload = {"jsonrpc": "2.0", "id": ident, "method": method}
        if params is not None:
            payload["params"] = params
        self.send(payload)
        deadline = time.time() + self.timeout
        while time.time() < deadline:
            try:
                msg = self.messages.get(timeout=max(0.1, deadline - time.time()))
            except queue.Empty:
                break
            if msg.get("_reader_error"):
                raise RuntimeError(msg["_reader_error"])
            if msg.get("id") == ident:
                if "error" in msg:
                    raise RuntimeError(json.dumps(msg["error"], ensure_ascii=False))
                return msg.get("result")
        raise TimeoutError("%s request timed out: %s" % (self.server, method))

    def notify(self, method, params=None):
        payload = {"jsonrpc": "2.0", "method": method}
        if params is not None:
            payload["params"] = params
        self.send(payload)

    def close(self):
        if self.proc.poll() is None:
            try:
                self.proc.terminate()
                self.proc.wait(timeout=5)
            except Exception:
                self.proc.kill()


def probe(server, timeout):
    client = SyncMcpClient(server, timeout=timeout)
    try:
        init = client.request("initialize", {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "mcp-sync-probe", "version": "0.1"},
        })
        client.notify("notifications/initialized", {})
        tools = client.request("tools/list", {})
        names = sorted(t.get("name", "") for t in tools.get("tools", []))
        return {
            "server": server,
            "ok": True,
            "server_info": init.get("serverInfo", {}),
            "tools": names,
            "stderr_tail": client.errors[-5:],
        }
    finally:
        client.close()


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("servers", nargs="*", default=["data", "codex-local"])
    parser.add_argument("--timeout", type=int, default=45)
    args = parser.parse_args(argv)

    ok = True
    for server in args.servers:
        try:
            result = probe(server, timeout=args.timeout)
            print("OK %s tools=%d %s" % (server, len(result["tools"]), result["tools"]))
        except Exception as exc:
            ok = False
            print("FAIL %s: %s %s" % (server, type(exc).__name__, str(exc)[:240]))
    print("RESULT", "OK" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
