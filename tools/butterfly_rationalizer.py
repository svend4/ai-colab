#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ==========================================
# [FILE ID CARD]
# ID: tools.butterfly_rationalizer
# TYPE: active-script
# DOMAIN: core.synthesis
# DEPTH_LEVEL: 2
# SUMMARY: Compress cauldron graph without information loss; dry-run by default.
# ==========================================
"""Butterfly Rationalizer — сжатие котла без потери информации.

Исполняемая формула рационализации (data7: min K(K') при I(K') >= (1-eps)*I(K);
перенос гейта p70 из MERIDIAN, план docs/18 пункты A3+G1):
каждая операция сжатия проходит ГЕЙТ — если покрытие информации падает ниже
(1-eps) от исходного, операция отклоняется с объяснением.

Дубли ищутся двумя ярусами:
  1) точные/нормализованные — ключи docstoolkit.dedup (SHA-256/16, протестированный
     модуль lorenzo); при недоступности — локальный эквивалент;
  2) near-дубли — SimHash из semantic_engine (hamming < порога).

I (информация) = множество информативных токенов живых атомов.

CLI:
    python tools/butterfly_rationalizer.py                  # dry-run
    python tools/butterfly_rationalizer.py --eps 0.1 --hamming 6 --json
    python tools/butterfly_rationalizer.py --apply --force-truncate
"""

import argparse
import hashlib
import json
import os
import re
import sys

from _ioutil import configure_output, safe_write

GRAPH_FILE = os.path.join("indexes", "cauldron_graph.json")
DOCSTOOLKIT_PATH = os.environ.get("AI_COLAB_DOCSTOOLKIT", "")

_STOP = {"и", "в", "на", "с", "по", "не", "что", "это", "как", "а", "но",
         "для", "из", "у", "о", "же", "к", "то",
         "the", "a", "an", "of", "to", "in", "and", "or", "is", "are"}


def tokenize(text):
    return {w for w in re.findall(r"[a-zа-яё][a-zа-яё\-]{2,}", text.lower())
            if w not in _STOP}


def norm_key(text):
    """Нормализованный ключ дубля: docstoolkit.dedup если доступен, иначе локально."""
    if DOCSTOOLKIT_PATH:
        try:
            toolkit_path = os.path.abspath(DOCSTOOLKIT_PATH)
            if toolkit_path not in sys.path:
                sys.path.insert(0, toolkit_path)
            from docstoolkit.dedup.key import compute_key, DeduplicationStrategy
            return compute_key(text, DeduplicationStrategy.NORMALIZED).key_hash, "docstoolkit"
        except Exception:
            pass
    normalized = " ".join(text.split()).lower()
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:16], "local"


def sim_fingerprint(text):
    """SimHash из semantic_engine (Котёл); None если модуль недоступен."""
    try:
        from semantic_engine import AdvancedAlgorithms
        return AdvancedAlgorithms.simhash(text)
    except Exception:
        return None


def hamming(h1, h2):
    x = (h1 ^ h2) & ((1 << 64) - 1)
    return bin(x).count("1")


def load_graph(path):
    if not os.path.exists(path):
        raise FileNotFoundError("graph not found: %s" % path)
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError("cauldron graph must be a JSON list")
    return data


def info_of(atoms, skip=frozenset()):
    tokens = set()
    for idx, atom in enumerate(atoms):
        if idx in skip:
            continue
        tokens |= tokenize(atom.get("content", ""))
    return tokens


def rationalize(graph, eps=0.1, hamming_threshold=12):
    atoms = [a for a in graph if isinstance(a, dict) and a.get("content")]
    passthrough = [a for a in graph if not (isinstance(a, dict) and a.get("content"))]

    I0 = info_of(atoms)
    if not I0:
        return {"atoms": atoms, "passthrough": passthrough, "ops": [],
                "removed": set(), "I0": 0, "key_engine": "-", "rejected": 0}

    removed = set()
    ops = []
    rejected = 0

    def gate_ok(candidate_idx):
        new_tokens = info_of(atoms, removed | {candidate_idx})
        return len(new_tokens) >= (1 - eps) * len(I0), len(I0) - len(new_tokens)

    # --- ярус 1: точные/нормализованные дубли (ключи dedup) -------------------
    key_engine = None
    groups = {}
    for idx, atom in enumerate(atoms):
        key, eng = norm_key(atom["content"])
        key_engine = key_engine or eng
        groups.setdefault(key, []).append(idx)
    for key, idxs in groups.items():
        for extra in idxs[1:]:
            ok, loss = gate_ok(extra)
            if ok:
                removed.add(extra)
                ops.append({"op": "dup", "hash": atoms[extra].get("hash", "?"),
                            "reason": "нормализованный дубль ключа %s (потеря %d токенов)" % (key[:8], loss)})
            else:
                rejected += 1
                ops.append({"op": "reject", "hash": atoms[extra].get("hash", "?"),
                            "reason": "гейт: дубль, но удаление теряет %d токенов > eps" % loss})

    # --- ярус 2: near-дубли по SimHash ----------------------------------------
    prints = {}
    for idx, atom in enumerate(atoms):
        if idx in removed:
            continue
        fp = sim_fingerprint(atom["content"])
        if fp is not None:
            prints[idx] = fp
    idxs = sorted(prints)
    for a_pos, i in enumerate(idxs):
        if i in removed:
            continue
        for j in idxs[a_pos + 1:]:
            if j in removed:
                continue
            ham = hamming(prints[i], prints[j])
            if ham >= hamming_threshold:
                continue
            # кандидат на удаление — атом с меньшим числом уникальных токенов
            uniq_i = tokenize(atoms[i]["content"]) - info_of(atoms, removed | {i})
            uniq_j = tokenize(atoms[j]["content"]) - info_of(atoms, removed | {j})
            victim = i if len(uniq_i) <= len(uniq_j) else j
            ok, loss = gate_ok(victim)
            if ok:
                removed.add(victim)
                ops.append({"op": "near", "hash": atoms[victim].get("hash", "?"),
                            "reason": "near-дубль (hamming %d) атома %s; потеря %d токенов — гейт пропустил"
                                      % (ham, atoms[j if victim == i else i].get("hash", "?"), loss)})
                if victim == i:
                    break
            else:
                rejected += 1
                ops.append({"op": "reject", "hash": atoms[victim].get("hash", "?"),
                            "reason": "гейт: near-дубль (hamming %d), но потеря %d токенов уронит I ниже (1-eps)"
                                      % (ham, loss)})

    return {"atoms": atoms, "passthrough": passthrough, "ops": ops,
            "removed": removed, "I0": len(I0), "key_engine": key_engine or "-",
            "rejected": rejected}


def report_payload(result, graph_path, eps, hamming_threshold, applied):
    atoms = result["atoms"]
    removed = result["removed"]
    I_after = len(info_of(atoms, removed))
    return {
        "schema": "butterfly_rationalizer.v1",
        "graph": graph_path,
        "mode": "apply" if applied else "dry-run",
        "applied": applied,
        "eps": eps,
        "hamming_threshold": hamming_threshold,
        "key_engine": result["key_engine"],
        "atoms_before": len(atoms),
        "atoms_after": len(atoms) - len(removed),
        "removed": len(removed),
        "rejected_by_gate": result["rejected"],
        "I0_tokens": result["I0"],
        "I_after_tokens": I_after,
        "info_kept_pct": round(100.0 * I_after / result["I0"], 1) if result["I0"] else 100.0,
        "ops": result["ops"],
    }


def render_text(p):
    lines = [
        "BUTTERFLY RATIONALIZER",
        "mode: %s" % p["mode"],
        "graph: %s" % p["graph"],
        "key engine: %s" % p["key_engine"],
        "eps: %.2f  hamming<: %s" % (p["eps"], p["hamming_threshold"]),
        "atoms: %s -> %s (removed %s, rejected by gate %s)"
        % (p["atoms_before"], p["atoms_after"], p["removed"], p["rejected_by_gate"]),
        "info: %s -> %s tokens (kept %.1f%%)"
        % (p["I0_tokens"], p["I_after_tokens"], p["info_kept_pct"]),
        "ops:",
    ]
    for op in p["ops"][:12]:
        lines.append("  [%s] %s — %s" % (op["op"], op["hash"], op["reason"]))
    if len(p["ops"]) > 12:
        lines.append("  ... ещё %d операций (см. --json)" % (len(p["ops"]) - 12))
    if not p["applied"]:
        lines.append("note: dry-run only; use --apply --force-truncate to write graph")
    return "\n".join(lines)


def parse_args(argv):
    parser = argparse.ArgumentParser(description="Compress cauldron graph without information loss (gated).")
    parser.add_argument("--graph", default=GRAPH_FILE, help="Graph JSON path to read/update.")
    parser.add_argument("--eps", type=float, default=0.1,
                        help="Допустимая доля потери информации (0..1), гейт I >= (1-eps)*I0.")
    parser.add_argument("--hamming", type=int, default=12,
                        help="Порог SimHash-близости для near-дублей (меньше = строже; "
                             "замер: 1 слово из 10 даёт ~6, чужие тексты ~33).")
    parser.add_argument("--apply", action="store_true", help="Write the compressed graph. Default is dry-run.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable report.")
    parser.add_argument("--force-truncate", action="store_true",
                        help="Allow safe_write to shrink the graph file (required with --apply).")
    return parser.parse_args(argv)


def main(argv=None):
    configure_output()
    args = parse_args(sys.argv[1:] if argv is None else argv)

    try:
        graph = load_graph(args.graph)
        result = rationalize(graph, args.eps, args.hamming)
        if args.apply:
            kept = [a for i, a in enumerate(result["atoms"]) if i not in result["removed"]]
            content = json.dumps(kept + result["passthrough"], ensure_ascii=False, indent=2) + "\n"
            safe_write(args.graph, content, force_truncate=args.force_truncate)
        payload = report_payload(result, args.graph, args.eps, args.hamming, args.apply)
    except Exception as exc:
        if args.json:
            print(json.dumps({"schema": "butterfly_rationalizer.v1", "ok": False, "error": str(exc)},
                             ensure_ascii=False))
        else:
            sys.stderr.write("ERROR: %s\n" % exc)
        return 1

    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(render_text(payload))
    return 0


if __name__ == "__main__":
    sys.exit(main())
