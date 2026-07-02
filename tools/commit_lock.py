#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
# ==========================================
# [FILE ID CARD]
# ID: tools.commit_lock
# TYPE: active-script
# DOMAIN: core
# DEPTH_LEVEL: 1
# SUMMARY: Скрипт commit_lock.py. Описание сгенерировано автоматически.
# ==========================================
"""
"""
Commit-lock (Уровень 0 политики коммитов, topics/commit-policy-streams-2026-06-21.md).

Атомарный короткоживущий advisory-лок, чтобы агенты НЕ дрались за git `index.lock`: перед
`generate + git add + git commit` агент берёт лок, после — отпускает. Коммиты сериализуются —
нет отскоков и фейлов на параллельном `index.lock`. TTL снимает лок упавшего агента.

Это сериализация, а не изоляция: от коммита ЧУЖОЙ half-done защищает не лок, а правило
**selective-add** (коммить только свои файлы, не `git add -A`). Полная изоляция — worktree
(Уровень 1).

CLI:
    python tools/commit_lock.py acquire <agent> [--ttl 120] [--wait 60]   # 0=взял, 1=не взял
    python tools/commit_lock.py release <agent> [--token <token>]         # токен печатает acquire
    python tools/commit_lock.py status

Пример (sh):
    if python tools/commit_lock.py acquire claude; then
      python tools/generate.py && git add <свои-файлы> && git commit -m "..." ;
      python tools/commit_lock.py release claude ;
    fi
"""
import os
import sys
import time
import uuid

from _ioutil import configure_output
from _cli import help_guard

ROOT = os.environ.get("COLLAB_ROOT") or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOCK = os.path.join(ROOT, "queues", "commit.lock")

configure_output()

# Токены успешных acquire ЭТОГО процесса: agent -> token. release() сверяет по ним
# содержимое лока, чтобы не снять лок, перехваченный после протухания нашего (аудит C10).
_OWNED = {}


def _read(path=None):
    p = path or LOCK
    if not os.path.exists(p):
        return None
    try:
        with open(p, encoding="utf-8") as f:
            d = {}
            for line in f.read().splitlines():
                if ":" in line:
                    k, v = line.split(":", 1)
                    d[k.strip()] = v.strip()
            return d
    except OSError:
        return None


def _fresh(d):
    try:
        return int(d.get("lease_epoch", "0")) > int(time.time())
    except (ValueError, TypeError):
        return False


def _body(agent, ttl, token):
    now = int(time.time())
    return "agent: %s\nepoch: %d\nlease_epoch: %d\ntoken: %s\n" % (agent, now, now + ttl, token)


def _write_excl(agent, ttl):
    token = uuid.uuid4().hex[:12]
    fd = os.open(LOCK, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
        f.write(_body(agent, ttl, token))
    return token


def _safe_name(s):
    """Компонент имени takeover-файла из содержимого лока (без спецсимволов путей)."""
    return "".join(c if (c.isalnum() or c in "-_") else "_" for c in str(s))[:40] or "none"


def _takeover(agent, ttl, stale):
    """Атомарный перехват ПРОТУХШЕГО лока (паттерн pipeline.try_claim, T-082/T-084; аудит C10).

    Слепой `os.remove(LOCK)` здесь ломал сериализацию: между чтением протухшего лока и
    удалением другой агент успевал снять его и взять СВОЙ свежий через O_EXCL — и remove
    сносил уже СВЕЖИЙ лок (двойное владение). O_EXCL закрывает только гонку СОЗДАНИЯ,
    не гонку УДАЛЕНИЯ. Поэтому: эксклюзивный takeover-lock с именем, выведенным из
    содержимого протухшего лока (agent+epoch+token) — оба контендера вычислят одно имя
    и `O_CREAT|O_EXCL` отдаст победу ровно одному; перепроверка содержимого ПОД lock'ом;
    подмена атомарно через временный файл + `os.replace`. (Как и в pipeline: если
    победитель упадёт между взятием takeover-lock и заменой, файл-гейт останется до
    ручной чистки; следующий ДРУГОЙ протухший лок даст другое имя и не заблокируется.)

    Возвращает token нового лока или None (перехват не удался — решит следующий проход)."""
    take = "%s.take.%s.%s.%s" % (LOCK, _safe_name(stale.get("agent")),
                                 _safe_name(stale.get("epoch")), _safe_name(stale.get("token", "")))
    try:
        tfd = os.open(take, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except OSError:  # FileExistsError/PermissionError — этот же протухший лок перехватывает другой
        return None
    try:
        os.close(tfd)
        # перепроверка ПОД lock'ом: на месте всё ещё ТОТ ЖЕ протухший лок, что мы читали?
        cur = _read()
        if (cur is None
                or cur.get("agent") != stale.get("agent")
                or cur.get("epoch") != stale.get("epoch")
                or cur.get("token", "") != stale.get("token", "")
                or _fresh(cur)):
            return None
        token = uuid.uuid4().hex[:12]
        tmp = "%s.tmp.%s" % (LOCK, token)
        with open(tmp, "w", encoding="utf-8", newline="\n") as f:
            f.write(_body(agent, ttl, token))
        # Windows может транзиентно отказать в os.replace — короткий ретрай, как в pipeline
        for _ in range(5):
            try:
                os.replace(tmp, LOCK)  # атомарная подмена протухшего лока нашим
                return token
            except PermissionError:
                time.sleep(0.02)
        try:
            os.remove(tmp)
        except OSError:
            pass
        return None
    finally:
        try:
            os.remove(take)
        except OSError:
            pass


def acquire(agent, ttl=120, wait=60):
    os.makedirs(os.path.dirname(LOCK), exist_ok=True)
    deadline = time.time() + wait
    while True:
        try:
            token = _write_excl(agent, ttl)
            _OWNED[agent] = token
            print("LOCK: взял commit-lock (%s, ttl %ds, token %s)" % (agent, ttl, token))
            return 0
        except FileExistsError:
            d = _read()
            if d and not _fresh(d):
                # протух — атомарный перехват (C10), НЕ слепой os.remove: см. _takeover
                token = _takeover(agent, ttl, d)
                if token is not None:
                    _OWNED[agent] = token
                    print("LOCK: перехватил протухший commit-lock (%s ← %s, ttl %ds, token %s)"
                          % (agent, d.get("agent", "?"), ttl, token))
                    return 0
                # перехват не вышел (другой контендер выиграл/лок сменился) — обычное ожидание
            if time.time() >= deadline:
                print("BUSY: commit-lock занят агентом %s — не дождался (%ds)"
                      % ((d or {}).get("agent", "?"), wait))
                return 1
            time.sleep(0.5)


def release(agent, token=None):
    """Снять свой лок. Сверяет не только имя агента, но и token содержимого (аудит C10):
    после протухания наш лок мог перехватить другой экземпляр — в т.ч. с ТЕМ ЖЕ именем
    агента, — и слепой os.remove сносил бы уже чужой свежий лок. token берётся из аргумента
    (CLI --token, печатает acquire) или из памяти процесса (_OWNED). Само удаление — через
    rename в уникальное имя + перепроверку содержимого, чтобы закрыть TOCTOU-окно между
    чтением и удалением."""
    d = _read()
    if d is None:
        print("OK: commit-lock свободен")
        return 0
    if d.get("agent") != agent:
        print("ОШИБКА: commit-lock держит %s, не ты (%s) — не снимаю" % (d.get("agent"), agent))
        return 1
    expect = token if token is not None else _OWNED.get(agent)
    if expect is not None and d.get("token") and d.get("token") != expect:
        print("ОШИБКА: commit-lock (%s) перехвачен другим экземпляром — токен не совпал, не снимаю" % agent)
        return 1
    # атомарно увести лок в уникальное имя и перепроверить содержимое ПЕРЕД удалением:
    # закрывает окно, где протухший наш лок уже перехвачен другим агентом (C10, TOCTOU)
    probe = "%s.rel.%s" % (LOCK, uuid.uuid4().hex[:12])
    moved = False
    for _ in range(5):
        try:
            os.replace(LOCK, probe)
            moved = True
            break
        except FileNotFoundError:
            _OWNED.pop(agent, None)
            print("OK: commit-lock свободен")
            return 0
        except OSError:
            time.sleep(0.02)  # транзиентный отказ Windows (файл читают) — короткий ретрай
    if not moved:
        print("ОШИБКА: не смог снять commit-lock (%s) — файл занят, попробуй ещё раз" % agent)
        return 1
    cur = _read(probe)
    ours = (cur is not None and cur.get("agent") == agent
            and (expect is None or not cur.get("token") or cur.get("token") == expect))
    if not ours:
        # увели ЧУЖОЙ свежий лок — вернуть на место (окно повторного клоббера микроскопическое)
        try:
            os.replace(probe, LOCK)
        except OSError:
            pass
        print("ОШИБКА: commit-lock перехвачен (%s) — не снимаю" % ((cur or {}).get("agent"),))
        return 1
    try:
        os.remove(probe)
    except OSError:
        pass
    _OWNED.pop(agent, None)
    print("UNLOCK: отпустил commit-lock (%s)" % agent)
    return 0


def status():
    d = _read()
    if d is None:
        print("commit-lock: свободен")
        return 0
    print("commit-lock: %s (%s), осталось %ds"
          % (d.get("agent"), "свежий" if _fresh(d) else "протух",
             max(0, int(d.get("lease_epoch", "0")) - int(time.time()))))
    return 0


def main():
    help_guard(__doc__)
    a = sys.argv[1:]
    if not a:
        print(__doc__)
        return 2
    cmd = a[0]
    ttl = int(a[a.index("--ttl") + 1]) if "--ttl" in a else 120
    wait = int(a[a.index("--wait") + 1]) if "--wait" in a else 60
    token = a[a.index("--token") + 1] if "--token" in a else None
    if cmd == "acquire" and len(a) > 1:
        return acquire(a[1], ttl=ttl, wait=wait)
    if cmd == "release" and len(a) > 1:
        return release(a[1], token=token)
    if cmd == "status":
        return status()
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main())
