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

Allowed roots for CLI:
    WORKBENCH_BASE=<db-root> INGEST_SOURCE_BASE=<source-root> python ingest.py repo data/workbench.db repo
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

DEFAULT_MAX_FILES = 1000


def ingest_repo_path(db, repo_path, agent="pipeline", verified=None,
                     db_base=None, source_base=None, max_files=DEFAULT_MAX_FILES):
    """Скан репозитория драйвером repo-runner → documents (+ риски) → audit."""
    conn = wb.init(db, base_dir=db_base)
    try:
        report = inventory.scan_repo(repo_path, max_files=max_files, base_dir=source_base)
        src = "repo:" + os.path.basename(os.path.normpath(repo_path))
        n = wb.ingest_repo(conn, report, source=src, verified=verified, max_documents=max_files)
        wb.log(conn, agent, "ingest_repo", repo_path, "files=%d" % n)
        return n
    finally:
        conn.close()


def ingest_dir(db, directory, agent="pipeline", verified=None,
               db_base=None, source_base=None, max_files=DEFAULT_MAX_FILES):
    """Скан папки драйвером files → documents → audit."""
    conn = wb.init(db, base_dir=db_base)
    try:
        src = "dir:" + os.path.basename(os.path.normpath(directory))
        n = 0
        for rel in fd.list_files(directory, max_files=max_files, base_dir=source_base):
            wb.add_document(conn, src, src + ":" + rel, type="file",
                            lang=os.path.splitext(rel)[1], source_last_verified=verified)
            n += 1
        wb.log(conn, agent, "ingest_dir", directory, "files=%d" % n)
        return n
    finally:
        conn.close()


def query(db, db_base=None, **kw):
    conn = wb.init(db, base_dir=db_base)
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
    db_base = os.environ.get("WORKBENCH_BASE") or os.getcwd()
    source_base = os.environ.get("INGEST_SOURCE_BASE") or os.getcwd()
    max_files = int(os.environ.get("INGEST_MAX_FILES") or DEFAULT_MAX_FILES)
    try:
        if cmd == "repo":
            print(json.dumps({"ingested": ingest_repo_path(db, target, db_base=db_base,
                                                           source_base=source_base,
                                                           max_files=max_files)}))
            return 0
        if cmd == "dir":
            print(json.dumps({"ingested": ingest_dir(db, target, db_base=db_base,
                                                     source_base=source_base,
                                                     max_files=max_files)}))
            return 0
    except Exception as exc:
        print(json.dumps({"error": type(exc).__name__, "message": str(exc)}, ensure_ascii=False))
        return 1
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main())
