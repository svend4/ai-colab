# ==========================================
# [FILE ID CARD]
# ID: tools.reflect_ingest
# TYPE: active-script
# DOMAIN: core
# DEPTH_LEVEL: 1
# SUMMARY: мозг авто-саморефлексии: находки blocks → severity + дедуп-ledger + рецидив.
# ==========================================
"""reflect_ingest.py — мозг авто-саморефлексии: находки blocks → severity + дедуп-ledger + рецидив.

Принимает JSON-результат `blocks.py run <block> --json` (stdin или --in файл), извлекает находки
(шаг rc!=0), присваивает severity (gate-fail=HIGH, advisory-flag=MEDIUM), дедупит против append-only
logs/reflection/ledger.json по хэшу (tool+нормализованный симптом). Считает РЕЦИДИВ: находка
вернулась через несколько коммитов = «полый цикл» (детектор сработал, но никто не починил).
Детерминированно, идемпотентно, БЕЗ workflow (переживает компактацию).

Философия: метрика — КАЧЕСТВО результата (рецидив↓, применяемость↑), НЕ число строк. Цель авто-петли —
чтобы находки ДОХОДИЛИ до починки, а не копились.

CLI:
  python tools/blocks.py run improve --json | python tools/reflect_ingest.py --commit <sha>
  python tools/reflect_ingest.py --in logs/reflection/<sha>.json --commit <sha>
  python tools/reflect_ingest.py --summary           # сводка ledger (открытые/рецидивы по severity)
  python tools/reflect_ingest.py --menu | python tools/decision_menu.py -   # находки→меню человеку (шаг 5)
  python tools/reflect_ingest.py --accept <hash|tool> --reason "..."   # принять (wontfix) — не каждый рецидив дефект
  echo '{"findings":[...]}' | python tools/reflect_ingest.py --source <имя> --commit <sha>  # ЛЮБОЙ источник → один цикл (7.3)
"""
import os
from _ioutil import configure_output
import re
import sys
import json
import time
import hashlib
from _cli import help_guard

configure_output()
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.environ.get("COLLAB_ROOT") or os.path.dirname(HERE)
LEDGER = os.path.join(ROOT, "logs", "reflection", "ledger.json")
RECUR_THRESHOLD = 3   # находка в ≥3 заходах подряд = полый цикл (детектор есть, починки нет)
COMMITS_KEEP = 12


def _symptom(tool, tail):
    """Стабильный короткий симптом: первая значимая строка tail, без чисел/путей-вариативности."""
    for line in (tail or "").splitlines():
        s = line.strip().lstrip("-•*[ ").strip()
        if not s or s.startswith("==="):
            continue
        s = re.sub(r"\d+", "#", s)            # числа → # (стабильность хэша)
        s = re.sub(r"\s+", " ", s)[:80]
        return s
    return tool


def _hash(tool, symptom):
    return hashlib.sha1(("%s::%s" % (tool, symptom)).encode("utf-8")).hexdigest()[:12]


def findings_from_blocks(data):
    """blocks-JSON → список находок. rc!=0: gate=HIGH, advisory=MEDIUM."""
    out = []
    block = data.get("block", "?")
    for st in data.get("steps", []):
        if st.get("skipped") or st.get("rc", 0) == 0:
            continue
        kind = st.get("kind", "advisory")
        sev = "high" if kind == "gate" else "medium"
        tool = st.get("tool", "?")
        sym = _symptom(tool, st.get("tail", ""))
        out.append({"hash": _hash(tool, sym), "tool": tool, "block": block,
                    "severity": sev, "symptom": sym, "detail": (st.get("tail") or "")[:300]})
    return out


def findings_from_generic(data, source="external"):
    """ОБОБЩЁННЫЙ источник: {"findings":[{tool,symptom,severity,detail?}]} → находки. Любой агент/тул/
    детектор шлёт находки в ОДИН метаболический цикл (стигмергия: следы в общем ledger, рецидив=сила
    следа). Большой объём от группы → единая обработка/дедуп/ROUTE. Вопрос 7.3 / 2.2.2."""
    out = []
    for f in data.get("findings", []):
        tool = f.get("tool") or source
        sym = f.get("symptom") or f.get("title") or "?"
        sev = f.get("severity") or f.get("sev") or "medium"
        out.append({"hash": _hash(tool, sym), "tool": tool, "block": f.get("block") or source,
                    "severity": sev, "symptom": sym, "detail": (f.get("detail") or "")[:300]})
    return out


def findings_auto(data, source="external"):
    """Авто-детект формата: blocks (есть steps) или обобщённый (есть findings)."""
    if isinstance(data, dict) and "steps" in data:
        return findings_from_blocks(data)
    return findings_from_generic(data, source)


def load_ledger():
    try:
        with open(LEDGER, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return {"findings": {}, "runs": []}


def save_ledger(led):
    os.makedirs(os.path.dirname(LEDGER), exist_ok=True)
    with open(LEDGER, "w", encoding="utf-8", newline="\n") as f:
        json.dump(led, f, ensure_ascii=False, indent=2)


def ingest(findings, commit, now=None):
    now = int(now if now is not None else time.time())
    led = load_ledger()
    fdb = led["findings"]
    cur_hashes = set()
    for fnd in findings:
        h = fnd["hash"]
        cur_hashes.add(h)
        e = fdb.get(h)
        if e is None:
            fdb[h] = {"tool": fnd["tool"], "block": fnd["block"], "severity": fnd["severity"],
                      "symptom": fnd["symptom"], "first_seen": now, "first_commit": commit,
                      "last_seen": now, "last_commit": commit, "count": 1, "status": "open",
                      "commits": [commit] if commit else []}
        else:
            e["last_seen"] = now
            e["last_commit"] = commit
            e["count"] = e.get("count", 1) + 1
            if e.get("status") != "accepted":  # принятое (wontfix) не ре-открываем при рецидиве
                e["status"] = "open"
            cm = e.get("commits", [])
            if commit and commit not in cm:
                cm.append(commit)
            e["commits"] = cm[-COMMITS_KEEP:]
    # находки этого блока, которых в текущем заходе НЕТ → помечаем resolved (по блоку, чтобы не путать)
    blocks_seen = {f["block"] for f in findings}
    for h, e in fdb.items():
        if h not in cur_hashes and e.get("block") in blocks_seen and e.get("status") == "open":
            e["status"] = "resolved"
            e["resolved_seen"] = now
    led["runs"].append({"commit": commit, "ts": now,
                        "high": sum(1 for f in findings if f["severity"] == "high"),
                        "medium": sum(1 for f in findings if f["severity"] == "medium")})
    led["runs"] = led["runs"][-COMMITS_KEEP * 4:]
    save_ledger(led)
    return led


def summarize(led):
    open_f = [e for e in led["findings"].values() if e.get("status") == "open"]
    recurring = [e for e in open_f if e.get("count", 1) >= RECUR_THRESHOLD]
    return {
        "open_total": len(open_f),
        "open_high": sum(1 for e in open_f if e["severity"] == "high"),
        "open_medium": sum(1 for e in open_f if e["severity"] == "medium"),
        "recurring": sorted(recurring, key=lambda e: -e.get("count", 0)),
        "resolved_total": sum(1 for e in led["findings"].values() if e.get("status") == "resolved"),
        "accepted_total": sum(1 for e in led["findings"].values() if e.get("status") == "accepted"),
    }


def accept(led, target, reason, now=None):
    """Пометить открытую находку «accepted» (wontfix) с обоснованием — уходит из полых циклов/меню.
    target = хэш ИЛИ имя tool (примет все открытые находки этого детектора). Не каждый рецидив = дефект:
    легитимное принятое состояние (напр. большой review-док — качество, не размер) — accept, не fix."""
    now = int(now if now is not None else time.time())
    hit = []
    for h, e in led["findings"].items():
        if e.get("status") != "open":
            continue
        if h == target or e.get("tool") == target:
            e["status"] = "accepted"
            e["accepted_reason"] = reason
            e["accepted_at"] = now
            hit.append(h)
    if hit:
        save_ledger(led)
    return hit


def to_menu(led):
    """Находки → JSON «меню решений» (decision_menu.py) для ЧЕЛОВЕКА. Приоритет: рецидивы, затем high.
    Авто только подача; ПРИНЯТИЕ (задача/правка) — ручное (D-006/D-018). Спека шаг 5."""
    s = summarize(led)
    high_open = [e for e in led["findings"].values()
                 if e.get("status") == "open" and e["severity"] == "high"]
    seen = set()
    candidates = []
    for e in s["recurring"] + high_open:  # рецидивы первыми, затем high
        k = (e["tool"], e["symptom"])
        if k not in seen:
            seen.add(k); candidates.append(e)
    options = []
    for i, e in enumerate(candidates[:8]):
        recur = e.get("count", 1) >= RECUR_THRESHOLD
        options.append({
            "key": chr(65 + i),
            "title": "%s — %s" % (e["tool"], e["symptom"][:55]),
            "gist": ("полый цикл ×%d" % e["count"]) if recur else ("%s, ×%d" % (e["severity"], e.get("count", 1))),
            "tags": {"risk": e["severity"], "effort": "?", "reversibility": "easy",
                     "scope": e.get("block", "")},
            "what": "Находка детектора %s (блок %s), повтор в %d заходах." % (e["tool"], e.get("block", "?"), e.get("count", 1)),
            "pros": ["починка убирает рецидив из ledger", "поднимает качество результата (не строки)"],
            "cons": (["рецидив: детектор видит раз за разом, никто не чинит → шум растёт"] if recur
                     else ["разовая находка — возможно, ещё разрешится сама"]),
            "means": "Детектор находит, но находка не доходит до починки — разрыв петли применяемости.",
            "leads_to": "Если не починить: ledger-шум↑, качество не движется; если починить: рецидив→resolved.",
            "responsibility": "Маршрут по обратимости/владению: своё→fix+тест; чужое→владельцу; governance→котёл.",
            "recommended": recur,
        })
    return {
        "title": "Саморефлексия — находки для ROUTE (рецидивы + high)",
        "context": "Авто-петля (post-commit→reflect→ingest) накопила находки. Полые циклы = детектор есть, "
                   "починки нет. Это подача человеку; авто-принятия нет (D-006).",
        "options": options,
        "recommendation": "Начни с рецидивов (×≥%d) — доказанно не чинятся сами. LOC не метрика; цель — рецидив↓." % RECUR_THRESHOLD,
        "how_to_choose": "Назови ключ — оформлю маршрут (fix/владельцу/котёл). «Другое» — свой вариант.",
    }


def main(argv):
    help_guard(__doc__, argv)
    as_json = "--json" in argv
    commit = None
    if "--commit" in argv:
        i = argv.index("--commit")
        if i + 1 < len(argv):
            commit = argv[i + 1]
    if "--menu" in argv:
        # JSON «меню решений» для человека (пайпить в decision_menu.py -)
        print(json.dumps(to_menu(load_ledger()), ensure_ascii=False, indent=2))
        return 0
    if "--accept" in argv:
        i = argv.index("--accept")
        target = argv[i + 1] if i + 1 < len(argv) else None
        reason = ""
        if "--reason" in argv:
            j = argv.index("--reason")
            reason = argv[j + 1] if j + 1 < len(argv) else ""
        if not target:
            print("reflect_ingest --accept <hash|tool> --reason '<обоснование>'"); return 2
        hit = accept(load_ledger(), target, reason or "(без обоснования)")
        print("принято (wontfix): %d находок по '%s' — ушли из полых циклов (%s)" % (
            len(hit), target, reason or "—"))
        return 0
    if "--summary" in argv:
        s = summarize(load_ledger())
        if as_json:
            print(json.dumps(s, ensure_ascii=False, indent=2)); return 0
        print("=== САМОРЕФЛЕКСИЯ — ledger (logs/reflection/ledger.json) ===")
        print("  открытых: %d  (high %d · medium %d) · resolved: %d · accepted: %d" % (
            s["open_total"], s["open_high"], s["open_medium"], s["resolved_total"], s["accepted_total"]))
        print("  ПОЛЫЕ ЦИКЛЫ (рецидив ≥%d заходов — детектор есть, починки нет): %d" % (
            RECUR_THRESHOLD, len(s["recurring"])))
        for e in s["recurring"][:15]:
            print("    [%s ×%d] %s: %s" % (e["severity"], e["count"], e["tool"], e["symptom"]))
        return 0
    # ingest из stdin или --in
    src = None
    if "--in" in argv:
        i = argv.index("--in")
        if i + 1 < len(argv):
            src = argv[i + 1]
    try:
        raw = open(src, encoding="utf-8").read() if src else sys.stdin.read()
        data = json.loads(raw)
    except (OSError, json.JSONDecodeError) as e:
        print("reflect_ingest: не прочитать JSON (%s)" % e); return 2
    source = "external"
    if "--source" in argv:
        i = argv.index("--source")
        if i + 1 < len(argv):
            source = argv[i + 1]
    findings = findings_auto(data, source)  # blocks ИЛИ обобщённый источник (любой агент/тул)
    led = ingest(findings, commit)
    s = summarize(led)
    print("ingest: источник %s — находок %d (high %d/med %d); ledger открытых %d, полых циклов %d" % (
        data.get("block", source), len(findings),
        sum(1 for f in findings if f["severity"] == "high"),
        sum(1 for f in findings if f["severity"] == "medium"),
        s["open_total"], len(s["recurring"])))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
