#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
# ==========================================
# [FILE ID CARD]
# ID: tools.test_metrics
# TYPE: active-script
# DOMAIN: core
# DEPTH_LEVEL: 1
# SUMMARY: Скрипт test_metrics.py. Описание сгенерировано автоматически.
# ==========================================
"""
"""Hermetic-тесты для tools/metrics.py (сводные метрики канона).

Изоляция через COLLAB_ROOT → временный канон с известными реестрами/очередью.
metrics.py вычисляет ROOT на import-time, поэтому запуск идёт через subprocess
с COLLAB_ROOT в env (--json контракт). Чистые функции (by_status / ready_blocked)
проверяются in-process.
"""
import os
import sys
import json
import tempfile
import shutil
import subprocess

from _ioutil import configure_output

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
configure_output()

from _canon import parse_front_matter  # фикстуры → проверяем согласованность парсинга
import metrics


def write_md(path, fm, body=""):
    lines = ["---"]
    for k, v in fm.items():
        lines.append("%s: %s" % (k, v))
    lines.append("---")
    lines.append("")
    lines.append(body)
    text = "\n".join(lines)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    # фикстура должна корректно читаться каноническим парсером
    parsed = parse_front_matter(text)
    assert parsed.get("id") == fm.get("id"), (parsed, fm)


def make_canon(root):
    for sub in ("tasks", "questions", "decisions", "topics",
                "queues/inbox", "queues/claimed", "queues/done", "queues/failed"):
        os.makedirs(os.path.join(root, sub), exist_ok=True)

    tdir = os.path.join(root, "tasks")
    # done-зависимость
    write_md(os.path.join(tdir, "T-001.md"), {"id": "T-001", "status": "done"})
    # todo без deps → ready
    write_md(os.path.join(tdir, "T-002.md"), {"id": "T-002", "status": "todo", "depends_on": ""})
    # todo, зависит от done T-001 → ready
    write_md(os.path.join(tdir, "T-003.md"), {"id": "T-003", "status": "todo", "depends_on": "T-001"})
    # todo, зависит от незавершённого T-002 → blocked
    write_md(os.path.join(tdir, "T-004.md"), {"id": "T-004", "status": "todo", "depends_on": "T-002"})
    # in-progress не считается ни ready, ни blocked
    write_md(os.path.join(tdir, "T-005.md"), {"id": "T-005", "status": "in-progress"})
    # README.md без id — не должен попасть в реестр
    with open(os.path.join(tdir, "README.md"), "w", encoding="utf-8", newline="\n") as f:
        f.write("# tasks\n")

    write_md(os.path.join(root, "questions", "Q-001.md"), {"id": "Q-001", "status": "open"})
    write_md(os.path.join(root, "decisions", "D-001.md"), {"id": "D-001", "status": "accepted"})
    write_md(os.path.join(root, "topics", "TOP-001.md"), {"id": "TOP-001", "status": "active"})

    # очередь: count_dir по суффиксам
    open(os.path.join(root, "queues/inbox", "a.md"), "w").close()
    open(os.path.join(root, "queues/inbox", "b.md"), "w").close()
    open(os.path.join(root, "queues/claimed", "c.claim.md"), "w").close()
    open(os.path.join(root, "queues/done", "d.done.md"), "w").close()
    # README.md в inbox исключается count_dir
    with open(os.path.join(root, "queues/inbox", "README.md"), "w", encoding="utf-8") as f:
        f.write("x\n")


def test_pure_functions():
    # by_status агрегирует по полю status
    items = [{"status": "todo"}, {"status": "todo"}, {"status": "done"}, {}]
    bs = metrics.by_status(items)
    assert bs == {"todo": 2, "done": 1, "?": 1}, bs

    # ready_blocked: todo с выполненными deps → ready, иначе blocked
    tasks = [
        {"id": "T-001", "status": "done"},
        {"id": "T-002", "status": "todo", "depends_on": ""},
        {"id": "T-003", "status": "todo", "depends_on": "T-001"},
        {"id": "T-004", "status": "todo", "depends_on": "T-002"},
        {"id": "T-005", "status": "in-progress"},
    ]
    ready, blocked = metrics.ready_blocked(tasks)
    assert (ready, blocked) == (2, 1), (ready, blocked)


def test_json_contract(root):
    env = dict(os.environ)
    env["COLLAB_ROOT"] = root
    env["PYTHONUTF8"] = "1"
    p = subprocess.run(
        [sys.executable, os.path.join(HERE, "metrics.py"), "--json"],
        env=env, capture_output=True, text=True, encoding="utf-8",
        errors="replace", stdin=subprocess.DEVNULL,
    )
    assert p.returncode == 0, (p.returncode, p.stdout, p.stderr)
    m = json.loads(p.stdout)

    assert m["tasks"]["total"] == 5, m["tasks"]
    assert m["tasks"]["by_status"] == {"done": 1, "todo": 3, "in-progress": 1}, m["tasks"]["by_status"]
    assert m["tasks"]["ready"] == 2 and m["tasks"]["blocked"] == 1, m["tasks"]

    assert m["questions"]["total"] == 1, m["questions"]
    assert m["decisions"]["total"] == 1, m["decisions"]
    assert m["topics"]["total"] == 1, m["topics"]

    q = m["queue"]
    assert q == {"inbox": 2, "claimed": 1, "done": 1, "failed": 0}, q


def test_human_runs(root):
    env = dict(os.environ)
    env["COLLAB_ROOT"] = root
    env["PYTHONUTF8"] = "1"
    p = subprocess.run(
        [sys.executable, os.path.join(HERE, "metrics.py")],
        env=env, capture_output=True, text=True, encoding="utf-8",
        errors="replace", stdin=subprocess.DEVNULL,
    )
    assert p.returncode == 0, (p.returncode, p.stdout, p.stderr)
    assert "=== " in p.stdout and "5" in p.stdout, p.stdout


def run():
    tmp = tempfile.mkdtemp(prefix="metrics_test_")
    try:
        make_canon(tmp)
        test_pure_functions()
        test_json_contract(tmp)
        test_human_runs(tmp)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print("TESTS OK metrics: by_status/ready_blocked + --json contract (tasks/queue/registries) + human render")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(run())
    except AssertionError as exc:
        print("TEST FAIL:", exc)
        sys.exit(1)
