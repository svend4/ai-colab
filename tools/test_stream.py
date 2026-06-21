#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Тест stream-пакетов (tools/stream.py) — create/list/adopt, герметично."""
import os
import sys
import shutil

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "drivers"))
from test_tmp import make_temp_dir

# Герметичность: и streams-root, и commit-lock уводим во временные каталоги
# ДО импорта модулей (cl.LOCK вычисляется из COLLAB_ROOT на импорте).
_TMP = make_temp_dir("ai_colab_stream_test_")
os.environ["COLLAB_ROOT"] = _TMP  # commit-lock пишет в _TMP/queues/commit.lock
os.environ["COLLAB_STREAMS_ROOT"] = os.path.join(_TMP, "streams")

sys.path.insert(0, HERE)
from _canon import parse_front_matter
import stream as st


def _read_fm(path):
    with open(path, encoding="utf-8") as f:
        return parse_front_matter(f.read())


def run():
    ok = True
    try:
        # create -> STREAM.md парсится каноническим парсером, status: proposed
        r1 = st.create("Commit Policy", "claude", "спорный вариант форка")
        path1 = r1["path"]
        assert os.path.isfile(path1), "STREAM.md должен существовать"
        fm = _read_fm(path1)
        assert fm.get("id") == r1["id"], fm
        assert fm.get("topic") == "commit-policy", fm  # topic slug
        assert fm.get("agent") == "claude", fm
        assert fm.get("status") == "proposed", fm
        assert fm.get("created"), fm
        assert "adopted_commit" not in fm, fm

        # второй пакет в другой теме + ready-пакет для фильтра
        r2 = st.create("infra", "codex", "альтернативный подход")
        st._rewrite_front_matter(r2["path"], {"status": "ready"})

        # list без фильтра видит оба
        allrows = st.list_packets()
        ids = {p["id"] for p in allrows}
        assert r1["id"] in ids and r2["id"] in ids, ids

        # list --ready-only фильтрует по статусу (proposed отсеивается)
        ready = st.list_packets(ready_only=True)
        ready_ids = {p["id"] for p in ready}
        assert r2["id"] in ready_ids, ready_ids
        assert r1["id"] not in ready_ids, "proposed не должен попадать в ready-only"

        # list по теме
        only_infra = st.list_packets(topic="infra")
        assert {p["id"] for p in only_infra} == {r2["id"]}, only_infra

        # adopt: front-matter обновлён атомарно (status + adopted_commit),
        # под commit-lock, остальные ключи сохранены
        res = st.adopt(r1["id"], "deadbeef123")
        assert res["adopted_commit"] == "deadbeef123", res
        fm2 = _read_fm(path1)
        assert fm2.get("status") == "adopted", fm2
        assert fm2.get("adopted_commit") == "deadbeef123", fm2
        assert fm2.get("id") == r1["id"], fm2
        assert fm2.get("agent") == "claude", fm2
        assert fm2.get("created") == fm.get("created"), "created должен сохраниться"
        # тело пакета не потеряно
        with open(path1, encoding="utf-8") as f:
            assert "# Stream:" in f.read(), "тело STREAM.md должно сохраниться"
        # лок отпущен после adopt
        assert st.cl._read() is None, "commit-lock должен быть отпущен"

        # adopt несуществующего -> ошибка
        try:
            st.adopt("нет-такого", "x")
            raise AssertionError("adopt несуществующего должен падать")
        except FileNotFoundError:
            pass

        print("TESTS OK stream: create/list/ready-only/adopt(atomic+locked)")
    except AssertionError as e:
        ok = False
        print("TEST FAIL:", e)
    finally:
        shutil.rmtree(_TMP, ignore_errors=True)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(run())
