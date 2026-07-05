"""
# ==========================================
# [FILE ID CARD]
# ID: tools.tests.test_adoption
# TYPE: active-script
# DOMAIN: core
# DEPTH_LEVEL: 1
# SUMMARY: Скрипт test_adoption.py. Описание сгенерировано автоматически.
# ==========================================
"""
"""Тест adoption.py — статические метрики применения. Проверяет структуру, не точные числа."""
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

os.environ.setdefault("PYTHONUTF8", "1")
HERE = _TOOLS_DIR  # tools/ — тест перенесён в tools/tests/ (C14)
sys.path.insert(0, HERE)
import adoption

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

TOOL_ST = {"active", "manual-cli", "referenced-only", "dormant"}
DEC_ST = {"code-linked", "doc-only"}
DOC_ST = {"cited", "orphan"}
WRITER_ST = {"safe-write", "direct-marked", "direct-allowlisted",
             "direct-canon", "direct-other", "no-write"}


def main():
    fails = []
    data = adoption.collect()
    for k in ("tools", "decisions", "docs", "summary"):
        if k not in data:
            fails.append("collect без ключа %r" % k)
    if not data.get("tools"):
        fails.append("0 инструментов — classify_tools пуст")
    for r in data.get("tools", []):
        if r["status"] not in TOOL_ST:
            fails.append("tool %s: статус %r вне набора" % (r["name"], r["status"]))
            break
    for r in data.get("decisions", []):
        if r["status"] not in DEC_ST:
            fails.append("decision %s: статус %r вне набора" % (r["name"], r["status"]))
            break
    for r in data.get("docs", []):
        if r["status"] not in DOC_ST:
            fails.append("doc %s: статус %r вне набора" % (r["name"], r["status"]))
            break
    # summary-тройки [good, total, pct]
    s = data.get("summary", {})
    for k in ("tools_applied", "decisions_enforced", "docs_cited"):
        v = s.get(k)
        if not (isinstance(v, list) and len(v) == 3):
            fails.append("summary[%r] не [good,total,pct]" % k)

    # --- C33: write-контур (правило «канон-путь → safe_write») ---
    if not data.get("writers"):
        fails.append("0 writers — classify_writers пуст")
    for r in data.get("writers", []):
        if r["status"] not in WRITER_ST:
            fails.append("writer %s: статус %r вне набора" % (r["name"], r["status"]))
            break
    if not isinstance(s.get("writers_unguarded"), int):
        fails.append("summary['writers_unguarded'] не int")
    # синтетика: усекающая запись по канон-пути БЕЗ гварда → WARN (direct-canon)
    src_direct = ('import os\n'
                  'p = os.path.join(ROOT, "tasks", "T-001.md")\n'
                  'f = open(p, "w", encoding="utf-8")\n'
                  'f.write("x")\n')
    got = adoption.writer_status(src_direct)
    if got != "direct-canon":
        fails.append("канон-писатель без гварда должен давать WARN direct-canon, а не %r" % got)
    # тот же исходник, но имя из WRITE_ALLOWLIST → тишина
    got = adoption.writer_status(src_direct, "pipeline.py")
    if got != "direct-allowlisted":
        fails.append("файл из WRITE_ALLOWLIST должен гаситься: %r" % got)
    # с safe_write → тишина
    src_safe = ('from _ioutil import safe_write\nimport os\n'
                'safe_write(os.path.join(ROOT, "tasks", "T-001.md"), "x")\n')
    got = adoption.writer_status(src_safe)
    if got != "safe-write":
        fails.append("safe_write-писатель должен быть safe-write, а не %r" % got)
    # с маркером-пометкой генерата → тишина
    got = adoption.writer_status("# direct-write-ok: генерат, переписывается целиком\n" + src_direct)
    if got != "direct-marked":
        fails.append("маркер direct-write-ok должен гасить WARN: %r" % got)
    # чтение канона без усекающей записи → no-write
    got = adoption.writer_status('t = open(os.path.join("tasks", "T-1.md"), encoding="utf-8").read()\n')
    if got != "no-write":
        fails.append("чтение канона без записи должно быть no-write, а не %r" % got)
    # усекающая запись ВНЕ канон-путей → вне правила (direct-other)
    got = adoption.writer_status('f = open(os.path.join("logs", "x.json"), "w")\n')
    if got != "direct-other":
        fails.append("запись вне канон-путей должна быть direct-other, а не %r" % got)

    if fails:
        print("FAIL test_adoption:")
        for f in fails:
            print("  -", f)
        sys.exit(1)
    print("OK test_adoption: collect() структура валидна (%d tools, %d decisions, %d docs) · "
          "C33 write-контур: unguarded=%d" % (len(data["tools"]), len(data["decisions"]),
                                              len(data["docs"]), s["writers_unguarded"]))


if __name__ == "__main__":
    main()
