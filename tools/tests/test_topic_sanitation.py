#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
# ==========================================
# [FILE ID CARD]
# ID: tools.tests.test_topic_sanitation
# TYPE: active-script
# DOMAIN: core.testing
# DEPTH_LEVEL: 2
# SUMMARY: тест topic_sanitation.py — залежавшиеся proposed/open-темы + D-017-флаг + dry-run.
# ==========================================
"""
"""Тест topic_sanitation.py — advisory-детектор болота идей (диагноз mavis FM-1).

Проверяем на фикстуре topics/ (tmp, вне git → fs-mtime как сигнал движения):
  - в «болото» попадают только proposed/open, старше N дней по свежайшему сигналу;
  - терминальные/свежие/иные-статусы НЕ попадают;
  - свежая front-matter дата спасает файл со старым mtime (max по сигналам);
  - D-017-вариант помечается variant=True и получает «сверить с D-017» (не archive);
  - detector НИЧЕГО не меняет на диске (dry-run);
  - сортировка старшее-первым; --age-days меняет порог.

Двухступенчатый канон (Q-W2-3):
  быстрый:  py -3 -m pytest tools/tests/test_topic_sanitation.py
  полный:   python tools/tests/test_topic_sanitation.py
"""
# --- бутстрап путей (C14): тест живёт в tools/tests/, инструменты — в tools/.
import os as _os
import sys as _sys
_TOOLS_DIR = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
if _TOOLS_DIR not in _sys.path:
    _sys.path.insert(0, _TOOLS_DIR)
# --- конец бутстрапа ---

import os
import sys
import time
import tempfile

import topic_sanitation as ts

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

DAY = 86400
# Фиксированное «сейчас» для детерминизма (2026-07-06, как currentDate проекта).
NOW = int(time.mktime((2026, 7, 6, 12, 0, 0, 0, 0, -1)))


def _w(root, name, body, age_days):
    """Записать topics/<name> с заданным телом и выставить fs-mtime в прошлое.

    В tmp (не git) git_mtimes() вернёт {} → детектор упадёт на fs-mtime, поэтому
    os.utime задаёт «движение файла» детерминированно.
    """
    p = os.path.join(root, "topics", name)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8", newline="\n") as f:
        f.write(body)
    t = NOW - age_days * DAY
    os.utime(p, (t, t))


def _fm(status=None, date=None, last_verified=None, related=None, title="t", variant=None):
    """Собрать front-matter + минимальное тело темы."""
    lines = ["---", "id: X", "type: topic", "title: %s" % title]
    if status is not None:
        lines.append("status: %s" % status)
    if date is not None:
        lines.append("date: %s" % date)
    if last_verified is not None:
        lines.append("last_verified: %s" % last_verified)
    if related is not None:
        lines.append("related: [%s]" % related)
    if variant is not None:
        lines.append("variant: %s" % variant)
    lines += ["---", "", "тело темы", ""]
    return "\n".join(lines)


def _by_file(cands):
    return {c["file"].split("/")[-1]: c for c in cands}


def run():
    fails = []
    with tempfile.TemporaryDirectory() as root:
        ts.ROOT = root

        # старая proposed (mtime 40д, дата тоже старая) → БОЛОТО
        _w(root, "old-proposed.md", _fm(status="proposed", date="2026-05-01"), age_days=40)
        # старая open (mtime 30д) → БОЛОТО
        _w(root, "old-open.md", _fm(status="open", date="2026-05-20"), age_days=30)
        # свежая proposed (mtime 3д) → НЕ болото
        _w(root, "fresh-proposed.md", _fm(status="proposed", date="2026-07-03"), age_days=3)
        # старый mtime (40д), но свежая last_verified (вчера) → НЕ болото (max по сигналам спасает)
        _w(root, "revived.md", _fm(status="proposed", last_verified="2026-07-05"), age_days=40)
        # старая, но терминальная (done) → НЕ болото (заморожена намеренно)
        _w(root, "old-done.md", _fm(status="done", date="2026-05-01"), age_days=40)
        # старая needs-decision (иной статус, не в SWAMP) → НЕ болото
        _w(root, "old-needs.md", _fm(status="needs-decision", date="2026-05-01"), age_days=40)
        # старый D-017-вариант (related содержит D-017) → БОЛОТО + variant?
        _w(root, "variant-topic.md",
           _fm(status="proposed", date="2026-05-01", related="D-017, T-9"), age_days=35)
        # README игнорируется даже старый
        _w(root, "README.md", "# readme\n", age_days=99)
        # файл без front-matter/статуса → игнор (нет болотного статуса)
        _w(root, "no-fm.md", "просто текст без шапки\n", age_days=99)

        data = ts.collect(age_days=14, now=NOW)
        cands = data["candidates"]
        by = _by_file(cands)

        # --- состав болота ---
        expect_swamp = {"old-proposed.md", "old-open.md", "variant-topic.md"}
        got = set(by.keys())
        if got != expect_swamp:
            fails.append("состав болота неверен: ожидалось %s, получено %s" % (expect_swamp, got))

        # свежие/терминальные/иные-статусы/README/без-fm — НЕ в болоте
        for n in ("fresh-proposed.md", "revived.md", "old-done.md", "old-needs.md",
                  "README.md", "no-fm.md"):
            if n in by:
                fails.append("%s ложно попал в болото" % n)

        # scanned учитывает все .md кроме README (8 файлов), swamp_total = proposed/open любого возраста
        if data["scanned"] != 8:
            fails.append("scanned=%d, ожидалось 8 (все кроме README)" % data["scanned"])
        # proposed/open всего: old-proposed, old-open, fresh-proposed, revived, variant-topic = 5
        if data["swamp_total"] != 5:
            fails.append("swamp_total=%d, ожидалось 5 (proposed/open любого возраста)" % data["swamp_total"])

        # --- D-017-вариант помечен и получил «сверить с D-017», не archive ---
        v = by.get("variant-topic.md")
        if v and not v["variant"]:
            fails.append("D-017-вариант не помечен variant=True")
        if v and "D-017" not in v["suggestion"]:
            fails.append("для варианта предложение не про D-017: %s" % v["suggestion"])
        # обычная proposed получает done/archive/задачу
        op = by.get("old-proposed.md")
        if op and op["variant"]:
            fails.append("обычная proposed ложно помечена variant")
        if op and not ("archive" in op["suggestion"] and "done" in op["suggestion"]):
            fails.append("для proposed нет done/archive в предложении: %s" % op["suggestion"])

        # --- сортировка: старшее первым (old-proposed 40д > variant 35д > old-open 30д) ---
        order = [c["file"].split("/")[-1] for c in cands]
        if order and order[0] != "old-proposed.md":
            fails.append("не отсортировано старшее-первым: %s" % order)
        ages = [c["age_days"] for c in cands]
        if ages != sorted(ages, reverse=True):
            fails.append("age_days не убывает: %s" % ages)

        # --- порог --age-days влияет: при 45д ничего не залежалось ---
        strict = ts.collect(age_days=45, now=NOW)
        if strict["candidates"]:
            fails.append("age-days=45 должно дать пусто, дало %d" % len(strict["candidates"]))
        # при 25д добавляется old-open (30д) — уже проходит; проверим что порог реально двигается
        loose = ts.collect(age_days=32, now=NOW)
        loose_names = {c["file"].split("/")[-1] for c in loose["candidates"]}
        if "old-open.md" in loose_names:
            fails.append("age-days=32: old-open (30д) не должен проходить порог 32")
        if "old-proposed.md" not in loose_names:
            fails.append("age-days=32: old-proposed (40д) должен проходить")

        # --- dry-run: файлы на диске не изменены (статусы целы) ---
        with open(os.path.join(root, "topics", "old-proposed.md"), encoding="utf-8") as f:
            if "status: proposed" not in f.read():
                fails.append("detector изменил файл (нарушен dry-run)")

    if fails:
        print("FAIL test_topic_sanitation:")
        for f in fails:
            print("  -", f)
        return 1
    print("OK test_topic_sanitation: болото=proposed/open+stale, D-017-флаг, dry-run, сортировка, порог")
    return 0


def test_topic_sanitation():
    """pytest-обёртка (быстрая ступень)."""
    assert run() == 0


if __name__ == "__main__":
    sys.exit(run())
