"""decision_propagation.py — детектор «решение принято, но не дошло до потребителей».

Чинит корень провала svend4 (Stefan: решения существуют, но не доходят до верха/исполнения и не
обнародованы для всех). assurance.py следит instructions→вершина; здесь — decisions→ПОТРЕБИТЕЛИ
(вопросы/задачи), которые ДОЛЖНЫ их отражать, но не цитируют/противоречат.

Два сигнала:
  A. back-ref gap: решение D ссылается на T-NNN/Q-NNN, но тот НЕ цитирует D обратно (одностороннее
     знание — D «знает» про задачу, задача про D не знает).
  B. stale-blocker: open-вопрос / blocked-задача несёт distinctive-токен (напр. `svend4`), который есть
     в теле ACCEPTED-решения, но НЕ цитирует это решение → возможно непропагированное решение.

CLI:
    python tools/decision_propagation.py            # сводка + находки
    python tools/decision_propagation.py --json
"""
import os
import re
import sys
import glob

os.environ.setdefault("PYTHONUTF8", "1")
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from _canon import parse_front_matter

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

ID_RE = re.compile(r"\b([DTQ]-\d{3})\b")
# distinctive-токен: слово с цифрой (svend4, T137) ИЛИ длинное латинское/кириллическое (>=6) — редкое, не проза
TOKEN_RE = re.compile(r"\b([A-Za-zА-Яа-я]+\d\w*|[A-Za-z]{6,})\b")
COMMON = {"decision", "proposed", "accepted", "current", "должен", "решение", "should", "external",
          "review", "status", "process", "policy", "stefan", "agent", "agents", "result", "before",
          "synthesis", "promotion", "default", "verified"}


def _items(subdir, prefix):
    out = {}
    for p in sorted(glob.glob(os.path.join(ROOT, subdir, prefix + "*.md"))):
        try:
            with open(p, encoding="utf-8", errors="replace") as f:
                text = f.read()
        except OSError:
            continue
        fm = parse_front_matter(text)
        iid = os.path.basename(p)[:-3]
        out[iid] = {"id": iid, "status": (fm.get("status") or "").strip(), "text": text,
                    "title": (fm.get("title") or "").strip(), "body": text}
    return out


def _refs(text):
    return set(ID_RE.findall(text or ""))


def _tokens(text):
    return {t.lower() for t in TOKEN_RE.findall(text or "")} - COMMON


def analyze():
    decisions = _items("decisions", "D-")
    questions = _items("questions", "Q-")
    tasks = _items("tasks", "T-")
    consumers = {}
    consumers.update(questions)
    consumers.update(tasks)

    back_ref_gaps = []   # D ссылается на X, X не цитирует D
    stale_blockers = []  # open/blocked X несёт токен accepted-D, не цитируя D

    for did, d in decisions.items():
        if d["status"] not in ("accepted", "proposed"):
            continue
        # A: back-ref
        for ref in _refs(d["body"]):
            if ref == did or ref not in consumers:
                continue
            if did not in _refs(consumers[ref]["body"]):
                cstatus = consumers[ref]["status"]
                back_ref_gaps.append({"decision": did, "consumer": ref,
                                      "consumer_status": cstatus,
                                      "decision_status": d["status"],
                                      "active": cstatus in ("open", "blocked", "todo", "doing")})

    # B: stale-blocker (только accepted-решения — они уже binding)
    accepted = {k: v for k, v in decisions.items() if v["status"] == "accepted"}
    for cid, c in consumers.items():
        if c["status"] not in ("open", "blocked", "todo", "doing"):
            continue
        c_tokens = _tokens(c["title"] + " " + c["body"])
        cited = _refs(c["body"])
        for did, d in accepted.items():
            if did in cited:
                continue
            d_tokens = _tokens(d["body"])
            # distinctive = есть цифра И алфавитный префикс >=4 (svend4 да; l1/l2/p3/t137 нет — шум)
            shared = sorted(t for t in (c_tokens & d_tokens)
                            if any(ch.isdigit() for ch in t) and len(re.sub(r"\d.*", "", t)) >= 4)
            if shared:
                stale_blockers.append({"consumer": cid, "consumer_status": c["status"],
                                       "decision": did, "shared_tokens": shared[:4]})

    return {"back_ref_gaps": back_ref_gaps, "stale_blockers": stale_blockers,
            "n_decisions": sum(1 for d in decisions.values() if d["status"] in ("accepted", "proposed"))}


def main(argv):
    import json
    data = analyze()
    if "--json" in argv:
        print(json.dumps(data, ensure_ascii=False, indent=2))
        return 1 if (data["back_ref_gaps"] or data["stale_blockers"]) else 0
    g, s = data["back_ref_gaps"], data["stale_blockers"]
    active = [x for x in g if x.get("active")]
    cosmetic = [x for x in g if not x.get("active")]
    print("=== DECISION-PROPAGATION (решения → потребители) ===")
    print("  решений: %d   АКТИВНЫХ-провалов: %d   косметич.cross-link(done): %d   stale-blockers: %d"
          % (data["n_decisions"], len(active), len(cosmetic), len(s)))
    if active:
        print("\n  A. АКТИВНЫЕ провалы (решение → open/blocked-потребитель, не цитирует обратно — реально не дошло):")
        for x in active[:20]:
            print("     %s → %s (%s) — не отражает решение" %
                  (x["decision"], x["consumer"], x["consumer_status"]))
    if s:
        print("\n  B. stale-blockers (open/blocked несёт токен accepted-решения, не цитируя его):")
        for x in s[:20]:
            print("     %s (%s) ↮ %s  [общий токен: %s]" %
                  (x["consumer"], x["consumer_status"], x["decision"], ", ".join(x["shared_tokens"])))
    if cosmetic:
        print("\n  (косметика: %d back-ref на done/answered — работа сделана, cross-link опционален)" % len(cosmetic))
    if not active and not s:
        print("\n  OK: решения дошли до всех АКТИВНЫХ потребителей (косметич.cross-link на done — опц.)")
    return 1 if (active or s) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
