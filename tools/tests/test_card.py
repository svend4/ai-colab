"""
# ==========================================
# [FILE ID CARD]
# ID: tools.tests.test_card
# TYPE: active-script
# DOMAIN: core
# DEPTH_LEVEL: 1
# SUMMARY: Скрипт test_card.py. Описание сгенерировано автоматически.
# ==========================================
"""
"""Тест card.py — фрактальная карточка-визитка. Типы, вложенность, семантика, from_proposals."""
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
import card

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

MENU = {
    "type": "menu", "title": "Меню-тест", "gist": "контекст",
    "children": [
        {"type": "decision", "key": "A", "title": "Реш А", "gist": "суть А", "recommended": True,
         "tags": {"risk": "low", "effort": "S", "reversibility": "easy"},
         "fields": {"what": "что", "pros": ["п1", "п2"], "cons": ["м1"],
                    "means": "значит А", "leads_to": "ведёт А", "responsibility": "отв А"},
         "detail_ref": "docs/x.md"},
        {"type": "block", "key": "B", "title": "Блок Б", "gist": "кластер",
         "fields": {"what": "что Б", "cluster": "validate+friction", "verdict": "BLOCK-OK"}},
    ],
    "recommendation": "А", "how_to_choose": "назови ключ",
}


def main():
    fails = []
    full = card.render_card(MENU, level=1)
    for n in ("[Меню]", "[Решение]", "[Блок]", "Что значит:", "К чему ведёт:", "Ответственность:",
              "значит А", "BLOCK-OK", "Рекомендация", "Как выбрать", "🔹", "⭐"):
        if n not in full:
            fails.append("рендер без %r" % n)
    # фрактал: каталог детей присутствует
    cat = card.render_catalog(MENU)
    for n in ("Реш А", "Блок Б", "low·S·easy"):
        if n not in cat:
            fails.append("каталог без %r" % n)
    # from_proposals: workflow-выход → меню
    mc = card.from_proposals({"proposals": [
        {"title": "T1", "recommendation": "do", "concrete_action": "act", "rationale": "why",
         "premise_note": "prem", "kind": "decision"}]})
    if mc.get("type") != "menu" or len(mc.get("children", [])) != 1:
        fails.append("from_proposals не дал меню с 1 ребёнком")
    if card.from_proposals([{"title": "x", "kind": "block"}])["children"][0]["type"] != "proposal":
        fails.append("from_proposals: kind=block не стал proposal-карточкой")
    # все типы валидны (один контракт)
    for t in card.CARD_TYPES:
        r = card.render_card({"type": t, "title": "t", "fields": {}}, level=2)
        if "[%s]" % card.CARD_TYPES[t][0] not in r:
            fails.append("тип %r не рендерит метку" % t)

    if fails:
        print("FAIL test_card:")
        for f in fails:
            print("  -", f)
        sys.exit(1)
    print("OK test_card: 8 типов + фрактал(каталог+дети) + семантика + from_proposals")


if __name__ == "__main__":
    main()
