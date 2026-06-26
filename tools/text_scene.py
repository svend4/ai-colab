"""text_scene.py — abstraction-view 2D-карточек канона с прогрессивным раскрытием (textscene MVP, Стадия 2).

Реализует «abstraction»-режим единого спека (topics/textscene-unified-spec-2026-06-26): берёт связный срез
канона (детерминированный BFS, как view.slice_ids после R1) и раскладывает его 2D-СЕТКОЙ карточек:
  Y = глубина BFS от seed (общее → частное),   X = позиция в уровне (детерм. по отсорт. id).
Карточка раскрывается по уровням (текстовый аналог pseudo-diffusion-сид → детали; это reveal-staging, НЕ
denoising — честно по разбору tvcp-text-diffusion-hybrid):
  L0 = ▦ тип+id        L1 = +gist (первая содержательная строка)        L2 = +тело целиком
`diffuse(steps)` — кадры: доля карточек с раскрытым телом растёт по порядку глубины (аналог Grid.DiffuseFrames
из pkg/pseudo, но над дискретным порядком раскрытия). Рендеры: ANSI-сетка боксов (ширина карточки КЛАМПИТСЯ —
урок per-op санитизации scene.Apply) и самодостаточный HTML (CSS-grid <details>, как view_html).

Инвариант (§6 спека): только ЧИТАЕТ канон, истину не мутирует (canon ≠ view).

CLI:
  python tools/text_scene.py <seed-id> --depth 2 --cols 3           # ANSI, L1 (меню+gist)
  python tools/text_scene.py <seed-id> --depth 2 --level 2          # всё тело
  python tools/text_scene.py <seed-id> --steps 5                    # кадры раскрытия (общее→частное)
  python tools/text_scene.py <seed-id> --html > scene.html
"""
import os
from _ioutil import configure_output
from _cli import help_guard
import sys
import html as _html

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import view  # переиспользуем load_canon (рёбра related/[[links]])

configure_output()
ROOT = os.environ.get("COLLAB_ROOT") or os.path.dirname(HERE)

TYPE_SINGULAR = {"tasks": "task", "decisions": "decision", "questions": "question",
                 "topics": "topic", "docs": "doc"}
CARD_W = 34  # ширина карточки; КЛАМП (карточка не «раздувает» сетку — урок scene.Apply per-op)


def _type_of(path):
    return TYPE_SINGULAR.get(path.split("/", 1)[0], path.split("/", 1)[0])


def _title(body, fid):
    for ln in body.splitlines():
        s = ln.strip()
        if s.startswith("#"):
            return (s.lstrip("# ").strip() or fid)[:60]
    return fid


def _gist(body):
    """Первая содержательная строка (>12 симв., без #/>) — «меню»-уровень карточки."""
    for ln in body.splitlines():
        s = ln.strip().lstrip("#>").strip()
        if len(s) > 12:
            return s[:120]
    return ""


def bfs_levels(canon, seed, depth):
    """[(id, level)] в ДЕТЕРМ. порядке (BFS, соседи отсортированы) — Y-ось = level. Зеркало R1-фикса view."""
    if seed not in canon:
        return []
    seen = {seed}
    out = [(seed, 0)]
    frontier = [seed]
    for lvl in range(1, max(0, depth) + 1):
        nxt = []
        for nid in frontier:
            for ln in sorted(canon.get(nid, {}).get("links", ())):
                if ln in canon and ln not in seen:
                    seen.add(ln); nxt.append(ln); out.append((ln, lvl))
        frontier = nxt
        if not frontier:
            break
    return out


def build_cells(canon, seed, depth):
    """Срез канона → упорядоченный список карточек {id,type,depth,title,gist,body,links}."""
    cells = []
    for fid, lvl in bfs_levels(canon, seed, depth):
        n = canon[fid]
        cells.append({
            "id": fid, "type": _type_of(n["path"]), "path": n["path"], "depth": lvl,
            "title": _title(n["body"], fid), "gist": _gist(n["body"]),
            "body": n["body"].strip(),
            "links": sorted(l for l in n.get("links", ()) if l in canon),
        })
    return cells


def _wrap(text, w):
    """Детерминированный жадный перенос по словам в ширину w (длинное слово — режется)."""
    out, cur = [], ""
    for word in text.split():
        if not cur:
            cur = word
        elif len(cur) + 1 + len(word) <= w:
            cur += " " + word
        else:
            out.append(cur); cur = word
        while len(cur) > w:
            out.append(cur[:w]); cur = cur[w:]
    if cur:
        out.append(cur)
    return out or [""]


def render_card(cell, L, w=CARD_W):
    """Карточка как список строк РОВНО ширины w (бокс). L0 шапка · L1 +gist+links · L2 +тело."""
    inner = w - 2
    lines = [("▦ %s %s" % (cell["type"], cell["id"]))[:inner]]
    if L >= 1 and cell["gist"]:
        lines.append("")
        lines += _wrap(cell["gist"], inner)
    if L >= 2 and cell["body"]:
        lines.append("·" * inner)
        for bl in cell["body"].splitlines():
            lines += _wrap(bl, inner) if bl.strip() else [""]
    if L >= 1 and cell["links"]:
        lines.append(("→ " + ", ".join(cell["links"]))[:inner])
    top = "┌" + "─" * inner + "┐"
    bot = "└" + "─" * inner + "┘"
    boxed = ["│" + ln.ljust(inner)[:inner] + "│" for ln in lines]
    return [top] + boxed + [bot]


def _stack(cards):
    """Карточки (списки строк) бок о бок → строки (короткие добиваются пробелами)."""
    if not cards:
        return []
    h = max(len(c) for c in cards)
    cards = [c + [" " * len(c[0])] * (h - len(c)) for c in cards]
    return ["  ".join(c[i] for c in cards) for i in range(h)]


def _render(cells, level_of, cols):
    """Бэнды по depth (Y), внутри бэнда — строки по cols (X). level_of: id→L."""
    out, by_depth = [], {}
    for c in cells:
        by_depth.setdefault(c["depth"], []).append(c)
    for d in sorted(by_depth):
        out.append("── уровень %d %s" % (d, "(seed)" if d == 0 else "(детальнее)"))
        band = by_depth[d]
        for i in range(0, len(band), cols):
            out += _stack([render_card(c, level_of(c["id"])) for c in band[i:i + cols]])
            out.append("")
    return "\n".join(out)


def render_ansi(cells, L, cols):
    return _render(cells, lambda _id: L, cols)


def diffuse(cells, cols, steps):
    """Кадры раскрытия: доля тел на L2 растёт alpha=i/(steps-1) по ПОРЯДКУ ГЛУБИНЫ (общее→частное)."""
    steps = max(2, steps)
    n = len(cells)
    frames = []
    for i in range(steps):
        alpha = i / (steps - 1)
        k = round(alpha * n)
        lv = {c["id"]: (2 if j < k else 1) for j, c in enumerate(cells)}
        frames.append("КАДР %d/%d  (тел раскрыто %d/%d, alpha=%.2f)\n%s" % (
            i + 1, steps, k, n, alpha, _render(cells, lambda _id: lv[_id], cols)))
    return frames


def render_html(cells, cols):
    esc = _html.escape
    parts = ['<!doctype html><meta charset="utf-8"><title>textscene</title>',
             '<style>body{background:#0b0f14;color:#cdd6e0;font:14px/1.55 ui-monospace,monospace;margin:1rem}'
             '.grid{display:grid;grid-template-columns:repeat(%d,minmax(0,1fr));gap:.55rem}'
             'details{border:1px solid #2a3340;border-radius:6px;padding:.4rem .6rem;background:#121821}'
             'summary{cursor:pointer;color:#7fd1ff}pre{white-space:pre-wrap;margin:.4rem 0 0;color:#aab6c4}'
             'small{color:#5f6f80}</style>' % max(1, cols),
             '<h2>textscene · abstraction-view</h2><div class="grid">']
    for c in cells:
        gist = (" — " + esc(c["gist"])) if c["gist"] else ""
        links = (" · → " + esc(", ".join(c["links"]))) if c["links"] else ""
        parts.append('<details><summary>▦ %s <b>%s</b>%s</summary><pre>%s</pre>'
                     '<small>%s%s · depth %d</small></details>' % (
                         esc(c["type"]), esc(c["id"]), gist, esc(c["body"]), esc(c["path"]), links, c["depth"]))
    parts.append('</div>')
    return "\n".join(parts)


def _opt_int(argv, flag, default):
    if flag in argv:
        i = argv.index(flag)
        if i + 1 < len(argv):
            try:
                return int(argv[i + 1])
            except ValueError:
                pass
    return default


def main(argv):
    help_guard(__doc__, argv)
    args = [a for a in argv if not a.startswith("--")]
    if not args:
        print("text_scene: нужен seed-id. Пример: text_scene.py D-030 --depth 2 --cols 3"); return 2
    seed = args[0]
    depth = _opt_int(argv, "--depth", 2)
    cols = _opt_int(argv, "--cols", 3)
    L = _opt_int(argv, "--level", 1)
    steps = _opt_int(argv, "--steps", 0)
    canon = view.load_canon()
    cells = build_cells(canon, seed, depth)
    if not cells:
        print("text_scene: seed '%s' не найден в каноне" % seed); return 2
    if "--html" in argv:
        print(render_html(cells, cols)); return 0
    if steps:
        for fr in diffuse(cells, cols, steps):
            print(fr); print()
        return 0
    print("=== textscene · seed=%s · depth=%d · %d карточек · L%d ===" % (seed, depth, len(cells), L))
    print(render_ansi(cells, L, cols))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
