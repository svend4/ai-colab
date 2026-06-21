#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Тесты sqlite driver (read-only) — против временной SQLite-БД."""
import os
import sys
import sqlite3

HERE = os.path.dirname(os.path.abspath(__file__))
DRIVERS = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, DRIVERS)
import sqlite_driver as sd
from test_tmp import temp_dir  # workspace-safe temp под ROOT/tmp-work


def run():
    ok = True
    try:
        with temp_dir("sqlite_test_") as d:
            db = os.path.join(d, "app.db")
            # подготовка БД (на запись — отдельным обычным соединением)
            c = sqlite3.connect(db)
            c.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT, secret TEXT)")
            c.execute("INSERT INTO users(name, secret) VALUES (?,?)", ("alice", "token=SUPERSECRETVAL"))
            c.execute("INSERT INTO users(name, secret) VALUES (?,?)", ("bob", "ok"))
            c.commit()
            c.close()

            tables = sd.list_tables(db, base_dir=d)
            assert tables == ["users"], tables

            schema = sd.table_schema(db, "users", base_dir=d)
            names = [col["name"] for col in schema]
            assert names == ["id", "name", "secret"], names

            head = sd.table_head(db, "users", base_dir=d)
            assert len(head) == 2, head
            import json
            blob = json.dumps(head, ensure_ascii=False)
            assert "SUPERSECRETVAL" not in blob, "секрет не замаскирован: %s" % blob

            q = sd.query(db, "SELECT name FROM users WHERE name='alice'", base_dir=d)
            assert len(q) == 1 and q[0]["name"] == "alice", q

            # read-only: запись через query запрещена guard'ом
            for bad in ("DELETE FROM users", "DROP TABLE users", "UPDATE users SET name='x'",
                        "INSERT INTO users(name) VALUES('z')"):
                try:
                    sd.query(db, bad, base_dir=d)
                    assert False, "не-SELECT прошёл: %s" % bad
                except sd.QueryNotAllowed:
                    pass

            # read-only на уровне СУБД: прямая запись через mode=ro соединение падает
            conn = sd._connect_ro(db, base_dir=d)
            try:
                conn.execute("CREATE TABLE x(a)")
                assert False, "mode=ro допустил запись"
            except sqlite3.OperationalError:
                pass
            finally:
                conn.close()

            # confinement и суффикс
            try:
                sd.list_tables("../escape.db", base_dir=d)
                assert False, "confinement не сработал"
            except sd.PathAccessError:
                pass
            try:
                sd.list_tables(os.path.join(d, "x.txt"), base_dir=d)
                assert False, "суффикс не проверен"
            except ValueError:
                pass

            print("TESTS OK sqlite: tables=%d cols=%d rows=%d (ro+guard+redaction)"
                  % (len(tables), len(names), len(head)))
    except AssertionError as e:
        ok = False
        print("TEST FAIL:", e)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(run())
