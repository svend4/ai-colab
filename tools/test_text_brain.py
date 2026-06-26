"""Тест text_brain.py — proposal-only · детерминизм offline · kind-фолбэк · write+load · llama-graceful."""
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import text_brain as tb
import text_mux as tm

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass


def main():
    fails = []

    # 1) propose: n ячеек, ВСЕ proposed, owner brain, детерминирован offline
    cells = tb.propose("оракул", kind="claim", n=3)
    if len(cells) != 3:
        fails.append("ожидалось 3 ячейки: %d" % len(cells))
    if any(c["status"] != "proposed" for c in cells):
        fails.append("ВСЕ ячейки должны быть proposed (brain не принимает): %s" % [c["status"] for c in cells])
    if any(not c["owner"].startswith("brain:") for c in cells):
        fails.append("owner должен быть brain:<model>: %s" % [c["owner"] for c in cells])
    if [c["id"] for c in cells] != [c["id"] for c in tb.propose("оракул", kind="claim", n=3)]:
        fails.append("offline propose должен быть ДЕТЕРМИНИРОВАН (одинаковые id)")
    if cells[0]["body"] != tb.propose("оракул", kind="claim", n=3)[0]["body"]:
        fails.append("offline body детерминирован")

    # 2) недопустимый kind → claim
    if tb.propose("t", kind="decision", n=1)[0]["kind"] != "claim":
        fails.append("kind вне KINDS → claim (модель не вправе предлагать decision/accept)")

    # 3) proposal-only инвариант: никакой kind не даёт accepted
    for k in tb.KINDS:
        if any(c["status"] == "accepted" for c in tb.propose("t", kind=k, n=2)):
            fails.append("kind %s не должен давать accepted" % k)

    # 4) write_proposals: валидные ячейки, грузятся text_mux, всё proposed, событие записано
    canvas = os.path.join(REPO_ROOT, "tmp-work", "text_brain_test_%d_%d" % (os.getpid(), time.time_ns()))
    os.makedirs(canvas, exist_ok=True)
    written = tb.write_proposals(canvas, cells)
    if len(written) != 3:
        fails.append("write_proposals: 3 файла, получено %d" % len(written))
    loaded, warn = tm.load_cells(canvas)
    if len(loaded) != 3 or warn:
        fails.append("text_mux должен загрузить 3 валидные ячейки без предупреждений: %d/%s" % (len(loaded), warn))
    if any(c["status"] != "proposed" for c in loaded):
        fails.append("на диске все ячейки proposed")
    ev = tm.read_events(os.path.join(canvas, "outbox"))
    if len(ev) != 3 or any(e.get("status") != "proposed" for e in ev):
        fails.append("должно быть 3 события cell_seed (proposed): %s" % ev)

    # 5) llama недоступна → graceful (offline-фолбэк в теле), не краш
    r = tb.propose("t", kind="claim", n=1, model="x", endpoint="http://127.0.0.1:1/v1")
    if len(r) != 1 or not r[0]["body"]:
        fails.append("недоступная llama → graceful фолбэк, не краш: %s" % r)
    if r[0]["status"] != "proposed":
        fails.append("даже при llama-фолбэке status proposed")

    if fails:
        print("FAIL test_text_brain:")
        for f in fails:
            print("  -", f)
        sys.exit(1)
    print("OK test_text_brain: proposal-only(никогда accepted) · offline-детерминизм · kind-фолбэк · write+load(text_mux) · события · llama-graceful")


if __name__ == "__main__":
    main()
