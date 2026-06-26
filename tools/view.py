"""view.py — релевантный СРЕЗ канона под задачу (подача контекста агенту), над существующими рёбрами.

Не новый формат: `view` собирает связный подграф канона обходом НАШИХ рёбер (`related:` front-matter +
`[[ссылки]]`) от seed до глубины N. Агенту подаётся рабочее множество, не весь репо. Режимы: frozen
(инлайн тела — самодостаточный срез) / live (пути+визитки — дёшево). Budget-aware (≈символы/4).

Публичные: load_canon, slice_ids, assemble. Это наш ответ «что подать в окно под ЭТУ задачу»
(`portals` отвечает «где кластеры», `view` — «что в окно»).

CLI:
  python tools/view.py <seed-id> --depth 2 --live
  python tools/view.py <seed-id> --frozen --budget 8000 [--name casus-x]
"""
import os
from _ioutil import configure_output
from _cli import help_guard
import sys
import re
import glob

configure_output()
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.environ.get("COLLAB_ROOT") or os.path.dirname(HERE)
CANON_DIRS = ("tasks", "decisions", "questions", "topics", "docs")


def load_canon(root=ROOT, dirs=CANON_DIRS):
    """id → {id, path, body, links}: канон-файлы с рёбрами (related: + [[ссылки]])."""
    canon = {}
    for d in dirs:
        for p in glob.glob(os.path.join(root, d, "**", "*.md"), recursive=True):
            try:
                text = open(p, encoding="utf-8", errors="replace").read()
            except OSError:
                continue
            fid = _front_id(text) or os.path.splitext(os.path.basename(p))[0]
            canon[fid] = {"id": fid, "path": os.path.relpath(p, root).replace("\\", "/"),
                          "body": _body(text), "links": _links(text)}
    return canon


def slice_ids(canon, seed, depth):
    """Связный подграф: BFS от seed по рёбрам до глубины depth (включительно).

    Порядок ДЕТЕРМИНИРОВАН: BFS-уровень, внутри уровня соседи отсортированы. Раньше
    возвращали `[seed]+[i for i in seen]`, где seen — set: итерация set-а строк НЕ
    insertion-ordered и зависит от PYTHONHASHSEED → порядок плыл между процессами
    (комментарий «BFS-порядок сохранён» был неверен). Теперь порядок копим в список,
    соседей (links — тоже set) сортируем перед обходом.
    """
    if seed not in canon:
        return []
    seen = {seed}
    order = [seed]
    frontier = [seed]
    for _ in range(max(0, depth)):
        nxt = []
        for nid in frontier:
            for ln in sorted(canon.get(nid, {}).get("links", ())):
                if ln in canon and ln not in seen:
                    seen.add(ln); nxt.append(ln); order.append(ln)
        frontier = nxt
        if not frontier:
            break
    return order


def assemble(canon, ids, mode="live", budget=0):
    """Срез в текст: live (пути+визитка) / frozen (инлайн тела); budget≈символы/4 (0 = без лимита)."""
    out = []
    used = 0
    cap = budget * 4 if budget else 0
    for i in ids:
        n = canon.get(i)
        if not n:
            continue
        if mode == "frozen":
            chunk = "## %s  (%s)\n%s\n" % (i, n["path"], n["body"].strip())
        else:
            chunk = "- %s  → %s%s" % (i, n["path"], _gist(n["body"]))
        if cap and used + len(chunk) > cap and used > 0:
            out.append("… [срез усечён по бюджету %d ток.; --depth/--budget расширяемы]" % budget)
            break
        out.append(chunk)
        used += len(chunk)
    return "\n".join(out), used


def _front_id(text):
    m = re.search(r"^id:\s*(.+)$", text[:600], re.M)
    return m.group(1).strip() if m else None


def _body(text):
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end >= 0:
            nl = text.find("\n", end + 1)
            return text[nl + 1:] if nl >= 0 else ""
    return text


def _links(text):
    links = set(re.findall(r"\[\[([^\]]+)\]\]", text))
    fm = text[:1500]
    m = re.search(r"^related:\s*\[(.*?)\]", fm, re.M | re.S)
    if m:
        links |= {x.strip().strip("'\"") for x in m.group(1).split(",") if x.strip()}
    for mm in re.finditer(r"^\s*-\s*([A-Za-z0-9_.\-]+)\s*$", _related_block(fm), re.M):
        links.add(mm.group(1).strip())
    return {l for l in links if l}


def _related_block(fm):
    m = re.search(r"^related:\s*\n((?:\s*-\s*.+\n)+)", fm, re.M)
    return m.group(1) if m else ""


def _gist(body):
    for ln in body.splitlines():
        s = ln.strip().lstrip("#> ").strip()
        if len(s) > 12:
            return "  — " + s[:80]
    return ""


def main(argv):
    help_guard(__doc__, argv)
    args = [a for a in argv if not a.startswith("--")]
    if not args:
        print("view: нужен seed-id. Пример: view.py D-030 --depth 2 --live"); return 2
    seed = args[0]
    depth = _opt_int(argv, "--depth", 2)
    budget = _opt_int(argv, "--budget", 0)
    mode = "frozen" if "--frozen" in argv else "live"
    canon = load_canon()
    if seed not in canon:
        cand = [i for i in canon if seed.lower() in i.lower()][:5]
        print("view: seed '%s' не найден. Похожие: %s" % (seed, ", ".join(cand) or "—")); return 2
    ids = slice_ids(canon, seed, depth)
    text, used = assemble(canon, ids, mode, budget)
    name = None
    if "--name" in argv:
        i = argv.index("--name")
        name = argv[i + 1] if i + 1 < len(argv) else None
    header = "=== VIEW '%s' seed=%s depth=%d mode=%s · блоков=%d · ~%d ток. ===" % (
        name or seed, seed, depth, mode, len(ids), used // 4)
    if name:
        os.makedirs(os.path.join(ROOT, "views"), exist_ok=True)
        fp = os.path.join(ROOT, "views", name + ".md")
        open(fp, "w", encoding="utf-8", newline="\n").write(header + "\n\n" + text + "\n")
        print(header)
        print("→ сохранён: views/%s.md" % name)
    else:
        print(header)
        print(text)
    return 0


def _opt_int(argv, flag, default):
    if flag in argv:
        try:
            return int(argv[argv.index(flag) + 1])
        except (ValueError, IndexError):
            pass
    return default


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
