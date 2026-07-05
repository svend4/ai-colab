#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
# ==========================================
# [FILE ID CARD]
# ID: tools.cohort
# TYPE: active-script
# DOMAIN: core
# DEPTH_LEVEL: 1
# SUMMARY: Скрипт cohort.py. Описание сгенерировано автоматически.
# ==========================================
"""
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
    python tools/cohort.py guard                 # ТРИГГЕРЫ Уровня-1 (Q-015 B): стоит ли уйти в --worktree
    python tools/cohort.py ship  <agent> <file...> [--run] [--strict]  # коммит под commit_lock + selective-add (Ур.0); --strict отказывает при foreign/same-file
    python tools/cohort.py self                  # САМОХОСТИНГ: движок проверяет/чинит сам себя, что улучшить дальше

Добавь `--json` к board/plan/self для машинно-читаемого вывода.
Добавь `--strict` к guard/ship/turn (opt-in, дефолт off — зеркало friction/pipeline --strict): обязательные
триггеры Уровня-1 (foreign-source, same-file; Q-013/D-022 §1,§4) делают exit!=0 и заставляют ship ОТКАЗАТЬ
в коммите в общее дерево. Прочие триггеры остаются recommended (печать, не блок).
"""
import os
import re
import sys
import json
import glob
import subprocess

from _ioutil import configure_output
from _cli import help_guard

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOLS = os.path.join(ROOT, "tools")
CAPS = os.path.join(ROOT, "system-capabilities.json")
sys.path.insert(0, TOOLS)
import ownership as own  # общий классификатор владения dirty-файлами (T-153, синтез подсистем)
from _canon import AGENTS_ROSTER  # единый ростер агентов (C36-a, волна 2)

# Триггеры Уровня-1 (D-022 / Q-015 B). Source-зоны: правка здесь связывает агентов через индекс/дерево.
SOURCE_DIRS = ("tasks/", "decisions/", "questions/", "tools/", "drivers/", "topics/", "docs/")
# Hot-files: генерируемые индексы и активно правимые соседом инструменты — править соло опасно.
HOT_FILES = {"TASKS.md", "QUESTIONS.md", "DECISIONS.md", "board.md", "STATUS.md", "index.json",
             "tools/top.py", "tools/portal.py", "tools/capabilities.py", "tools/generate.py"}

# MANDATORY триггеры (Q-013:124 / D-022 §1 A,E §4 Вариант-1): только same-file коллизия и чужой
# STALE-источник (foreign) — единственные ДОКАЗАННЫЕ потери. Остальные триггеры (hot-tool,
# stale-index, gate-poison) — recommended (печать, не блок). В --strict только эти двое возвращают
# nonzero и заставляют ship отказать в коммите в общее дерево.
MANDATORY_TRIGGERS = ("foreign-source", "same-file")


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
    # Ростер — из _canon.AGENTS_ROSTER (C36-a): без локального хардкода имён.
    agents = list(AGENTS_ROSTER)[:max(1, n)]
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

def turn(agent, do_run=False, strict=False):
    """Безопасная параллельная смена одного агента: контекст -> взять -> работать -> гейт -> ship.

    Авто-эскалация (D-022 п.1): перед сменой проверяем триггеры Уровня-1 (guard) — если активны,
    лучше уйти в свой worktree, а не коммитить в общее дерево."""
    print("=== СМЕНА АГЕНТА: %s ===" % agent)
    print("\nТриггеры Уровня-1 (guard) перед стартом:")
    grc = guard(agent=agent, strict=strict)
    if strict and grc != 0:
        print("\n--strict: обязательный триггер Уровня-1 активен — смена остановлена. "
              "Уйди в worktree (flow.py start --worktree --run), затем повтори turn.")
        return grc
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

def ship(agent, files, message=None, do_run=False, strict=False):
    """Полный безопасный цикл коммита в общем дереве (политика Уровень 0):
    commit_lock (сериализация) → selective-add (только свои файлы) → regenerate (чтобы pre-commit hook
    не падал на устарелости от чужих незакоммиченных правок) → commit → release. Индексы regenerate
    оставляем не-staged — их закоммитит владелец изменивших источников."""
    if not files:
        print("ship: укажи файлы (selective-add; никогда git add -A в общем дереве)")
        return 2
    if strict:  # opt-in blocking (mirrors friction/pipeline --strict): обязательный триггер -> ОТКАЗ
        norm = [f.replace("\\", "/") for f in files]
        foreign = set(own.summary(norm, agent=agent)["by"]["foreign"])
        same_file = {p for p in norm if p in _foreign_branch_files(self_agent=agent)}
        hit = sorted(foreign | same_file)
        if hit:
            kinds = (["foreign-source"] if foreign else []) + (["same-file"] if same_file else [])
            print("ОТКАЗ (--strict): %s — обязательный триггер Уровня-1 (%s). "
                  "Коммит в общее дерево запрещён: уйди в worktree "
                  "(python tools/flow.py start %s <task> --worktree --run) и влей через merge_gate." %
                  (", ".join(hit), ", ".join(kinds), agent))
            return 1
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


# ---------------------------------------------------------------- guard (триггеры Уровня-1)

def _foreign_branch_files(self_agent=None):
    """Пути, затронутые незамёрженными ветками ДРУГИХ агентов (agent/<other>/<task>).

    Read-only: для каждой ветки agent/* (кроме своей) берём файлы её коммитов, ещё не влитых
    в HEAD (git diff --name-only HEAD...branch). Это «другой агент уже трогает этот файл в своём
    притоке» — основа same-file детекта (LS-2, D-022 §4 Вариант-1). Никогда не бросает."""
    rc, out = _git("for-each-ref", "--format=%(refname:short)", "refs/heads/agent")
    files = set()
    for br in (out or "").splitlines():
        br = br.strip()
        if not br.startswith("agent/"):
            continue
        # agent/<name>/<task> — пропустить СВОЮ ветку
        parts = br.split("/")
        if self_agent and len(parts) >= 2 and parts[1] == self_agent:
            continue
        rc2, diff = _git("diff", "--name-only", "HEAD...%s" % br)
        if rc2 == 0:
            for ln in diff.splitlines():
                p = ln.strip().replace("\\", "/")
                if p:
                    files.add(p)
    return files


def guard(as_json=False, agent=None, strict=False):
    """Детектор триггеров Уровня-1 (Q-015 B / D-022): связывает ли текущее состояние агентов так,
    что лучше уйти в свой worktree (--worktree), а не коммитить в общее дерево. Снимает LS-5
    (нет видимости, что правит сосед). Ownership-aware (T-153): триггерит только на ЧУЖИЕ
    заявленные файлы, не на свои/generated/volatile — через общий `tools/ownership.py`."""
    _, st = _git("status", "--short")
    changed = [(ln[:2].strip(), ln[3:].strip().strip('"')) for ln in st.splitlines() if len(ln) > 3]

    def norm(p):
        return p.replace("\\", "/")

    paths = [norm(p) for _code, p in changed]
    # foreign = source-файл, привязанный к задаче ДРУГОГО агента (не свой/generated/volatile/unknown).
    foreign = sorted(own.summary(paths, agent=agent)["by"]["foreign"])
    # same-file = мой dirty-путь, который ДРУГОЙ агент уже трогает в своём притоке (LS-2, D-022 §4).
    fb = _foreign_branch_files(self_agent=agent)
    same_file = sorted({p for p in paths if p in fb})
    # hot-tools: общие ИНСТРУМЕНТЫ (не генерируемые индексы — те регенерируются) — правка соседом = коллизия.
    hot_set = {h for h in HOT_FILES if h.startswith("tools/")}
    hot_tools = sorted({p for p in paths if p in hot_set})
    rc, gen = _run("generate.py", "--check")
    stale = (rc != 0) or ("STALE" in gen) or ("устарел" in gen)
    # gate-poison: общий validate-гейт уже КРАСНЫЙ (часто из-за чужой half-done) → hook блокирует коммит ВСЕМ.
    _, val = _run("validate.py")
    m = re.search(r"ERROR=(\d+)", val)
    poison_errs = [ln.strip()[:90] for ln in val.splitlines() if ln.strip().startswith("ERROR:")][:3]
    poison = bool(m and int(m.group(1)) > 0)

    # recipe — кросс-линк на детектор Codex (friction.py recipe <alias>), синтез #4.
    triggers = []
    if foreign:
        triggers.append({"trigger": "foreign-source", "files": foreign, "recipe": "foreign"})
    if same_file:
        triggers.append({"trigger": "same-file", "files": same_file, "recipe": "foreign"})
    if hot_tools:
        triggers.append({"trigger": "hot-tool", "files": hot_tools, "recipe": "dirty"})
    if stale:
        triggers.append({"trigger": "stale-index", "files": ["generate --check"], "recipe": "stale-index"})
    if poison:
        triggers.append({"trigger": "gate-poison", "files": poison_errs or ["validate ERROR>0"], "recipe": "gate-poison"})
    level1 = bool(triggers)
    # mandatory = подмножество, которое в --strict БЛОКИРУЕТ (foreign-source, same-file).
    mandatory = [t for t in triggers if t["trigger"] in MANDATORY_TRIGGERS]
    blocked = strict and bool(mandatory)

    if as_json:
        print(json.dumps({"level1_recommended": level1, "triggers": triggers,
                          "mandatory": [t["trigger"] for t in mandatory],
                          "strict": strict, "blocked": blocked}, ensure_ascii=False, indent=2))
        return 1 if blocked else 0
    line = "=" * 60
    print(line); print("COHORT GUARD — триггеры Уровня-1 (Q-015 B / D-022)"); print(line)
    if not triggers:
        print("  триггеров нет — Уровень-0 ок (selective-add + commit_lock + ship).")
    for t in triggers:
        more = " …" if len(t["files"]) > 6 else ""
        print("  [!] %-20s %s%s" % (t["trigger"], ", ".join(t["files"][:6]), more))
    if triggers:
        print("\n  Рецепты (детектор Codex): " + " · ".join(
            "friction.py recipe %s" % t.get("recipe", "?") for t in triggers))
    if poison:
        print("\n  GATE-POISON: общий validate-гейт КРАСНЫЙ — коммит в master заблокирован ВСЕМ "
              "(часто чужая half-done). Worktree бери от ЧИСТОЙ базы; merge — когда гейт очистится.")
    print("\nВывод: %s" % (
        "УРОВЕНЬ-1 → `python tools/flow.py start <agent> <task> --worktree --run` (свой индекс/дерево)"
        if level1 else
        "УРОВЕНЬ-0 ок → `python tools/cohort.py ship <agent> <files> --message \"...\" --run`"))
    if blocked:
        print("\n  [STRICT BLOCK] обязательные триггеры: %s — коммит в общее дерево ОТКЛОНЁН. "
              "Уйди в worktree (flow.py start --worktree) и вливай через merge_gate." %
              ", ".join(t["trigger"] for t in mandatory))
    print(line)
    return 1 if blocked else 0


# ---------------------------------------------------------------- CLI

def main():
    help_guard(__doc__)
    a = sys.argv[1:]
    if not a:
        print(__doc__)
        return 2
    cmd = a[0]
    rest = a[1:]
    as_json = _flag(rest, "--json")
    do_run = _flag(rest, "--run")
    strict = _flag(rest, "--strict")
    pos = [x for x in rest if not x.startswith("--")]
    try:
        if cmd == "board":
            return board(as_json=as_json)
        if cmd == "plan":
            n = int(pos[0]) if pos and pos[0].isdigit() else 2
            return plan(n=n, as_json=as_json)
        if cmd == "turn" and pos:
            return turn(pos[0], do_run=do_run, strict=strict)
        if cmd == "gate" and pos:
            return gate(pos[0])
        if cmd == "guard":
            return guard(as_json=as_json, agent=pos[0] if pos else None, strict=strict)
        if cmd == "ship":
            r = list(rest)
            msg = None
            if "--message" in r:
                i = r.index("--message")
                msg = r[i + 1] if i + 1 < len(r) else None
                del r[i:i + 2]  # убрать флаг + значение, чтобы оно не попало в файлы
            p = [x for x in r if not x.startswith("--")]
            if len(p) >= 2:
                return ship(p[0], p[1:], message=msg, do_run=do_run, strict=strict)
            return ship(p[0] if p else "", [], message=msg, do_run=do_run, strict=strict)
        if cmd == "self":
            return self_host(as_json=as_json)
    except Exception as exc:  # noqa: BLE001 — единая точка, понятная ошибка вместо трейсбэка
        print("ОШИБКА: %s: %s" % (type(exc).__name__, exc))
        return 1
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main())
