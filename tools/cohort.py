#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
cohort (вершина пирамиды, форк-вариант Claude по D-017) — «одна кнопка» для ПАРАЛЛЕЛЬНОЙ
много-агентной работы и для работы системы НАД САМОЙ СОБОЙ.

Это комплемент к `tools/top.py` (панель Codex, T-138): top.py = кнопки для человека и одиночного
агента (start/health/take/snapshot/knowledge); cohort.py добавляет то, что подчёркнул Stefan и чего
в панели нет — как нескольким агентам работать ОДНОВРЕМЕННО без коллизий, и как движок обслуживает
сам себя. Ничего нового внизу не строит: только группирует уже работающие инструменты в сценарии.

Аудитория двойная: человек читает таблицы; агент берёт `--json`. Безопасно по умолчанию —
side-effect команды (`turn`, `ship`) только ПЕЧАТАЮТ план, пока не передан `--run` (как в flow.py).

Команды:
    python tools/cohort.py board                 # ДАШБОРД параллельной работы (котёл+claim+дрейф+здоровье)
    python tools/cohort.py plan [N]              # раздать N агентам разные готовые задачи без коллизий
    python tools/cohort.py turn  <agent> [--run] # безопасная параллельная смена агента (взять→контекст→гейт→ship)
    python tools/cohort.py gate  <agent>         # пред-merge гейт (merge_gate: validate+generate --check+permissions)
    python tools/cohort.py ship  <agent> <file...> [--run]  # коммит под commit_lock + selective-add (политика Ур.0)
    python tools/cohort.py self                  # САМОХОСТИНГ: движок проверяет/чинит сам себя, что улучшить дальше

Добавь `--json` к board/plan/self для машинно-читаемого вывода.
"""
import os
import re
import sys
import json
import glob
import subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOLS = os.path.join(ROOT, "tools")
CAPS = os.path.join(ROOT, "system-capabilities.json")


def configure_output():
    for name in ("stdout", "stderr"):
        s = getattr(sys, name, None)
        if s is not None and hasattr(s, "reconfigure"):
            s.reconfigure(encoding="utf-8", errors="replace")


configure_output()


def _run(script, *args):
    """Запустить tools/<script> и вернуть (rc, текст). Read-only по умолчанию у вызываемых."""
    p = subprocess.run([sys.executable, os.path.join(TOOLS, script), *args],
                       cwd=ROOT, capture_output=True, text=True,
                       encoding="utf-8", errors="replace", stdin=subprocess.DEVNULL)
    return p.returncode, (p.stdout or "") + (p.stderr or "")


def _git(*args):
    p = subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True,
                       encoding="utf-8", errors="replace", stdin=subprocess.DEVNULL)
    return p.returncode, (p.stdout or "")


def _flag(args, name):
    return name in args


def _caps():
    try:
        with open(CAPS, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def _active_claims():
    """Список (task, holder) из queues/claimed/*.claim.md — кто что держит (не трогать чужое)."""
    out = []
    for p in sorted(glob.glob(os.path.join(ROOT, "queues", "claimed", "*.claim.md"))):
        task = os.path.basename(p)[:-len(".claim.md")]
        holder = "?"
        try:
            for line in open(p, encoding="utf-8", errors="replace"):
                m = re.match(r"\s*agent\s*:\s*(\S+)", line)
                if m:
                    holder = m.group(1)
                    break
        except OSError:
            pass
        out.append((task, holder))
    return out


def _pipeline_sections():
    """Вернуть {in_work:[..], ready:[..], blocked:[..]} из pipeline.py status."""
    _, out = _run("pipeline.py", "status")
    sec = {"in_work": [], "ready": [], "blocked": []}
    cur = None
    for ln in out.splitlines():
        s = ln.strip()
        if "В РАБОТЕ" in s:
            cur = "in_work"; continue
        if "ГОТОВЫ К ВЗЯТИЮ" in s:
            cur = "ready"; continue
        if "ЗАБЛОКИРОВАН" in s or "НЕ ГОТОВ" in s:
            cur = "blocked"; continue
        if cur and s and s[0:1] in ("T", "Q", "D", "-", "•") and "(" in s:
            sec[cur].append(s.lstrip("-• ").strip())
    return sec


def _ready_ids():
    """id готовых к взятию задач (через dispatch.py, источник готовности по DAG)."""
    rc, out = _run("dispatch.py")
    ids = re.findall(r"\bT-\d+\b", out)
    # сохранить порядок, без дублей
    seen, res = set(), []
    for i in ids:
        if i not in seen:
            seen.add(i); res.append(i)
    return res


# ---------------------------------------------------------------- board

def board(as_json=False):
    sec = _pipeline_sections()
    claims = _active_claims()
    _, drift = _run("drift_check.py")
    drift_head = (drift.strip().splitlines() or ["?"])[0]
    c = _caps() or {}
    _, log = _git("log", "--oneline", "-5")
    data = {
        "stage": c.get("stage"),
        "drivers": "%s/%s ready" % (c.get("drivers_ready"), c.get("drivers_total")),
        "in_work": sec["in_work"], "ready": sec["ready"], "blocked": sec["blocked"],
        "active_claims": [{"task": t, "holder": h} for t, h in claims],
        "drift": drift_head,
        "recent_commits": [l for l in log.splitlines() if l.strip()],
    }
    if as_json:
        print(json.dumps(data, ensure_ascii=False, indent=2))
        return 0
    line = "=" * 64
    print(line); print("COHORT BOARD — параллельная работа над серединой пирамиды"); print(line)
    print("Стадия: %s | драйверы: %s" % (data["stage"], data["drivers"]))
    print("Дрейф:  %s" % data["drift"])
    print("\nВ РАБОТЕ (%d):" % len(sec["in_work"]))
    for x in sec["in_work"] or ["  (никто)"]:
        print("  " + x)
    print("\nЗАНЯТО claim'ами (не трогать чужое):")
    for t, h in claims or [("(нет)", "")]:
        print("  %-28s %s" % (t, h))
    print("\nГОТОВЫ К ВЗЯТИЮ (%d) — можно разобрать параллельно:" % len(sec["ready"]))
    for x in sec["ready"] or ["  (пусто)"]:
        print("  " + x)
    print("\nЗАБЛОКИРОВАНЫ (%d):" % len(sec["blocked"]))
    for x in sec["blocked"] or ["  (нет)"]:
        print("  " + x)
    print("\nПоследние коммиты:")
    for l in data["recent_commits"]:
        print("  " + l)
    print("\nДальше: `cohort.py plan` (раздать) · `cohort.py turn <agent>` · `cohort.py self`")
    print(line)
    return 0


# ---------------------------------------------------------------- plan

def plan(n=2, as_json=False):
    ready = _ready_ids()
    claims = {t for t, _ in _active_claims()}
    free = [t for t in ready if t not in claims]
    agents = ["claude", "codex", "mavis", "novax"][:max(1, n)]
    assign = {a: [] for a in agents}
    for i, task in enumerate(free):
        assign[agents[i % len(agents)]].append(task)
    if as_json:
        print(json.dumps({"agents": agents, "free_ready": free, "assignment": assign},
                         ensure_ascii=False, indent=2))
        return 0
    print("ПАРАЛЛЕЛЬНАЯ РАЗДАЧА (%d агентов, %d свободных готовых задач)" % (len(agents), len(free)))
    print("Принцип: каждому — РАЗНЫЕ задачи; атомарный claim снимает гонку (pipeline next).")
    for a in agents:
        ids = assign[a] or ["(нет — взять из общего котла позже)"]
        print("  %-8s -> %s" % (a, ", ".join(ids)))
    print("\nКаждый агент стартует своей сменой: `python tools/cohort.py turn <agent> --run`")
    return 0


# ---------------------------------------------------------------- turn

def turn(agent, do_run=False):
    """Безопасная параллельная смена одного агента: контекст -> взять -> работать -> гейт -> ship."""
    print("=== СМЕНА АГЕНТА: %s ===" % agent)
    _, mine = _run("pipeline.py", "mine", agent)
    print("\nТвои активные задачи:")
    for l in (mine.strip().splitlines() or ["  (нет)"])[:6]:
        print("  " + l.strip())
    ready = _ready_ids()
    claims = {t for t, _ in _active_claims()}
    free = [t for t in ready if t not in claims]
    print("\nСвободные готовые задачи: %s" % (", ".join(free) or "(пусто)"))
    steps = [
        ("взять следующую (атомарно, без коллизий)", [sys.executable, "tools/pipeline.py", "next", agent]),
        ("...сделать работу в своей зоне (selective-add потом)...", None),
        ("гейт перед merge", [sys.executable, "tools/cohort.py", "gate", agent]),
        ("безопасный коммит", [sys.executable, "tools/cohort.py", "ship", agent, "<твои файлы>", "--run"]),
    ]
    print("\nПлан смены:")
    for desc, cmd in steps:
        print("  - " + desc)
        if cmd:
            print("      $ " + " ".join(cmd))
    if not do_run:
        print("\n(печать; добавь --run, чтобы реально взять следующую задачу)")
        return 0
    print("\n--run: беру следующую задачу...")
    rc, out = _run("pipeline.py", "next", agent)
    print(out.strip())
    return rc


# ---------------------------------------------------------------- gate

def gate(agent):
    """Пред-merge гейт = merge_gate.check (validate + generate --check + permissions)."""
    rc, out = _run("merge_gate.py", "check", agent)
    print(out.strip() or "(merge_gate без вывода)")
    return rc


# ---------------------------------------------------------------- ship

def ship(agent, files, message=None, do_run=False):
    """Полный безопасный цикл коммита в общем дереве (политика Уровень 0):
    commit_lock (сериализация) → selective-add (только свои файлы) → regenerate (чтобы pre-commit hook
    не падал на устарелости от чужих незакоммиченных правок) → commit → release. Индексы regenerate
    оставляем не-staged — их закоммитит владелец изменивших источников."""
    if not files:
        print("ship: укажи файлы (selective-add; никогда git add -A в общем дереве)")
        return 2
    msg = message or "ship(%s): %s" % (agent, ", ".join(files))
    plan_cmds = [
        ("взять commit-lock (сериализация)", [sys.executable, "tools/commit_lock.py", "acquire", agent]),
        ("добавить ТОЛЬКО свои файлы", ["git", "add", *files]),
        ("обновить индексы (hook не упадёт на чужой устарелости)", [sys.executable, "tools/generate.py"]),
        ("коммит", ["git", "commit", "-m", msg]),
        ("освободить lock", [sys.executable, "tools/commit_lock.py", "release", agent]),
    ]
    print("SHIP (%s): %d файл(ов) — commit_lock + selective-add + regenerate" % (agent, len(files)))
    for desc, cmd in plan_cmds:
        print("  - %s\n      $ %s" % (desc, " ".join(cmd)))
    if not do_run:
        print("\n(печать; добавь --run [--message \"...\"], чтобы выполнить)")
        return 0
    rc, _ = _run("commit_lock.py", "acquire", agent)
    if rc != 0:
        print("commit-lock занят — попробуй позже (другой агент коммитит)")
        return rc
    try:
        rc1, _o = _git("add", *files)
        _run("generate.py")  # обновить производные индексы (не-staged) — hook увидит свежее дерево
        rc2, out2 = _git("commit", "-m", msg)
        print("git add rc=%d, commit rc=%d" % (rc1, rc2))
        if rc2 != 0:
            print((out2.strip()[-300:]) or "(commit не прошёл — см. hook)")
    finally:
        _run("commit_lock.py", "release", agent)
    return 0


# ---------------------------------------------------------------- self (самохостинг)

def self_host(as_json=False):
    """Движок обслуживает сам себя: прогнать собственную quality-автоматику и сказать, что улучшить."""
    checks = []

    def add(name, rc, out, ok_if_zero=True):
        ok = (rc == 0) if ok_if_zero else True
        checks.append({"check": name, "ok": ok, "head": (out.strip().splitlines() or [""])[0][:90]})

    rc, out = _run("validate.py")
    m = re.search(r"ERROR=(\d+)", out)
    add("validate (канон)", 0 if (m and int(m.group(1)) == 0) else 1, out)
    rc, out = _run("generate.py", "--check")
    add("generate --check (навигация свежа)", rc, out)
    rc, out = _run("capabilities.py", "--check")
    add("capabilities --check (манифест свеж)", rc, out)
    rc, out = _run("drift_check.py")
    add("drift_check (docs↔факт)", rc, out)
    sec = _pipeline_sections()

    todo = []
    for ch in checks:
        if not ch["ok"]:
            if "generate" in ch["check"]:
                todo.append("Навигация устарела → `python tools/generate.py` (под commit_lock).")
            elif "capabilities" in ch["check"]:
                todo.append("Манифест способностей устарел → `python tools/capabilities.py snapshot`.")
            elif "drift" in ch["check"]:
                todo.append("Дрейф: " + ch["head"])
            elif "validate" in ch["check"]:
                todo.append("Канон сломан → смотри `python tools/validate.py`.")
    if sec["ready"]:
        todo.append("В котле %d готовых задач → раздать: `python tools/cohort.py plan`." % len(sec["ready"]))

    if as_json:
        print(json.dumps({"checks": checks, "ready_count": len(sec["ready"]), "todo": todo},
                         ensure_ascii=False, indent=2))
        return 0
    line = "=" * 64
    print(line); print("COHORT SELF — движок проверяет и обслуживает сам себя"); print(line)
    for ch in checks:
        print("  [%s] %-34s %s" % ("OK" if ch["ok"] else "!!", ch["check"], ch["head"]))
    print("\nЧто улучшить дальше (self-hosting backlog):")
    for t in todo or ["  всё зелёное — взять задачу из котла: `cohort.py plan`"]:
        print("  - " + t)
    print(line)
    return 0 if all(c["ok"] for c in checks) else 1


# ---------------------------------------------------------------- CLI

def main():
    a = sys.argv[1:]
    if not a:
        print(__doc__)
        return 2
    cmd = a[0]
    rest = a[1:]
    as_json = _flag(rest, "--json")
    do_run = _flag(rest, "--run")
    pos = [x for x in rest if not x.startswith("--")]
    try:
        if cmd == "board":
            return board(as_json=as_json)
        if cmd == "plan":
            n = int(pos[0]) if pos and pos[0].isdigit() else 2
            return plan(n=n, as_json=as_json)
        if cmd == "turn" and pos:
            return turn(pos[0], do_run=do_run)
        if cmd == "gate" and pos:
            return gate(pos[0])
        if cmd == "ship":
            r = list(rest)
            msg = None
            if "--message" in r:
                i = r.index("--message")
                msg = r[i + 1] if i + 1 < len(r) else None
                del r[i:i + 2]  # убрать флаг + значение, чтобы оно не попало в файлы
            p = [x for x in r if not x.startswith("--")]
            if len(p) >= 2:
                return ship(p[0], p[1:], message=msg, do_run=do_run)
            return ship(p[0] if p else "", [], message=msg, do_run=do_run)
        if cmd == "self":
            return self_host(as_json=as_json)
    except Exception as exc:  # noqa: BLE001 — единая точка, понятная ошибка вместо трейсбэка
        print("ОШИБКА: %s: %s" % (type(exc).__name__, exc))
        return 1
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main())
