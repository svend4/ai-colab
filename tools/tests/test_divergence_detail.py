"""
# ==========================================
# [FILE ID CARD]
# ID: tools.test_divergence_detail
# TYPE: active-script
# DOMAIN: core
# DEPTH_LEVEL: 1
# SUMMARY: Скрипт test_divergence_detail.py. Описание сгенерировано автоматически.
# ==========================================
"""
"""Тест divergence_detail.py — детализация перед консенсусом (мнимый/подлинный/pending)."""
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
import tempfile

os.environ.setdefault("PYTHONUTF8", "1")
HERE = _TOOLS_DIR  # tools/ — тест перенесён в tools/tests/ (C14)
sys.path.insert(0, HERE)
import divergence_detail as dd

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

DOC = """# Детализация расхождений темы X

## строгий гейт на каждое изменение -vs- лёгкий гейт без трения
- условия: строгий нужен при общем дереве; лёгкий — при изолированных worktree. Разные ниши.
- evidence: оба подтверждены практикой в своих режимах
- риск: строгий принимает риск трения; лёгкий — риск коллизий
- охват: про разные режимы работы
- verdict: мнимый

## консенсус по большинству -vs- консенсус по смыслу
- условия: одинаковые — оба про один режим
- evidence: смысл подтверждён, большинство опровергнуто red-team
- риск: большинство рискует правдоподобной ошибкой
- охват: одно и то же
- verdict: подлинный

## seal по хешу -vs- seal по времени
- условия: пока не разобрано
- verdict: open
"""


def main():
    fails = []

    # facets: 4 подвопроса, покрывают условия/evidence/риск/охват
    fs = dd.facets("A", "B")
    if len(fs) != 4:
        fails.append("facets должен дать 4 подвопроса, дал %d" % len(fs))
    joined = " ".join(fs).lower()
    for k in ("услови", "evidence", "риск", "охват"):
        if k not in joined:
            fails.append("facets не покрывает фасет: %s" % k)

    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "x.md")
        open(p, "w", encoding="utf-8", newline="\n").write(DOC)
        recs = dd.parse_records(p)
        if len(recs) != 3:
            fails.append("ожидалось 3 записи, получено %d" % len(recs))

        g = dd.gate(recs)
        if len(g["scoped"]) != 1:
            fails.append("мнимый→scoped должен быть 1: %s" % len(g["scoped"]))
        elif not g["scoped"][0]["условия"]:
            fails.append("мнимый обязан нести фасет условия (DD-4)")
        if len(g["to_resolve"]) != 1:
            fails.append("подлинный→разрешение должен быть 1")
        if len(g["pending"]) != 1:
            fails.append("open→pending должен быть 1")
        # pending: не все фасеты заполнены
        if dd._filled(g["pending"][0]) >= 4:
            fails.append("pending-запись не должна быть полностью детализирована")
        # запись A -vs- B разобрана на две стороны
        if not (g["scoped"][0]["a"] and g["scoped"][0]["b"]):
            fails.append("пара A -vs- B не разобрана на стороны")

    if fails:
        print("FAIL test_divergence_detail:")
        for f in fails:
            print("  -", f)
        sys.exit(1)
    print("OK test_divergence_detail: facets(4) · мнимый→scoped · подлинный→разрешение · open→pending(DD-1)")


if __name__ == "__main__":
    main()
