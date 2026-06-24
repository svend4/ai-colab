#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
# ==========================================
# [FILE ID CARD]
# ID: tools.demo_bridge
# TYPE: active-script
# DOMAIN: core
# DEPTH_LEVEL: 1
# SUMMARY: Скрипт demo_bridge.py. Описание сгенерировано автоматически.
# ==========================================
"""
"""
Демо «среднего слоя» AI-OS Bridge (T-078 follow-up) — один запуск показывает, что
получает AI-агент от верифицированных read-only драйверов на реальной локальной папке:

  файлы (карта + поиск с redaction) + инвентаризация репозитория (языки/тесты/риски)
  + память (workbench.db: занести документы и найти по запросу).

Это ровно те движки, которые `gateway` (drivers/gateway/mcp_server.py) отдаёт AI-клиенту
за ОДНИМ MCP-разъёмом. Демо вызывает их напрямую (быстро, без поднятия stdio-сервера, поэтому
работает в любой среде, включая ту, где async MCP stdio падает WinError 5).

Запуск:
    python tools/demo_bridge.py [папка]      # по умолчанию data/fixtures
"""
import os
import sys
from _ioutil import configure_output
import importlib.util

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DRIVERS = os.path.join(ROOT, "drivers")

configure_output()

def _load(name, *parts):
    spec = importlib.util.spec_from_file_location(name, os.path.join(DRIVERS, *parts))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

def main():
    target = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else os.path.join(ROOT, "data", "fixtures")
    if not os.path.isdir(target):
        print("нет папки: %s" % target)
        return 2

    fd = _load("demo_files", "files", "files_driver.py")
    inv = _load("demo_inv", "repo-runner", "inventory.py")
    wb = _load("demo_wb", "workbench", "workbench.py")
    gl = _load("demo_gl", "git-log", "git_log.py")

    line = "=" * 64
    print(line)
    print("AI-OS Bridge — демо среднего слоя")
    print("Папка (allowed-root): %s" % target)
    print(line)

    # 1) файлы: карта
    summ = fd.summarize(target, base_dir=target)
    print("\n[1] files.summarize — карта папки")
    print("    файлов: %d, всего байт: %d" % (summ["files"], summ["total_bytes"]))
    print("    по расширениям: %s" % summ["by_ext"])

    files = fd.list_files(target, base_dir=target)
    print("\n[2] files.list — первые файлы")
    for rel in files[:8]:
        print("    - %s" % rel)

    # 3) файлы: поиск (redaction секретов работает на выдаче)
    term = "sample"
    hits = fd.search(term, target, base_dir=target, max_hits=5)
    print("\n[3] files.search(%r) — совпадения (секреты в выдаче маскируются)" % term)
    for h in hits[:5]:
        print("    %s:%s  %s" % (h["path"], h["line"], h["text"][:80]))
    if not hits:
        print("    (нет совпадений)")

    # 4) repo-runner: инвентаризация (код не запускается)
    rep = inv.scan_repo(target, base_dir=target)
    s = rep.get("summary", {})
    print("\n[4] repo-runner.inspect — инвентаризация (read-only, без запуска кода)")
    print("    языки: %s" % s.get("languages", s.get("by_lang", {})))
    print("    есть тесты: %s | рисков помечено: %s"
          % (s.get("has_tests"), len(rep.get("risks", []))))

    # 5) workbench память: занести документы и найти
    tmp = os.path.join(ROOT, "logs", "demo_bridge.db")
    if os.path.exists(tmp):
        os.remove(tmp)
    conn = wb.init(tmp, base_dir=ROOT)
    try:
        added = 0
        for rel in files:
            full = os.path.join(target, rel)
            try:
                first = open(full, encoding="utf-8", errors="replace").readline().strip()
            except OSError:
                first = ""
            wb.add_document(conn, source="demo", path=rel,
                            type=os.path.splitext(rel)[1].lstrip(".") or "file",
                            summary=first[:120])
            added += 1
        print("\n[5] workbench.memory — занесено документов: %d" % added)
        found = wb.query_documents(conn, text=term, limit=5)
        print("    query(text=%r) → %d совпадений:" % (term, len(found)))
        for d in found[:5]:
            print("    - %s [%s] %s" % (d.get("path"), d.get("type"), (d.get("summary") or "")[:50]))
    finally:
        conn.close()
        if os.path.exists(tmp):
            os.remove(tmp)

    # 6) git-log: история репозитория (если target — git; иначе показываем сам репозиторий)
    git_target = target if os.path.isdir(os.path.join(target, ".git")) else ROOT
    note = "" if git_target == target else "  (target не git — показываю сам репозиторий)"
    print("\n[6] git-log — история репозитория%s" % note)
    try:
        gs = gl.summary(git_target, base_dir=os.path.dirname(git_target))
        print("    ветка: %s | всего коммитов: %s | авторов: %s"
              % (gs.get("branch"), gs.get("total_commits"), gs.get("authors")))
        for c in gl.recent_commits(git_target, n=3, base_dir=os.path.dirname(git_target)):
            print("    %s %s %s — %s" % (c["hash"], c["date"], c["author"], c["subject"][:48]))
    except Exception as exc:
        print("    (git-log недоступен: %s)" % exc)

    print("\n" + line)
    print("Итог: один allowed-root + пять способностей (файлы/поиск/инвентаризация/память/история),")
    print("read-only и без запуска кода — это и есть «средний слой», который gateway отдаёт")
    print("AI-агенту за одним MCP-разъёмом. svend4 (запуск чужого кода) — отдельный слой + песочница.")
    print(line)
    return 0

if __name__ == "__main__":
    sys.exit(main())
