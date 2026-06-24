"""autolink.py — ADVISORY: предложения, как ДОЗРЕТЬ незрелым атомам (type/gist/topic).

Замыкает петлю с maturity.py: maturity НАХОДИТ недозрелых → autolink ПРЕДЛАГАЕТ как дозреть.
Строго advisory — НЕ применяет (только предложения для ROUTE-гейта / человека). Тип — детерминированно
(из id-префикса/папки); gist — эвристически (первая проза); topic — по co-citation. Read-only.

CLI:
  python tools/autolink.py               # все предложения сгруппированы
  python tools/autolink.py --json        # машинно (для ROUTE-гейта)
  python tools/autolink.py --kind type   # только type-backfill (детерминированно) | gist | topic
"""
import os
from _ioutil import configure_output
import re
import sys
import json

configure_output()
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.environ.get("COLLAB_ROOT") or os.path.dirname(HERE)
sys.path.insert(0, HERE)
import edges
from _cli import help_guard

TYPE_BY_PREFIX = {"T-": "task", "D-": "decision", "Q-": "question"}
TYPE_BY_FOLDER = {"topics": "topic", "docs": "doc", "streams": "stream", "drivers": "driver",
                  "questions": "question", "tasks": "task", "decisions": "decision"}


def suggest_type(n):
    """Детерминированно: тип из id-префикса, иначе из папки."""
    if (n["fm"].get("type") or "").strip():
        return None
    pfx = n["id"][:2] if n["id"] else ""
    t = TYPE_BY_PREFIX.get(pfx) or TYPE_BY_FOLDER.get(n["folder"])
    if not t:
        return None
    return {"id": n["id"] or n["slug"], "file": n["path"], "field": "type",
            "suggest": t, "basis": "id-префикс" if pfx in TYPE_BY_PREFIX else "папка %s" % n["folder"]}


def _first_prose(body):
    b = re.sub(r"^---.*?\n---\n?", "", body, count=1, flags=re.S)
    for line in b.splitlines():
        s = line.strip()
        if not s or s[0] in "#>|" or s.startswith("```") or s.startswith("---") or s.startswith("!["):
            continue
        s = re.sub(r"[*_`]", "", s)  # снять markdown-эмфазу
        return s[:110]
    return ""


def suggest_gist(n):
    """Эвристически: gist из первой прозы (для атомов с title, но без gist)."""
    if (n["fm"].get("gist") or "").strip():
        return None
    if not (n["fm"].get("title") or "").strip():
        return None
    prose = _first_prose(n["body"])
    if not prose:
        return None
    return {"id": n["id"] or n["slug"], "file": n["path"], "field": "gist",
            "suggest": prose, "basis": "первая проза"}


def suggest_topics(nodes, by_id):
    """По co-citation: атом-изолят, который часто цитируется ВМЕСТЕ с неким хабом → предложить related."""
    # лёгкая версия: изоляты (0 структурных рёбер), для которых есть ≥1 cites — предложить превратить в related
    elist = edges.build_edges(nodes, by_id, {n["slug"]: k for k, n in nodes.items()})
    deg, cited_by = {}, {}
    for e in elist:
        if e["type"] in ("depends", "related", "superseded", "basis") and not e["dangling"]:
            deg[e["src"]] = deg.get(e["src"], 0) + 1
            deg[e["dst"]] = deg.get(e["dst"], 0) + 1
        if e["type"] == "cites" and not e["dangling"]:
            cited_by.setdefault(e["dst"], []).append(e["src"])
    def _is_atom(k):  # реальный атом T/D/Q, не генерируемый агрегат (DECISIONS/board/dialog) и не док
        return len(k) >= 3 and k[:2] in ("T-", "D-", "Q-")

    out = []
    for key, n in nodes.items():
        if not (n["id"] and n["id"][:2] in ("T-", "D-", "Q-")):
            continue
        if deg.get(key, 0) == 0 and n["status"] not in ("done", "rejected", "superseded", "answered"):
            # только СЕМАНТИЧЕСКИЕ цитирующие (атомы), не агрегаты-навигация
            citers = [c for c in cited_by.get(key, []) if _is_atom(c) and c != key]
            if citers:
                out.append({"id": n["id"], "file": n["path"], "field": "related",
                            "suggest": citers[:3],
                            "basis": "цитируется атомами %d× (изолят без структурных рёбер)" % len(citers)})
    return out


def collect():
    nodes, by_id, by_slug = edges.load_nodes()
    types, gists = [], []
    for key, n in nodes.items():
        st = suggest_type(n)
        if st:
            types.append(st)
        gs = suggest_gist(n)
        if gs and n["id"] and n["id"][:2] in ("T-", "D-", "Q-"):  # gist-предложения только для рабочих атомов
            gists.append(gs)
    topics = suggest_topics(nodes, by_id)
    types.sort(key=lambda x: x["id"])
    return {"type": types, "gist": gists, "topic": topics}


def main(argv):
    help_guard(__doc__, argv)
    as_json = "--json" in argv
    kind = None
    if "--kind" in argv:
        i = argv.index("--kind")
        if i + 1 < len(argv):
            kind = argv[i + 1]
    data = collect()
    if kind:
        data = {kind: data.get(kind, [])}
    if as_json:
        print(json.dumps(data, ensure_ascii=False, indent=2))
        return 0
    print("=== AUTOLINK — предложения дозреть (ADVISORY, не применяется) ===")
    labels = {"type": "type-backfill (детерминированно)", "gist": "gist-suggest (эвристика)",
              "topic": "related из cites (изоляты)"}
    for k in ("type", "gist", "topic"):
        items = data.get(k, [])
        if k not in data:
            continue
        print("\n  ▸ %s: %d" % (labels[k], len(items)))
        for it in items[:15]:
            sug = it["suggest"]
            sug = ", ".join(sug) if isinstance(sug, list) else sug
            print("    %s  %s: %s   (%s)" % (it["id"], it["field"], sug, it["basis"]))
        if len(items) > 15:
            print("    … и ещё %d" % (len(items) - 15))
    print("\n  → применять выборочно через ROUTE (свои атомы; чужие — владельцу).")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
