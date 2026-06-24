#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
# ==========================================
# [FILE ID CARD]
# ID: tools.agent_queue
# TYPE: active-script
# DOMAIN: core
# DEPTH_LEVEL: 1
# SUMMARY: Скрипт agent_queue.py. Описание сгенерировано автоматически.
# ==========================================
"""
"""
Очередь 2.0 — атомарный рабочий цикл задач для многих агентов (Этап D из scaling-design).

Агент НЕ двигает файлы руками — он вызывает этот инструмент, а инструмент меняет
`queues/*` консистентно. Это лечит дефект смоук-теста T-004 (ручной move/delete).

Команды:
    python tools/agent_queue.py list
    python tools/agent_queue.py claim    <task> <agent> [--ttl MIN]
    python tools/agent_queue.py complete <task> <agent> --claim-id ID [--result PATH]
    python tools/agent_queue.py fail     <task> <agent> --claim-id ID [--reason TEXT]
    python tools/agent_queue.py release  <task> <agent> --claim-id ID
    python tools/agent_queue.py check

Где <task> — имя файла задания в `queues/inbox/<task>.md` (без .md).
Для pipeline-режима check также признаёт claim на `tasks/<task>.md`.

Гарантии:
- Атомарность: новый claim создаётся через O_CREAT|O_EXCL (атомарно на одной ФС) —
  два агента не получат claim одновременно.
- TTL: claim «свежий», пока lease_until в будущем; протухший claim можно перехватить.
- Fencing: каждый claim получает уникальный claim_id; complete/fail требуют его —
  агент, чей claim перехватили, не сможет завершить задачу и затереть чужую работу.
"""
import os
import sys
from _ioutil import configure_output
import time
import argparse
import binascii

configure_output()

ROOT = os.environ.get("COLLAB_ROOT") or os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)
Q = os.path.join(ROOT, "queues")
DEFAULT_TTL_MIN = 30

def now_epoch():
    return int(time.time())

def human(epoch):
    return time.strftime("%Y-%m-%d %H:%M", time.localtime(epoch))

def token():
    return binascii.hexlify(os.urandom(8)).decode()

def claim_path(task):
    return os.path.join(Q, "claimed", task + ".claim.md")

def inbox_path(task):
    return os.path.join(Q, "inbox", task + ".md")

def task_source_path(task):
    return os.path.join(ROOT, "tasks", task + ".md")

from _canon import parse_fm  # единый парсер front-matter (T-085, находка L)

def read_claim(task):
    pth = claim_path(task)
    if not os.path.exists(pth):
        return None
    with open(pth, encoding="utf-8") as f:
        return parse_fm(f.read())

def is_fresh(claim):
    try:
        return int(claim.get("lease_epoch", "0")) > now_epoch()
    except ValueError:
        return False

def claim_text(d):
    return (
        "---\n"
        "task: %(task)s\n"
        "agent: %(agent)s\n"
        "claim_id: %(claim_id)s\n"
        "claimed_at: %(claimed_at)s\n"
        "lease_until: %(lease_until)s\n"
        "lease_epoch: %(lease_epoch)s\n"
        "---\n\n"
        "# Claim: %(task)s — %(agent)s\n\n"
        "Lease до %(lease_until)s. Fencing claim_id: %(claim_id)s.\n"
    ) % d

def write_claim(task, d, overwrite):
    pth = claim_path(task)
    os.makedirs(os.path.dirname(pth), exist_ok=True)
    text = claim_text(d)
    if overwrite:
        with open(pth, "w", encoding="utf-8", newline="\n") as f:
            f.write(text)
    else:
        fd = os.open(pth, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
            f.write(text)

def require_holder(task, agent, claim_id):
    c = read_claim(task)
    if c is None:
        print("ERROR: нет активного claim для %s" % task)
        return None
    if c.get("agent") != agent:
        print("ERROR: claim принадлежит %s, не %s" % (c.get("agent"), agent))
        return None
    if c.get("claim_id") != claim_id:
        print("ERROR: неверный claim_id (fencing) — возможно, claim перехвачен")
        return None
    return c

def cmd_claim(a):
    task, agent = a.task, a.agent
    if not os.path.exists(inbox_path(task)):
        print("ERROR: нет задания queues/inbox/%s.md" % task)
        return 1
    existing = read_claim(task)
    if existing and is_fresh(existing) and existing.get("agent") != agent:
        print(
            "BUSY: задачу держит %s до %s (claim_id %s)"
            % (existing.get("agent"), existing.get("lease_until"), existing.get("claim_id"))
        )
        return 1
    cid = token()
    lease = now_epoch() + a.ttl * 60
    d = {
        "task": task,
        "agent": agent,
        "claim_id": cid,
        "claimed_at": human(now_epoch()),
        "lease_until": human(lease),
        "lease_epoch": str(lease),
    }
    try:
        write_claim(task, d, overwrite=bool(existing))
    except FileExistsError:
        print("RACE: claim только что создан другим агентом — повтори")
        return 1
    if existing and not is_fresh(existing):
        note = "перехвачен протухший claim"
    elif existing:
        note = "продлён свой claim"
    else:
        note = "claim создан"
    print("OK: %s. task=%s agent=%s lease_until=%s" % (note, task, agent, d["lease_until"]))
    print("claim_id=%s  (сохрани для complete/fail)" % cid)
    return 0

def cmd_complete(a):
    if require_holder(a.task, a.agent, a.claim_id) is None:
        return 1
    done = os.path.join(Q, "done", a.task + ".done.md")
    os.makedirs(os.path.dirname(done), exist_ok=True)
    with open(done, "w", encoding="utf-8", newline="\n") as f:
        f.write(
            "# Выполнено: %s\n\n- Агент: %s\n- Результат: %s\n- Завершено: %s\n"
            % (a.task, a.agent, a.result or "(см. queues/outbox/)", human(now_epoch()))
        )
    for pth in (inbox_path(a.task), claim_path(a.task)):
        if os.path.exists(pth):
            os.remove(pth)
    print("OK: %s завершена; done-маркер создан, inbox и claim очищены" % a.task)
    return 0

def cmd_fail(a):
    if require_holder(a.task, a.agent, a.claim_id) is None:
        return 1
    failed = os.path.join(Q, "failed", a.task + ".failed.md")
    os.makedirs(os.path.dirname(failed), exist_ok=True)
    with open(failed, "w", encoding="utf-8", newline="\n") as f:
        f.write(
            "# Не выполнено: %s\n\n- Агент: %s\n- Причина: %s\n- Время: %s\n"
            % (a.task, a.agent, a.reason or "(не указана)", human(now_epoch()))
        )
    if os.path.exists(claim_path(a.task)):
        os.remove(claim_path(a.task))
    print("OK: %s → failed; claim снят (inbox оставлен для повтора)" % a.task)
    return 0

def cmd_release(a):
    if require_holder(a.task, a.agent, a.claim_id) is None:
        return 1
    os.remove(claim_path(a.task))
    print("OK: claim на %s снят" % a.task)
    return 0

def cmd_list(a):
    inbox_dir = os.path.join(Q, "inbox")
    tasks = sorted(
        f[:-3] for f in os.listdir(inbox_dir) if f.endswith(".md") and f != "README.md"
    )
    if not tasks:
        print("inbox пуст")
        return 0
    for task in tasks:
        c = read_claim(task)
        if c is None:
            print("[свободна]      %s" % task)
        elif is_fresh(c):
            print("[занята]        %s — %s до %s" % (task, c.get("agent"), c.get("lease_until")))
        else:
            print("[claim протух]  %s — был %s, можно перехватить" % (task, c.get("agent")))
    return 0

def cmd_check(a):
    problems = 0
    cdir = os.path.join(Q, "claimed")
    if os.path.isdir(cdir):
        for f in os.listdir(cdir):
            if not f.endswith(".claim.md"):
                continue
            task = f[: -len(".claim.md")]
            done = os.path.join(Q, "done", task + ".done.md")
            has_inbox = os.path.exists(inbox_path(task))
            has_task_source = os.path.exists(task_source_path(task))
            has_done = os.path.exists(done)
            if not has_inbox and not has_task_source and not has_done:
                print("WARN: claim без задания и без done: %s" % task)
                problems += 1
    print("check: проблем %d" % problems)
    return 1 if problems else 0

def main():
    ap = argparse.ArgumentParser(prog="agent_queue.py")
    sub = ap.add_subparsers(dest="cmd")

    s = sub.add_parser("claim")
    s.add_argument("task")
    s.add_argument("agent")
    s.add_argument("--ttl", type=int, default=DEFAULT_TTL_MIN)
    s.set_defaults(fn=cmd_claim)

    for name, fn in (("complete", cmd_complete), ("fail", cmd_fail), ("release", cmd_release)):
        s = sub.add_parser(name)
        s.add_argument("task")
        s.add_argument("agent")
        s.add_argument("--claim-id", required=True, dest="claim_id")
        if name == "complete":
            s.add_argument("--result", default=None)
        if name == "fail":
            s.add_argument("--reason", default=None)
        s.set_defaults(fn=fn)

    s = sub.add_parser("list")
    s.set_defaults(fn=cmd_list)
    s = sub.add_parser("check")
    s.set_defaults(fn=cmd_check)

    a = ap.parse_args()
    if not getattr(a, "fn", None):
        ap.print_help()
        return 2
    return a.fn(a)

if __name__ == "__main__":
    sys.exit(main())
