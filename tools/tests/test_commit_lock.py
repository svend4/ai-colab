#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
# ==========================================
# [FILE ID CARD]
# ID: tools.tests.test_commit_lock
# TYPE: active-script
# DOMAIN: core
# DEPTH_LEVEL: 1
# SUMMARY: Скрипт test_commit_lock.py. Описание сгенерировано автоматически.
# ==========================================
"""
"""Тест commit-lock (tools/commit_lock.py) — сериализация коммитов."""
# --- бутстрап путей (C14, аудит 2026-07-02): тест живёт в tools/tests/, инструменты — в tools/.
# Вставка ДО локальных импортов, чтобы standalone-запуск работал из нового места.
import os as _os
import sys as _sys
_TOOLS_DIR = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
if _TOOLS_DIR not in _sys.path:
    _sys.path.insert(0, _TOOLS_DIR)
# --- конец бутстрапа ---

import os
import sys
import time
import shutil

HERE = _TOOLS_DIR  # tools/ — тест перенесён в tools/tests/ (C14)
REPO_ROOT = os.path.dirname(HERE)


def prepare_root():
    candidates = [
        os.path.join(r"C:\tmp", "ai_colab_commit_lock_test"),
        os.path.join(REPO_ROOT, "tmp-work", "commit_lock_test_runtime"),
    ]
    last_error = None
    for root in candidates:
        try:
            shutil.rmtree(root, ignore_errors=True)
            os.makedirs(os.path.join(root, "queues"), exist_ok=True)
            probe = os.path.join(root, "queues", ".write_probe")
            with open(probe, "w", encoding="utf-8", newline="\n") as f:
                f.write("ok")
            os.remove(probe)
            return root
        except OSError as exc:
            last_error = exc
    raise RuntimeError("no writable commit_lock test root: %r" % (last_error,))


ROOT = prepare_root()
os.environ["COLLAB_ROOT"] = ROOT
sys.path.insert(0, HERE)
import commit_lock as cl


def run():
    ok = True
    try:
        assert cl.acquire("claude", wait=0) == 0, "первый acquire должен взять"
        assert (cl._read() or {}).get("agent") == "claude", cl._read()
        assert cl.acquire("codex", wait=0) == 1, "занятый лок не должен браться"
        assert cl.release("codex") == 1, "чужой release не должен снимать"
        assert cl.release("claude") == 0, "свой release снимает"
        assert cl.acquire("codex", wait=0) == 0, "после release свободно"
        assert cl.release("codex") == 0

        # Протухший лок снимается и берётся.
        with open(cl.LOCK, "w", encoding="utf-8", newline="\n") as f:
            f.write("agent: ghost\nepoch: 1\nlease_epoch: 1\n")
        assert cl.acquire("claude", wait=0) == 0, "протухший лок должен перехватываться"
        assert (cl._read() or {}).get("agent") == "claude", cl._read()
        cl.release("claude")

        # C10-1 (гонка удаления): B перехватил протухший лок — A не должен снести лок B.
        # Раньше acquire делал слепой os.remove(LOCK) по устаревшему чтению и сносил
        # уже СВЕЖИЙ лок B (двойное владение); теперь перехват обязан провалиться.
        with open(cl.LOCK, "w", encoding="utf-8", newline="\n") as f:
            f.write("agent: ghost\nepoch: 1\nlease_epoch: 1\n")
        stale = cl._read()  # A прочитал протухший лок и «завис» перед снятием
        assert cl.acquire("B", wait=0) == 0, "B перехватывает тот же протухший лок"
        b_lock = cl._read()
        assert b_lock and b_lock.get("agent") == "B", b_lock
        assert cl._takeover("A", 120, stale) is None, "перехват A по устаревшему чтению должен провалиться"
        assert cl._read() == b_lock, "свежий лок B должен остаться нетронутым: %r" % (cl._read(),)
        assert cl.acquire("A", wait=0) == 1, "лок B свежий — A не должен взять"
        assert cl.release("A") == 1, "чужой release тоже не снимает лок B"
        assert cl.release("B") == 0

        # C10-2 (TOCTOU в release): сверяется token содержимого, а не только имя агента.
        assert cl.acquire("claude", wait=0) == 0
        now = int(time.time())
        with open(cl.LOCK, "w", encoding="utf-8", newline="\n") as f:
            # перехват ДРУГИМ экземпляром с тем же именем агента: другой token
            f.write("agent: claude\nepoch: %d\nlease_epoch: %d\ntoken: deadbeef0000\n" % (now, now + 120))
        assert cl.release("claude") == 1, "release не должен снимать перехваченный лок (токен не совпал)"
        assert (cl._read() or {}).get("token") == "deadbeef0000", "перехваченный лок должен уцелеть"
        assert cl.release("claude", token="deadbeef0000") == 0, "с верным токеном release снимает"
        assert cl._read() is None, "после release лок снят"

        print("TESTS OK commit_lock: acquire/busy/release/stale-takeover/"
              "delete-race(C10)/release-token(C10)")
    except AssertionError as e:
        ok = False
        print("TEST FAIL:", e)
    finally:
        shutil.rmtree(ROOT, ignore_errors=True)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(run())
