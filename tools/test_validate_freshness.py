#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Тест driver_freshness_warning (tools/validate.py) — age-WARN драйверов, детерминированно (фикс today)."""
import os
import sys
import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import validate as v


def configure_output():
    for name in ("stdout", "stderr"):
        s = getattr(sys, name, None)
        if s is not None and hasattr(s, "reconfigure"):
            s.reconfigure(encoding="utf-8", errors="replace")


configure_output()


def run():
    ok = True
    today = datetime.date(2026, 6, 23)
    try:
        # старше 30 дн. → WARN
        old = (today - datetime.timedelta(days=40)).isoformat()
        msg = v.driver_freshness_warning(old, today=today)
        assert msg and "пере-сверь" in msg, "40 дн. должно давать WARN: %r" % msg

        # ровно 30 дн. → НЕ WARN (порог строгий >); 31 → WARN
        d30 = (today - datetime.timedelta(days=30)).isoformat()
        d31 = (today - datetime.timedelta(days=31)).isoformat()
        assert v.driver_freshness_warning(d30, today=today) is None, "ровно 30 дн. не должно WARN"
        assert v.driver_freshness_warning(d31, today=today), "31 дн. должно WARN"

        # свежий → None
        recent = (today - datetime.timedelta(days=3)).isoformat()
        assert v.driver_freshness_warning(recent, today=today) is None, "3 дн. не должно WARN"

        # мусор/пусто/битый формат → None (никогда не падает)
        for bad in ("", None, "2026-13-99", "вчера", "2026/06/01", "20260601"):
            assert v.driver_freshness_warning(bad, today=today) is None, "битый ввод не WARN: %r" % bad

        # кастомный max_days
        d10 = (today - datetime.timedelta(days=10)).isoformat()
        assert v.driver_freshness_warning(d10, today=today, max_days=7), "10>7 должно WARN при max_days=7"

        print("TESTS OK validate freshness: >30 дн. → WARN, граница строгая, мусор безопасен, кастомный SLA")
    except AssertionError as e:
        ok = False
        print("TEST FAIL:", e)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(run())
