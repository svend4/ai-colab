"""
# ==========================================
# [FILE ID CARD]
# ID: tools.tests.test_decision_propagation
# TYPE: active-script
# DOMAIN: core
# DEPTH_LEVEL: 1
# SUMMARY: Скрипт test_decision_propagation.py. Описание сгенерировано автоматически.
# ==========================================
"""
"""Тест decision_propagation.py — детектор «решение не дошло до потребителей»."""
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
import decision_propagation as dp

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass


def main():
    fails = []
    # _refs извлекает D-/T-/Q- id
    r = dp._refs("Решение D-020 переформулировало T-020 и снимает Q-009; см. D-021.")
    for need in ("D-020", "T-020", "Q-009", "D-021"):
        if need not in r:
            fails.append("_refs не нашёл %s" % need)
    if "D-99" in r or "T-9999" in r:
        fails.append("_refs ловит неверный формат")

    # _tokens: distinctive (svend4) да, common-проза нет
    t = dp._tokens("svend4 external decision proposed промежуточный")
    if "svend4" not in t:
        fails.append("_tokens потерял svend4")
    if "decision" in t or "proposed" in t:
        fails.append("_tokens не отфильтровал common")

    # analyze() структура + содержимое
    data = dp.analyze()
    for k in ("back_ref_gaps", "stale_blockers", "n_decisions"):
        if k not in data:
            fails.append("analyze без %r" % k)
    if not isinstance(data.get("back_ref_gaps"), list) or not isinstance(data.get("stale_blockers"), list):
        fails.append("gaps/blockers не списки")
    if data.get("n_decisions", 0) <= 0:
        fails.append("0 решений — analyze пуст")
    # каждый gap несёт decision+consumer
    for g in data["back_ref_gaps"][:5]:
        if "decision" not in g or "consumer" not in g:
            fails.append("back_ref_gap без decision/consumer")
            break
    # РЕГРЕССИЯ: Q-009 пропагирован (цитирует D-020) → НЕ в stale_blockers
    q009_flagged = any(b.get("consumer") == "Q-009" for b in data["stale_blockers"])
    if q009_flagged:
        fails.append("Q-009 всё ещё во stale_blockers — пропагация D-020 не отражена (регрессия)")

    if fails:
        print("FAIL test_decision_propagation:")
        for f in fails:
            print("  -", f)
        sys.exit(1)
    print("OK test_decision_propagation: _refs + _tokens + analyze(структура) + Q-009-регрессия (%d gaps, %d blockers)"
          % (len(data["back_ref_gaps"]), len(data["stale_blockers"])))


if __name__ == "__main__":
    main()
