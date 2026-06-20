#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Сквозной поток (T-053): драйвер сканирует → workbench.db → поиск.

Связывает L2-драйверы (`files`, `repo-runner`) с L6-памятью (`workbench.db`):
скан → запись документов в базу → audit → запрос. Это рабочий ответ на цель
«обрабатывать/классифицировать/обновлять/отвечать по большому объёму информации».

CLI:
    python ingest.py repo <db.db> <repo-path>
    python ingest.py dir  <db.db> <directory>
"""
import os
import sys
import json

HERE = os.path.dirname(os.path.abspath(__file__))
DRIVERS = os.path.dirname(HERE)
import importlib.util


def _load(name, *parts):
    """Загрузить модуль драйвера по явному пути (в drivers/ два разных inventory.py — bare import коллизирует)."""
    path = os.path.join(DRIVERS, *parts)
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


wb = _load("wb_workbench", "workbench", "workbench.py")
inventory = _load("rr_inventory", "repo-runner", "inventory.py")
fd = _load("files_driver_mod", "files", "files_driver.py")


def configure_output():
    for name in ("stdout", "stderr"):
        s = getattr(sys, name, None)
        if s is not None and hasattr(s, "reconfigure"):
            s.reconfigure(encoding="utf-8", errors="replace")


configure_output()


def ingest_repo_path(db, repo_path, agent="pipeline", verified=None):
    """Скан репозитория драйвером repo-runner → documents (+ риски) → audit."""
    conn = wb.init(db)
    try:
        report = inventory.scan_repo(repo_path)
        src = "repo:" + os.path.basename(os.path.normpath(repo_path))
        n = wb.ingest_repo(conn, report, source=src, verified=verified)
        wb.log(conn, agent, "ingest_repo", repo_path, "files=%d" % n)
        return n
    finally:
        conn.close()


def ingest_dir(db, directory, agent="pipeline", verified=None):
    """Скан папки драйвером files → documents → audit."""
    conn = wb.init(db)
    try:
        src = "dir:" + os.path.basename(os.path.normpath(directory))
        n = 0
        for rel in fd.list_files(directory):
            wb.add_document(conn, src, src + ":" + rel, type="file",
                            lang=os.path.splitext(rel)[1], source_last_verified=verified)
            n += 1
        wb.log(conn, agent, "ingest_dir", directory, "files=%d" % n)
        return n
    finally:
        conn.close()


def query(db, **kw):
    conn = wb.init(db)
    try:
        return wb.query_documents(conn, **kw)
    finally:
        conn.close()


def main():
    a = sys.argv[1:]
    if len(a) < 3:
        print(__doc__)
        return 2
    cmd, db, target = a[0], a[1], a[2]
    if cmd == "repo":
        print(json.dumps({"ingested": ingest_repo_path(db, target)}))
        return 0
    if cmd == "dir":
        print(json.dumps({"ingested": ingest_dir(db, target)}))
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main())
