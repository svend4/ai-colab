#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
# ==========================================
# [FILE ID CARD]
# ID: tools.thread
# TYPE: active-script
# DOMAIN: core.thread
# DEPTH_LEVEL: 1
# SUMMARY: File-native thread objects for the headless workbench.
# ==========================================
"""
"""
File-native thread registry for the headless Zed-like workbench (T-264).

A thread is a durable object stored under a topic:

    topics/<topic>/threads/<thread-id>/THREAD.json
    topics/<topic>/threads/<thread-id>/messages/*.md
    topics/<topic>/threads/<thread-id>/artifacts/

The tool is intentionally small and stdlib-only. It does not call shells, models
or PTYs. It only creates JSON metadata and append-only Markdown messages.

CLI:
    python tools/thread.py init <topic> --agent codex [--mode read-only] [--json]
    python tools/thread.py status <thread-id> [--json]
    python tools/thread.py add-message <thread-id> <role> --text "..." [--json]
    python tools/thread.py add-message <thread-id> <role> --file path/in/workspace.md [--json]
    python tools/thread.py add-output <thread-id> path/in/workspace.md [--kind report] [--json]
    python tools/thread.py list [--topic <topic>] [--json]
"""
import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = Path(os.environ.get("COLLAB_ROOT", str(HERE.parent))).resolve()
TOPICS = ROOT / "topics"
sys.path.insert(0, str(HERE))
from _cli import die, help_guard
from _ioutil import configure_output

configure_output()

SCHEMA = "thread.v1"
MESSAGE_SCHEMA = "thread_message.v1"
MODES = {"read-only", "draft", "build", "terminal"}
ROLES = {"user", "assistant", "agent", "system", "tool", "reviewer"}
SLUG_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,119}$")


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def slug(value: str, label: str) -> str:
    value = (value or "").strip()
    if not SLUG_RE.match(value) or ".." in value:
        die("%s must be ASCII slug: letters/digits/dot/underscore/hyphen, no path traversal" % label)
    return value


def ensure_inside_root(path: Path) -> Path:
    resolved = path.resolve()
    try:
        resolved.relative_to(ROOT.resolve())
    except ValueError:
        die("path outside workspace: %s" % path)
    return resolved


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


def json_dump(path: Path, data: dict) -> None:
    text = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(text, encoding="utf-8", newline="\n")
    os.replace(tmp, path)


def thread_dir(topic: str, thread_id: str) -> Path:
    return TOPICS / topic / "threads" / thread_id


def thread_json_path(topic: str, thread_id: str) -> Path:
    return thread_dir(topic, thread_id) / "THREAD.json"


def iter_threads(topic: str | None = None):
    roots = []
    if topic:
        roots.append(TOPICS / slug(topic, "topic") / "threads")
    elif TOPICS.exists():
        roots.extend(p / "threads" for p in TOPICS.iterdir() if p.is_dir())
    for root in roots:
        if not root.is_dir():
            continue
        for path in sorted(root.glob("*/THREAD.json")):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except Exception:
                continue
            yield path, data


def find_thread(thread_id: str) -> tuple[Path, dict]:
    thread_id = slug(thread_id, "thread-id")
    hits = [(p, d) for p, d in iter_threads() if d.get("id") == thread_id]
    if not hits:
        die("thread not found: %s" % thread_id, 1)
    if len(hits) > 1:
        die("ambiguous thread id: %s" % thread_id, 1)
    return hits[0]


def unique_thread_id(topic: str, agent: str) -> str:
    base = "thread-%s-%s" % (datetime.now().strftime("%Y%m%d-%H%M%S"), agent)
    candidate = base
    n = 2
    while thread_json_path(topic, candidate).exists():
        candidate = "%s-%d" % (base, n)
        n += 1
    return candidate


def init_thread(topic: str, agent: str, mode: str = "read-only", task_id: str | None = None,
                stream_id: str | None = None, worktree: str | None = None,
                model: str | None = None, tools: list[str] | None = None) -> dict:
    topic = slug(topic, "topic")
    agent = slug(agent, "agent")
    if mode not in MODES:
        die("mode must be one of: %s" % ", ".join(sorted(MODES)))
    created = now_iso()
    thread_id = unique_thread_id(topic, agent)
    tdir = thread_dir(topic, thread_id)
    (tdir / "messages").mkdir(parents=True, exist_ok=False)
    (tdir / "artifacts").mkdir(parents=True, exist_ok=True)
    data = {
        "schema": SCHEMA,
        "id": thread_id,
        "topic": topic,
        "status": "open",
        "agent": agent,
        "mode": mode,
        "task_id": task_id,
        "stream_id": stream_id,
        "worktree": worktree,
        "model": model,
        "tools": tools or [],
        "outputs": [],
        "checks": [],
        "messages": [],
        "created_at": created,
        "updated_at": created,
    }
    json_dump(tdir / "THREAD.json", data)
    return data


def load_thread(thread_id: str) -> tuple[Path, dict]:
    path, data = find_thread(thread_id)
    if data.get("schema") != SCHEMA:
        die("unsupported thread schema in %s" % rel(path), 1)
    return path, data


def next_message_path(thread_path: Path, role: str) -> Path:
    messages = thread_path.parent / "messages"
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    base = "%s-%s" % (stamp, role)
    candidate = messages / ("%s.md" % base)
    n = 2
    while candidate.exists():
        candidate = messages / ("%s-%d.md" % (base, n))
        n += 1
    return candidate


def add_message(thread_id: str, role: str, text: str | None = None, file_path: str | None = None) -> dict:
    if role not in ROLES:
        die("role must be one of: %s" % ", ".join(sorted(ROLES)))
    if (text is None) == (file_path is None):
        die("provide exactly one of --text or --file")
    thread_path, data = load_thread(thread_id)
    source = "inline"
    if file_path is not None:
        source_path = ensure_inside_root((ROOT / file_path).resolve() if not os.path.isabs(file_path) else Path(file_path))
        text = source_path.read_text(encoding="utf-8")
        source = rel(source_path)
    message_path = next_message_path(thread_path, role)
    created = now_iso()
    body = text or ""
    content = (
        "---\n"
        "schema: %s\n"
        "thread_id: %s\n"
        "role: %s\n"
        "created_at: %s\n"
        "source: %s\n"
        "---\n\n%s\n"
    ) % (MESSAGE_SCHEMA, data["id"], role, created, source, body.rstrip())
    message_path.write_text(content, encoding="utf-8", newline="\n")
    entry = {
        "role": role,
        "path": rel(message_path),
        "source": source,
        "created_at": created,
    }
    data.setdefault("messages", []).append(entry)
    data["updated_at"] = created
    json_dump(thread_path, data)
    return entry


def add_output(thread_id: str, output_path: str, kind: str = "output") -> dict:
    thread_path, data = load_thread(thread_id)
    target = ensure_inside_root((ROOT / output_path).resolve() if not os.path.isabs(output_path) else Path(output_path))
    created = now_iso()
    entry = {
        "kind": kind,
        "path": rel(target),
        "exists": target.exists(),
        "created_at": created,
    }
    data.setdefault("outputs", []).append(entry)
    data["updated_at"] = created
    json_dump(thread_path, data)
    return entry


def print_result(data, as_json: bool) -> None:
    if as_json:
        print(json.dumps(data, ensure_ascii=False, indent=2))
    else:
        if isinstance(data, dict):
            for k in ("id", "topic", "status", "agent", "mode", "path"):
                if k in data:
                    print("%s: %s" % (k, data[k]))
        else:
            for item in data:
                print("%s  %s  %s  %s" % (
                    item.get("id"), item.get("status"), item.get("agent"), item.get("topic")
                ))


def cmd_init(args) -> int:
    data = init_thread(
        args.topic,
        agent=args.agent,
        mode=args.mode,
        task_id=args.task_id,
        stream_id=args.stream_id,
        worktree=args.worktree,
        model=args.model,
        tools=args.tool or [],
    )
    data["path"] = rel(thread_json_path(data["topic"], data["id"]))
    print_result(data, args.json)
    return 0


def cmd_status(args) -> int:
    path, data = load_thread(args.thread_id)
    data = dict(data)
    data["path"] = rel(path)
    print_result(data, args.json)
    return 0


def cmd_add_message(args) -> int:
    entry = add_message(args.thread_id, args.role, text=args.text, file_path=args.file)
    print_result(entry, args.json)
    return 0


def cmd_add_output(args) -> int:
    entry = add_output(args.thread_id, args.path, kind=args.kind)
    print_result(entry, args.json)
    return 0


def cmd_list(args) -> int:
    rows = []
    for path, data in iter_threads(topic=args.topic):
        rows.append({
            "id": data.get("id"),
            "topic": data.get("topic"),
            "status": data.get("status"),
            "agent": data.get("agent"),
            "mode": data.get("mode"),
            "path": rel(path),
        })
    print_result(rows, args.json)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="File-native thread objects for the headless workbench.")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("init")
    p.add_argument("topic")
    p.add_argument("--agent", required=True)
    p.add_argument("--mode", default="read-only", choices=sorted(MODES))
    p.add_argument("--task-id")
    p.add_argument("--stream-id")
    p.add_argument("--worktree")
    p.add_argument("--model")
    p.add_argument("--tool", action="append")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_init)

    p = sub.add_parser("status")
    p.add_argument("thread_id")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_status)

    p = sub.add_parser("add-message")
    p.add_argument("thread_id")
    p.add_argument("role")
    group = p.add_mutually_exclusive_group(required=True)
    group.add_argument("--text")
    group.add_argument("--file")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_add_message)

    p = sub.add_parser("add-output")
    p.add_argument("thread_id")
    p.add_argument("path")
    p.add_argument("--kind", default="output")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_add_output)

    p = sub.add_parser("list")
    p.add_argument("--topic")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_list)

    return parser


def main(argv=None) -> int:
    help_guard(__doc__, argv)
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
