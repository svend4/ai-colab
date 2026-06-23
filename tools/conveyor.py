#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
conveyor — НАДЗИРАТЕЛЬ конвейера воркфлоу: следит, чтобы он не осушался, и за активностью оркестратора.

Проблема: оркестратор (агент) запускает фоновые воркфлоу, но НИЧЕГО не следит, что их в полёте
достаточно (>=цель) и что оркестратор вообще «тикает». Конвейер тихо встаёт до 0-1 ноды.
Этот инструмент — внешняя память + сигнал дозалива (docs/workflow-conveyor-policy.md §3-bis, §6):

  • реестр запущенных воркфлоу (logs/conveyor.json, runtime, gitignored): id, label, kind, state, depends, output;
  • на каждом действии оркестратора пишется heartbeat — staleness ловит «оркестратор замолчал»;
  • `status` считает in-flight против цели и ПЕЧАТАЕТ ВЕРДИКТ: REFILL / PROCESS / IDLE + exit-код
    (1 = нужно действие) — чтобы за конвейером можно было следить и из hook/CI/wakeup.

Дисциплина: landing воркфлоу переводит его inflight->landed (in-flight падает) => status сразу требует
дозалить. Если `land` пришёл без `--output`, status отдельно подсветит missing-output: воркфлоу
завершён, но оркестратору нечего машинно извлекать. Так «вернулся к первому + сразу долил следующий»
становится проверяемым, а не на память.

CLI:
  python tools/conveyor.py launch <id> <label> [--kind K] [--depends D]   # зарегистрировать запуск
  python tools/conveyor.py land  <id> [--output PATH]  # .output пришёл (inflight->landed + ref)
  python tools/conveyor.py ship  <id>            # обработан/отгружен (landed->shipped)
  python tools/conveyor.py dismiss <id> [--reason R]
  python tools/conveyor.py tick                  # оркестратор жив (обнови heartbeat)
  python tools/conveyor.py target <N>            # задать цель in-flight (масштаб под надобность; не зашито в 2)
  python tools/conveyor.py plan <N> [--span 3]   # reduce-иерархия 3:1 для N продюсеров (бригады/дирижёры/глубина)
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
        w.pop("output", None)
    else:
        d["workflows"].append({"id": wid, "label": label, "kind": kind,
                               "state": "inflight", "launched": _now_iso(), "depends_on": depends})
    _touch(d)
    return "launch: %s (%s) inflight" % (label, wid)


def _set_state(d, wid, state, output=None):
    w = _find(d, wid)
    if not w:
        return "нет воркфлоу %s в реестре" % wid
    w["state"] = state
    if output is not None:
        w["output"] = output
    _touch(d)
    msg = "%s -> %s (%s)" % (w.get("label", wid), state, wid)
    if output is not None:
        msg += " output=%s" % output
    return msg


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
    landed_outputs = [
        {"id": w["id"], "label": w.get("label", w["id"]), "output": w.get("output")}
        for w in landed
        if w.get("output")
    ]
    landed_without_output = [w for w in landed if not w.get("output")]
    idle_age = _age_min(d.get("heartbeat"), now)
    actions = []
    deficit = target - len(inflight)
    if deficit > 0:
        actions.append("REFILL: запусти ещё %d (in-flight %d < цель %d) — `conveyor.py next`"
                       % (deficit, len(inflight), target))
    if landed:
        actions.append("PROCESS: %d приземлившихся ждут обработки: %s"
                       % (len(landed), ", ".join(w.get("label", w["id"]) for w in landed)))
    if landed_without_output:
        actions.append("PROCESS-MISSING-OUTPUT: %d landed без output/ref: %s — добавь `conveyor.py land <id> --output <path>` или dismiss с причиной"
                       % (len(landed_without_output), ", ".join(w.get("label", w["id"]) for w in landed_without_output)))
    if idle_age is not None and idle_age > idle_min:
        actions.append("IDLE: оркестратор молчит %.0f мин (> %d) — тикни/долей или заверши конвейер" % (idle_age, idle_min))
    return {
        "target": target,
        "n_inflight": len(inflight), "n_landed": len(landed), "n_shipped": len(shipped),
        "inflight": [w.get("label", w["id"]) for w in inflight],
        "landed": [w.get("label", w["id"]) for w in landed],
        "landed_outputs": landed_outputs,
        "landed_without_output": [w.get("label", w["id"]) for w in landed_without_output],
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
    if a.get("landed_outputs"):
        L.append("  landed output: " + ", ".join("%s -> %s" % (w["label"], w["output"]) for w in a["landed_outputs"]))
    if a.get("landed_without_output"):
        L.append("  landed без output: " + ", ".join(a["landed_without_output"]))
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


def _backlog_key(text):
    return re.split(r"[:(]", text or "")[0].strip()


def _norm_key(text):
    return re.sub(r"[^0-9a-zа-яё]+", " ", (text or "").lower()).strip()


def _compact_key(text):
    return re.sub(r"[^0-9a-zа-яё]+", "", (text or "").lower())


def _workflow_index(workflows):
    raw = " ".join((w.get("label", "") + " " + w.get("id", "")) for w in workflows)
    return _norm_key(raw), _compact_key(raw)


def _candidate_seen(item, launched_norm, launched_compact):
    key = _backlog_key(item)
    norm = _norm_key(key)
    compact = _compact_key(key)
    return bool((norm and norm in launched_norm) or (len(compact) >= 8 and compact in launched_compact))


def backlog_candidates(d, path=BACKLOG):
    """Темы из «Готовы к запуску» бэклога, ещё НЕ заведённые в реестр (нормализованный label/id dedup)."""
    if not os.path.exists(path):
        return []
    txt = open(path, encoding="utf-8", errors="replace").read()
    m = re.search(r"##\s*Готовы к запуску.*?\n(.*?)(?:\n##\s|\Z)", txt, re.S)
    if not m:
        return []
    items = re.findall(r"^\s*\d+\.\s*(.+?)\s*$", m.group(1), re.M)
    launched_norm, launched_compact = _workflow_index(d.get("workflows", []))
    out = []
    for it in items:
        if not _candidate_seen(it, launched_norm, launched_compact):
            out.append(it.strip())
    return out


def plan_hierarchy(n_producers, span=3):
    """Reduce-дерево с фан-ином `span` (3:1 span-of-control): producers → integrators →
    conductors → chief... Возвращает слои снизу вверх: {level, role, count, fan_in}.
    Верхний слой (count <= span) коммитит оркестратор-человек."""
    span = max(2, int(span))
    n = max(0, int(n_producers))
    roles = ["producer", "integrator (бригада)", "conductor (дирижёр)", "chief-conductor"]
    layers = [{"level": 0, "role": "producer", "count": n, "fan_in": span}]
    if n <= 0:
        return layers
    count, lvl = n, 0
    while True:
        lvl += 1
        parents = -(-count // span)  # ceil(count/span)
        role = roles[lvl] if lvl < len(roles) else "L%d-conductor" % lvl
        layers.append({"level": lvl, "role": role, "count": parents, "fan_in": span})
        if parents <= span:
            break
        count = parents
    return layers


def render_plan(n, span, layers):
    integr = sum(L["count"] for L in layers if L["level"] >= 1)
    top = layers[-1]["count"]
    depth = layers[-1]["level"]
    total = n + integr
    overhead = (100.0 * integr / n) if n else 0.0
    out = ["=" * 60,
           "CONVEYOR PLAN — reduce-иерархия %d:1 (span of control)" % span, "=" * 60,
           "producers: %d · глубина: %d уровн. · интеграторов: %d" % (n, depth, integr),
           "воркфлоу всего: %d · накладные интеграции: ~%.0f%% (геом. предел ~50%%)" % (total, overhead),
           "верх (≤%d) коммитит оркестратор-человек: %d артефакт(ов)" % (span, top),
           "-" * 60]
    for L in reversed(layers):
        out.append("  L%d %-22s × %-5d %s" % (L["level"], L["role"], L["count"], "•" * min(L["count"], 42)))
    out.append("=" * 60)
    return "\n".join(out)


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
            output = _arg(a, "--output") if cmd == "land" else None
            print(_set_state(d, a[1], "landed" if cmd == "land" else "shipped", output=output))
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
        if cmd == "target" and len(a) >= 2:
            d["target_min"] = max(1, int(a[1]))
            _touch(d)
            save(d)
            print("target_min = %d (флот масштабируется под открытые вопросы; "
                  "потолок — полоса обработки оркестратора)" % d["target_min"])
            return 0
        if cmd == "plan" and len(a) >= 2:
            span = int(_arg(a, "--span", 3))
            print(render_plan(int(a[1]), span, plan_hierarchy(int(a[1]), span)))
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
