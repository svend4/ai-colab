"""Тест seq_merge.py — 3-way построчный мёрж тела (diff3)."""
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
import seq_merge as sm

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass


def main():
    fails = []

    # непересекающиеся правки: ours меняет строку 2, theirs строку 3 → ОБЕ сливаются, нет конфликта
    base = "строка1\nстрока2\nстрока3"
    ours = "строка1\nOURS2\nстрока3"
    theirs = "строка1\nстрока2\nTHEIRS3"
    text, conf = sm.merge_lines(base, ours, theirs)
    if conf:
        fails.append("непересекающиеся правки не должны конфликтовать: %r" % text)
    if "OURS2" not in text or "THEIRS3" not in text:
        fails.append("обе непересекающиеся правки должны быть в результате: %r" % text)

    # пересечение: оба меняют строку 2 по-разному → конфликт ТОЛЬКО на строке 2
    o2 = "строка1\nO-версия\nстрока3"
    t2 = "строка1\nT-версия\nстрока3"
    text2, conf2 = sm.merge_lines(base, o2, t2)
    if not conf2:
        fails.append("разные правки одной строки → конфликт")
    if "O-версия" not in text2 or "T-версия" not in text2 or "<<<<<<<" not in text2:
        fails.append("обе версии + маркеры на пересечении: %r" % text2)
    if "строка1" not in text2 or "строка3" not in text2:
        fails.append("непересекающиеся строки 1 и 3 должны остаться чистыми вне маркеров")
    # строка1 и строка3 не должны быть внутри маркеров (конфликт локализован)
    between = text2.split("<<<<<<<")[1].split(">>>>>>>")[0]
    if "строка1" in between or "строка3" in between:
        fails.append("конфликт не локализован — захватил неизменные строки")

    # одинаковая правка обеих сторон → нет конфликта
    text3, conf3 = sm.merge_lines(base, ours, ours)
    if conf3 or "OURS2" not in text3:
        fails.append("идентичная правка обеих сторон → без конфликта")

    # добавление строки одной стороной → сливается
    text4, conf4 = sm.merge_lines(base, base + "\nновая ours", base)
    if conf4 or "новая ours" not in text4:
        fails.append("добавление строки ours должно слиться: %r" % text4)

    if fails:
        print("FAIL test_seq_merge:")
        for f in fails:
            print("  -", f)
        sys.exit(1)
    print("OK test_seq_merge: непересекающиеся→чисто · пересечение→локальные маркеры · идентичные→ок · добавление→ок")


if __name__ == "__main__":
    main()
