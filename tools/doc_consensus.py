#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
# ==========================================
# [FILE ID CARD]
# ID: tools.doc_consensus
# TYPE: active-script
# DOMAIN: core
# DEPTH_LEVEL: 1
# SUMMARY: Скрипт doc_consensus.py. Описание сгенерировано автоматически.
# ==========================================
"""
"""
doc_consensus (Q-017, слияние документации агентов) — находит ОБЩИЕ пункты и РАЗНОГЛАСИЯ между доками.

Сканирует несколько markdown-документов (разных агентов/людей) по одной теме, выделяет «пункты»
(буллеты / заголовки / строки таблиц / содержательные абзацы), кластеризует похожие по содержанию (Jaccard на токенах) и даёт:
- **Консенсус** — пункты, встречающиеся в >=2 документах, с cross-reference `file:line` где встречаются;
- **Разногласия** — пункты только из одного документа (сгруппированы по файлу).

Это автоматизация ручного синтеза (opinion-synthesis): консенсус → описание в mainline, разногласия →
детализировать/обосновать (модель D-017). READ-ONLY, чистая stdlib.

CLI:
    python tools/doc_consensus.py report --files a.md b.md [c.md ...] [--out reports/x.md] [--thr 0.4]
        [--divergence-out path]  # вынести разногласия в ОТДЕЛЬНЫЙ файл (D-017), оставив консенсус+ссылку
    python tools/doc_consensus.py report --topic <topic> [--out ...]   # доки темы через variants.py
    python tools/doc_consensus.py report --semantic --files a.md b.md [--semantic-budget N]
        # --semantic шелит в $DOC_CONSENSUS_AGENT (LLM); по умолчанию — no-cost лексический путь.
"""
import os
import re
import sys
from _ioutil import configure_output
from _cli import help_guard
import json
import subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOLS = os.path.join(ROOT, "tools")
# Шумовые слова (ru+en), чтобы Jaccard ловил суть, а не служебные.
STOP = set((
    "the a an and or of to in is are for with on at by as be it this that not from into "
    "и в на по для что как это не из то же был быть эти об от со про или нет так уже там где "
    "к у о а но если чтобы при над под между его её их мы вы они оно тот эта все весь"
).split())

configure_output()

# Лёгкий стемминг: чтобы «безопасность/безопасности», «коммит/коммиты» совпадали (cross-agent проза
# одни идеи пишет разными формами). Грубо, без морфологии — отсечь частые окончания.
_RU_SUF = sorted((
    "ость", "ения", "иями", "ями", "ами", "ого", "ому", "ыми", "ими", "ах", "ях", "ов", "ев",
    "ий", "ый", "ая", "ое", "ые", "ться", "ть", "ет", "ут", "ют", "ам", "ом", "ем", "ах", "и", "ы", "а", "у", "е",
), key=len, reverse=True)
_EN_SUF = ("ings", "ing", "ies", "ed", "es", "s")

def _stem(w):
    for suf in _RU_SUF:
        if w.endswith(suf) and len(w) - len(suf) >= 4:
            return w[:-len(suf)]
    for suf in _EN_SUF:
        if w.endswith(suf) and len(w) - len(suf) >= 4:
            return w[:-len(suf)]
    return w

def _norm_tokens(text):
    t = text.lower()
    t = re.sub(r"`[^`]*`", " ", t)
    t = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", t)
    t = re.sub(r"[^0-9a-zа-яё_-]+", " ", t)
    return {_stem(w) for w in t.split() if len(w) > 2 and w not in STOP}

def _append_unit(out, text, rel, line_no):
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) < 8 or set(text) <= set("-|: "):
        return
    toks = _norm_tokens(text)
    if len(toks) >= 2:
        where = "%s:%d" % (rel, line_no)
        out.append({"id": where, "text": text[:160], "tokens": toks, "where": where, "doc": rel})

def units(path, root=ROOT):
    """Извлечь пункты дока: bullets, #/## headings, table rows and meaningful paragraphs."""
    rel = os.path.relpath(path, root).replace("\\", "/")
    out = []
    try:
        lines = open(path, encoding="utf-8", errors="replace").read().splitlines()
    except OSError:
        return out

    in_fm = False
    in_code = False
    para = []
    para_start = None

    def flush_para():
        nonlocal para, para_start
        if para:
            _append_unit(out, " ".join(para), rel, para_start or 1)
            para = []
            para_start = None

    for i, ln in enumerate(lines, 1):
        s = ln.strip()
        if i == 1 and s == "---":
            in_fm = True
            continue
        if in_fm:
            if s == "---":
                in_fm = False
            continue
        if s.startswith("```"):
            flush_para()
            in_code = not in_code
            continue
        if in_code:
            continue
        if not s:
            flush_para()
            continue

        m = (re.match(r"^[-*+]\s+(.*)", s) or re.match(r"^#{1,4}\s+(.*)", s)
             or re.match(r"^\|\s*(.+?)\s*\|", s))
        if m:
            flush_para()
            _append_unit(out, m.group(1), rel, i)
            continue

        if set(s) <= set("-|: "):
            flush_para()
            continue
        if para_start is None:
            para_start = i
        para.append(s)

    flush_para()
    return out

def _jaccard(a, b):
    if not a or not b:
        return 0.0
    return len(a & b) / float(len(a | b))

def analyze(paths, root=ROOT, thr=0.4):
    """Кластеризовать пункты; вернуть {consensus, divergent, docs}."""
    all_units = []
    for p in paths:
        all_units.extend(units(p, root))
    clusters = []  # {rep: tokens(первого), members: [unit], docs: set}
    for u in all_units:
        best, best_sim = None, thr
        for c in clusters:
            sim = _jaccard(u["tokens"], c["rep"])
            if sim >= best_sim:
                best, best_sim = c, sim
        if best is not None:
            best["members"].append(u)
            best["docs"].add(u["doc"])
        else:
            clusters.append({"rep": u["tokens"], "members": [u], "docs": {u["doc"]}})
    consensus = sorted((c for c in clusters if len(c["docs"]) >= 2),
                       key=lambda c: -len(c["docs"]))
    divergent = [c for c in clusters if len(c["docs"]) == 1]
    docs = sorted({u["doc"] for u in all_units})
    return {"consensus": consensus, "divergent": divergent, "docs": docs, "n_units": len(all_units)}

SEMANTIC_THR = 0.65  # high-thr pre-cluster: only obvious paraphrase+stem matches settle mechanically

def _rep(cluster):
    """Longest-token member — same representative render() picks (:181)."""
    return max(cluster["members"], key=lambda u: len(u["tokens"]))

def _residue(res):
    """Split analyze() result into settled high-confidence clusters and the residue
    sent to the agent. Settled = clusters already in >=2 docs (res['consensus']).
    Residue = one representative per settled multi-member cluster + every divergent unit."""
    settled = res["consensus"]                      # high-confidence mechanical clusters, >=2 docs
    residue = [_rep(c) for c in settled]            # one rep per settled cluster (re-judgeable anchor)
    for c in res["divergent"]:                      # singletons (one member each by construction)
        residue.extend(c["members"])
    # de-dup by id, preserve order
    seen, uniq = set(), []
    for u in residue:
        if u["id"] not in seen:
            seen.add(u["id"]); uniq.append(u)
    return settled, uniq

AGENT_BATCH = 50            # ~40-60 units/call (cost bound, q017-...:70,103)
AGENT_ENV = "DOC_CONSENSUS_AGENT"  # shell command template; absent => no agent configured

_AGENT_PROMPT = (
    "You merge agent-written docs. Judge CONCEPTUAL identity between units across docs "
    "(same idea in different words), NOT lexical overlap. Return ONLY JSON:\n"
    '{"consensus":[{"ids":["<unit-id>",...],"rationale":"why one idea"}],'
    '"divergences":[{"id":"<unit-id>","claim":"...","docs":["..."],'
    '"reason":"why it stands alone","resolves":"what would settle it"}]}\n'
    "Units (JSON):\n"
)

def _run_agent(payload_json):
    """Shell out to the synthesizer agent; return raw stdout. Returns '' when no agent
    is configured (DOC_CONSENSUS_AGENT unset) — keeps --semantic degrade-safe and
    is the single seam tests monkeypatch."""
    cmd = os.environ.get(AGENT_ENV)
    if not cmd:
        return ""
    p = subprocess.run(cmd, shell=True, input=_AGENT_PROMPT + payload_json,
                       cwd=ROOT, capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    return p.stdout or ""

def _parse_agent(raw):
    """Tolerant: agent may wrap JSON in prose/fences. Extract outermost {...}."""
    if not raw:
        return {"consensus": [], "divergences": []}
    m = re.search(r"\{.*\}", raw, re.DOTALL)
    try:
        d = json.loads(m.group(0) if m else raw)
    except (ValueError, AttributeError):
        return {"consensus": [], "divergences": []}
    return {"consensus": d.get("consensus") or [], "divergences": d.get("divergences") or []}

def _semantic_pass(residue, budget=None):
    """Batch residue (~50/call), call agent, union consensus groups by shared unit-id.
    Returns (groups, divergences):
      groups: [{"ids": set(unit-id), "rationale": str}]
      divergences: {unit-id: {claim, docs, reason, resolves}}"""
    groups, divergences = [], {}
    n_batches = (len(residue) + AGENT_BATCH - 1) // AGENT_BATCH
    if budget is not None and n_batches > budget:
        raise ValueError("semantic budget exceeded: need %d agent calls, budget %d" % (n_batches, budget))
    for i in range(0, len(residue), AGENT_BATCH):
        batch = residue[i:i + AGENT_BATCH]
        payload = json.dumps(
            [{"id": u["id"], "doc": u["doc"], "where": u["where"], "text": u["text"]} for u in batch],
            ensure_ascii=False)
        parsed = _parse_agent(_run_agent(payload))
        for g in parsed["consensus"]:
            ids = set(g.get("ids") or [])
            if len(ids) < 2:
                continue
            merged = None
            for existing in groups:                 # union across batches by shared id
                if existing["ids"] & ids:
                    existing["ids"] |= ids
                    if not existing["rationale"]:
                        existing["rationale"] = g.get("rationale", "")
                    merged = existing
                    break
            if merged is None:
                groups.append({"ids": ids, "rationale": g.get("rationale", "")})
        for d in parsed["divergences"]:
            if d.get("id"):
                divergences[d["id"]] = d
    return groups, divergences

def _merge(settled, groups, all_units):
    """Transitive union of mechanical clusters + semantic groups by unit-id.
    Returns {'consensus': [{members:[unit], rationale:str, mechanical:bool}],
             'divergent_ids': set(unit-id left unmerged)}."""
    by_id = {u["id"]: u for u in all_units}
    # expand each settled cluster's full membership, keyed by representative id
    rep_to_members = {_rep(c)["id"]: c["members"] for c in settled}
    merged_consensus, used_ids = [], set()

    # 1) semantic groups, transitively absorbing mechanical clusters they touch
    for g in groups:
        members, ids = [], set()
        for uid in g["ids"]:
            for u in rep_to_members.get(uid, [by_id[uid]] if uid in by_id else []):
                if u["id"] not in ids:
                    ids.add(u["id"]); members.append(u)
        if len({u["doc"] for u in members}) >= 2:   # consensus must span >=2 docs
            merged_consensus.append({"members": members, "rationale": g["rationale"],
                                     "mechanical": False})
            used_ids |= ids

    # 2) settled mechanical clusters the agent never referenced -> keep as mechanical consensus
    for c in settled:
        if _rep(c)["id"] not in used_ids:
            merged_consensus.append({"members": c["members"], "rationale": "", "mechanical": True})
            used_ids |= {u["id"] for u in c["members"]}

    divergent_ids = {u["id"] for u in all_units} - used_ids
    return {"consensus": merged_consensus, "divergent_ids": divergent_ids}

def analyze_semantic(paths, root=ROOT, thr=SEMANTIC_THR, agent_label=None, budget=None):
    all_units = []
    for p in paths:
        all_units.extend(units(p, root))
    res = analyze(paths, root=root, thr=thr)          # high-thr mechanical pre-cluster
    settled, residue = _residue(res)
    groups, sem_div = _semantic_pass(residue, budget=budget)
    merged = _merge(settled, groups, all_units)
    by_id = {u["id"]: u for u in all_units}
    divergent = [by_id[i] for i in sorted(merged["divergent_ids"]) if i in by_id]
    return {"semantic": True, "consensus": merged["consensus"], "divergent": divergent,
            "divergence_detail": sem_div, "docs": sorted({u["doc"] for u in all_units}),
            "n_units": len(all_units), "agent": agent_label or os.environ.get(AGENT_ENV, "(none)")}

def render(res):
    if res.get("semantic"):
        return _render_semantic(res)
    L = []
    L.append("# Doc-consensus отчёт")
    L.append("")
    L.append("Документы (%d): %s" % (len(res["docs"]), ", ".join("`%s`" % d for d in res["docs"])))
    L.append("Пунктов всего: %d · консенсус-кластеров: %d · одиночных: %d"
             % (res["n_units"], len(res["consensus"]), len(res["divergent"])))
    L.append("")
    L.append("## Консенсус (пункты в >=2 документах) — кандидаты в mainline-описание")
    L.append("")
    if not res["consensus"]:
        L.append("_(общих пунктов не найдено при текущем пороге)_")
    for c in res["consensus"]:
        rep = max(c["members"], key=lambda u: len(u["tokens"]))
        L.append("- **%s**" % rep["text"])
        L.append("  - встречается в %d док.: %s" % (len(c["docs"]),
                 ", ".join("`%s`" % w for w in sorted(u["where"] for u in c["members"]))))
    L.append("")
    L.append("## Разногласия (пункт только в одном документе) — детализировать/обосновать (D-017)")
    L.append("")
    by_doc = {}
    for c in res["divergent"]:
        u = c["members"][0]
        by_doc.setdefault(u["doc"], []).append(u)
    for doc in sorted(by_doc):
        L.append("### `%s` — уникальные пункты (%d)" % (doc, len(by_doc[doc])))
        for u in by_doc[doc][:30]:
            L.append("- %s  _(%s)_" % (u["text"], u["where"]))
        if len(by_doc[doc]) > 30:
            L.append("- … ещё %d" % (len(by_doc[doc]) - 30))
        L.append("")
    return "\n".join(L)

def _render_semantic(res):
    """Семантический отчёт (--semantic). status: proposed — материал для котла,
    ничего не auto-accepted (D-017/D-018). Каждый консенсус несёт ОБА свидетельства:
    Jaccard-члены (file:line) + rationale агента."""
    L = []
    L.append("---")
    L.append("status: proposed")
    L.append("source-docs:")
    for d in res["docs"]:
        L.append("  - %s" % d)
    L.append("semantic-agent: %s" % res.get("agent", "(none)"))
    L.append("---")
    L.append("")
    L.append("# Doc-consensus отчёт (semantic)")
    L.append("")
    L.append("ничего не auto-accepted — материал для котла (D-017/D-018)")
    L.append("")
    L.append("Документы (%d): %s" % (len(res["docs"]), ", ".join("`%s`" % d for d in res["docs"])))
    L.append("Пунктов всего: %d · консенсус-кластеров: %d · одиночных: %d"
             % (res["n_units"], len(res["consensus"]), len(res["divergent"])))
    L.append("")
    L.append("## Консенсус (пункты в >=2 документах) — кандидаты в mainline-описание")
    L.append("")
    if not res["consensus"]:
        L.append("_(общих пунктов не найдено)_")
    for c in res["consensus"]:
        rep = _rep(c)
        L.append("- **%s**" % rep["text"])
        L.append("  - встречается в %d док.: %s" % (len({u["doc"] for u in c["members"]}),
                 ", ".join("`%s`" % w for w in sorted(u["where"] for u in c["members"]))))
        rationale = c.get("rationale") or ""
        if not rationale or c.get("mechanical"):
            rationale = rationale or "(механический матч)"
        L.append("  - почему это одна идея: %s" % rationale)
    L.append("")
    L.append("## Разногласия (пункт только в одном документе) — детализировать/обосновать (D-017)")
    L.append("")
    detail = res.get("divergence_detail") or {}
    by_doc = {}
    for u in res["divergent"]:
        by_doc.setdefault(u["doc"], []).append(u)
    for doc in sorted(by_doc):
        L.append("### `%s` — уникальные пункты (%d)" % (doc, len(by_doc[doc])))
        for u in by_doc[doc][:30]:
            d = detail.get(u["id"])
            if d:
                L.append("- %s  _(%s)_" % (u["text"], u["where"]))
                L.append("  - утверждение: %s" % d.get("claim", u["text"]))
                docs_ref = d.get("docs") or []
                if docs_ref:
                    L.append("  - док(и): %s" % ", ".join("`%s`" % x for x in docs_ref))
                L.append("  - причина: %s" % d.get("reason", ""))
                L.append("  - что разрешит: %s" % d.get("resolves", ""))
            else:
                L.append("- %s  _(%s)_" % (u["text"], u["where"]))
        if len(by_doc[doc]) > 30:
            L.append("- … ещё %d" % (len(by_doc[doc]) - 30))
        L.append("")
    return "\n".join(L)

def _topic_files(topic):
    p = subprocess.run([sys.executable, os.path.join(TOOLS, "variants.py"), "index"],
                       cwd=ROOT, capture_output=True, text=True, encoding="utf-8",
                       errors="replace", stdin=subprocess.DEVNULL)
    try:
        idx = json.loads(p.stdout or "{}")
    except ValueError:
        return []
    return [v["file"] for v in idx.get(topic, []) if v.get("file", "").endswith(".md")]

def _arg(a, flag, default=None):
    return a[a.index(flag) + 1] if flag in a and a.index(flag) + 1 < len(a) else default

def main():
    help_guard(__doc__)
    a = sys.argv[1:]
    if not a or a[0] != "report":
        print(__doc__)
        return 2
    thr = float(_arg(a, "--thr", "0.4"))
    out_path = _arg(a, "--out")
    files = []
    if "--files" in a:
        i = a.index("--files") + 1
        while i < len(a) and not a[i].startswith("--"):
            files.append(a[i])
            i += 1
    elif "--topic" in a:
        files = _topic_files(_arg(a, "--topic"))
    if len(files) < 2:
        print("Нужно >=2 документа (--files a.md b.md или --topic <topic> с >=2 вариантами).")
        return 2
    abs_files = [os.path.join(ROOT, f) if not os.path.isabs(f) else f for f in files]
    if "--semantic" in a:
        sem_thr = float(_arg(a, "--thr", str(SEMANTIC_THR)))
        sem_budget = _arg(a, "--semantic-budget")
        try:
            budget = int(sem_budget) if sem_budget is not None else None
        except ValueError:
            print("--semantic-budget должен быть целым числом")
            return 2
        try:
            res = analyze_semantic(abs_files, thr=sem_thr, budget=budget)
        except ValueError as exc:
            print(str(exc))
            return 1
    else:
        res = analyze(abs_files, thr=thr)
    text = render(res)
    # --divergence-out: вынести секцию разногласий в ОТДЕЛЬНЫЙ файл (D-017 — детализация в др. документе),
    # оставив в основном отчёте только консенсус/середину + ссылку. Пост-split по заголовку, render не трогаем.
    div_out = _arg(a, "--divergence-out")
    if div_out:
        marker = "## Разногласия"
        idx = text.find(marker)
        if idx != -1:
            ddest = div_out if os.path.isabs(div_out) else os.path.join(ROOT, div_out)
            os.makedirs(os.path.dirname(ddest) or ".", exist_ok=True)
            with open(ddest, "w", encoding="utf-8", newline="\n") as f:
                f.write("---\nstatus: proposed\nkind: divergence\n---\n\n"
                        "# Разногласия (вынесено из consensus, D-017 — детализировать/обосновать)\n\n"
                        + text[idx:] + "\n")
            text = (text[:idx].rstrip() + "\n\n> Разногласия вынесены в отдельный документ для детализации: `%s` (D-017).\n"
                    % os.path.relpath(ddest, ROOT))
            print("Разногласия → %s" % os.path.relpath(ddest, ROOT))
    if out_path:
        dest = out_path if os.path.isabs(out_path) else os.path.join(ROOT, out_path)
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        with open(dest, "w", encoding="utf-8", newline="\n") as f:
            f.write(text + "\n")
        print("Записано: %s" % os.path.relpath(dest, ROOT))
    else:
        print(text)
    return 0

if __name__ == "__main__":
    sys.exit(main())
