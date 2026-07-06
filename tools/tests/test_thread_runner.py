"""
# ==========================================
# [FILE ID CARD]
# ID: tools.test_thread_runner
# TYPE: active-script
# DOMAIN: core
# DEPTH_LEVEL: 1
# SUMMARY: Скрипт test_thread_runner.py. Описание сгенерировано автоматически.
# ==========================================
"""
"""Тест thread_runner.py — terminal-thread runner (контекст-retrieval → синтетик-шаг → append)."""
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
import thread_runner as tr
import canon_index as ci

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass


def _w(d, sub, name, txt):
    os.makedirs(os.path.join(d, sub), exist_ok=True)
    p = os.path.join(d, sub, name)
    open(p, "w", encoding="utf-8", newline="\n").write(txt)
    return p


def main():
    fails = []
    with tempfile.TemporaryDirectory() as d:
        # канон + индекс
        _w(d, "decisions", "merge.md", "---\nid: D-MERGE\ntype: decision\n---\n# Merge\nкрдт field-level мёрж канона вместо строчных конфликтов\n")
        _w(d, "topics", "other.md", "---\nid: T-OTHER\ntype: topic\n---\n# Other\nнесвязанная тема про погоду\n")
        db = os.path.join(d, "idx.db")
        ci.build(root=d, db_path=db, dirs=("decisions", "topics"))

        # тред с задачей про мёрж
        thread = _w(d, "threads", "t1.md", "---\nid: TH-1\nagent: alice\ntask: как решить конфликты мёржа канона\n---\n# Тред\n")

        r = tr.run(thread, db_path=db, use_llama=False, k=3)
        # retrieval нашёл релевантный блок D-MERGE (не T-OTHER)
        if "D-MERGE" not in r["ids"]:
            fails.append("retrieval должен найти D-MERGE под задачу про мёрж: %s" % r["ids"])
        if "T-OTHER" in r["ids"]:
            fails.append("несвязанный T-OTHER не должен попасть в контекст: %s" % r["ids"])
        # шаг дописан в файл
        body = open(thread, encoding="utf-8").read()
        if "## шаг 1" not in body:
            fails.append("шаг 1 должен быть дописан в тред")
        if "alice" not in body or "D-MERGE" not in body:
            fails.append("шаг должен нести агента и id контекста: %s" % body[-200:])

        # второй прогон → шаг 2 (инкремент)
        r2 = tr.run(thread, db_path=db, use_llama=False, k=3)
        if r2["step"] != 2:
            fails.append("второй прогон должен быть шаг 2: %s" % r2["step"])
        if open(thread, encoding="utf-8").read().count("## шаг ") != 2:
            fails.append("в треде должно быть 2 шага")

        # llama недоступна → graceful фолбэк (не краш)
        r3 = tr.step("задача", "ctx", use_llama=True, endpoint="http://127.0.0.1:1/v1", model="x")
        if "фолбэк" not in r3 and "offline" not in r3:
            fails.append("недоступная llama → offline-фолбэк, не краш: %s" % r3[:60])

    if fails:
        print("FAIL test_thread_runner:")
        for f in fails:
            print("  -", f)
        sys.exit(1)
    print("OK test_thread_runner: retrieval→релевантный блок · шаг-append · инкремент шага · llama-фолбэк")


if __name__ == "__main__":
    main()
