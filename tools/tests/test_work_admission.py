# ast: allow-subprocess
#!/usr/bin/env python3
# [FILE ID CARD]
# id: tools/tests/test_work_admission.py
# purpose: Тест Гейта B — потолок слотов, очередь при переполнении, release, TTL-очистка, re-acquire.
# mode: test (временный SLOTS_DIR в системном temp, канон и git не трогает)
# related: tools/work_admission.py
"""Самопроверка work_admission: cap + очередь + fencing + TTL."""
import importlib.util
import json
import os
import shutil
import tempfile
import time

_TOOLS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_spec = importlib.util.spec_from_file_location("work_admission",
                                               os.path.join(_TOOLS, "work_admission.py"))
wa = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(wa)


def _tmp():
    d = tempfile.mkdtemp(prefix="work_admission_test_")
    wa.SLOTS_DIR = os.path.join(d, "logs", "slots")
    wa.LOCK_PATH = os.path.join(wa.SLOTS_DIR, ".admit.lock")
    return d


def test_cap_and_queue():
    d = _tmp()
    try:
        ok1, t1 = wa.acquire("claude", slots=2, wait=0)
        ok2, t2 = wa.acquire("codex", slots=2, wait=0)
        ok3, t3 = wa.acquire("mavis", slots=2, wait=0)   # 3-й при 2 слотах → очередь
        assert ok1 and ok2, "первые два должны взять слот"
        assert not ok3, "третий при 2 слотах должен уйти в очередь (False)"
        s = wa.status(slots=2)
        assert s["slots_used"] == 2 and s["slots_free"] == 0, s
        print("  OK: cap=2 держится, 3-й в очереди")
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_release_frees_slot():
    d = _tmp()
    try:
        ok1, t1 = wa.acquire("claude", slots=2, wait=0)
        wa.acquire("codex", slots=2, wait=0)
        assert not wa.acquire("mavis", slots=2, wait=0)[0], "полно → очередь"
        assert wa.release("claude", t1), "release своего слота"
        ok3, _ = wa.acquire("mavis", slots=2, wait=0)
        assert ok3, "после release слот освободился для mavis"
        print("  OK: release освобождает слот для очереди")
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_reacquire_no_double():
    d = _tmp()
    try:
        wa.acquire("claude", slots=2, wait=0)
        wa.acquire("claude", slots=2, wait=0)   # повторно тот же агент
        s = wa.status(slots=2)
        assert s["slots_used"] == 1, "повторный acquire того же агента не занимает 2 слота: %s" % s
        print("  OK: re-acquire того же агента не удваивает слот")
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_ttl_cleanup():
    d = _tmp()
    try:
        wa._ensure_dir()
        # слот-«крашнувшийся»: ts далеко в прошлом, ttl мал
        p = wa._slot_path("ghost")
        with open(p, "w", encoding="utf-8") as f:
            json.dump({"agent": "ghost", "ts": time.time() - 9999, "ttl": 60, "token": "x"}, f)
        active = wa._active_slots(ttl=60)
        assert all(a != "ghost" for a, _ in active), "протухший слот должен быть снят по TTL"
        assert not os.path.exists(p), "файл протухшего слота удалён"
        print("  OK: TTL снимает слот крашнувшегося агента")
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_release_fencing():
    d = _tmp()
    try:
        ok, t = wa.acquire("claude", slots=2, wait=0)
        assert not wa.release("claude", token="wrong-token"), "release с чужим токеном не снимает"
        assert os.path.exists(wa._slot_path("claude")), "слот на месте после чужого release"
        assert wa.release("claude", token=t), "release со своим токеном снимает"
        print("  OK: fencing — release только своим токеном")
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_slots_autodetect():
    # число слотов = max(1, cores - reserve); при reserve>=cores → 1
    assert wa._slots(slots=None, reserve=999) == 1, "reserve>=cores → минимум 1 слот"
    assert wa._slots(slots=5) == 5, "явный --slots переопределяет"
    print("  OK: авто-определение слотов (ядра−запас), минимум 1, явный override")


def run():
    test_cap_and_queue()
    test_release_frees_slot()
    test_reacquire_no_double()
    test_ttl_cleanup()
    test_release_fencing()
    test_slots_autodetect()
    print("TESTS OK work_admission: cap+очередь + release + re-acquire + TTL + fencing + автослоты")


if __name__ == "__main__":
    run()
