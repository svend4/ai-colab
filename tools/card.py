"""card.py — универсальная КАРТОЧКА-визитка: фрактальная единица коммуникации (средний слой).

Обобщает decision_menu в общий стандарт. Карточка = top(тип·название·суть·теги) + середина
(метаданные; СЕМАНТИЧЕСКИЕ выделены) + дети(вложенные карточки — фрактал) + основание(detail_ref).
Между кодом («поваренная книга» внизу — все детали) и агентом/человеком (меню вверху — суть).
Стандарт подачи/обработки/коммуникации здесь-и-сейчас: код↔агент↔человек.

Типы (одна форма, разные поля): menu · decision · recipe · block · review · complaint · proposal · process.

CLI:
    python tools/card.py card.json                    # отрендерить карточку/дерево
    python tools/card.py proposals.json --from-proposals   # workflow-proposals → меню-карточка
    python tools/card.py - [--toc]                    # из stdin (--toc = только каталог-верхушки)
"""
import os
from _ioutil import configure_output
import sys
import json

configure_output()

# Тип → (человеко-метка, упорядоченные поля середины)
CARD_TYPES = {
    "menu":      ("Меню", []),
    "decision":  ("Решение", ["what", "pros", "cons", "means", "leads_to", "responsibility"]),
    "recipe":    ("Рецепт", ["what", "when", "steps", "pitfalls"]),
    "block":     ("Блок", ["what", "cluster", "verdict"]),
    "review":    ("Отзыв", ["what", "liked", "issues"]),
    "complaint": ("Жалоба", ["what", "impact", "wanted"]),
    "proposal":  ("Предложение", ["what", "value", "cost", "means", "leads_to"]),
    "process":   ("Процесс", ["what", "state", "next", "blockers"]),
}
SEMANTIC = {"means", "leads_to", "responsibility", "value"}  # семантические поля — выделяются
FIELD_LABEL = {
    "what": "Что", "pros": "Плюсы", "cons": "Минусы / риски", "means": "Что значит",
    "leads_to": "К чему ведёт", "responsibility": "Ответственность", "when": "Когда",
    "steps": "Шаги", "pitfalls": "Подводные камни", "cluster": "Кластер", "verdict": "Вердикт",
    "liked": "Понравилось", "issues": "Проблемы", "impact": "Влияние", "wanted": "Хотелось бы",
    "value": "Ценность", "cost": "Цена", "state": "Состояние", "next": "Дальше", "blockers": "Блокеры",
}


def _tags(card):
    t = card.get("tags", {}) or {}
    parts = [t.get("risk"), t.get("effort"), t.get("reversibility")]
    return "·".join(p for p in parts if p)


def _render_value(v):
    if isinstance(v, list):
        return "\n" + "\n".join("  - %s" % x for x in v) if v else " —"
    return " " + str(v)


def render_catalog(card):
    """Верхушка-каталог по детям (фрактал: оглавление вложенных карточек)."""
    kids = card.get("children", [])
    if not kids:
        return ""
    out = ["| ключ | тип | название | суть | теги |", "|---|---|---|---|---|"]
    for i, k in enumerate(kids):
        key = k.get("key") or chr(65 + i)
        star = " ⭐" if k.get("recommended") else ""
        label = CARD_TYPES.get(k.get("type", "decision"), ("?", []))[0]
        out.append("| **%s**%s | %s | %s | %s | %s |" % (
            key, star, label, k.get("title", ""), k.get("gist", ""), _tags(k) or "—"))
    return "\n".join(out)


def render_card(card, level=2, key=None):
    """Фрактальный рендер: top → середина(поля) → дети(рекурсия) → основание."""
    ctype = card.get("type", "decision")
    label, fields = CARD_TYPES.get(ctype, ("Карточка", ["what"]))
    head = "#" * min(level, 6)
    kpfx = ("%s — " % key) if key else ""
    star = " ⭐" if card.get("recommended") else ""
    tags = _tags(card)
    out = ["%s %s%s [%s]%s" % (head, kpfx, card.get("title", ""), label, star)]
    if card.get("gist"):
        out.append("_%s_" % card["gist"])
    if tags:
        out.append("`%s`" % tags + (" · scope: %s" % card["tags"]["scope"] if card.get("tags", {}).get("scope") else ""))
    out.append("")
    cf = card.get("fields", {}) or {}
    for f in fields:
        if f in cf:
            mark = "🔹 " if f in SEMANTIC else ""
            out.append("**%s%s:**%s" % (mark, FIELD_LABEL.get(f, f), _render_value(cf[f])))
    # фрактал: каталог + дети
    kids = card.get("children", [])
    if kids:
        out += ["", render_catalog(card), ""]
        for i, k in enumerate(kids):
            out.append(render_card(k, level=level + 1, key=k.get("key") or chr(65 + i)))
            out.append("")
    if card.get("detail_ref"):
        out.append("→ основание (детали): `%s`" % card["detail_ref"])
    if card.get("recommendation"):
        out += ["", "**Рекомендация:** " + card["recommendation"]]
    if card.get("how_to_choose"):
        out += ["", "**Как выбрать:** " + card["how_to_choose"]]
    return "\n".join(out)


def from_proposals(data):
    """workflow-выход {proposals:[...]} ИЛИ [...] → меню-карточка decision/proposal-карточек."""
    props = data.get("proposals", data) if isinstance(data, dict) else data
    children = []
    for i, p in enumerate(props or []):
        children.append({
            "type": "proposal" if p.get("kind") == "block" else "decision",
            "key": chr(65 + i), "title": p.get("title", p.get("target", "?"))[:70],
            "gist": p.get("recommendation", ""),
            "fields": {"what": p.get("concrete_action", p.get("detail", ""))[:300],
                       "means": p.get("rationale", "")[:300],
                       "responsibility": p.get("premise_note", p.get("apply_note", ""))[:300]},
            "detail_ref": ", ".join(p.get("files", [])) if p.get("files") else "",
        })
    return {"type": "menu", "title": "Меню из proposals", "children": children}


def main(argv):
    args = list(argv)
    toc = "--toc" in args
    from_prop = "--from-proposals" in args
    args = [a for a in args if not a.startswith("--")]
    src = args[0] if args else "-"
    try:
        data = json.load(sys.stdin) if src == "-" else json.load(open(src, encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        print("card: не прочитать (%s)" % e)
        return 2
    card = from_proposals(data) if from_prop else data
    if not isinstance(card, dict):
        print("card: ожидаю объект-карточку {type,title,...}")
        return 2
    if toc:
        print(render_catalog(card) or "(нет детей для каталога)")
    else:
        print(render_card(card, level=1))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
