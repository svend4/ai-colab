# ast: allow-subprocess
# ==========================================
# [FILE ID CARD]
# ID: tools.commit_queue
# TYPE: active-script
# DOMAIN: core
# DEPTH_LEVEL: 1
# SUMMARY: справедливая ОЧЕРЕДЬ коммитов + темпоральное предсохранение + богатая обратная связь.
# ==========================================
"""commit_queue.py — справедливая ОЧЕРЕДЬ коммитов + темпоральное предсохранение + богатая обратная связь.

Проблема (поймана вживую): параллельные `git commit` дерутся за `.git/index.lock` → немой "File exists"
без контекста; работа коммитера может потеряться; нет порядка (thundering-herd retry). `commit_lock.py`
сериализует, но на busy говорит лишь «занят агентом X». Этот слой НАД commit_lock добавляет 4 вещи,
которые делают коллизию информативной и безопасной:

  1. БОГАТАЯ обратная связь — кто держит, как давно взят, сколько осталось по TTL, твоя позиция N из M
     (а не «занято»). Видит и РЕАЛЬНЫЙ `.git/index.lock` (возраст по mtime) — ту самую коллизию вслепую.
  2. ОЧЕРЕДЬ FIFO с позициями — лок берёт ТОЛЬКО голова очереди (справедливость: нет давки и голодания).
  3. ТЕМПОРАЛЬНОЕ ПРЕДСОХРАНЕНИЕ — staged-diff коммитера кладётся в тикет (.patch) с пометкой queued:
     работа durable и восстановима, даже если агент умер / контекст кончился / лок не освободился.
  4. ЕДИНЫЙ СЛОВАРЬ ФЛАГОВ с семантикой — статусы тикета (☐ queued · ⟳ active · ★ done · ✗ failed)
     зеркалят статусы ячеек text_mux; технический коммит и семантическое слияние — один синтез-конвейер
     (см. topics/commit-queue-and-synthesis-2026-06-26).

CLI:
  python tools/commit_queue.py enqueue <agent> [--intent "..."] [--save]  # встать в очередь (+предсохранить staged)
  python tools/commit_queue.py board                                      # доска: .git-lock + держатель + очередь
  python tools/commit_queue.py turn <agent> --ticket <id> [--ttl 120]     # моя ли очередь? голова → берёт лок
  python tools/commit_queue.py done <agent> --ticket <id>                 # отпустить лок + закрыть тикет
  python tools/commit_queue.py fail <agent> --ticket <id> [--reason ...]  # отпустить лок, тикет → failed (для recover)
  python tools/commit_queue.py recover                                    # незавершённые тикеты с предсохранением
"""
import os
from _ioutil import configure_output
from _cli import help_guard
import sys
import time
import json
import glob
import binascii
import re
import subprocess

configure_output()
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import commit_lock as cl  # переиспользуем advisory-лок (голову очереди сериализует он)

ROOT = os.environ.get("COLLAB_ROOT") or os.path.dirname(HERE)
QDIR = os.path.join(ROOT, "queues", "commit-queue")
FLAG = {"queued": "☐", "active": "⟳", "done": "★", "failed": "✗"}
LIVE = ("queued", "active")
TICKET_RE = re.compile(r"^\d+-[0-9a-f]{12}$")


def now_epoch():
    return int(time.time())


def _token():
    return binascii.hexlify(os.urandom(6)).decode()


def _valid_ticket_id(tid):
    return isinstance(tid, str) and bool(TICKET_RE.match(tid))


def _require_ticket_id(tid):
    if not _valid_ticket_id(tid):
        raise ValueError("некорректный ticket id: %r" % tid)
    return tid


def _ticket_path(tid):
    return os.path.join(QDIR, _require_ticket_id(tid) + ".json")


def _patch_path(tid):
    return os.path.join(QDIR, _require_ticket_id(tid) + ".patch")


def _quarantine_corrupt(path, exc):
    """Битый тикет НЕ исчезает молча (аудит C37): WARN в stderr + карантин.

    Перекладываем файл в queues/commit-queue/corrupt/ (перемещение, не удаление —
    след остаётся для разбора), а в stderr печатаем имя тикета и причину: агент,
    вставший в очередь, больше не «пропадает» для остальных без диагностики.
    """
    name = os.path.basename(path)
    cdir = os.path.join(QDIR, "corrupt")
    try:
        os.makedirs(cdir, exist_ok=True)
        os.replace(path, os.path.join(cdir, name))
        note = "перенесён в queues/commit-queue/corrupt/"
    except OSError as move_exc:
        note = "перенести в corrupt/ не удалось: %s" % move_exc
    print("WARN commit_queue: битый тикет %s (%s) — %s" % (name, exc, note), file=sys.stderr)


def _load_all():
    """Все тикеты, отсортированы по (created_epoch, id) = FIFO."""
    out = []
    for p in glob.glob(os.path.join(QDIR, "*.json")):
        try:
            # with-блок обязателен: иначе на Windows незакрытый handle из traceback
            # не даст перенести битый файл в corrupt/ (os.replace → WinError 32)
            with open(p, encoding="utf-8") as fh:
                out.append(json.load(fh))
        except Exception as exc:
            _quarantine_corrupt(p, exc)
            continue
    return sorted(out, key=lambda t: (int(t.get("created_epoch", 0)), t.get("id", "")))


def _live():
    return [t for t in _load_all() if t.get("status") in LIVE]


def enqueue(agent, intent="", staged_diff=None, epoch=None):
    """Встать в очередь: создать тикет (status=queued) + опц. ТЕМПОРАЛЬНО предсохранить staged-diff."""
    os.makedirs(QDIR, exist_ok=True)
    ep = int(epoch if epoch is not None else now_epoch())
    tid = "%d-%s" % (ep, _token())
    t = {"id": tid, "agent": agent, "intent": intent or "", "status": "queued",
         "created_epoch": ep, "has_patch": bool(staged_diff)}
    if staged_diff:
        with open(_patch_path(tid), "w", encoding="utf-8", newline="\n") as fh:
            fh.write(staged_diff)
    # атомарно: O_EXCL по уникальному (epoch+token) имени
    fd = os.open(_ticket_path(tid), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(t, fh, ensure_ascii=False, indent=2)
    return t


def position(tid):
    """Позиция тикета среди живых (1 = голова). 0 — не в очереди."""
    if not _valid_ticket_id(tid):
        return 0
    for i, t in enumerate(_live(), 1):
        if t["id"] == tid:
            return i
    return 0


def _save(t):
    with open(_ticket_path(t["id"]), "w", encoding="utf-8", newline="\n") as fh:
        json.dump(t, fh, ensure_ascii=False, indent=2)


def _get(tid):
    if not _valid_ticket_id(tid):
        return None
    for t in _load_all():
        if t["id"] == tid:
            return t
    return None


def git_index_lock_info():
    """Реальный `.git/index.lock` — та самая немая коллизия. Возраст по mtime."""
    p = os.path.join(ROOT, ".git", "index.lock")
    if not os.path.exists(p):
        return {"exists": False}
    try:
        age = max(0, now_epoch() - int(os.path.getmtime(p)))
    except OSError:
        age = 0
    return {"exists": True, "age_s": age, "path": p}


def commit_lock_info():
    """Держатель advisory commit-lock: кто, как давно взят, сколько осталось по TTL."""
    d = cl._read()
    if not d:
        return None
    try:
        epoch = int(d.get("epoch", 0)); lease = int(d.get("lease_epoch", 0))
    except (ValueError, TypeError):
        epoch = lease = 0
    return {"agent": d.get("agent", "?"), "held_for_s": max(0, now_epoch() - epoch),
            "ttl_remaining_s": max(0, lease - now_epoch()), "fresh": lease > now_epoch()}


def board_text():
    """Богатая доска: .git-lock + держатель advisory-лока + очередь с позициями/возрастом/предсохранением."""
    gl, ci, q = git_index_lock_info(), commit_lock_info(), _live()
    out = ["=== COMMIT QUEUE ==="]
    if gl["exists"]:
        out.append("⚠ .git/index.lock ЗАНЯТ %ds — raw git процесс или зависший: %s" % (gl["age_s"], gl["path"]))
    else:
        out.append("  .git/index.lock: свободен")
    if ci:
        out.append("  commit-lock: держит '%s' — взят %ds назад, осталось %ds по TTL (%s)" % (
            ci["agent"], ci["held_for_s"], ci["ttl_remaining_s"], "свежий" if ci["fresh"] else "ПРОТУХ"))
    else:
        out.append("  commit-lock: свободен")
    out.append("  очередь: %d живых тикет(ов)" % len(q))
    for i, t in enumerate(q, 1):
        out.append("    %d. %s %s '%s' — %ds назад%s%s" % (
            i, FLAG.get(t["status"], "?"), t["id"], t["agent"], now_epoch() - int(t["created_epoch"]),
            (" · %s" % t["intent"]) if t.get("intent") else "",
            " · 💾предсохранено" if t.get("has_patch") else ""))
    return "\n".join(out)


def turn(agent, tid, ttl=120):
    """Моя ли очередь? Лок берёт ТОЛЬКО голова. Возвращает (ready: bool, feedback: str)."""
    if not _valid_ticket_id(tid):
        return False, "некорректный ticket id: %r" % tid
    q = _live()
    if not q or q[0]["id"] != tid:
        pos = position(tid)
        if pos == 0:
            return False, "тикет %s не в очереди (закрыт?)" % tid
        ahead = q[0]
        return False, ("ЖДИ: позиция %d из %d. Впереди '%s' (%s). Работа предсохранена — не потеряна.\n%s" % (
            pos, len(q), ahead["agent"], FLAG.get(ahead["status"], "?"), board_text()))
    head = q[0]
    if head["status"] == "active":
        return True, "уже твоя очередь (⟳ active) — коммить и закрывай (done)"
    rc = cl.acquire(agent, ttl=ttl, wait=0)
    if rc == 0:
        head["status"] = "active"; _save(head)
        return True, "★ ТВОЯ ОЧЕРЕДЬ: commit-lock взят (%s, ttl %ds). Коммить, потом `done`." % (agent, ttl)
    # голова, но advisory-лок держит кто-то некооперативный (raw git / другой)
    return False, "ЖДИ: ты голова, но commit-lock занят:\n%s" % board_text()


def done(agent, tid):
    """Успех: отпустить commit-lock + закрыть тикет (удалить файлы тикета и предсохранение)."""
    if not _valid_ticket_id(tid):
        return "✗ некорректный ticket id: %r" % tid
    cl.release(agent)
    for p in (_ticket_path(tid), _patch_path(tid)):
        try:
            os.remove(p)
        except OSError:
            pass
    return "★ тикет %s закрыт, commit-lock отпущен" % tid


def fail(agent, tid, reason=""):
    """Неуспех: отпустить лок, тикет → failed (предсохранение СОХРАНЯЕТСЯ для recover)."""
    if not _valid_ticket_id(tid):
        return "✗ некорректный ticket id: %r" % tid
    cl.release(agent)
    t = _get(tid)
    if t:
        t["status"] = "failed"; t["reason"] = reason; _save(t)
    return "✗ тикет %s → failed%s (предсохранение сохранено для recover)" % (tid, (": " + reason) if reason else "")


def recover():
    """Незавершённые тикеты с предсохранением (агент умер / лок не освободился) — что можно восстановить."""
    return [t for t in _load_all() if t.get("has_patch") and t.get("status") in ("queued", "active", "failed")]


def _staged_diff():
    try:
        p = subprocess.run(["git", "diff", "--cached"], cwd=ROOT, capture_output=True, text=True,
                           encoding="utf-8", errors="replace", stdin=subprocess.DEVNULL)
        return p.stdout or ""
    except Exception:
        return ""


def _opt(argv, flag, default=None):
    if flag in argv:
        i = argv.index(flag)
        if i + 1 < len(argv):
            return argv[i + 1]
    return default


def main(argv):
    help_guard(__doc__, argv)
    if not argv:
        print(__doc__); return 2
    cmd = argv[0]
    if cmd == "board":
        print(board_text()); return 0
    if cmd == "recover":
        r = recover()
        if not r:
            print("recover: незавершённых тикетов с предсохранением нет"); return 0
        print("recover: %d тикет(ов) с предсохранённой работой:" % len(r))
        for t in r:
            print("  %s %s '%s' %s → %s" % (FLAG.get(t["status"], "?"), t["id"], t["agent"],
                                            t.get("status"), _patch_path(t["id"])))
        return 0
    if cmd == "enqueue" and len(argv) > 1:
        agent = argv[1]
        diff = _staged_diff() if "--save" in argv else None
        t = enqueue(agent, intent=_opt(argv, "--intent", ""), staged_diff=diff)
        print("☐ в очереди: тикет %s (позиция %d)%s" % (
            t["id"], position(t["id"]), " · 💾staged предсохранён" if t["has_patch"] else ""))
        print(board_text())
        return 0
    tid = _opt(argv, "--ticket")
    if cmd == "turn" and len(argv) > 1 and tid:
        ready, msg = turn(argv[1], tid, ttl=int(_opt(argv, "--ttl", "120")))
        print(msg)
        return 0 if ready else 1
    if cmd == "done" and len(argv) > 1 and tid:
        print(done(argv[1], tid)); return 0
    if cmd == "fail" and len(argv) > 1 and tid:
        print(fail(argv[1], tid, reason=_opt(argv, "--reason", ""))); return 0
    print(__doc__); return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
