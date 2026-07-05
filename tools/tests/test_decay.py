"""Тест decay.py — ось времени (температура по возрасту, stale-active сигнал)."""
# --- бутстрап путей (C14, аудит 2026-07-02): тест живёт в tools/tests/, инструменты — в tools/.
# Вставка ДО локальных импортов, чтобы standalone-запуск работал из нового места.
import os as _os
import sys as _sys
_TOOLS_DIR = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
if _TOOLS_DIR not in _sys.path:
    _sys.path.insert(0, _TOOLS_DIR)
# --- конец бутстрапа ---

import os
import sys
import time
import tempfile

os.environ.setdefault("PYTHONUTF8", "1")
HERE = _TOOLS_DIR  # tools/ — тест перенесён в tools/tests/ (C14)
sys.path.insert(0, HERE)
import decay

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

DAY = 86400


def _w(root, rel, txt, age_days):
    p = os.path.join(root, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8", newline="\n") as f:
        f.write(txt)
    # выставить fs-mtime в прошлое (git_mtimes вернёт {} в не-git temp → fallback на fs)
    t = time.time() - age_days * DAY
    os.utime(p, (t, t))


def main():
    fails = []
    with tempfile.TemporaryDirectory() as root:
        decay.ROOT = root
        now = int(time.time())
        # старый + активный → cold + stale-active
        _w(root, "tasks/T-1.md", "---\nid: T-1\ntype: task\nstatus: todo\n---\nт\n", age_days=30)
        # свежий + активный → hot, НЕ stale
        _w(root, "tasks/T-2.md", "---\nid: T-2\ntype: task\nstatus: doing\n---\nт\n", age_days=0)
        # старый, но терминальный → cold, НЕ stale (заморожен намеренно)
        _w(root, "tasks/T-3.md", "---\nid: T-3\ntype: task\nstatus: done\n---\nт\n", age_days=40)
        # средний возраст + активный → warm + stale
        _w(root, "questions/Q-1.md", "---\nid: Q-1\ntype: question\nstatus: open\n---\nт\n", age_days=8)

        data = decay.collect(now=now)
        temps = {r["id"]: r["temp"] for r in data["rows"]}
        if temps.get("T-1") != "cold":
            fails.append("T-1 (30д) не cold: %s" % temps.get("T-1"))
        if temps.get("T-2") != "hot":
            fails.append("T-2 (0д) не hot: %s" % temps.get("T-2"))
        if temps.get("Q-1") != "warm":
            fails.append("Q-1 (8д) не warm: %s" % temps.get("Q-1"))

        sa_ids = {r["id"] for r in data["stale_active"]}
        if "T-1" not in sa_ids:
            fails.append("cold+todo T-1 не в stale_active")
        if "Q-1" not in sa_ids:
            fails.append("warm+open Q-1 не в stale_active")
        if "T-2" in sa_ids:
            fails.append("hot T-2 ложно в stale_active")
        if "T-3" in sa_ids:
            fails.append("терминальный (done) T-3 ложно в stale_active")
        # сортировка: самый старый (T-1, 30д) раньше Q-1 (8д)
        if data["stale_active"] and data["stale_active"][0]["id"] != "T-1":
            fails.append("stale_active не отсортирован по возрасту (старшее первым)")

    if fails:
        print("FAIL test_decay:")
        for f in fails:
            print("  -", f)
        sys.exit(1)
    print("OK test_decay: температура hot/warm/cold + stale-active (актив+несвеж) + терминал-исключён + сортировка")


if __name__ == "__main__":
    main()
