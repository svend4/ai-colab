#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
# ==========================================
# [FILE ID CARD]
# ID: tools.test_stream
# TYPE: active-script
# DOMAIN: core
# DEPTH_LEVEL: 1
# SUMMARY: Скрипт test_stream.py. Описание сгенерировано автоматически.
# ==========================================
"""
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


def _write_complete_ready_stream(path, stream_id, topic="infra", agent="codex"):
    body = """---
id: {stream_id}
topic: {topic}
agent: {agent}
status: ready-for-synthesis
created: 2026-06-25
variant_policy: independent-first
synthesis_ready: true
status_note: variant completed
---

# Stream: {stream_id}

## 00. Причина независимого варианта

Тестовый stream для проверки готовности.

## 01. Условия применимости

Применимо к независимым stream-пакетам, которые уже готовы к машинной сверке.

## 02. Независимый ответ агента

Полный тестовый вариант заполнен и не оставляет шаблонный текст.

## 03. Потенциал, который нужно раскрыть до синтеза

- новые под-вопросы: проверка полноты
- edge cases: legacy packets
- альтернативные реализации: strict lint позже
- риски и ограничения: не ломать proposed/draft

## 04. Сравнение с известными вариантами

- Похожие пункты: stream lifecycle
- Отличия: readiness lint
- Что этот вариант добавляет сверх уже написанного: incomplete_ready
- Что может оказаться настоящим шумовым дублем после синтеза: нет

## 05. Evidence / проверки

`tools/test_stream.py` проверяет положительный и отрицательный случаи.

## 06. Вопросы другим агентам и людям

- Нужно ли расширять strict mode на ready-for-review?

## 07. Synthesis contract

- consensus candidates: readiness lint нужен
- divergence candidates: степень строгости
- adoption target: tools/stream.py
- reject/supersede condition: общий triad_lint заменит проверку

## 08. Adoption

Тестовый пакет не переносится в mainline.
""".format(stream_id=stream_id, topic=topic, agent=agent)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(body)

def run():
    ok = True
    try:
        # create -> STREAM.md парсится каноническим парсером, status: proposed, independent-first policy
        r1 = st.create("Commit Policy", "claude", "спорный вариант форка")
        path1 = r1["path"]
        assert os.path.isfile(path1), "STREAM.md должен существовать"
        fm = _read_fm(path1)
        assert fm.get("id") == r1["id"], fm
        assert fm.get("topic") == "commit-policy", fm  # topic slug
        assert fm.get("agent") == "claude", fm
        assert fm.get("status") == "proposed", fm
        assert fm.get("created"), fm
        assert fm.get("variant_policy") == "independent-first", fm
        assert fm.get("synthesis_ready") == "false", fm
        assert "adopted_commit" not in fm, fm

        # второй пакет в другой теме + ready-for-synthesis пакет для фильтра.
        # Сначала он шаблонный, поэтому check должен показать incomplete_ready.
        r2 = st.create("infra", "codex", "альтернативный подход")
        m2 = st.mark(r2["id"], "ready-for-synthesis", "variant completed")
        assert m2["status"] == "ready-for-synthesis", m2
        fm_ready = _read_fm(r2["path"])
        assert fm_ready.get("status") == "ready-for-synthesis", fm_ready
        assert fm_ready.get("synthesis_ready") == "true", fm_ready
        assert fm_ready.get("status_note") == "variant completed", fm_ready
        c_incomplete = st.check()
        assert any(x["id"] == r2["id"] for x in c_incomplete["incomplete_ready"]), c_incomplete
        _write_complete_ready_stream(r2["path"], r2["id"])
        c_complete = st.check()
        assert not any(x["id"] == r2["id"] for x in c_complete["incomplete_ready"]), c_complete

        # list без фильтра видит оба
        allrows = st.list_packets()
        ids = {p["id"] for p in allrows}
        assert r1["id"] in ids and r2["id"] in ids, ids

        # list --ready-only фильтрует по статусу (proposed отсеивается, ready-for-synthesis входит)
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

        # mark/adopt несуществующего или с плохим статусом -> ошибка
        try:
            st.mark(r2["id"], "bad-status")
            raise AssertionError("mark с плохим статусом должен падать")
        except ValueError:
            pass
        try:
            st.adopt("нет-такого", "x")
            raise AssertionError("adopt несуществующего должен падать")
        except FileNotFoundError:
            pass

        # check (P-11): сейчас r1=adopted(terminal), r2=ready(свежий) -> чисто
        c = st.check()
        assert not c["stale"] and not c["broken"] and not c["incomplete_ready"], "свежие/terminal/complete-ready не должны быть stale/broken/incomplete: %s" % c
        # состарим открытый пакет -> stale
        r3 = st.create("aging", "claude", "старый набросок")
        st._rewrite_front_matter(r3["path"], {"created": "2000-01-01"})
        c2 = st.check(max_age_days=14)
        assert any(s["id"] == r3["id"] for s in c2["stale"]), "старый proposed -> stale: %s" % c2
        # битый front-matter -> broken
        bdir = os.path.join(st.streams_root(), "broketopic", "brokeid")
        os.makedirs(bdir)
        with open(os.path.join(bdir, "STREAM.md"), "w", encoding="utf-8") as f:
            f.write("нет тут front-matter\n")
        c3 = st.check()
        assert any(b["id"] == "brokeid" for b in c3["broken"]), "битый front-matter -> broken: %s" % c3

        print("TESTS OK stream: create/mark/list/ready-only/adopt + check(stale/broken/incomplete_ready)")
    except AssertionError as e:
        ok = False
        print("TEST FAIL:", e)
    finally:
        shutil.rmtree(_TMP, ignore_errors=True)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(run())
