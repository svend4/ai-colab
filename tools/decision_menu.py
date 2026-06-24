"""
# ==========================================
# [FILE ID CARD]
# ID: tools.decision_menu
# TYPE: active-script
# DOMAIN: core
# DEPTH_LEVEL: 1
# SUMMARY: Скрипт decision_menu.py. Описание сгенерировано автоматически.
# ==========================================
"""
"""decision_menu.py — рендерер «меню решений» (средний слой пирамиды подачи людям).

Стандарт: docs/decision-menu-standard.md. Переводит структурный выход (proposals агентов /
варианты оркестратора) в человеко-меню: каталог-верхушка (суть+теги) + карточки-середина
(что · плюсы · минусы · ЧТО ЗНАЧИТ · К ЧЕМУ ВЕДЁТ · ОТВЕТСТВЕННОСТЬ) + рекомендация. Не «2 слова»
и не весь агентский детейл — середина, из которой человек выбирает.

CLI:
    python tools/decision_menu.py menu.json            # полное меню
    python tools/decision_menu.py menu.json --toc      # только каталог-верхушка
    python tools/decision_menu.py -                    # читать меню из stdin
"""
import os
from _ioutil import configure_output
import sys
import json

configure_output()


def _tags(o):
    t = o.get("tags", {}) or {}
    parts = [t.get("risk"), t.get("effort"), t.get("reversibility")]
    return "·".join(p for p in parts if p) or "—"


def render_toc(menu):
    """Верхушка-каталог: одна строка на вариант."""
    out = ["## Меню — каталог", "", "| ключ | вариант | суть | риск·усилие·обр. |",
           "|---|---|---|---|"]
    for o in menu.get("options", []):
        star = " ⭐" if o.get("recommended") else ""
        out.append("| **%s**%s | %s | %s | %s |" % (
            o.get("key", "?"), star, o.get("title", ""), o.get("gist", ""), _tags(o)))
    return "\n".join(out)


def _bullets(items):
    items = items or []
    if isinstance(items, str):
        items = [items]
    return "\n".join("  - %s" % x for x in items) if items else "  - —"


def render_card(o):
    """Середина: карточка варианта с метаданными (семантические выделены)."""
    star = " ⭐ (рекомендуется)" if o.get("recommended") else ""
    lines = [
        "### %s — %s%s" % (o.get("key", "?"), o.get("title", ""), star),
        "_%s_" % _tags(o) + ("  ·  scope: %s" % o["tags"]["scope"] if o.get("tags", {}).get("scope") else ""),
        "",
        "**Что:** %s" % o.get("what", "—"),
        "",
        "**Плюсы:**", _bullets(o.get("pros")),
        "**Минусы / риски:**", _bullets(o.get("cons")),
        "",
        "**Что значит:** %s" % o.get("means", "—"),
        "**К чему ведёт:** %s" % o.get("leads_to", "—"),
        "**Ответственность:** %s" % o.get("responsibility", "—"),
    ]
    if o.get("detail_ref"):
        lines.append("→ детали (основание): `%s`" % o["detail_ref"])
    return "\n".join(lines)


def render_full(menu):
    out = []
    if menu.get("title"):
        out.append("# %s" % menu["title"])
    if menu.get("context"):
        out += ["", menu["context"]]
    out += ["", render_toc(menu), "", "## Варианты — карточки", ""]
    for o in menu.get("options", []):
        out.append(render_card(o))
        out.append("")
    if menu.get("recommendation"):
        out += ["## Рекомендация", "", menu["recommendation"], ""]
    out += ["## Как выбрать", "",
            menu.get("how_to_choose",
                     "Назовите ключ (A/B/…) — или комбинацию; «другое» — свой вариант текстом.")]
    return "\n".join(out)


def _load(arg):
    if arg == "-" or arg is None:
        return json.load(sys.stdin)
    with open(arg, encoding="utf-8") as f:
        return json.load(f)


def main(argv):
    args = list(argv)
    toc_only = "--toc" in args
    args = [a for a in args if not a.startswith("--")]
    src = args[0] if args else "-"
    try:
        menu = _load(src)
    except (OSError, json.JSONDecodeError) as e:
        print("decision_menu: не прочитать меню (%s)" % e)
        return 2
    if not isinstance(menu, dict) or "options" not in menu:
        print("decision_menu: ожидаю {title, options:[...]}")
        return 2
    print(render_toc(menu) if toc_only else render_full(menu))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
