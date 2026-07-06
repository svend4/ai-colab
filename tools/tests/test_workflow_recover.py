"""
# ==========================================
# [FILE ID CARD]
# ID: tools.test_workflow_recover
# TYPE: active-script
# DOMAIN: core
# DEPTH_LEVEL: 1
# SUMMARY: Скрипт test_workflow_recover.py. Описание сгенерировано автоматически.
# ==========================================
"""
"""Тест workflow_recover.py — разбор журнала · сводка started/completed/pending · dump в файлы."""
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
import json
import time

HERE = _TOOLS_DIR  # tools/ — тест перенесён в tools/tests/ (C14)
REPO_ROOT = os.path.dirname(HERE)
ROOT = os.path.join(REPO_ROOT, "tmp-work", "wf_recover_test_%d_%d" % (os.getpid(), time.time_ns()))
os.makedirs(ROOT, exist_ok=True)
os.environ["COLLAB_ROOT"] = ROOT

sys.path.insert(0, HERE)
import workflow_recover as wr

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass


def run():
    fails = []
    try:
        # синтетический журнал: 3 started, 2 result (1 в полёте/потерян), + битая строка
        lines = [
            json.dumps({"type": "started", "agentId": "a1", "key": "discover:questions"}),
            json.dumps({"type": "started", "agentId": "a2", "key": "discover:decisions"}),
            json.dumps({"type": "started", "agentId": "a3", "key": "synthesize"}),
            "{битый json",
            json.dumps({"type": "result", "agentId": "a1", "key": "discover:questions", "result": {"records": [1, 2]}}),
            json.dumps({"type": "result", "agentId": "a2", "key": "discover:decisions", "result": "текстовый итог"}),
        ]
        p = wr.parse_journal(lines)
        if p["started"] != {"a1": "discover:questions", "a2": "discover:decisions", "a3": "synthesize"}:
            fails.append("started неверно: %s" % p["started"])
        if len(p["results"]) != 2:
            fails.append("должно быть 2 завершённых: %d" % len(p["results"]))
        if p["pending"] != ["a3"]:
            fails.append("pending (started без result) = [a3]: %s" % p["pending"])

        # recover из файла + counts
        jp = os.path.join(ROOT, "journal.jsonl")
        open(jp, "w", encoding="utf-8", newline="\n").write("\n".join(lines))
        r = wr.recover(jp)
        if r["counts"] != {"started": 3, "completed": 2, "pending": 1}:
            fails.append("counts: %s" % r["counts"])

        # dump: 2 файла, dict→json, str→как есть
        out = os.path.join(ROOT, "recovered")
        w = wr.dump(r, out)
        if len(w) != 2:
            fails.append("dump должен записать 2 файла: %d" % len(w))
        bodies = [open(f, encoding="utf-8").read() for f in w]
        if not any("records" in b for b in bodies) or not any("текстовый итог" in b for b in bodies):
            fails.append("dump должен содержать и dict-результат, и текстовый: %s" % [b[:30] for b in bodies])

        # _journal_path: каталог → journal.jsonl
        if not wr._journal_path(ROOT).endswith("journal.jsonl"):
            fails.append("_journal_path(dir) → dir/journal.jsonl")

        # пустой/отсутствующий журнал не падает
        if wr.recover(os.path.join(ROOT, "нет.jsonl")) is not None:
            fails.append("несуществующий журнал → None")

        if fails:
            print("FAIL test_workflow_recover:")
            for f in fails:
                print("  -", f)
            return 1
        print("OK test_workflow_recover: разбор журнала · started/completed/pending · counts · dump(dict+str) · _journal_path · missing")
        return 0
    finally:
        pass


if __name__ == "__main__":
    sys.exit(run())
