#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Конвейер задач (pipeline.py, T-027) — «общий котёл».

Агент атомарно берёт следующую готовую задачу, делает, отчитывается, берёт
следующую. Несколько агентов работают параллельно через один конвейер — гонку
за одну задачу снимает атомарный claim (O_CREAT|O_EXCL, как в queue.py).

Объединяет dispatch.py (готовность по DAG) и queue.py (атомарный захват) в одну
операцию pull-next: между «увидел задачу» и «занял» нет окна для перехвата.

    python tools/pipeline.py next   <agent>                 # атомарно занять след. готовую задачу
    python tools/pipeline.py claim  <agent> <T-id>          # атомарно занять конкретную ready-задачу
    python tools/pipeline.py done   <agent> <T-id> [--claim ID] [--report "..."] [--applied "..."]
    python tools/pipeline.py fail   <agent> <T-id> [--claim ID] [--reason "..."]
    python tools/pipeline.py status                          # лента конвейера (одна форма)
    python tools/pipeline.py snapshot                        # записать PIPELINE.md + logs/pipeline.json
    python tools/pipeline.py heartbeat <agent> <T-id> [--progress N] [--note "..."] [--eta "..."]
    python tools/pipeline.py mine   <agent>                  # мои активные задачи

Готовая задача = status:todo + все depends_on done + не занята свежим claim'ом
и не является placeholder-задачей.
Отчёты: per-task done-маркер `queues/done/<id>.done.md` (источник правды, без
конфликтов) + строка в ленте `status`. Источник правды по статусу — tasks/*.md.
"""
import os
import re
import sys
import time
import uuid
import json


def configure_output():
    for name in ("stdout", "stderr"):
        s = getattr(sys, name, None)
        if s is not None and hasattr(s, "reconfigure"):
            s.reconfigure(encoding="utf-8", errors="replace")


configure_output()

ROOT = os.environ.get("COLLAB_ROOT") or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TASKS = os.path.join(ROOT, "tasks")
CLAIMED = os.path.join(ROOT, "queues", "claimed")
DONE = os.path.join(ROOT, "queues", "done")
FAILED = os.path.join(ROOT, "queues", "failed")
LOGS = os.path.join(ROOT, "logs")
HEARTBEAT_DIR = os.path.join(LOGS, "heartbeat")
PIPELINE_MD = os.path.join(ROOT, "PIPELINE.md")
PIPELINE_JSON = os.path.join(LOGS, "pipeline.json")
LIVE_MD = os.path.join(ROOT, "LIVE.md")
HEARTBEAT_JSON = os.path.join(LOGS, "heartbeat.json")
PRANK = {"high": 0, "normal": 1, "low": 2, "": 1}
DEFAULT_TTL_MIN = 30
SERVICE_TOPIC_PREFIXES = ("docs/", "tools/", "decisions/", "drivers/", "core/", "portals/", "collab/", "sandbox/")
SERVICE_TITLE_WORDS = ("pipeline", "instruction", "commit", "merge", "gate", "policy", "driver", "governance", "sandbox", "portal", "index", "evidence")


from _canon import parse_fm  # единый парсер front-matter (T-085, находка L)


def collect_tasks():
    out = {}
    if not os.path.isdir(TASKS):
        return out
    for fn in os.listdir(TASKS):
        if not fn.endswith(".md") or fn == "README.md":
            continue
        path = os.path.join(TASKS, fn)
        with open(path, encoding="utf-8") as f:
            fm = parse_fm(f.read())
        tid = fm.get("id")
        if not tid:
            continue
        out[tid] = {
            "id": tid,
            "title": fm.get("title", ""),
            "status": fm.get("status", "todo"),
            "priority": fm.get("priority", "normal"),
            "owner": fm.get("owner", "—"),
            "topic": fm.get("topic", ""),
            "risk": fm.get("risk", ""),
            "deps": re.findall(r"T-\d+", fm.get("depends_on", "")),
            "path": path,
        }
    return out


def claim_path(tid):
    return os.path.join(CLAIMED, "%s.claim.md" % tid)


def claim_is_fresh(tid):
    p = claim_path(tid)
    if not os.path.exists(p):
        return False
    try:
        with open(p, encoding="utf-8") as f:
            fm = parse_fm(f.read())
        return int(fm.get("lease_epoch", "0")) > int(time.time())
    except Exception:
        return False


def claim_holder(tid):
    p = claim_path(tid)
    if not os.path.exists(p):
        return None
    try:
        with open(p, encoding="utf-8") as f:
            return parse_fm(f.read())
    except OSError:
        # Windows may briefly deny access while another worker is replacing the
        # claim. Treat this as a transient no-holder view; callers retry or fail
        # safe instead of crashing.
        return None


def try_claim(tid, agent, ttl_min=DEFAULT_TTL_MIN):
    """Атомарно занять задачу. Возвращает claim_id или None (занято свежим claim'ом).

    Перехват протухшего claim тоже атомарен (T-082, ревью T-078 находка I): гейтится
    эксклюзивным lock-файлом, имя которого выведено из claim_id ПРОТУХШЕГО claim. Два
    агента, увидевшие один и тот же протухший claim, вычислят одинаковое имя lock'а, и
    `O_CREAT|O_EXCL` отдаст победу ровно одному; победитель подменяет claim атомарно через
    временный файл + `os.replace`. (Замечание: при падении победителя между взятием lock и
    заменой lock может остаться — разрешается через reconcile_state/ручную чистку.)
    """
    os.makedirs(CLAIMED, exist_ok=True)
    p = claim_path(tid)
    cid = uuid.uuid4().hex[:12]
    lease = int(time.time()) + ttl_min * 60
    body = ("---\ntask: %s\nagent: %s\nclaim_id: %s\nlease_epoch: %d\n---\n"
            % (tid, agent, cid, lease))
    try:
        fd = os.open(p, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except PermissionError:
        return None
    except FileExistsError:
        old = claim_holder(tid)
        if old is None:
            return None  # claim исчез между проверками — возьмёт следующий проход
        if int(old.get("lease_epoch", "0")) > int(time.time()):
            return None  # занято живым агентом
        # протух — атомарный перехват под эксклюзивным lock'ом по старому claim_id
        lock = "%s.take.%s" % (p, old.get("claim_id") or "none")
        try:
            lfd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError:
            return None  # другой агент уже перехватывает этот же протухший claim
        except PermissionError:
            return None
        try:
            os.close(lfd)
            # повторная проверка ПОД lock'ом: claim всё ещё тот же протухший?
            # закрывает гонку (T-084-перепроверка), когда другой агент успел
            # перехватить и СНЯТЬ lock между чтением `old` и взятием lock'а здесь —
            # иначе поздний агент перезапишет уже свежий claim (двойной захват).
            cur = claim_holder(tid)
            if (cur is None
                    or cur.get("claim_id") != old.get("claim_id")
                    or int(cur.get("lease_epoch", "0")) > int(time.time())):
                return None
            tmp = "%s.tmp.%s" % (p, cid)
            with open(tmp, "w", encoding="utf-8", newline="\n") as f:
                f.write(body)
            # Windows can transiently deny os.replace while another thread/process is
            # touching the same claim path. Keep the stale-takeover lock and retry a
            # few times; if it still fails, return no-claim instead of leaking a
            # background thread exception through tests/agents.
            for _ in range(5):
                try:
                    os.replace(tmp, p)  # атомарная подмена протухшего claim новым
                    return cid
                except PermissionError:
                    time.sleep(0.02)
            try:
                os.remove(tmp)
            except OSError:
                pass
            return None
        finally:
            try:
                os.remove(lock)
            except OSError:
                pass
    with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
        f.write(body)
    return cid


def set_status(path, new):
    with open(path, encoding="utf-8") as f:
        text = f.read()
    if not text.startswith("---"):
        return False
    end = text.find("\n---", 3)
    if end == -1:
        return False
    head, rest = text[:end], text[end:]
    head2 = re.sub(r"(?m)^status:.*$", "status: " + new, head, count=1)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(head2 + rest)
    return True


def is_placeholder_task(t):
    title = (t.get("title") or "").strip()
    return title == "(зарезервировано — заполните)"


def ready_sorted(tasks):
    done_ids = {t["id"] for t in tasks.values() if t["status"] == "done"}
    ready = []
    for t in tasks.values():
        if t["status"] != "todo":
            continue
        if is_placeholder_task(t):
            continue
        if any(d not in done_ids for d in t["deps"]):
            continue
        if claim_is_fresh(t["id"]):
            continue
        ready.append(t)
    ready.sort(key=lambda t: (PRANK.get(t["priority"], 1), t["id"]))
    return ready


def _claim_success(agent, task, cid):
    set_status(task["path"], "doing")
    print("ЗАНЯЛ: %s — %s" % (task["id"], task["title"]))
    print("agent=%s claim_id=%s file=tasks/%s.md" % (agent, cid, task["id"]))
    print("Сделай задачу, затем: python tools/pipeline.py done %s %s --claim %s --report \"...\" --applied \"AGENTS.md, PROTOCOL.md, Checks\""
          % (agent, task["id"], cid))


def cmd_next(agent):
    tasks = collect_tasks()
    for t in ready_sorted(tasks):
        cid = try_claim(t["id"], agent)
        if cid:
            _claim_success(agent, t, cid)
            return 0
    print("КОТЁЛ ПУСТ: готовых задач нет (всё done / занято / заблокировано зависимостями).")
    return 0


def targeted_claim_error(tid, tasks):
    if tid not in tasks:
        return "задачи %s нет" % tid
    t = tasks[tid]
    done_ids = {x["id"] for x in tasks.values() if x["status"] == "done"}
    if t["status"] != "todo":
        return "status: %s" % t["status"]
    if is_placeholder_task(t):
        return "placeholder task"
    missing = [d for d in t["deps"] if d not in done_ids]
    if missing:
        return "depends_on: " + ", ".join(missing)
    if claim_is_fresh(tid):
        h = claim_holder(tid) or {}
        return "занято агентом %s" % h.get("agent", "?")
    return None


def cmd_claim(agent, tid):
    """Атомарно занять конкретную ready-задачу без риска взять другую через next."""
    tasks = collect_tasks()
    err = targeted_claim_error(tid, tasks)
    if err:
        print("НЕ ГОТОВО: %s ← %s" % (tid, err))
        return 1
    cid = try_claim(tid, agent)
    if not cid:
        print("ЗАНЯТО: %s — claim уже перехвачен другим агентом" % tid)
        return 1
    _claim_success(agent, tasks[tid], cid)
    return 0


def _release(tid):
    p = claim_path(tid)
    if os.path.exists(p):
        os.remove(p)


def _marker(dirpath, tid, suffix, agent, text, extra=None):
    os.makedirs(dirpath, exist_ok=True)
    p = os.path.join(dirpath, "%s.%s.md" % (tid, suffix))
    extra = extra or {}
    header = [
        "---",
        "task: %s" % tid,
        "agent: %s" % agent,
        "epoch: %d" % int(time.time()),
    ]
    for key in sorted(extra):
        value = str(extra[key] or "").replace("\n", " ").strip()
        if value:
            header.append("%s: %s" % (key, value))
    header.append("---")
    with open(p, "w", encoding="utf-8", newline="\n") as f:
        f.write("%s\n\n%s\n" % ("\n".join(header), text))


def _check_holder(tid, agent, claim_id):
    """Совещательная проверка держателя claim перед завершением задачи.

    Возвращает None если ок, иначе строку с ошибкой. Имя агента проверяется всегда
    (как раньше); claim_id (fencing-token) — только если он передан: тогда обязан
    совпасть с текущим держателем, иначе агент с перехваченным/протухшим claim не
    сможет завершить чужую/устаревшую работу (T-082, ревью T-078 находка H).
    """
    h = claim_holder(tid)
    if h and h.get("agent") not in (agent, None):
        return "задача %s занята агентом %s, не тобой (%s)" % (tid, h.get("agent"), agent)
    if claim_id is not None and (not h or h.get("claim_id") != claim_id):
        return ("claim_id не совпадает (перехвачен/протух): задача %s, держатель %s, передан %s"
                % (tid, (h or {}).get("claim_id"), claim_id))
    return None


def _needs_applied_evidence(task):
    topic = (task.get("topic") or "").replace("\\", "/")
    title = (task.get("title") or "").lower()
    if any(topic.startswith(prefix) for prefix in SERVICE_TOPIC_PREFIXES):
        return True
    return any(word in title for word in SERVICE_TITLE_WORDS)


def cmd_done(agent, tid, report, claim_id=None, applied=None):
    tasks = collect_tasks()
    if tid not in tasks:
        print("ОШИБКА: задачи %s нет" % tid)
        return 1
    err = _check_holder(tid, agent, claim_id)
    if err:
        print("ОШИБКА: " + err)
        return 1
    if not applied and _needs_applied_evidence(tasks[tid]):
        print("WARN: %s закрывается без --applied; для служебных задач добавляй evidence применённых инструкций" % tid)
    set_status(tasks[tid]["path"], "done")
    marker_text = report or "done"
    if applied:
        marker_text = "%s\n\nApplied instructions: %s" % (marker_text, applied)
    _marker(DONE, tid, "done", agent, marker_text, {"applied": applied})
    _release(tid)
    print("ГОТОВО: %s → done (%s). Бери следующую: python tools/pipeline.py next %s" % (tid, agent, agent))
    return 0


def cmd_fail(agent, tid, reason, claim_id=None):
    tasks = collect_tasks()
    if tid not in tasks:
        print("ОШИБКА: задачи %s нет" % tid)
        return 1
    err = _check_holder(tid, agent, claim_id)
    if err:
        print("ОШИБКА: " + err)
        return 1
    set_status(tasks[tid]["path"], "blocked")
    _marker(FAILED, tid, "failed", agent, reason or "failed")
    _release(tid)
    print("НЕ ВЫШЛО: %s → blocked (%s): %s" % (tid, agent, reason or ""))
    return 0


def cmd_mine(agent):
    n = 0
    if os.path.isdir(CLAIMED):
        for fn in sorted(os.listdir(CLAIMED)):
            if not fn.endswith(".claim.md"):
                continue
            fm = claim_holder(fn[:-len(".claim.md")]) or {}
            if fm.get("agent") == agent:
                fresh = "свежий" if int(fm.get("lease_epoch", "0")) > int(time.time()) else "протух"
                print("%s — claim_id=%s (%s)" % (fm.get("task"), fm.get("claim_id"), fresh))
                n += 1
    if not n:
        print("У %s нет активных задач." % agent)
    return 0


def build_pipeline_state():
    tasks = collect_tasks()
    done_ids = {t["id"] for t in tasks.values() if t["status"] == "done"}
    doing, ready, blocked = [], [], []
    for t in sorted(tasks.values(), key=lambda x: x["id"]):
        if t["status"] == "doing":
            h = claim_holder(t["id"]) or {}
            if not h:
                blocked.append({
                    "id": t["id"],
                    "title": t["title"],
                    "reason": "doing without active claim",
                })
            elif not claim_is_fresh(t["id"]):
                blocked.append({
                    "id": t["id"],
                    "title": t["title"],
                    "reason": "doing with stale claim",
                })
            else:
                doing.append({
                    "id": t["id"],
                    "title": t["title"],
                    "agent": h.get("agent", "?"),
                    "claim_id": h.get("claim_id", ""),
                    "lease_epoch": h.get("lease_epoch", ""),
                })
        elif t["status"] == "blocked":
            blocked.append({
                "id": t["id"],
                "title": t["title"],
                "reason": "status: blocked",
            })
        elif t["status"] == "todo":
            missing = [d for d in t["deps"] if d not in done_ids]
            if is_placeholder_task(t):
                blocked.append({
                    "id": t["id"],
                    "title": t["title"],
                    "reason": "placeholder task",
                })
            elif missing or claim_is_fresh(t["id"]):
                blocked.append({
                    "id": t["id"],
                    "title": t["title"],
                    "reason": ", ".join(missing) or "занято",
                })
            else:
                ready.append({
                    "id": t["id"],
                    "title": t["title"],
                    "priority": t["priority"],
                    "owner": t["owner"],
                })
    return {
        "epoch": int(time.time()),
        "doing": doing,
        "ready": ready,
        "blocked": blocked,
    }


def render_status_text(state):
    lines = ["=== КОНВЕЙЕР ==="]
    lines.append("\nВ РАБОТЕ (%d):" % len(state["doing"]))
    for item in state["doing"]:
        lines.append("  %s [%s] %s" % (item["id"], item["agent"], item["title"]))
    lines.append("\nГОТОВЫ К ВЗЯТИЮ (%d):" % len(state["ready"]))
    for item in state["ready"]:
        lines.append("  %s (%s) %s" % (item["id"], item["priority"], item["title"]))
    lines.append("\nНЕ ГОТОВЫ / ЗАБЛОКИРОВАНЫ (%d):" % len(state["blocked"]))
    for item in state["blocked"]:
        lines.append("  %s ← %s" % (item["id"], item["reason"]))
    return "\n".join(lines)


def render_pipeline_md(state):
    lines = [
        "# PIPELINE",
        "",
        "Автоматический снимок конвейера. Генерируется командой `python tools/pipeline.py snapshot`.",
        "",
        "## В работе",
        "",
        "| Задача | Агент | Claim | Lease epoch | Название |",
        "|---|---|---|---|---|",
    ]
    if state["doing"]:
        for item in state["doing"]:
            lines.append("| %s | %s | %s | %s | %s |" % (
                item["id"], item["agent"], item["claim_id"], item["lease_epoch"], item["title"]))
    else:
        lines.append("| — | — | — | — | — |")
    lines += [
        "",
        "## Готовы к взятию",
        "",
        "| Задача | Приоритет | Owner | Название |",
        "|---|---|---|---|",
    ]
    if state["ready"]:
        for item in state["ready"]:
            lines.append("| %s | %s | %s | %s |" % (
                item["id"], item["priority"], item["owner"], item["title"]))
    else:
        lines.append("| — | — | — | — |")
    lines += [
        "",
        "## Заблокированы",
        "",
        "| Задача | Причина | Название |",
        "|---|---|---|",
    ]
    if state["blocked"]:
        for item in state["blocked"]:
            lines.append("| %s | %s | %s |" % (item["id"], item["reason"], item["title"]))
    else:
        lines.append("| — | — | — |")
    lines.append("")
    return "\n".join(lines)


def cmd_status():
    print(render_status_text(build_pipeline_state()))
    return 0


def cmd_snapshot():
    state = build_pipeline_state()
    os.makedirs(LOGS, exist_ok=True)
    with open(PIPELINE_JSON, "w", encoding="utf-8", newline="\n") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)
        f.write("\n")
    with open(PIPELINE_MD, "w", encoding="utf-8", newline="\n") as f:
        f.write(render_pipeline_md(state))
    write_heartbeat_views()
    print("SNAPSHOT: PIPELINE.md + logs/pipeline.json обновлены")
    return 0


def safe_agent_name(agent):
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", agent.strip()) or "unknown"


def collect_heartbeats():
    items = []
    if not os.path.isdir(HEARTBEAT_DIR):
        return items
    now = int(time.time())
    for fn in sorted(os.listdir(HEARTBEAT_DIR)):
        if not fn.endswith(".json"):
            continue
        path = os.path.join(HEARTBEAT_DIR, fn)
        try:
            with open(path, encoding="utf-8") as f:
                item = json.load(f)
        except Exception:
            continue
        item["age_seconds"] = max(0, now - int(item.get("epoch", 0)))
        item["fresh"] = item["age_seconds"] <= 15 * 60
        items.append(item)
    items.sort(key=lambda x: x.get("agent", ""))
    return items


def render_live_md(items):
    lines = [
        "# LIVE",
        "",
        "Добровольный heartbeat агентов. Обновляется командой `python tools/pipeline.py heartbeat ...` или `snapshot`.",
        "",
        "| Агент | Задача | Прогресс | ETA | Возраст | Статус | Заметка |",
        "|---|---|---|---|---|---|---|",
    ]
    if not items:
        lines.append("| — | — | — | — | — | — | — |")
    for item in items:
        status = "fresh" if item.get("fresh") else "stale"
        lines.append("| %s | %s | %s%% | %s | %ss | %s | %s |" % (
            item.get("agent", "—"),
            item.get("task", "—"),
            item.get("progress", 0),
            item.get("eta", ""),
            item.get("age_seconds", ""),
            status,
            str(item.get("note", "")).replace("|", "/"),
        ))
    lines.append("")
    return "\n".join(lines)


def write_heartbeat_views():
    items = collect_heartbeats()
    os.makedirs(LOGS, exist_ok=True)
    with open(HEARTBEAT_JSON, "w", encoding="utf-8", newline="\n") as f:
        json.dump({"epoch": int(time.time()), "agents": items}, f, ensure_ascii=False, indent=2)
        f.write("\n")
    with open(LIVE_MD, "w", encoding="utf-8", newline="\n") as f:
        f.write(render_live_md(items))


def cmd_heartbeat(agent, tid, progress, note, eta):
    os.makedirs(HEARTBEAT_DIR, exist_ok=True)
    try:
        progress_i = max(0, min(100, int(progress or 0)))
    except ValueError:
        progress_i = 0
    item = {
        "agent": agent,
        "task": tid,
        "progress": progress_i,
        "note": note or "",
        "eta": eta or "",
        "epoch": int(time.time()),
    }
    path = os.path.join(HEARTBEAT_DIR, "%s.json" % safe_agent_name(agent))
    tmp = path + ".tmp.%s" % uuid.uuid4().hex[:8]
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
        json.dump(item, f, ensure_ascii=False, indent=2)
        f.write("\n")
    os.replace(tmp, path)
    write_heartbeat_views()
    print("HEARTBEAT: %s %s %s%%" % (agent, tid, progress_i))
    return 0


def main():
    a = sys.argv[1:]
    flags = {}
    pos = []
    i = 0
    while i < len(a):
        if a[i] == "--report" and i + 1 < len(a):
            flags["report"] = a[i + 1]; i += 2
        elif a[i] == "--reason" and i + 1 < len(a):
            flags["reason"] = a[i + 1]; i += 2
        elif a[i] == "--progress" and i + 1 < len(a):
            flags["progress"] = a[i + 1]; i += 2
        elif a[i] == "--note" and i + 1 < len(a):
            flags["note"] = a[i + 1]; i += 2
        elif a[i] == "--eta" and i + 1 < len(a):
            flags["eta"] = a[i + 1]; i += 2
        elif a[i] == "--claim" and i + 1 < len(a):
            flags["claim"] = a[i + 1]; i += 2
        elif a[i] == "--applied" and i + 1 < len(a):
            flags["applied"] = a[i + 1]; i += 2
        else:
            pos.append(a[i]); i += 1
    if not pos:
        print(__doc__)
        return 2
    cmd = pos[0]
    if cmd == "next" and len(pos) >= 2:
        return cmd_next(pos[1])
    if cmd == "claim" and len(pos) >= 3:
        return cmd_claim(pos[1], pos[2])
    if cmd == "done" and len(pos) >= 3:
        return cmd_done(pos[1], pos[2], flags.get("report"), flags.get("claim"), flags.get("applied"))
    if cmd == "fail" and len(pos) >= 3:
        return cmd_fail(pos[1], pos[2], flags.get("reason"), flags.get("claim"))
    if cmd == "mine" and len(pos) >= 2:
        return cmd_mine(pos[1])
    if cmd == "status":
        return cmd_status()
    if cmd == "snapshot":
        return cmd_snapshot()
    if cmd == "heartbeat" and len(pos) >= 3:
        return cmd_heartbeat(pos[1], pos[2], flags.get("progress"), flags.get("note"), flags.get("eta"))
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main())
