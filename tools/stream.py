#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Stream-пакеты (Уровень 2, *tooling*-слой к T-136) — жизненный цикл форк-пакетов.

Закрывает инструментальный пробел Уровня 1 из T-136, НЕ принимая governance-решение
(оно остаётся в котле, D-018). stream = форк-пакет варианта в
`streams/<topic>/<id>/STREAM.md` с front-matter (id/topic/agent/status/created,
опц. adopted_commit). Так несколько агентов параллельно развивают подходы, а mainline
остаётся узкой (см. `streams/README.md`, `docs/commit-stream-policy.md`).

CLI:
    python tools/stream.py create <topic> <agent> <reason>
        # создаёт streams/<topic>/<id>/STREAM.md, status: proposed
    python tools/stream.py list [<topic>] [--ready-only]
        # перечисляет пакеты (по статусу; --ready-only — только status: ready)
    python tools/stream.py adopt <stream-id> <commit>
        # status: adopted + adopted_commit; сериализуется под commit-lock

Корень streams переопределяется (для герметичных тестов):
    COLLAB_STREAMS_ROOT=<dir>   или   --root <dir>
"""
import os
import sys
import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from _canon import parse_front_matter  # единый парсер front-matter (T-085)
import commit_lock as cl  # сериализация записи под общий commit-lock (Уровень 0)


def configure_output():
    for name in ("stdout", "stderr"):
        s = getattr(sys, name, None)
        if s is not None and hasattr(s, "reconfigure"):
            s.reconfigure(encoding="utf-8", errors="replace")


configure_output()

READY_STATUSES = ("ready", "adopted")


def streams_root(override=None):
    return os.path.abspath(
        override or os.environ.get("COLLAB_STREAMS_ROOT") or os.path.join(ROOT, "streams")
    )


def _slug(text):
    keep = []
    for ch in (text or "").strip().lower():
        if ch.isalnum() or ch in "-_":
            keep.append(ch)
        elif ch in " /\\.":
            keep.append("-")
    s = "".join(keep).strip("-")
    while "--" in s:
        s = s.replace("--", "-")
    return s or "stream"


def _now_id(agent):
    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M")
    return "%s-%s" % (stamp, _slug(agent))


def packet_text(ident, topic, agent, reason, created, status="proposed"):
    return (
        "---\n"
        "id: %s\n"
        "topic: %s\n"
        "agent: %s\n"
        "status: %s\n"
        "created: %s\n"
        "---\n\n"
        "# Stream: %s\n\n"
        "## Причина форка\n\n"
        "%s\n\n"
        "## Вариант\n\n"
        "(заполните: подход, patch/notes/evidence рядом в этой папке)\n\n"
        "## Adoption\n\n"
        "Перенос в mainline — только после review и явного `adopt` "
        "(governance-решение остаётся в котле, D-018).\n"
        % (ident, topic, agent, status, created, ident, reason or "(не указана)")
    )


def create(topic, agent, reason, root=None):
    root = streams_root(root)
    topic_slug = _slug(topic)
    topic_dir = os.path.join(root, topic_slug)
    os.makedirs(topic_dir, exist_ok=True)

    created = datetime.date.today().isoformat()
    base = _now_id(agent)
    for n in range(1000):
        ident = base if n == 0 else "%s-%d" % (base, n + 1)
        pkt_dir = os.path.join(topic_dir, ident)
        try:
            os.makedirs(pkt_dir)
        except FileExistsError:
            continue
        path = os.path.join(pkt_dir, "STREAM.md")
        # O_EXCL: атомарный claim, чтобы два агента не заняли один файл
        fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
            f.write(packet_text(ident, topic_slug, agent, reason, created))
        return {"id": ident, "topic": topic_slug, "path": path}
    raise RuntimeError("не удалось выдать свободный stream-id за 1000 попыток")


def _iter_packets(root, topic=None):
    root = streams_root(root)
    if not os.path.isdir(root):
        return
    topics = [topic] if topic else sorted(os.listdir(root))
    for t in topics:
        tdir = os.path.join(root, t)
        if not os.path.isdir(tdir):
            continue
        for ident in sorted(os.listdir(tdir)):
            path = os.path.join(tdir, ident, "STREAM.md")
            if not os.path.isfile(path):
                continue
            with open(path, encoding="utf-8") as f:
                fm = parse_front_matter(f.read())
            yield {
                "id": fm.get("id", ident),
                "topic": fm.get("topic", t),
                "agent": fm.get("agent", "?"),
                "status": fm.get("status", "?"),
                "created": fm.get("created", "?"),
                "adopted_commit": fm.get("adopted_commit"),
                "path": path,
            }


def list_packets(topic=None, ready_only=False, root=None):
    out = []
    for p in _iter_packets(root, topic=topic):
        if ready_only and p["status"] not in READY_STATUSES:
            continue
        out.append(p)
    return out


def _find_packet(stream_id, root):
    for p in _iter_packets(root):
        if p["id"] == stream_id:
            return p
    return None


def _rewrite_front_matter(path, updates):
    with open(path, encoding="utf-8") as f:
        text = f.read()
    if not text.startswith("---"):
        raise ValueError("нет front-matter в %s" % path)
    end = text.find("\n---", 3)
    if end == -1:
        raise ValueError("незакрытый front-matter в %s" % path)
    head = text[3:end]
    body = text[end + 4:]  # после "\n---"

    lines = head.strip("\n").splitlines()
    seen = set()
    new_lines = []
    for line in lines:
        if ":" in line:
            k = line.split(":", 1)[0].strip()
            if k in updates:
                new_lines.append("%s: %s" % (k, updates[k]))
                seen.add(k)
                continue
        new_lines.append(line)
    for k, v in updates.items():
        if k not in seen:
            new_lines.append("%s: %s" % (k, v))

    new_text = "---\n" + "\n".join(new_lines) + "\n---" + body
    # Атомарная замена: пишем во временный файл и переименовываем.
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
        f.write(new_text)
    os.replace(tmp, path)


def adopt(stream_id, commit, agent="stream", root=None):
    p = _find_packet(stream_id, root)
    if p is None:
        raise FileNotFoundError("stream не найден: %s" % stream_id)
    # Сериализуем запись под общий commit-lock (Уровень 0): не дерёмся за общий канон.
    locked = cl.acquire(agent, wait=cl_wait()) == 0
    if not locked:
        raise RuntimeError("не удалось взять commit-lock для adopt")
    try:
        _rewrite_front_matter(p["path"], {"status": "adopted", "adopted_commit": commit})
    finally:
        cl.release(agent)
    return {"id": stream_id, "path": p["path"], "adopted_commit": commit}


def cl_wait():
    # короткое ожидание лока: тесты герметичны, лок почти всегда свободен
    return 30


def _argval(argv, flag):
    if flag in argv:
        i = argv.index(flag)
        if i + 1 < len(argv):
            return argv[i + 1]
    return None


def main():
    argv = sys.argv[1:]
    if not argv:
        print(__doc__)
        return 2
    cmd = argv[0]
    root = _argval(argv, "--root")
    ready_only = "--ready-only" in argv
    pos = [a for a in argv[1:] if not a.startswith("--")]
    # --root забирает следующий позиционный токен — уберём его из pos
    if root is not None and root in pos:
        pos.remove(root)

    try:
        if cmd == "create" and len(pos) >= 3:
            topic, agent = pos[0], pos[1]
            reason = " ".join(pos[2:])
            r = create(topic, agent, reason, root=root)
            print("stream создан: %s (topic=%s)" % (r["id"], r["topic"]))
            print("Файл: %s — заполните вариант" % r["path"])
            return 0
        if cmd == "list":
            topic = pos[0] if pos else None
            rows = list_packets(topic=topic, ready_only=ready_only, root=root)
            if not rows:
                print("(нет stream-пакетов)")
                return 0
            for p in rows:
                extra = " adopted_commit=%s" % p["adopted_commit"] if p["adopted_commit"] else ""
                print("%-7s %-20s %-22s %s%s"
                      % (p["status"], p["topic"], p["id"], p["agent"], extra))
            return 0
        if cmd == "adopt" and len(pos) >= 2:
            r = adopt(pos[0], pos[1], root=root)
            print("adopt %s -> adopted (commit=%s)" % (r["id"], r["adopted_commit"]))
            print("Файл: %s" % r["path"])
            return 0
    except Exception as exc:
        print("ОШИБКА: %s: %s" % (type(exc).__name__, exc))
        return 1
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main())
