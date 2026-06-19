#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тест атомарности claim под реальной гонкой (предложение Mavis из dogfood-прогона).

Запускает N параллельных `queue.py claim` на ОДНУ задачу во временной папке и
проверяет, что побеждает ровно один (гарантия O_CREAT|O_EXCL). Рабочий
репозиторий не трогает — всё во временной директории системы.

    python tools/race_test.py [N] [RAUNDS]
        N       — сколько параллельных claim в раунде (по умолчанию 8)
        RAUNDS  — сколько раундов подряд (по умолчанию 1)

Пример: python tools/race_test.py 8 5   # 5 раундов по 8 параллельных claim
Выход: 0 — все раунды OK (1 победитель, N-1 проигравших); 1 — хоть один FAIL.
Temp-папку можно задать через COLLAB_RACE_TMP (иначе C:\\tmp при наличии или системный temp).
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


def one_round(n):
    """Один раунд: n параллельных claim на одну задачу. Возвращает (winners, losers)."""
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
        return winners, losers
    finally:
        shutil.rmtree(root, ignore_errors=True)


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    n = int(args[0]) if len(args) > 0 else 8
    rounds = int(args[1]) if len(args) > 1 else 1

    all_ok = True
    for r in range(1, rounds + 1):
        winners, losers = one_round(n)
        ok = winners == 1 and losers == n - 1
        all_ok = all_ok and ok
        print("раунд %d/%d: победителей=%d, проигравших=%d, параллельных=%d — %s"
              % (r, rounds, winners, losers, n, "OK" if ok else "FAIL"))

    print("ИТОГ: %s — атомарность %s (%d раунд(ов), N=%d)"
          % ("OK" if all_ok else "FAIL",
             "подтверждена" if all_ok else "НАРУШЕНА", rounds, n))
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
