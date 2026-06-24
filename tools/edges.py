"""edges.py — типизированный граф связей (DIV-07/08): первоклассные направленные рёбра над атомами.

ВТОРАЯ ОСЬ проекта. Дерево (папки/пирамида = ГДЕ живёт атом) ⟂ граф (типизированные рёбра = КАК
связан). НЕ меняет хранилище — извлекает рёбра, уже неявно лежащие во front-matter
(depends_on / superseded_by / related / l1_basis / topic) + inline id-ссылки в теле. Делает
неявный граф ПЕРВОКЛАССНЫМ и запрашиваемым/проверяемым. Реализует DIV-07 (типизированное ребро как
объект) и DIV-08 (две ортогональные оси физически: containment vs typed-edges).

Типы рёбер (поле → тип · направление · семантика):
  depends_on     A →depends→ B      A нуждается в B          направленное; цикл = дефект
  superseded_by  A →superseded→ B   B заменяет A             направленное; цепочки
  related        A →related→ B      связь как написана       взаимность НЕ навязывается (инфо)
  l1_basis       portal →basis→ X   портал опирается на tool направленное
  topic          atom →in_topic→ T  тематическая группировка ось-тема (⟂ папка)
  (тело)         A ·cites· B        id упомянут в тексте     слабое

CLI:
  python tools/edges.py check        # дефекты графа: висячие рёбра · циклы depends · supersede · изоляты
  python tools/edges.py stats        # сводка: узлы, рёбра по типам, изоляты, компоненты связности
  python tools/edges.py neighbors <id>  # окрестность атома — ОБЕ оси (папка/уровень + рёбра in/out)
  python tools/edges.py impact <id>     # blast-radius: кого транзитивно сломает правка (обратный BFS depends/basis)
  python tools/edges.py path <a> <b>    # кратчайший путь a→b по структурным рёбрам (как связаны)
  python tools/edges.py --json <sub>
"""
import os
from _ioutil import configure_output
import re
import sys
import json
import glob

configure_output()
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.environ.get("COLLAB_ROOT") or os.path.dirname(HERE)
sys.path.insert(0, HERE)
from _canon import parse_fm

DIRS = ["tasks", "decisions", "questions", "topics", "docs", "portals", "core", "streams", "drivers", "collab"]
ID_RE = re.compile(r'\b([TDQ]-\d+|[A-Z]-\d{3})\b')
# id-пространства внутри агрегированных докумен­тов (не отдельные файл-атомы): friction F-NN,
# консенсус C-NN, разногласия DIV-NN — валидные ссылки, но живут секциями внутри docs/topics.
EXTERNAL_RE = re.compile(r'^(F|C|DIV)-\d+$')
# структурные рёбра: поле front-matter → тип ребра.
# LIST = значение может быть списком ([a, b] или a, b); SCALAR = одиночный токен.
LIST_FIELDS = {"depends_on": "depends", "related": "related", "l1_basis": "basis",
               "superseded_by": "superseded", "detail_ref": "detail", "sources": "source"}
SCALAR_FIELDS = {"topic": "in_topic"}
DIRECTED = {"depends", "superseded", "basis", "in_topic", "cites", "detail", "source"}


def _slug(path):
    return os.path.basename(path)[:-3]


def _split_list(val):
    """'[a, b]' или 'a, b' → ['a','b'] (наивно, но канон прост)."""
    val = (val or "").strip().strip("[]").strip()
    if not val:
        return []
    return [x.strip().strip("'\"") for x in val.split(",") if x.strip()]


def load_nodes():
    """Все атомы канона → {key: node}. key = id (если есть) иначе slug."""
    nodes, by_id, by_slug = {}, {}, {}
    # корневые .md (AGENTS.md, PROTOCOL.md, LIVE.md, PIPELINE.md, dialog.md…) — тоже узлы графа
    paths = list(glob.glob(os.path.join(ROOT, "*.md")))
    for d in DIRS:
        paths += glob.glob(os.path.join(ROOT, d, "**", "*.md"), recursive=True)
    for p in paths:
            if os.path.basename(p) in ("README.md",):
                continue
            try:
                txt = open(p, encoding="utf-8", errors="replace").read()
            except OSError:
                continue
            fm = parse_fm(txt) or {}
            slug = _slug(p)
            nid = (fm.get("id") or "").strip()
            key = nid or slug
            rel = os.path.relpath(p, ROOT).replace("\\", "/")
            folder = rel.split("/")[0] if "/" in rel else "(root)"
            node = {"key": key, "id": nid, "slug": slug, "folder": folder, "path": rel,
                    "type": fm.get("type", ""), "status": fm.get("status", ""),
                    "level": fm.get("level", ""), "title": fm.get("title", slug),
                    "fm": fm, "body": txt}
            nodes[key] = node
            if nid:
                by_id[nid] = key
            by_slug[slug] = key
    return nodes, by_id, by_slug


def _resolve(tok, by_id, by_slug):
    tok = (tok or "").strip().strip("'\"")
    if tok in by_id:
        return by_id[tok]
    if tok in by_slug:
        return by_slug[tok]
    # ссылка с расширением (AGENTS.md, PROTOCOL.md) → пробуем slug без .md
    if tok.endswith(".md") and tok[:-3] in by_slug:
        return by_slug[tok[:-3]]
    # путь tools/x.py (l1_basis) — узел-инструмент вне канона: ключ как есть
    if tok.endswith(".py") or "/" in tok:
        return tok
    return None  # не разрешилось → висячее


def build_edges(nodes, by_id, by_slug):
    """Извлечь все типизированные рёбра. Возврат: список {src, dst, type, raw, dangling}."""
    edges = []
    for key, n in nodes.items():
        fm = n["fm"]
        seen_targets = set()
        # значения берём из КАНОНИЧЕСКОГО parse_fm (не своя regex — иначе \s* перепрыгивает строки)
        for field, etype in LIST_FIELDS.items():
            for tok in _split_list(fm.get(field, "")):
                dst = _resolve(tok, by_id, by_slug)
                edges.append({"src": key, "dst": dst or tok, "type": etype, "raw": tok,
                              "dangling": dst is None and not EXTERNAL_RE.match(tok),
                              "external": bool(EXTERNAL_RE.match(tok))})
                if dst:
                    seen_targets.add(dst)
        for field, etype in SCALAR_FIELDS.items():
            raw = (fm.get(field) or "").strip()
            if raw:
                dst = _resolve(raw, by_id, by_slug)
                # in_topic больше НЕ исключаем молча — неразрешённая тема честно = dangling
                # (разделим в check на жёсткое vs тема-без-файла, но не прячем)
                edges.append({"src": key, "dst": dst or raw, "type": etype,
                              "raw": raw, "dangling": dst is None})
                if dst:
                    seen_targets.add(dst)
        # слабые cites: id в теле, не учтённые структурно и не self
        body = re.sub(r"^---.*?\n---", "", n["body"], count=1, flags=re.S)
        for m in set(ID_RE.findall(body)):
            dk = by_id.get(m)
            if dk and dk != key and dk not in seen_targets:
                edges.append({"src": key, "dst": dk, "type": "cites", "raw": m, "dangling": False})
    return edges


# ---- проверки графа ----
def find_cycles(edges):
    """Циклы в depends-подграфе (A→B→…→A) — реальный дефект зависимостей."""
    adj = {}
    for e in edges:
        if e["type"] == "depends" and not e["dangling"]:
            adj.setdefault(e["src"], []).append(e["dst"])
    cycles, WHITE, GREY, BLACK = [], 0, 1, 2
    color = {}

    def dfs(u, stack):
        color[u] = GREY
        for v in adj.get(u, []):
            if color.get(v, WHITE) == GREY:
                i = stack.index(v) if v in stack else 0
                cycles.append(stack[i:] + [v])
            elif color.get(v, WHITE) == WHITE:
                dfs(v, stack + [v])
        color[u] = BLACK

    for u in list(adj):
        if color.get(u, WHITE) == WHITE:
            dfs(u, [u])
    # дедуп по множеству узлов
    uniq, seen = [], set()
    for c in cycles:
        sig = frozenset(c)
        if sig not in seen:
            seen.add(sig)
            uniq.append(c)
    return uniq


TERMINAL_STATUS = ("done", "rejected", "answered", "accepted", "superseded")


def check(nodes, edges, by_id):
    out = {"dangling": [], "topic_unresolved": [], "cycles": [], "terminal_cycles": [],
           "supersede": [], "asym_related": [], "missing_type": [], "isolates": [], "active_isolates": []}
    # ЧЕСТНО: жёсткие висячие (depends/related/…) ОТДЕЛЬНО от тема-без-файла (in_topic) — не прячем
    for e in edges:
        if not e["dangling"]:
            continue
        if e["type"] == "in_topic":
            out["topic_unresolved"].append("%s →in_topic→ %s (нет файла-темы)" % (e["src"], e["raw"]))
        else:
            out["dangling"].append("%s →%s→ %s (нет такого атома)" % (e["src"], e["type"], e["raw"]))
    # циклы: РАЗДЕЛЯЕМ активные (жёсткое — блокирует порядок) от терминальных (все done/accepted —
    # историч. артефакт, не runtime-проблема). Иначе гейт завалит коммиты на старом done↔done.
    for c in find_cycles(edges):
        label = " → ".join(c)
        if all(nodes.get(k, {}).get("status", "") in TERMINAL_STATUS for k in c):
            out["terminal_cycles"].append(label + " (все терминальные — историч. артефакт)")
        else:
            out["cycles"].append(label)
    # supersede-целостность: A superseded_by B → A должен быть в терминальном статусе
    for e in edges:
        if e["type"] == "superseded" and not e["dangling"]:
            a = nodes.get(e["src"], {})
            if a.get("status") not in ("superseded", "done", "rejected", "answered", "accepted"):
                out["supersede"].append("%s superseded_by %s, но статус '%s' (не терминальный)"
                                        % (e["src"], e["raw"], a.get("status")))
    # асимметричный related: A—related—B, но не B—related—A (документирован как взаимный)
    rel = set()
    for e in edges:
        if e["type"] == "related" and not e["dangling"]:
            rel.add((e["src"], e["dst"]))
    for a, b in sorted(rel):
        if (b, a) not in rel and nodes.get(b, {}).get("id"):  # только атом↔атом (не пути-файлы)
            out["asym_related"].append("%s →related→ %s (нет обратного %s→%s)" % (a, b, b, a))
    # атомы без поля type (гигиена; ломает отображение)
    for key, n in nodes.items():
        if n["id"] and not n["type"]:
            out["missing_type"].append(key)
    # изоляты: id-атомы (T/D/Q) без структурного ребра; РАЗДЕЛЯЕМ фундамент vs активные
    deg = {}
    for e in edges:
        if e["type"] in ("depends", "related", "superseded", "basis"):
            deg[e["src"]] = deg.get(e["src"], 0) + 1
            if not e["dangling"]:
                deg[e["dst"]] = deg.get(e["dst"], 0) + 1
    for key, n in nodes.items():
        if n["id"] and n["id"][:2] in ("T-", "D-", "Q-") and deg.get(key, 0) == 0:
            row = "%s (%s, %s)" % (key, n["type"] or "?", n["status"])
            # активная задача-изолят = кандидат на линковку; accepted/done решение-фундамент = норма
            if n["id"].startswith("T-") and n["status"] in ("todo", "doing", "blocked"):
                out["active_isolates"].append(row + " — активная задача без рёбер (кандидат на линковку)")
            elif n["status"] not in ("done", "rejected", "superseded", "answered"):
                out["isolates"].append(row + " — фундамент без рёбер (норма)")
    return out


def stats(nodes, edges):
    by_type = {}
    dangling = 0
    for e in edges:
        by_type[e["type"]] = by_type.get(e["type"], 0) + 1
        dangling += 1 if e["dangling"] else 0
    return {"nodes": len(nodes), "edges": len(edges), "by_type": by_type, "dangling": dangling}


def neighbors(nid, nodes, edges, by_id):
    key = by_id.get(nid, nid)
    n = nodes.get(key)
    if not n:
        return None
    out = {"id": nid, "axis_tree": {"folder": n["folder"], "level": n["level"], "type": n["type"],
                                    "status": n["status"], "title": n["title"]},
           "axis_graph": {"out": [], "in": []}}
    for e in edges:
        if e["src"] == key:
            out["axis_graph"]["out"].append("%s→ %s" % (e["type"], e["raw"]))
        if e["dst"] == key and not e["dangling"]:
            out["axis_graph"]["in"].append("%s ←%s" % (e["src"], e["type"]))
    return out


# ---- транзитивные запросы (управление каскадом) ----
IMPACT_TYPES = ("depends", "basis")  # «кого сломает правка X» = кто транзитивно зависит/опирается на X


def impact(nid, nodes, edges, by_id):
    """Blast-radius: все атомы, транзитивно зависящие от nid (обратный BFS по depends/basis)."""
    key = by_id.get(nid, nid)
    if key not in nodes:
        return None
    radj = {}  # dst → [src] (обратное ребро: src зависит от dst)
    for e in edges:
        if e["type"] in IMPACT_TYPES and not e["dangling"]:
            radj.setdefault(e["dst"], []).append(e["src"])
    seen, affected, queue = {key}, [], [(key, 0)]
    i = 0
    while i < len(queue):
        u, d = queue[i]; i += 1
        for v in radj.get(u, []):
            if v not in seen:
                seen.add(v); affected.append({"id": v, "dist": d + 1}); queue.append((v, d + 1))
    affected.sort(key=lambda x: (x["dist"], x["id"]))
    return affected


def path(a, b, nodes, edges, by_id):
    """Кратчайший направленный путь a→b по структурным рёбрам (как связаны). None если нет."""
    ka, kb = by_id.get(a, a), by_id.get(b, b)
    if ka not in nodes or kb not in nodes:
        return None
    adj = {}  # src → [(dst, type)]
    for e in edges:
        if e["type"] in ("depends", "related", "superseded", "basis", "in_topic") and not e["dangling"]:
            adj.setdefault(e["src"], []).append((e["dst"], e["type"]))
    prev, queue, i = {ka: None}, [ka], 0
    while i < len(queue):
        u = queue[i]; i += 1
        if u == kb:
            break
        for v, t in adj.get(u, []):
            if v not in prev:
                prev[v] = (u, t); queue.append(v)
    if kb not in prev:
        return None
    chain, cur = [], kb
    while cur != ka:
        u, t = prev[cur]
        chain.append({"from": u, "type": t, "to": cur}); cur = u
    return list(reversed(chain))


def main(argv):
    as_json = "--json" in argv
    args = [a for a in argv if not a.startswith("--")]
    sub = args[0] if args else "check"
    nodes, by_id, by_slug = load_nodes()
    edges = build_edges(nodes, by_id, by_slug)

    if sub == "stats":
        s = stats(nodes, edges)
        if as_json:
            print(json.dumps(s, ensure_ascii=False, indent=2)); return 0
        print("=== ГРАФ СВЯЗЕЙ (вторая ось) ===")
        print("  узлов: %d   рёбер: %d   висячих: %d" % (s["nodes"], s["edges"], s["dangling"]))
        for t, c in sorted(s["by_type"].items(), key=lambda x: -x[1]):
            print("    %-12s %4d" % (t, c))
        return 0

    if sub == "neighbors":
        if len(args) < 2:
            print("edges neighbors <id>"); return 2
        r = neighbors(args[1], nodes, edges, by_id)
        if r is None:
            print("нет атома %s" % args[1]); return 1
        if as_json:
            print(json.dumps(r, ensure_ascii=False, indent=2)); return 0
        t = r["axis_tree"]
        print("=== %s — две оси ===" % r["id"])
        print("  ОСЬ-ДЕРЕВО (где): %s/ · уровень %s · %s · %s" % (t["folder"], t["level"] or "—", t["type"] or "?", t["status"]))
        print("  ОСЬ-ГРАФ (как):")
        print("    out: %s" % (", ".join(r["axis_graph"]["out"]) or "—"))
        print("    in:  %s" % (", ".join(r["axis_graph"]["in"]) or "—"))
        return 0

    if sub == "impact":
        if len(args) < 2:
            print("edges impact <id>"); return 2
        r = impact(args[1], nodes, edges, by_id)
        if r is None:
            print("нет атома %s" % args[1]); return 1
        if as_json:
            print(json.dumps({"id": args[1], "affected": r}, ensure_ascii=False, indent=2)); return 0
        print("=== BLAST-RADIUS правки %s (кто транзитивно зависит) ===" % args[1])
        print("  затронуто атомов: %d" % len(r))
        for a in r[:25]:
            st = nodes.get(a["id"], {}).get("status", "")
            print("    [d%d] %s (%s)" % (a["dist"], a["id"], st))
        if len(r) > 25:
            print("    … и ещё %d" % (len(r) - 25))
        return 0

    if sub == "path":
        if len(args) < 3:
            print("edges path <a> <b>"); return 2
        r = path(args[1], args[2], nodes, edges, by_id)
        if as_json:
            print(json.dumps({"from": args[1], "to": args[2], "path": r}, ensure_ascii=False, indent=2)); return 0
        if r is None:
            print("пути %s → %s нет (или нет атома)" % (args[1], args[2])); return 1
        print("=== ПУТЬ %s → %s (длина %d) ===" % (args[1], args[2], len(r)))
        for step in r:
            print("    %s --%s--> %s" % (step["from"], step["type"], step["to"]))
        return 0

    # check
    c = check(nodes, edges, by_id)
    if as_json:
        print(json.dumps(c, ensure_ascii=False, indent=2))
        return 0 if not (c["dangling"] or c["cycles"]) else 1
    print("=== ПРОВЕРКА ГРАФА (DIV-07/08) ===")
    HARD = {"dangling", "cycles"}
    for kind, label in (("dangling", "Висячие рёбра атом→атом (жёсткое)"),
                        ("cycles", "Активные циклы depends_on (жёсткое)"),
                        ("terminal_cycles", "Терминальные циклы (done↔done — историч., мягкое)"),
                        ("topic_unresolved", "Темы без файла-атома (in_topic, мягкое)"),
                        ("asym_related", "Асимметричный related (инфо: взаимность не навязывается)"),
                        ("supersede", "Supersede-целостность"),
                        ("missing_type", "Атомы без поля type (гигиена)"),
                        ("active_isolates", "Активные задачи-изоляты (кандидаты на линковку)"),
                        ("isolates", "Изоляты-фундамент (норма)")):
        items = c[kind]
        mark = "✗" if (kind in HARD and items) else ("•" if items else "✓")
        print("  %s %s: %d" % (mark, label, len(items)))
        for it in items[:12]:
            print("      - %s" % it)
        if len(items) > 12:
            print("      … и ещё %d" % (len(items) - 12))
    hard = bool(c["dangling"] or c["cycles"])
    print("\n  %s" % ("✗ есть жёсткие дефекты графа (висячие атом→атом / циклы)" if hard
                      else "✓ жёстких дефектов нет (висячих атом→атом и циклов); мягкие — см. выше"))
    return 1 if hard else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
