#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ==========================================
# [FILE ID CARD]
# ID: tools.pipeline
# TYPE: active-script
# DOMAIN: core.orchestration
# DEPTH_LEVEL: 1
# SUMMARY: Конвейер задач: атомарный claim, done/fail, heartbeat, snapshot и общий котёл агентов.
# ==========================================
"""
Конвейер задач (pipeline.py, T-027) — «общий котёл».

Агент атомарно берёт следующую готовую задачу, делает, отчитывается, берёт
следующую. Несколько агентов работают параллельно через один конвейер — гонку
за одну задачу снимает атомарный claim (O_CREAT|O_EXCL, как в queue.py).

Объединяет dispatch.py (готовность по DAG) и queue.py (атомарный захват) в одну
операцию pull-next: между «увидел задачу» и «занял» нет окна для перехвата.

    python tools/pipeline.py next   <agent>                 # атомарно занять след. готовую задачу
    python tools/pipeline.py claim  <agent> <T-id>          # атомарно занять конкретную ready-задачу
    python tools/pipeline.py done   <agent> <T-id> [--claim ID] [--report "..."] [--applied "..."] [--strict]
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
from _ioutil import configure_output, atomic_write
from _cli import help_guard
import _claims  # общие claim-примитивы queues/claimed (волна 2, C35-a)
import hashlib
import time
import uuid
import json

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
DEFAULT_TTL_MIN = _claims.DEFAULT_TTL_MIN  # единый TTL lease (C35-a)
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
            "kind": fm.get("kind", "code"),
            "deps": re.findall(r"T-\d+", fm.get("depends_on", "")),
            "path": path,
        }
    return out

def claim_path(tid):
    return _claims.claim_file(CLAIMED, tid)

def claim_is_fresh(tid):
    return _claims.claim_is_fresh(claim_path(tid))

def claim_holder(tid):
    # OSError → None внутри _claims.read_claim: Windows может кратковременно
    # запрещать доступ, пока другой воркер подменяет claim через os.replace;
    # вызывающие повторяют попытку или отказывают безопасно, не падая.
    return _claims.read_claim(claim_path(tid))

def try_claim(tid, agent, ttl_min=DEFAULT_TTL_MIN):
    """Атомарно занять задачу. Возвращает claim_id или None (занято свежим claim'ом).

    Механика вынесена в общий модуль `_claims` (волна 2, C35-a) и сохранена
    1-в-1 с фиксами гонок T-082/T-084: создание — `create_claim`
    (O_CREAT|O_EXCL); перехват протухшего claim — `takeover_claim`
    (эксклюзивный lock, имя которого выведено из claim_id ПРОТУХШЕГО claim,
    перепроверка под lock'ом, атомарная подмена через os.replace).
    Формат claim-файла не изменился: task/agent/claim_id/lease_epoch.
    """
    os.makedirs(CLAIMED, exist_ok=True)
    p = claim_path(tid)
    cid = uuid.uuid4().hex[:12]
    lease = int(time.time()) + ttl_min * 60
    body = ("---\ntask: %s\nagent: %s\nclaim_id: %s\nlease_epoch: %d\n---\n"
            % (tid, agent, cid, lease))
    try:
        _claims.create_claim(p, body)
        return cid
    except PermissionError:
        return None
    except FileExistsError:
        old = claim_holder(tid)
        if old is None:
            return None  # claim исчез между проверками — возьмёт следующий проход
        if _claims.is_fresh(old):
            return None  # занято живым агентом
        # протух — атомарный перехват (takeover-lock + перепроверка + os.replace)
        return cid if _claims.takeover_claim(p, body, old) else None

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
    # источник правды по статусу — tasks/*.md: пишем атомарно (аудит C49)
    atomic_write(path, head2 + rest)
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

import random

def cmd_next(agent, kind=None, ratio=None):
    tasks = collect_tasks()
    ready = ready_sorted(tasks)
    
    if ratio:
        try:
            parts = ratio.split(",")
            weights = {}
            for p in parts:
                k, v = p.split(":")
                weights[k.strip()] = int(v.strip())
            total = sum(weights.values())
            r = random.randint(1, total)
            cumulative = 0
            for k, v in weights.items():
                cumulative += v
                if r <= cumulative:
                    kind = k
                    break
        except Exception as exc:
            # опечатка в --ratio больше НЕ игнорируется молча (аудит C37):
            # раньше выбор шёл не по заявленным весам, и никто не узнавал
            print("ОШИБКА: не удалось разобрать --ratio %r (%s). "
                  "Формат: kind:вес[,kind:вес], например code:7,docs:3" % (ratio, exc))
            return 2

    if kind:
        preferred = [t for t in ready if t.get("kind") == kind]
        others = [t for t in ready if t.get("kind") != kind]
        ordered_ready = preferred + others
    else:
        ordered_ready = ready

    for t in ordered_ready:
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
    # fencing проверяется выше по стеку (_check_holder в cmd_done/cmd_fail),
    # поэтому снятие безусловное (C35-a: общий примитив release_claim)
    _claims.release_claim(claim_path(tid))

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

def _evidence_gaps(applied, marker_text):
    """Причины, почему applied-evidence недостаточно (пустой список => evidence ок).

    Переиспользует instructions.check_report_text (один валидатор evidence) и добавляет
    проверку на «формальное» evidence — только boilerplate-троица без task-specific ссылки.
    """
    if not applied or applied.strip().lower() in ("none", "-", ""):
        return ["нет applied-evidence (--applied)"]
    try:
        from instructions import check_report_text  # ленивый импорт: без циклов на загрузке
        missing = check_report_text(marker_text)
    except Exception:  # noqa: BLE001
        missing = []
    if missing:
        return ["слабое evidence (нет: %s)" % ", ".join(missing)]
    parts = [p.strip().lower() for p in re.split(r"[,\n]", applied) if p.strip()]
    meaningful = [p for p in parts if p not in ("agents.md", "protocol.md", "checks", "checks:")]
    if not any(("/" in p or p.endswith(".md") or p.endswith(".py") or re.search(r"\b[dft]-\d", p))
               for p in meaningful):
        return ["формальное evidence (нет task-specific ссылки)"]
    return []

def cmd_done(agent, tid, report, claim_id=None, applied=None, strict=False):
    if not claim_id:
        print("ОШИБКА: для завершения задачи (done) требуется указать --claim ID")
        return 1
    tasks = collect_tasks()
    if tid not in tasks:
        print("ОШИБКА: задачи %s нет" % tid)
        return 1
    err = _check_holder(tid, agent, claim_id)
    if err:
        print("ОШИБКА: " + err)
        return 1
    marker_text = report or "done"
    if applied:
        marker_text = "%s\n\nApplied instructions: %s" % (marker_text, applied)
    if _needs_applied_evidence(tasks[tid]):
        gaps = _evidence_gaps(applied, marker_text)
        if gaps:
            detail = "; ".join(gaps)
            if strict:  # opt-in строгий гейт (warn->block, S3 лестницы Q-016) — дефолт остаётся мягким
                print("ОТКАЗ: %s не закрыт — strict applied-evidence gate: %s. "
                      "Добавь --applied с реальными ссылками (AGENTS.md, PROTOCOL.md, файл/решение, Checks)." % (tid, detail))
                return 1
            print("WARN: %s закрывается без полноценного evidence (%s); для служебных задач добавляй --applied" % (tid, detail))
    set_status(tasks[tid]["path"], "done")
    _marker(DONE, tid, "done", agent, marker_text, {"applied": applied})
    _release(tid)
    print("ГОТОВО: %s → done (%s). Бери следующую: python tools/pipeline.py next %s" % (tid, agent, agent))
    return 0

def cmd_fail(agent, tid, reason, claim_id=None):
    if not claim_id:
        print("ОШИБКА: для отмены задачи (fail) требуется указать --claim ID")
        return 1
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
    # производные файлы пишем атомарно: параллельный читатель никогда не видит
    # усечённый pipeline.json/PIPELINE.md (аудит C49)
    atomic_write(PIPELINE_JSON, json.dumps(state, ensure_ascii=False, indent=2) + "\n")
    atomic_write(PIPELINE_MD, render_pipeline_md(state))
    write_heartbeat_views()
    print("SNAPSHOT: PIPELINE.md + logs/pipeline.json обновлены")
    return 0

def safe_agent_name(agent):
    """Имя агента → безопасное имя heartbeat-файла (аудит C49).

    Кириллица и прочие юникод-буквы сохраняются (\\w с re.UNICODE): «иван» и
    «пётр» больше не схлопываются в один файл `_.json`. Если что-то всё же
    пришлось вычистить — добавляется короткий хэш ИСХОДНОГО имени, так что два
    разных «грязных» имени гарантированно не перетирают друг друга. Для чистых
    ASCII-имён (claude, codex) результат совпадает с прежним — обратная
    совместимость имён файлов сохранена.
    """
    raw = (agent or "").strip()
    if not raw:
        return "unknown"
    cleaned = re.sub(r"[^\w.-]+", "_", raw, flags=re.UNICODE)
    if cleaned != raw:
        # часть символов вычищена — уникальность гарантирует хэш исходного имени
        cleaned = "%s.%s" % (cleaned or "unknown", hashlib.sha1(raw.encode("utf-8")).hexdigest()[:8])
    return cleaned

# heartbeat по закрытой (done) задаче старше этого TTL — призрак: задача давно
# завершена, запись только вводит читателя LIVE.md в заблуждение (аудит C22)
DONE_HEARTBEAT_TTL_S = 15 * 60

def collect_heartbeats():
    items = []
    if not os.path.isdir(HEARTBEAT_DIR):
        return items
    now = int(time.time())
    # статусы задач — для автоочистки призрачных heartbeat по done-задачам (аудит C22)
    statuses = {t["id"]: t["status"] for t in collect_tasks().values()}
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
        # автоочистка: задача закрыта (done), heartbeat старше TTL — удаляем
        # per-agent файл (volatile runtime-артефакт), чтобы LIVE.md не показывал
        # «работу в процессе» по давно закрытым задачам (аудит C22)
        if (statuses.get(item.get("task")) == "done"
                and item["age_seconds"] > DONE_HEARTBEAT_TTL_S):
            try:
                os.remove(path)
            except OSError:
                pass
            continue
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
    # атомарно: параллельный collect_heartbeats/json.load не увидит обрезанный
    # heartbeat.json (аудит C49)
    atomic_write(HEARTBEAT_JSON,
                 json.dumps({"epoch": int(time.time()), "agents": items}, ensure_ascii=False, indent=2) + "\n")
    atomic_write(LIVE_MD, render_live_md(items))

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
    help_guard(__doc__)
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
        elif a[i] == "--kind" and i + 1 < len(a):
            flags["kind"] = a[i + 1]; i += 2
        elif a[i] == "--ratio" and i + 1 < len(a):
            flags["ratio"] = a[i + 1]; i += 2
        elif a[i] == "--strict":
            flags["strict"] = True; i += 1
        else:
            pos.append(a[i]); i += 1
    if not pos:
        print(__doc__)
        return 2
    cmd = pos[0]
    if cmd == "next" and len(pos) >= 2:
        return cmd_next(pos[1], kind=flags.get("kind"), ratio=flags.get("ratio"))
    if cmd == "claim" and len(pos) >= 3:
        return cmd_claim(pos[1], pos[2])
    if cmd == "done" and len(pos) >= 3:
        return cmd_done(pos[1], pos[2], flags.get("report"), flags.get("claim"),
                        flags.get("applied"), strict=flags.get("strict", False))
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
