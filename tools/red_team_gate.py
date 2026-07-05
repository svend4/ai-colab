# ==========================================
# [FILE ID CARD]
# ID: tools.red_team_gate
# TYPE: active-script
# DOMAIN: core.validation
# DEPTH_LEVEL: 1
# SUMMARY: выходной гейт: консенсус в канон, только если ПЕРЕЖИЛ опровержение (не голоса).
# ==========================================
"""red_team_gate.py — выходной гейт: консенсус в канон, только если ПЕРЕЖИЛ опровержение (не голоса).

Выходная симметрия к ripeness_gate (вход). P-5 / merit-промоция котла (2 линзы порознь: science +
collectives red-team). Принцип: «по смыслу» = «пережил атаку», а не «набрал голоса». Гейт читает
red-team-записи и маршрутизирует core-claim консенсуса:
  survived → cleared (можно промоутить в канон);
  refuted  → rejected → в NEGATIVE-SET С ПРИЧИНОЙ (апоптоз, не молчаливо; INV-NO-SILENT-APOPTOSIS);
  open/нет → pending (нужен red team, промоушн запрещён).
Опровержение — подключаемый агент (LLM); сам гейт ДЕТЕРМИНИРОВАН (лишь проверяет записи).

Формат redteam/<topic>.md: секции `## <claim>` с буллетами `- verdict: survived|refuted|open`,
`- reason: ...`, `- attack: ...`.

CLI:
  python tools/red_team_gate.py <redteam-file.md>   # маршрут записей
  python tools/red_team_gate.py --board             # по всем redteam/*.md
  python tools/red_team_gate.py --json
"""
import os
from _ioutil import configure_output
from _cli import help_guard
import sys
import re
import glob

configure_output()
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.environ.get("COLLAB_ROOT") or os.path.dirname(HERE)
VERDICTS = ("survived", "refuted", "open")
REFUTE_QUORUM = 2  # симметрия ADD↔REMOVE: убить claim нужно >=2 независимых опровергателя, не 1 tombstone


def parse_records(path):
    """Red-team-записи из markdown: на каждый `## claim` — verdict/reason/attack из буллетов."""
    try:
        lines = open(path, encoding="utf-8", errors="replace").read().splitlines()
    except OSError:
        return []
    recs = []
    cur = None
    for ln in lines:
        h = re.match(r"^##\s+(.*)", ln)
        if h:
            cur = {"claim": h.group(1).strip(), "verdict": "open", "reason": "", "attack": "", "severity": ""}
            recs.append(cur)
            continue
        if cur:
            m = re.match(r"^\s*-\s*(verdict|reason|attack|severity)\s*:\s*(.*)", ln, re.I)
            if m:
                key, val = m.group(1).lower(), m.group(2).strip()
                if key == "verdict":
                    v = val.lower().split()[0] if val else "open"
                    cur["verdict"] = v if v in VERDICTS else "open"
                else:
                    cur[key] = val
    return recs


def _breaks(rec):
    """Сколько НЕЗАВИСИМЫХ опровергателей реально сломали claim (по списку severity, 'survived' не в счёт)."""
    return sum(1 for s in rec.get("severity", "").split(",") if s.strip() and s.strip().lower() != "survived")


def gate(records):
    """Маршрут с симметрией ADD↔REMOVE: убить claim (rejected) нужно >=REFUTE_QUORUM независимых
    опровергателей; один tombstone → contested (как одиночный свидетель при добавлении — недостаточно)."""
    refuted = [r for r in records if r["verdict"] == "refuted"]
    return {
        "cleared": [r for r in records if r["verdict"] == "survived"],
        "rejected": [r for r in refuted if _breaks(r) >= REFUTE_QUORUM],   # независимо подтверждено → negative-set
        "contested": [r for r in refuted if _breaks(r) < REFUTE_QUORUM],   # 1 tombstone → нужно ещё (симметрия)
        "pending": [r for r in records if r["verdict"] == "open"],
    }


def promotable(claim_texts, records):
    """Какие core-claim можно промоутить: те, у кого есть запись survived (RT-1)."""
    survived = [r["claim"] for r in records if r["verdict"] == "survived"]
    out = []
    for c in claim_texts:
        ok = any(_overlap(c, s) for s in survived)
        out.append({"claim": c, "promotable": ok})
    return out


def _overlap(a, b):
    """Грубое совпадение claim по ключевым токенам (>=0.5 Jaccard) — связать core-claim с записью."""
    ta = {w for w in re.findall(r"[0-9a-zа-яё]{3,}", a.lower())}
    tb = {w for w in re.findall(r"[0-9a-zа-яё]{3,}", b.lower())}
    if not ta or not tb:
        return False
    return len(ta & tb) / len(ta | tb) >= 0.5


def _flags(g):
    f = []
    if g["rejected"]:
        f.append("⛔ %d refuted (>=кворума) → negative-set (НЕ молчаливо, с причиной)" % len(g["rejected"]))
    if g.get("contested"):
        f.append("◐ %d contested (1 опровергатель) — НЕ убит: нужен 2-й, симметрия с ADD" % len(g["contested"]))
    if g["pending"]:
        f.append("⏳ %d pending — промоушн запрещён до red team (RT-1)" % len(g["pending"]))
    return f


def _report(g, title):
    print("=== RED-TEAM-ГЕЙТ (выход): %s ===" % title)
    print("  cleared→канон: %d · rejected→negative-set: %d · contested(1 tombstone): %d · pending: %d" % (
        len(g["cleared"]), len(g["rejected"]), len(g.get("contested", [])), len(g["pending"])))
    for r in g["cleared"]:
        print("  ✅ %s" % r["claim"][:90])
    for r in g["rejected"]:
        print("  ⛔ %s" % r["claim"][:80])
        if r["reason"]:
            print("       причина(антиген): %s" % r["reason"][:100])
    for r in g.get("contested", []):
        print("  ◐ %s — оспорен 1 опровергателем, НЕ убит (нужен независимый 2-й)" % r["claim"][:70])
    for r in g["pending"]:
        print("  ⏳ %s — нужен red team" % r["claim"][:80])
    for fl in _flags(g):
        print("  " + fl)


def main(argv):
    help_guard(__doc__, argv)
    import json
    as_json = "--json" in argv
    args = [a for a in argv if not a.startswith("--")]
    if "--board" in argv or not args:
        files = sorted(glob.glob(os.path.join(ROOT, "redteam", "*.md")))
        results = []
        for fp in files:
            g = gate(parse_records(fp))
            g["file"] = os.path.relpath(fp, ROOT).replace("\\", "/")
            results.append(g)
        if as_json:
            print(json.dumps(results, ensure_ascii=False, indent=2)); return 0
        if not results:
            print("red_team_gate: нет redteam/*.md (ещё не было red-team-проверок)"); return 0
        for g in results:
            _report(g, os.path.basename(g["file"]))
            print()
        return 0
    p = args[0] if os.path.isabs(args[0]) else os.path.join(ROOT, args[0])
    recs = parse_records(p)
    g = gate(recs)
    if as_json:
        print(json.dumps(g, ensure_ascii=False, indent=2)); return 0
    if not recs:
        print("red_team_gate: записей не найдено в %s" % p); return 2
    _report(g, os.path.basename(p))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
