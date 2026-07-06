"""
# ==========================================
# [FILE ID CARD]
# ID: tools.test_git_reconcile
# TYPE: active-script
# DOMAIN: core
# DEPTH_LEVEL: 1
# SUMMARY: Скрипт test_git_reconcile.py. Описание сгенерировано автоматически.
# ==========================================
"""
"""Тест git_reconcile.py — merge-driver интерфейс (base/ours/theirs → field-merge в ours, exit-код)."""
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
import time

os.environ.setdefault("PYTHONUTF8", "1")
HERE = _TOOLS_DIR  # tools/ — тест перенесён в tools/tests/ (C14)
sys.path.insert(0, HERE)
import git_reconcile as gr

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass


def _w(d, name, related, status, body):
    p = os.path.join(d, name)
    open(p, "w", encoding="utf-8", newline="\n").write(
        "---\nid: x\nstatus: %s\nrelated: [%s]\n---\n%s\n" % (status, ", ".join(related), body))
    return p


def main():
    fails = []
    d = os.path.join(os.path.dirname(HERE), "tmp-work", "git_reconcile_test_%d_%d" % (os.getpid(), time.time_ns()))
    os.makedirs(d, exist_ok=True)
    if True:
        # чистый случай: ours добавил c, theirs добавил d, тело тронул только theirs
        base = _w(d, "base.md", ["a", "b"], "proposed", "базовое тело")
        ours = _w(d, "ours.md", ["a", "b", "c"], "accepted", "базовое тело")
        theirs = _w(d, "theirs.md", ["a", "b", "d"], "proposed", "тело theirs")
        conflicts = gr.reconcile_files(base, ours, theirs)
        if conflicts:
            fails.append("чистый случай не должен дать конфликтов: %s" % conflicts)
        merged = open(ours, encoding="utf-8").read()
        if not ("c" in merged and "d" in merged):
            fails.append("related должно слиться union {a,b,c,d} в ours: %s" % merged[:80])
        if "accepted" not in merged:
            fails.append("status accepted (ours) должен сохраниться")
        if "тело theirs" not in merged:
            fails.append("тело theirs (только theirs тронул) должно попасть")
        if gr.main([base, ours, theirs]) != 0:
            fails.append("exit-код чистого слияния должен быть 0")

        # конфликт тела: оба тронули по-разному → exit 1 + маркеры
        base2 = _w(d, "b2.md", ["a"], "proposed", "база")
        o2 = _w(d, "o2.md", ["a"], "proposed", "версия ours")
        t2 = _w(d, "t2.md", ["a"], "proposed", "версия theirs")
        rc = gr.main([base2, o2, t2])
        if rc != 1:
            fails.append("конфликт тела должен дать exit 1: %s" % rc)
        m2 = open(o2, encoding="utf-8").read()
        if "версия ours" not in m2 or "версия theirs" not in m2 or "<<<<<<<" not in m2:
            fails.append("обе версии тела + маркеры должны быть в ours (не потеряно): %s" % m2[:90])

        # size-guard (C33): theirs ЗАКОННО срезал крупное тело (ours не трогал) —
        # safe_write-гвард не роняет драйвер, а даёт конфликт на доразбор + файл записан
        big = "\n".join("строка %d" % i for i in range(40))
        b3 = _w(d, "b3.md", ["a"], "proposed", big)
        o3 = _w(d, "o3.md", ["a"], "proposed", big)
        t3 = _w(d, "t3.md", ["a"], "proposed", "коротко")
        conflicts3 = gr.reconcile_files(b3, o3, t3)
        m3 = open(o3, encoding="utf-8").read()
        if "коротко" not in m3:
            fails.append("слитый результат (тело theirs) должен быть записан несмотря на гвард")
        if "строка 39" in m3:
            fails.append("тело theirs должно заменить ours (3-way: ours не трогал)")
        if not any(c.startswith("size-guard") for c in conflicts3):
            fails.append("сильное сжатие должно дать size-guard-конфликт (не молча): %s" % conflicts3)

    if fails:
        print("FAIL test_git_reconcile:")
        for f in fails:
            print("  -", f)
        sys.exit(1)
    print("OK test_git_reconcile: чистый field-merge→exit0 · related-union · конфликт-тела→exit1+маркеры(без потерь) · size-guard C33")


if __name__ == "__main__":
    main()
