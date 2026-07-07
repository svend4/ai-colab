# ast: allow-subprocess
#!/usr/bin/env python3
# [FILE ID CARD]
# id: tools/work_admission.py
# purpose: Гейт B многоагентной работы — потолок одновременных тяжёлых агентов + очередь.
#          Слотов ≈ ядра−запас; лишние агенты ждут/встают в очередь, а не грузят машину.
# inputs: agent, --slots/--reserve/--ttl/--wait; состояние — logs/slots/*.slot (runtime, gitignored)
# outputs: acquire 0=слот взят / 1=очередь (нет слота); release; status
# mode: пишет ТОЛЬКО в logs/slots/ (runtime-лизинги), канон не трогает
# related: worktree_gate.py (Гейт A), commit_lock.py, queue.py (fencing), D-022, D-036, T-274
"""work_admission.py — потолок одновременности + очередь (Гейт B).

Мотив (уточнение Stefan 2026-07-07): worktree-изоляция (Гейт A) убирает коллизию дерева, но
НЕ ограничивает СКОЛЬКО тяжёлых агентов работает разом — 6 агентов даже в своих worktree
перегрузят 4 ядра. Нужен кап: активных тяжёлых агентов ≤ (ядра − запас); лишние ждут в очереди.

Модель: N слотов-лизингов в logs/slots/<agent>.slot (runtime, gitignored). Перед тяжёлой
работой агент берёт слот; нет свободного — ждёт (--wait) или встаёт в очередь (exit 1). Слот
крашнувшегося агента снимается по TTL. Fencing: release снимает ТОЛЬКО свой слот (по токену),
count+create под коротким O_EXCL-локом (иначе гонка над-подписки — урок commit_lock из аудита).

Авто-порог: слотов = max(1, cpu_count − reserve). На 4-ядерной, reserve=1 → 3 слота.

CLI:
    python tools/work_admission.py acquire <agent> [--wait 60] [--ttl 1200] [--slots N] [--reserve K]
        # exit 0 = слот взят (можно работать); 1 = слотов нет (встань в очередь/отложи)
    python tools/work_admission.py release <agent>
    python tools/work_admission.py status [--json]
    python tools/work_admission.py slots        # печатает вычисленное число слотов
"""
from __future__ import annotations
import argparse
import errno
import json
import os
import sys
import time

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

ROOT = os.environ.get("COLLAB_ROOT") or os.getcwd()
SLOTS_DIR = os.path.join(ROOT, "logs", "slots")
LOCK_PATH = os.path.join(SLOTS_DIR, ".admit.lock")
DEFAULT_TTL = 1200          # слот протухает через 20 мин без обновления (крашнувшийся агент)
DEFAULT_RESERVE = 1         # оставить ядро под систему/git
LOCK_STALE = 10             # короткий крит-лок count+create протухает за 10с
_EPOCH = 1751000000         # фиксированная база (Date.now недоступен в некоторых средах — тут time.time ок)


def _slots(slots=None, reserve=DEFAULT_RESERVE):
    """Число слотов: явное --slots, иначе max(1, cpu_count − reserve)."""
    if slots and slots > 0:
        return slots
    cores = os.cpu_count() or int(os.environ.get("NUMBER_OF_PROCESSORS", "4") or 4)
    return max(1, cores - max(0, reserve))


def _ensure_dir():
    try:
        os.makedirs(SLOTS_DIR, exist_ok=True)
    except OSError:
        pass


def _now():
    return time.time()


def _read(path):
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def _write_atomic(path, data):
    tmp = path + ".tmp.%d" % os.getpid()
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
        json.dump(data, f, ensure_ascii=False)
    for _ in range(5):
        try:
            os.replace(tmp, path)
            return True
        except PermissionError:
            time.sleep(0.05)   # Windows: файл занят антивирусом/индексатором — ретрай
    try:
        os.remove(tmp)
    except OSError:
        pass
    return False


def _slot_path(agent):
    safe = "".join(c for c in agent if c.isalnum() or c in "-_")
    return os.path.join(SLOTS_DIR, "%s.slot" % (safe or "agent"))


def _active_slots(ttl):
    """Список (agent, data) свежих слотов (не протухших)."""
    _ensure_dir()
    out = []
    now = _now()
    try:
        names = os.listdir(SLOTS_DIR)
    except OSError:
        return out
    for name in names:
        if not name.endswith(".slot"):
            continue
        p = os.path.join(SLOTS_DIR, name)
        d = _read(p)
        if not d:
            continue
        if now - d.get("ts", 0) > d.get("ttl", ttl):
            # протухший слот крашнувшегося агента — снять (fencing: удаляем по совпадению файла)
            try:
                os.remove(p)
            except OSError:
                pass
            continue
        out.append((d.get("agent"), d))
    return out


class _CritLock:
    """Короткий O_EXCL-лок вокруг count+create (иначе гонка над-подписки слотов)."""
    def __enter__(self):
        _ensure_dir()
        deadline = _now() + 5
        while True:
            try:
                fd = os.open(LOCK_PATH, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                os.write(fd, str(os.getpid()).encode())
                os.close(fd)
                return self
            except OSError as e:
                if e.errno != errno.EEXIST:
                    return self  # не смогли — работаем без лока (advisory)
                # снять протухший крит-лок
                try:
                    if _now() - os.path.getmtime(LOCK_PATH) > LOCK_STALE:
                        os.remove(LOCK_PATH)
                        continue
                except OSError:
                    pass
                if _now() > deadline:
                    return self  # не дождались — advisory, продолжаем
                time.sleep(0.05)

    def __exit__(self, *exc):
        try:
            os.remove(LOCK_PATH)
        except OSError:
            pass
        return False


def _make_token():
    return "%x" % (int(_now() * 1000) ^ (os.getpid() << 8))


def acquire(agent, slots=None, reserve=DEFAULT_RESERVE, ttl=DEFAULT_TTL, wait=0):
    """Взять слот. Возвращает (True, token) если взял; (False, None) если очередь."""
    n_slots = _slots(slots, reserve)
    deadline = _now() + max(0, wait)
    while True:
        with _CritLock():
            active = _active_slots(ttl)
            mine = [d for a, d in active if a == agent]
            if mine:
                # уже держу слот — обновить (heartbeat), не занимать второй
                d = mine[0]
                d["ts"] = _now()
                _write_atomic(_slot_path(agent), d)
                return True, d.get("token")
            if len(active) < n_slots:
                token = _make_token()
                _write_atomic(_slot_path(agent),
                              {"agent": agent, "ts": _now(), "ttl": ttl, "token": token})
                return True, token
        # слотов нет
        if _now() >= deadline:
            return False, None
        time.sleep(min(2.0, max(0.2, wait / 20.0)))


def release(agent, token=None):
    """Снять СВОЙ слот (fencing по token, если задан)."""
    p = _slot_path(agent)
    d = _read(p)
    if not d:
        return False
    if token and d.get("token") != token:
        return False  # не мой актуальный слот (перехвачен) — не снимаю чужое
    try:
        os.remove(p)
        return True
    except OSError:
        return False


def status(ttl=DEFAULT_TTL, slots=None, reserve=DEFAULT_RESERVE):
    active = _active_slots(ttl)
    n_slots = _slots(slots, reserve)
    return {
        "slots_total": n_slots,
        "slots_used": len(active),
        "slots_free": max(0, n_slots - len(active)),
        "agents": [a for a, _ in active],
        "cores": os.cpu_count(),
    }


def main(argv=None):
    p = argparse.ArgumentParser(prog="work_admission.py",
                                description="Гейт B: потолок одновременности + очередь.")
    sub = p.add_subparsers(dest="cmd")
    for name in ("acquire", "release"):
        sp = sub.add_parser(name)
        sp.add_argument("agent")
        sp.add_argument("--slots", type=int, default=None)
        sp.add_argument("--reserve", type=int, default=DEFAULT_RESERVE)
        sp.add_argument("--ttl", type=int, default=DEFAULT_TTL)
        if name == "acquire":
            sp.add_argument("--wait", type=int, default=0)
        else:
            sp.add_argument("--token", default=None)
    st = sub.add_parser("status"); st.add_argument("--json", action="store_true")
    st.add_argument("--slots", type=int, default=None); st.add_argument("--reserve", type=int, default=DEFAULT_RESERVE)
    sl = sub.add_parser("slots"); sl.add_argument("--reserve", type=int, default=DEFAULT_RESERVE)
    args = p.parse_args(argv)

    if args.cmd == "slots":
        print(_slots(None, args.reserve))
        return 0
    if args.cmd == "acquire":
        ok, token = acquire(args.agent, args.slots, args.reserve, args.ttl, args.wait)
        if ok:
            print("ADMIT: слот взят (%s, token %s). Можно работать." % (args.agent, token))
            return 0
        s = status(args.ttl, args.slots, args.reserve)
        print("QUEUE: слотов нет (%d/%d заняты: %s). Встань в очередь / отложи тяжёлую работу или "
              "работай в worktree и ограничь нагрузку." % (s["slots_used"], s["slots_total"],
                                                           ", ".join(s["agents"])))
        return 1
    if args.cmd == "release":
        ok = release(args.agent, args.token)
        print("RELEASE: %s" % ("слот освобождён" if ok else "нет моего слота (или перехвачен)"))
        return 0
    s = status()
    if getattr(args, "json", False):
        print(json.dumps(s, ensure_ascii=False))
    else:
        print("work_admission: слотов %d, занято %d (%s), свободно %d; ядер %s" % (
            s["slots_total"], s["slots_used"], ", ".join(s["agents"]) or "—",
            s["slots_free"], s["cores"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
