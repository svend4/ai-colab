#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
conveyor — НАДЗИРАТЕЛЬ конвейера воркфлоу: следит, чтобы он не осушался, и за активностью оркестратора.

Проблема: оркестратор (агент) запускает фоновые воркфлоу, но НИЧЕГО не следит, что их в полёте
достаточно (>=цель) и что оркестратор вообще «тикает». Конвейер тихо встаёт до 0-1 ноды.
Этот инструмент — внешняя память + сигнал дозалива (docs/workflow-conveyor-policy.md §3-bis, §6):

  • реестр запущенных воркфлоу (logs/conveyor.json, runtime, gitignored): id, label, kind, state, depends;
  • на каждом действии оркестратора пишется heartbeat — staleness ловит «оркестратор замолчал»;
  • `status` считает in-flight против цели и ПЕЧАТАЕТ ВЕРДИКТ: REFILL / PROCESS / IDLE + exit-код
    (1 = нужно действие) — чтобы за конвейером можно было следить и из hook/CI/wakeup.

Дисциплина: landing воркфлоу переводит его inflight->landed (in-flight падает) => status сразу требует
дозалить. Так «вернулся к первому + сразу долил следующий» становится проверяемым, а не на память.

CLI:
  python tools/conveyor.py launch <id> <label> [--kind K] [--depends D]   # зарегистрировать запуск
  python tools/conveyor.py land  <id>            # .output пришёл (inflight->landed)
  python tools/conveyor.py ship  <id>            # обработан/отгружен (landed->shipped)
  python tools/conveyor.py dismiss <id> [--reason R]
  python tools/conveyor.py tick                  # оркестратор жив (обнови heartbeat)
  python tools/conveyor.py status [--target N] [--idle M] [--json]
  python tools/conveyor.py next                  # кандидаты дозалива из перспективного бэклога
"""
import os
import re
import sys
import json
import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LEDGER = os.path.join(ROOT, "logs", "conveyor.json")
BACKLOG = os.path.join(ROOT, "темы", "perspective-backlog-2026-06-23.md")
DEFAULT_TARGET = 2
DEFAULT_IDLE_MIN = 20


def configure_output():
    for name in ("stdout", "stderr"):
        s = getattr(sys, name, None)
        if s is not None and hasattr(s, "reconfigure"):
            s.reconfigure(encoding="utf-8", errors="replace")


configure_output()


def _now_iso():
    return datetime.datetime.now().replace(microsecond=0).isoformat()


def load(path=LEDGER):
    if os.path.exists(path):
        try:
            with open(path, encoding="utf-8") as f:
                d = json.load(f)
        except (OSError, ValueError):
            d = {}
    else:
        d = {}
    d.setdefault("target_min", DEFAULT_TARGET)
    d.setdefault("idle_min", DEFAULT_IDLE_MIN)
    d.setdefault("heartbeat", None)
    d.setdefault("workflows", [])
    return d


def save(d, path=LEDGER):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)
        f.write("\n")
    os.replace(tmp, path)


def _find(d, wid):
    for w in d["workflows"]:
        if w.get("id") == wid:
            return w
    return None


def _touch(d, now=None):
    d["heartbeat"] = now or _now_iso()


def cmd_launch(d, wid, label, kind="workflow", depends="none"):
    w = _find(d, wid)
    if w:
        w.update(label=label, kind=kind, depends_on=depends, state="inflight")
    else:
        d["workflows"].append({"id": wid, "label": label, "kind": kind,
                               "state": "inflight", "launched": _now_iso(), "depends_on": depends})
    _touch(d)
    return "launch: %s (%s) inflight" % (label, wid)


def _set_state(d, wid, state):
    w = _find(d, wid)
    if not w:
        return "нет воркфлоу %s в реестре" % wid
    w["state"] = state
    _touch(d)
    return "%s -> %s (%s)" % (w.get("label", wid), state, wid)


def _age_min(ts, now):
    if not ts:
        return None
    try:
        t0 = datetime.datetime.fromisoformat(ts)
    except ValueError:
        return None
    return round((now - t0).total_seconds() / 60.0, 1)


def assess(d, now, target=None, idle_min=None):
    """Чистая оценка состояния конвейера. now — datetime; target/idle переопределяют ledger."""
    target = d.get("target_min", DEFAULT_TARGET) if target is None else target
    idle_min = d.get("idle_min", DEFAULT_IDLE_MIN) if idle_min is None else idle_min
    inflight = [w for w in d["workflows"] if w.get("state") == "inflight"]
    landed = [w for w in d["workflows"] if w.get("state") == "landed"]
    shipped = [w for w in d["workflows"] if w.get("state") == "shipped"]
    idle_age = _age_min(d.get("heartbeat"), now)
    actions = []
    deficit = target - len(inflight)
    if deficit > 0:
        actions.append("REFILL: запусти ещё %d (in-flight %d < цель %d) — `conveyor.py next`"
                       % (deficit, len(inflight), target))
    if landed:
        actions.append("PROCESS: %d приземлившихся ждут обработки: %s"
                       % (len(landed), ", ".join(w.get("label", w["id"]) for w in landed)))
    if idle_age is not None and idle_age > idle_min:
        actions.append("IDLE: оркестратор молчит %.0f мин (> %d) — тикни/долей или заверши конвейер" % (idle_age, idle_min))
    return {
        "target": target,
        "n_inflight": len(inflight), "n_landed": len(landed), "n_shipped": len(shipped),
        "inflight": [w.get("label", w["id"]) for w in inflight],
        "landed": [w.get("label", w["id"]) for w in landed],
        "idle_age_min": idle_age,
        "deficit": max(0, deficit),
        "actions": actions,
        "healthy": not actions,
    }


def render_status(a):
    L = ["=" * 56, "CONVEYOR — надзиратель конвейера воркфлоу", "=" * 56,
         "in-flight: %d / цель %d   landed-ждут: %d   shipped: %d"
         % (a["n_inflight"], a["target"], a["n_landed"], a["n_shipped"])]
    if a["inflight"]:
        L.append("  в полёте: " + ", ".join(a["inflight"]))
    if a["idle_age_min"] is not None:
        L.append("  heartbeat: %.0f мин назад" % a["idle_age_min"])
    L.append("-" * 56)
    if a["healthy"]:
        L.append("OK: конвейер полон, оркестратор активен, очередь обработана")
    else:
        for act in a["actions"]:
            L.append("  ▸ " + act)
    L.append("=" * 56)
    return "\n".join(L)


def backlog_candidates(d, path=BACKLOG):
    """Темы из «Готовы к запуску» бэклога, ещё НЕ заведённые в реестр (по подстроке label)."""
    if not os.path.exists(path):
        return []
    txt = open(path, encoding="utf-8", errors="replace").read()
    m = re.search(r"##\s*Готовы к запуску.*?\n(.*?)(?:\n##\s|\Z)", txt, re.S)
    if not m:
        return []
    items = re.findall(r"^\s*\d+\.\s*(.+?)\s*$", m.group(1), re.M)
    launched = " ".join((w.get("label", "") + " " + w.get("id", "")) for w in d["workflows"]).lower()
    out = []
    for it in items:
        key = re.split(r"[:(]", it)[0].strip().lower()[:18]
        if key and key not in launched:
            out.append(it.strip())
    return out


def _arg(a, flag, default=None):
    return a[a.index(flag) + 1] if flag in a and a.index(flag) + 1 < len(a) else default


def main():
    a = sys.argv[1:]
    if not a:
        print(__doc__)
        return 2
    cmd = a[0]
    d = load()
    try:
        if cmd == "launch" and len(a) >= 3:
            print(cmd_launch(d, a[1], a[2], _arg(a, "--kind", "workflow"), _arg(a, "--depends", "none")))
            save(d)
            return 0
        if cmd in ("land", "ship") and len(a) >= 2:
            print(_set_state(d, a[1], "landed" if cmd == "land" else "shipped"))
            save(d)
            return 0
        if cmd == "dismiss" and len(a) >= 2:
            print(_set_state(d, a[1], "dismissed") + (" — " + _arg(a, "--reason", "") if "--reason" in a else ""))
            save(d)
            return 0
        if cmd == "tick":
            _touch(d)
            save(d)
            print("tick: heartbeat %s" % d["heartbeat"])
            return 0
        if cmd == "status":
            target = int(_arg(a, "--target", d.get("target_min", DEFAULT_TARGET)))
            idle = int(_arg(a, "--idle", d.get("idle_min", DEFAULT_IDLE_MIN)))
            res = assess(d, datetime.datetime.now(), target=target, idle_min=idle)
            if "--json" in a:
                print(json.dumps(res, ensure_ascii=False, indent=2))
            else:
                print(render_status(res))
            return 1 if not res["healthy"] else 0
        if cmd == "next":
            cands = backlog_candidates(d)
            if not cands:
                print("Бэклог пуст или все заведены — пересними бэклог (сканер) или заверши конвейер.")
                return 0
            print("Кандидаты дозалива (из перспективного бэклога, ещё не запущены):")
            for c in cands:
                print("  • " + c)
            return 0
    except Exception as exc:  # noqa: BLE001
        print("ОШИБКА: %s: %s" % (type(exc).__name__, exc))
        return 1
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main())
