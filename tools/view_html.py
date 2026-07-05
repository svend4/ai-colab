# ==========================================
# [FILE ID CARD]
# ID: tools.view_html
# TYPE: active-script
# DOMAIN: core.retrieval
# DEPTH_LEVEL: 1
# SUMMARY: компиляция среза канона в самодостаточный <details>-каскад HTML (progressive disclosure).
# ==========================================
"""view_html.py — компиляция среза канона в самодостаточный <details>-каскад HTML (progressive disclosure).

Реализует исходную тему беседы про .inf (U6–U7: «меню заголовки → клик → детали») и P17 (компиляция в
<details>-HTML, открывается где угодно — «shareit hosting» один файл, без сервера и без опасного JS,
только нативная сворачиваемость). Над НАШИМ каноном: берёт срез от view.py (обход related/[[ссылки]]),
рендерит каждый блок как свёрнутый <details><summary>id — визитка</summary>тело + ссылки</details>.

CLI:
  python tools/view_html.py <seed-id> --depth 2 [--out view.html] [--open]
"""
import os
from _ioutil import configure_output
from _cli import help_guard
import sys
import html as _html
import view as _view

configure_output()
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.environ.get("COLLAB_ROOT") or os.path.dirname(HERE)

_CSS = ("body{font:15px/1.5 system-ui,sans-serif;max-width:50rem;margin:2rem auto;padding:0 1rem;"
        "background:#0f1115;color:#d8dee9}summary{cursor:pointer;font-weight:600;color:#88c0d0}"
        "details{border-left:2px solid #3b4252;margin:.4rem 0;padding:.2rem .8rem}"
        "pre{white-space:pre-wrap;color:#e5e9f0;font:13px/1.5 ui-monospace,monospace}"
        "a{color:#a3be8c}.id{color:#5e81ac;font-weight:700}.lnk{font-size:12px;color:#7a8499}")


def compile_html(canon, ids, title="view"):
    """Срез канона → самодостаточный HTML с <details>-каскадом (свёрнуто по умолчанию, raw plain-text внутри)."""
    parts = ["<!doctype html><html><head><meta charset='utf-8'>",
             "<meta name='viewport' content='width=device-width,initial-scale=1'>",
             "<title>%s</title><style>%s</style></head><body>" % (_html.escape(title), _CSS),
             "<h1>%s</h1><p class='lnk'>%d блоков · progressive disclosure: клик по заголовку = раскрыть</p>"
             % (_html.escape(title), len(ids))]
    have = set(ids)
    for i in ids:
        n = canon.get(i)
        if not n:
            continue
        gist = _view._gist(n["body"]).lstrip("— ").strip() or n["path"]
        links = [l for l in sorted(n["links"]) if l in have]
        lnk = (" <span class='lnk'>→ " + ", ".join("<a href='#%s'>%s</a>" % (l, l) for l in links) + "</span>") if links else ""
        parts.append(
            "<details id='%s'><summary><span class='id'>%s</span> — %s</summary>"
            "<p class='lnk'>%s%s</p><pre>%s</pre></details>" % (
                _html.escape(i), _html.escape(i), _html.escape(gist[:90]),
                _html.escape(n["path"]), lnk, _html.escape(n["body"].strip())))
    parts.append("</body></html>")
    return "\n".join(parts)


def main(argv):
    help_guard(__doc__, argv)
    args = [a for a in argv if not a.startswith("--")]
    if not args:
        print("view_html: нужен seed-id. Пример: view_html.py D-030 --depth 2 --out view.html"); return 2
    seed = args[0]
    depth = _opt_int(argv, "--depth", 2)
    canon = _view.load_canon()
    if seed not in canon:
        cand = [i for i in canon if seed.lower() in i.lower()][:5]
        print("view_html: seed '%s' не найден. Похожие: %s" % (seed, ", ".join(cand) or "—")); return 2
    ids = _view.slice_ids(canon, seed, depth)
    doc = compile_html(canon, ids, "view: %s (depth %d)" % (seed, depth))
    out = None
    if "--out" in argv:
        i = argv.index("--out")
        out = argv[i + 1] if i + 1 < len(argv) else None
    if not out:
        out = os.path.join(ROOT, "views", "%s.html" % seed)
    out = out if os.path.isabs(out) else os.path.join(ROOT, out)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    open(out, "w", encoding="utf-8", newline="\n").write(doc)
    print("=== VIEW-HTML: seed=%s depth=%d · %d блоков → %s ===" % (
        seed, depth, len(ids), os.path.relpath(out, ROOT).replace("\\", "/")))
    print("  открыть где угодно (самодостаточный, свёрнутый <details>-каскад, без сервера)")
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
