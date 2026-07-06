#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Тесты data driver (read-only CSV/TSV)."""
import os
import sys
import json
import shutil

HERE = os.path.dirname(os.path.abspath(__file__))
DRIVERS_ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, DRIVERS_ROOT)
import data_driver as dd
from test_tmp import make_temp_dir


def _payload_bytes(value):
    return len(json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode("utf-8"))


def run():
    d = make_temp_dir("data_test_")
    csvp = os.path.join(d, "t.csv")
    with open(csvp, "w", encoding="utf-8", newline="") as f:
        f.write("name,age,city\nAlice,30,NY\nBob,,LA\n")
    os.makedirs(os.path.join(d, "sub"))
    with open(os.path.join(d, "sub", "u.tsv"), "w", encoding="utf-8", newline="") as f:
        f.write("a\tb\n1\t2\n")
    ok = True
    try:
        tables = dd.list_tables(d)
        assert sorted(tables) == ["sub/u.tsv", "t.csv"], tables

        assert dd.columns(csvp) == ["name", "age", "city"], "columns неверны"

        bomp = os.path.join(d, "bom.csv")
        with open(bomp, "w", encoding="utf-8-sig", newline="") as f:
            f.write("name,age\nDana,41\n")
        assert dd.columns(bomp) == ["name", "age"], "UTF-8 BOM не должен попадать в имя первой колонки"
        hb = dd.head(bomp, n=1)
        assert "name" in hb[0] and "\ufeffname" not in hb[0], hb
        sb = dd.summarize(bomp)
        assert sb["non_empty"]["name"] == 1, sb


        h = dd.head(csvp, n=1)
        assert len(h) == 1 and h[0]["name"] == "Alice" and h[0]["city"] == "NY", h

        s = dd.summarize(csvp)
        assert s["rows"] == 2, s
        assert s["non_empty"]["age"] == 1, "пустая ячейка age не учтена"  # Bob age пуст

        # redaction секретов в значениях ячеек (T-080, ревью T-078 находка F)
        secp = os.path.join(d, "s.csv")
        with open(secp, "w", encoding="utf-8", newline="") as f:
            f.write("user,note\nbob,AKIA1234567890ABCD12\nsue,token=supersecretvalue\n")
        hs = dd.head(secp, n=2)
        joined = json.dumps(hs, ensure_ascii=False)
        assert "AKIA1234567890ABCD12" not in joined, "AWS-ключ не замаскирован в head"
        assert "supersecretvalue" not in joined, "token-значение не замаскировано в head"
        assert "***" in joined, "нет маркера маскировки в head"

        # bounded payloads: list_tables/columns/summarize keep large responses under max_bytes.
        for i in range(20):
            with open(os.path.join(d, "sub", "many_%02d.csv" % i), "w", encoding="utf-8", newline="") as f:
                f.write("x\n%d\n" % i)
        full_tables = dd.list_tables(d, max_bytes=None)
        limited_tables = dd.list_tables(d, max_bytes=80)
        assert len(limited_tables) < len(full_tables), limited_tables
        assert _payload_bytes(limited_tables) <= 80, limited_tables

        wide_cols = ["col_%03d" % i for i in range(40)]
        widep = os.path.join(d, "wide.csv")
        with open(widep, "w", encoding="utf-8", newline="") as f:
            f.write(",".join(wide_cols) + "\n")
            f.write(",".join("v" for _ in wide_cols) + "\n")
        all_cols = dd.columns(widep, max_bytes=None)
        limited_cols = dd.columns(widep, max_bytes=90)
        assert len(limited_cols) < len(all_cols), limited_cols
        assert _payload_bytes(limited_cols) <= 90, limited_cols

        summary_limit = _payload_bytes({
            "path": os.path.abspath(widep),
            "rows": 1,
            "columns": [],
            "non_empty": {},
            "truncated": True,
            "total_columns": len(wide_cols),
        }) + 90
        limited_summary = dd.summarize(widep, max_bytes=summary_limit)
        assert limited_summary.get("truncated") is True, limited_summary
        assert limited_summary.get("total_columns") == len(wide_cols), limited_summary
        assert len(limited_summary["columns"]) < len(all_cols), limited_summary
        assert _payload_bytes(limited_summary) <= summary_limit, limited_summary

        try:
            dd.columns(csvp, base_dir=os.path.join(d, "sub"))
            assert False, "base_dir не ограничивает выход за allowed-root"
        except dd.PathAccessError:
            pass

        print("TESTS OK tables=%d cols=%d rows=%d" % (len(tables), len(dd.columns(csvp)), s["rows"]))
    except AssertionError as e:
        ok = False
        print("TEST FAIL:", e)
    finally:
        shutil.rmtree(d, ignore_errors=True)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(run())
