#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тест атомарности claim под реальной гонкой (предложение Mavis из dogfood-прогона).

Запускает N параллельных `queue.py claim` на ОДНУ задачу во временной папке и
проверяет, что побеждает ровно один (гарантия O_CREAT|O_EXCL). Рабочий
репозиторий не трогает — всё во временной директории системы.

    python tools/race_test.py [N]     # по умолчанию N = 8

Выход: 0 — атомарность подтверждена (1 победитель, N-1 проигравших); 1 — нарушена.
"""
import os
import sys
import shutil
import tempfile
import subprocess


def configure_output():
    for name in ("stdout", "stderr"):
        s = getattr(sys, name, None)
        if s is not None and hasattr(s, "reconfigure"):
            s.reconfigure(encoding="utf-8", errors="replace")


configure_output()

HERE = os.path.dirname(os.path.abspath(__file__))
QUEUE = os.path.join(HERE, "queue.py")


def temp_base():
    base = os.environ.get("COLLAB_RACE_TMP")
    if base:
        return base
    if os.name == "nt" and os.path.isdir(r"C:\tmp"):
        return r"C:\tmp"
    return tempfile.gettempdir()


def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 8
    root = tempfile.mkdtemp(prefix="race_", dir=temp_base())
    try:
        for d in ("inbox", "claimed", "done", "failed"):
            os.makedirs(os.path.join(root, "queues", d))
        with open(os.path.join(root, "queues", "inbox", "racetask.md"), "w", encoding="utf-8") as f:
            f.write("# racetask\n")

        env = dict(os.environ, COLLAB_ROOT=root)
        procs = [
            subprocess.Popen(
                [sys.executable, QUEUE, "claim", "racetask", "agent%d" % i],
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=env,
            )
            for i in range(n)
        ]
        outs = [p.communicate()[0].decode("utf-8", "replace") for p in procs]

        winners = sum(1 for o in outs if "claim создан" in o)
        losers = sum(1 for o in outs if ("RACE" in o or "BUSY" in o))
        print("Параллельных claim: %d" % n)
        print("Победителей (claim создан): %d" % winners)
        print("Проигравших (RACE/BUSY):   %d" % losers)
        ok = winners == 1 and losers == n - 1
        print("РЕЗУЛЬТАТ: %s — атомарность %s"
              % ("OK" if ok else "FAIL", "подтверждена" if ok else "НАРУШЕНА"))
        return 0 if ok else 1
    finally:
        shutil.rmtree(root, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
