"""
# ==========================================
# [FILE ID CARD]
# ID: tools.test_adoption
# TYPE: active-script
# DOMAIN: core
# DEPTH_LEVEL: 1
# SUMMARY: Скрипт test_adoption.py. Описание сгенерировано автоматически.
# ==========================================
"""
"""Тест adoption.py — статические метрики применения. Проверяет структуру, не точные числа."""
import os
import sys

os.environ.setdefault("PYTHONUTF8", "1")
HERE = os.path.dirname(os.path.abspath(__file__))
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

    if fails:
        print("FAIL test_adoption:")
        for f in fails:
            print("  -", f)
        sys.exit(1)
    print("OK test_adoption: collect() структура валидна (%d tools, %d decisions, %d docs)"
          % (len(data["tools"]), len(data["decisions"]), len(data["docs"])))


if __name__ == "__main__":
    main()
