# ==========================================
# [FILE ID CARD]
# ID: tools.workflow_recover
# TYPE: active-script
# DOMAIN: core
# DEPTH_LEVEL: 1
# SUMMARY: восстановление ПАРТИАЛ-результатов фонового workflow (durability слоя оркестрации).
# ==========================================
"""workflow_recover.py — восстановление ПАРТИАЛ-результатов фонового workflow (durability слоя оркестрации).

Проблема (запрос Stefan + формула D-031, шаг 2 «durability-первым» на слое ОРКЕСТРАЦИИ): фоновый workflow
идёт часами; если умрёт (компакция/сбой), жалко терять часы. Но каждый ЗАВЕРШЁННЫЙ агент УЖЕ durable — его
результат пишется в `journal.jsonl` (тот же источник, из которого идёт resume). Этот инструмент выуживает все
завершённые результаты ДАЖЕ из недоделанного/мёртвого workflow → партиал-сохранение по факту, ничего не теряется.

journal.jsonl: записи `started{agentId,key}` и `result{agentId,key,result}`. Завершён = есть `result`.
Незавершён (started без result) = в полёте ИЛИ умер — но это видно, и завершённые соседи целы.

CLI:
  python tools/workflow_recover.py <journal.jsonl | каталог-workflow>      # сводка + агенты + превью
  python tools/workflow_recover.py <...> --dump <out-dir>                  # выгрузить каждый результат в файл
  python tools/workflow_recover.py --latest [--base <projects-dir>]        # последний workflow по mtime
  python tools/workflow_recover.py <...> --json
"""
import os
from _ioutil import configure_output
from _cli import help_guard
import sys
import re
import json
import glob

configure_output()
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.environ.get("COLLAB_ROOT") or os.path.dirname(HERE)
DEFAULT_BASE = os.path.expanduser(os.path.join("~", ".claude", "projects"))


def parse_journal(lines):
    """Чистый разбор строк journal.jsonl → {started:{aid:key}, results:[{agentId,key,result}], pending:[aid]}.

    Тестируемо без harness. Завершён = пришёл result; pending = started без result (в полёте/умер)."""
    started, results = {}, {}
    for ln in lines:
        ln = ln.strip()
        if not ln:
            continue
        try:
            d = json.loads(ln)
        except (ValueError, TypeError):
            continue
        t, aid = d.get("type"), d.get("agentId")
        if not aid:
            continue
        if t == "started":
            started.setdefault(aid, d.get("key", aid))
        elif t == "result":
            results[aid] = {"agentId": aid, "key": d.get("key", started.get(aid, aid)), "result": d.get("result")}
    pending = [aid for aid in started if aid not in results]
    return {"started": started, "results": list(results.values()), "pending": pending}


def _journal_path(arg):
    if os.path.isdir(arg):
        return os.path.join(arg, "journal.jsonl")
    return arg


def _latest_journal(base):
    cands = glob.glob(os.path.join(base, "**", "subagents", "workflows", "wf_*", "journal.jsonl"), recursive=True)
    if not cands:
        return None
    return max(cands, key=lambda p: os.path.getmtime(p))


def recover(journal_path):
    """Прочитать журнал → партиал-результаты + сводка (started/completed/pending)."""
    if not os.path.exists(journal_path):
        return None
    with open(journal_path, encoding="utf-8", errors="replace") as fh:
        p = parse_journal(fh)
    p["journal"] = journal_path
    p["counts"] = {"started": len(p["started"]), "completed": len(p["results"]), "pending": len(p["pending"])}
    return p


def _as_text(result):
    if isinstance(result, str):
        return result
    return json.dumps(result, ensure_ascii=False, indent=2)


def dump(parsed, out_dir):
    """Выгрузить результат каждого завершённого агента в отдельный файл (партиал-сохранение на диск)."""
    os.makedirs(out_dir, exist_ok=True)
    written = []
    for i, r in enumerate(parsed["results"]):
        slug = re.sub(r"[^A-Za-z0-9_.-]+", "_", str(r["key"]))[:60] or ("agent_%d" % i)
        body = _as_text(r["result"])
        path = os.path.join(out_dir, "%02d-%s.txt" % (i, slug))
        with open(path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(body)
        written.append(path)
    return written


def main(argv):
    help_guard(__doc__, argv)
    args = [a for a in argv if not a.startswith("--")]
    if "--latest" in argv:
        base = _opt(argv, "--base", DEFAULT_BASE)
        jp = _latest_journal(base)
        if not jp:
            print("workflow_recover: workflow не найден под %s" % base); return 2
    elif args:
        jp = _journal_path(args[0])
    else:
        print("workflow_recover: нужен путь к journal.jsonl/каталогу или --latest"); return 2

    p = recover(jp)
    if p is None:
        print("workflow_recover: журнал не найден: %s" % jp); return 2

    if "--dump" in argv:
        out = _opt(argv, "--dump") or os.path.join(ROOT, "sandbox", "recovered")
        w = dump(p, out)
        print("workflow_recover: выгружено %d результат(ов) → %s" % (len(w), out))
        return 0
    if "--json" in argv:
        print(json.dumps({"counts": p["counts"], "completed": [{"key": r["key"]} for r in p["results"]],
                          "pending": p["pending"], "journal": jp}, ensure_ascii=False, indent=2))
        return 0
    c = p["counts"]
    print("=== ВОССТАНОВЛЕНИЕ WORKFLOW · %s ===" % os.path.basename(os.path.dirname(jp)))
    print("  агентов: %d начато · %d ЗАВЕРШЕНО (durable) · %d в полёте/потеряно" % (
        c["started"], c["completed"], c["pending"]))
    print("  завершённые (партиал-результаты целы):")
    for r in p["results"]:
        prev = _as_text(r["result"]).replace("\n", " ")[:90]
        print("    ✓ %-22s %s" % (str(r["key"])[:22], prev))
    if p["pending"]:
        print("  в полёте/потеряно: %s" % ", ".join(a[:10] for a in p["pending"]))
    print("\n  (--dump <dir> — выгрузить каждый результат в файл; они уже durable в журнале)")
    return 0


def _opt(argv, flag, default=None):
    if flag in argv:
        i = argv.index(flag)
        if i + 1 < len(argv):
            return argv[i + 1]
    return default


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
