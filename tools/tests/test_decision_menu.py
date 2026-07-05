"""
# ==========================================
# [FILE ID CARD]
# ID: tools.tests.test_decision_menu
# TYPE: active-script
# DOMAIN: core
# DEPTH_LEVEL: 1
# SUMMARY: Скрипт test_decision_menu.py. Описание сгенерировано автоматически.
# ==========================================
"""
"""Тест decision_menu.py — рендерер меню решений. Проверяет каталог + карточки + семантические поля."""
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
import decision_menu as dm

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

MENU = {
    "title": "Тест-меню",
    "context": "Ситуация для теста.",
    "options": [
        {"key": "A", "title": "Вариант А", "gist": "суть А",
         "tags": {"risk": "low", "effort": "S", "reversibility": "easy", "scope": "tools/"},
         "what": "что А", "pros": ["плюс1", "плюс2"], "cons": ["минус1"],
         "means": "значение А", "leads_to": "ведёт А", "responsibility": "ответственность А",
         "detail_ref": "docs/x.md", "recommended": True},
        {"key": "B", "title": "Вариант Б", "gist": "суть Б",
         "tags": {"risk": "high", "effort": "L", "reversibility": "irreversible"},
         "what": "что Б", "pros": ["плюс"], "cons": ["минус"],
         "means": "значение Б", "leads_to": "ведёт Б", "responsibility": "ответственность Б"},
    ],
    "recommendation": "рекомендую А",
}


def main():
    fails = []
    toc = dm.render_toc(MENU)
    for needle in ("каталог", "Вариант А", "суть Б", "low·S·easy", "⭐"):
        if needle not in toc:
            fails.append("каталог без %r" % needle)

    full = dm.render_full(MENU)
    # семантические поля ОБЯЗАНЫ присутствовать (ядро стандарта)
    for needle in ("Что значит:", "К чему ведёт:", "Ответственность:",
                   "Плюсы:", "Минусы", "значение А", "ведёт Б", "Рекомендация", "Как выбрать"):
        if needle not in full:
            fails.append("меню без %r" % needle)
    # рекомендованный помечен
    if "рекомендуется" not in full:
        fails.append("recommended не помечен в карточке")
    # detail_ref ведёт в основание
    if "docs/x.md" not in full:
        fails.append("detail_ref (основание) не отрендерен")

    if fails:
        print("FAIL test_decision_menu:")
        for f in fails:
            print("  -", f)
        sys.exit(1)
    print("OK test_decision_menu: каталог + карточки + семантические поля (что-значит/ведёт/ответственность)")


if __name__ == "__main__":
    main()
