#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
# ==========================================
# [FILE ID CARD]
# ID: tools.commit_lock
# TYPE: active-script
# DOMAIN: core
# DEPTH_LEVEL: 1
# SUMMARY: Скрипт commit_lock.py. Описание сгенерировано автоматически.
# ==========================================
"""
"""
Commit-lock (Уровень 0 политики коммитов, topics/commit-policy-streams-2026-06-21.md).

Атомарный короткоживущий advisory-лок, чтобы агенты НЕ дрались за git `index.lock`: перед
`generate + git add + git commit` агент берёт лок, после — отпускает. Коммиты сериализуются —
нет отскоков и фейлов на параллельном `index.lock`. TTL снимает лок упавшего агента.

Это сериализация, а не изоляция: от коммита ЧУЖОЙ half-done защищает не лок, а правило
**selective-add** (коммить только свои файлы, не `git add -A`). Полная изоляция — worktree
(Уровень 1).

CLI:
    python tools/commit_lock.py acquire <agent> [--ttl 120] [--wait 60]   # 0=взял, 1=не взял
    python tools/commit_lock.py release <agent>
    python tools/commit_lock.py status

Пример (sh):
    if python tools/commit_lock.py acquire claude; then
      python tools/generate.py && git add <свои-файлы> && git commit -m "..." ;
      python tools/commit_lock.py release claude ;
    fi
"""
import os
import sys
import time

from _ioutil import configure_output

ROOT = os.environ.get("COLLAB_ROOT") or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOCK = os.path.join(ROOT, "queues", "commit.lock")

configure_output()


def _read():
    if not os.path.exists(LOCK):
        return None
    try:
        with open(LOCK, encoding="utf-8") as f:
            d = {}
            for line in f.read().splitlines():
                if ":" in line:
                    k, v = line.split(":", 1)
                    d[k.strip()] = v.strip()
            return d
    except OSError:
        return None


def _fresh(d):
    try:
        return int(d.get("lease_epoch", "0")) > int(time.time())
    except (ValueError, TypeError):
        return False


def _write_excl(agent, ttl):
    body = "agent: %s\nepoch: %d\nlease_epoch: %d\n" % (agent, int(time.time()), int(time.time()) + ttl)
    fd = os.open(LOCK, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
        f.write(body)


def acquire(agent, ttl=120, wait=60):
    os.makedirs(os.path.dirname(LOCK), exist_ok=True)
    deadline = time.time() + wait
    while True:
        try:
            _write_excl(agent, ttl)
            print("LOCK: взял commit-lock (%s, ttl %ds)" % (agent, ttl))
            return 0
        except FileExistsError:
            d = _read()
            if d and not _fresh(d):
                # протух — снять и попробовать заново (гонку снимет O_EXCL)
                try:
                    os.remove(LOCK)
                except OSError:
                    pass
                continue
            if time.time() >= deadline:
                print("BUSY: commit-lock занят агентом %s — не дождался (%ds)"
                      % ((d or {}).get("agent", "?"), wait))
                return 1
            time.sleep(0.5)


def release(agent):
    d = _read()
    if d is None:
        print("OK: commit-lock свободен")
        return 0
    if d.get("agent") != agent:
        print("ОШИБКА: commit-lock держит %s, не ты (%s) — не снимаю" % (d.get("agent"), agent))
        return 1
    try:
        os.remove(LOCK)
    except OSError:
        pass
    print("UNLOCK: отпустил commit-lock (%s)" % agent)
    return 0


def status():
    d = _read()
    if d is None:
        print("commit-lock: свободен")
        return 0
    print("commit-lock: %s (%s), осталось %ds"
          % (d.get("agent"), "свежий" if _fresh(d) else "протух",
             max(0, int(d.get("lease_epoch", "0")) - int(time.time()))))
    return 0


def main():
    a = sys.argv[1:]
    if not a:
        print(__doc__)
        return 2
    cmd = a[0]
    ttl = int(a[a.index("--ttl") + 1]) if "--ttl" in a else 120
    wait = int(a[a.index("--wait") + 1]) if "--wait" in a else 60
    if cmd == "acquire" and len(a) > 1:
        return acquire(a[1], ttl=ttl, wait=wait)
    if cmd == "release" and len(a) > 1:
        return release(a[1])
    if cmd == "status":
        return status()
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main())
