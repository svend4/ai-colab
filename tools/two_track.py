"""
# ==========================================
# [FILE ID CARD]
# ID: tools.two_track
# TYPE: active-script
# DOMAIN: core
# DEPTH_LEVEL: 1
# SUMMARY: Скрипт two_track.py. Описание сгенерировано автоматически.
# ==========================================
"""
"""two_track.py — двухтрековая классификация работы для котла/конвейера.

Запрос Stefan: при заходе в котёл каждая единица помечается одним из ДВУХ больших типов, чтобы
видеть две части (лево/право, чёрное/белое) и выбирать трек в пропорции.

  ТРЕК-1 КОНСЕНСУС → mark READY-RATIFY-BUILD: 2+ агента+человек согласны, документировано →
    остаётся ратифицировать (котёл) → писать код по описанию (обобщение/внедрение).
  ТРЕК-2 РАЗНОГЛАСИЕ → mark PENDING-DETAIL: ещё спорно → детализировать/обосновывать/достраивать/
    доп-вопросы. Под-тип: conflict (доки противоречат, нужен котёл) | standalone (нужен 2-й голос).

Источник — разбор-доки (consensus + divergence), произведённые doc_consensus/group-разбором.
Агент фильтрует трек: --track ratify|detail. Конвейер двигает обе части.

CLI:
    python tools/two_track.py board [--json]                 # обе части + счётчики
    python tools/two_track.py --track ratify [--json]        # только Трек-1 (консенсус)
    python tools/two_track.py --track detail [--json]        # только Трек-2 (разногласия)
    python tools/two_track.py --consensus F --divergence F   # свои разбор-доки
"""
import os
import re
import sys
import json
import glob

os.environ.setdefault("PYTHONUTF8", "1")
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from _ioutil import configure_output

configure_output()

ITEM_RE = re.compile(r"^###\s+([A-Z]+-\d+)\.?\s+(.*)$")
SUB_RE = re.compile(r"^##\s+([A-ZА-Я])\.\s+(.*)$")


def _latest(pattern):
    files = sorted(glob.glob(os.path.join(ROOT, pattern)))
    return files[-1] if files else None


def _parse(path, track, mark):
    """Извлечь ### XXX-NN. items; подхватывать ## A./B. как под-категорию (для divergence)."""
    items, subcat = [], ""
    if not path or not os.path.isfile(path):
        return items
    with open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            ms = SUB_RE.match(line.rstrip())
            if ms:
                subcat = ms.group(2).strip()[:48]
                continue
            mi = ITEM_RE.match(line.rstrip())
            if mi:
                items.append({"id": mi.group(1), "title": mi.group(2).strip(),
                              "track": track, "mark": mark, "subcat": subcat})
    return items


def collect(consensus=None, divergence=None):
    consensus = consensus or _latest("topics/razbor-consensus-*.md")
    divergence = divergence or _latest("topics/razbor-divergence-*.md")
    track1 = [i for i in _parse(consensus, "ratify", "READY-RATIFY-BUILD") if i["id"].startswith("C-")]
    track2 = _parse(divergence, "detail", "PENDING-DETAIL")
    return {"consensus_doc": os.path.relpath(consensus, ROOT) if consensus else None,
            "divergence_doc": os.path.relpath(divergence, ROOT) if divergence else None,
            "track1_ratify": track1, "track2_detail": track2}


def render(data, only=None):
    t1, t2 = data["track1_ratify"], data["track2_detail"]
    n1, n2 = len(t1), len(t2)
    total = n1 + n2 or 1
    L = ["=== ДВА ТРЕКА (котёл/конвейер) ==="]
    L.append("  ТРЕК-1 КОНСЕНСУС (ратифицировать→строить): %d   |   ТРЕК-2 РАЗНОГЛАСИЕ (детализировать): %d"
             % (n1, n2))
    L.append("  пропорция готового: %d%% консенсус / %d%% разногласие" % (round(100 * n1 / total), round(100 * n2 / total)))
    if only in (None, "ratify"):
        L += ["", "── ТРЕК-1: READY-RATIFY-BUILD (%d) — 2+ агента согласны → котёл-ратификация → код по описанию" % n1]
        for i in t1:
            L.append("  [%s] %s" % (i["id"], i["title"][:78]))
    if only in (None, "detail"):
        L += ["", "── ТРЕК-2: PENDING-DETAIL (%d) — спорно → детализировать/обосновывать/доп-вопросы" % n2]
        cur = None
        for i in t2:
            if i["subcat"] != cur:
                cur = i["subcat"]
                L.append("  · %s" % cur)
            L.append("    [%s] %s" % (i["id"], i["title"][:74]))
    return "\n".join(L)


def main(argv):
    a = list(argv)
    as_json = "--json" in a
    only = None
    if "--track" in a:
        i = a.index("--track")
        only = a[i + 1] if i + 1 < len(a) else None
        if only not in ("ratify", "detail"):
            print("--track ratify|detail")
            return 2
    cons = a[a.index("--consensus") + 1] if "--consensus" in a else None
    div = a[a.index("--divergence") + 1] if "--divergence" in a else None
    data = collect(cons, div)
    if as_json:
        out = dict(data)
        if only == "ratify":
            out = {"track1_ratify": data["track1_ratify"]}
        elif only == "detail":
            out = {"track2_detail": data["track2_detail"]}
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return 0
    print(render(data, only=only))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
