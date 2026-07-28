#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ==========================================
# [FILE ID CARD]
# ID: tools.butterfly_graph_builder
# TYPE: active-script
# DOMAIN: core.synthesis
# DEPTH_LEVEL: 2
# SUMMARY: Builds a cauldron atom graph from markdown reports; dry-run by default.
# ==========================================
"""Butterfly Graph Builder — атомизация markdown-отчетов в локальный смысловой граф.

Инструмент читает `.md` файлы из очереди/архива, разбивает их на параграфы-атомы
и готовит обновление `indexes/cauldron_graph.json`.

CLI:
    python tools/butterfly_graph_builder.py
    python tools/butterfly_graph_builder.py --apply
    python tools/butterfly_graph_builder.py --source-dir queues/outbox --graph indexes/cauldron_graph.json --json

Без `--apply` рабочее дерево не меняется. Это важно для multi-agent режима:
агент сначала видит, что будет записано, а только потом явно применяет результат.
"""

import argparse
import hashlib
import json
import os
import sys

from _ioutil import configure_output, safe_write


SOURCE_DIR = "queues/outbox"
GRAPH_FILE = os.path.join("indexes", "cauldron_graph.json")


def generate_hash(text):
    """Stable short hash for atom identity.

    ФИКС Б4: md5/8 = 32 бита — по парадоксу дней рождения коллизии становятся
    регулярными уже при ~65 тыс. атомов, и новые атомы МОЛЧА теряются в дедупе.
    Теперь md5/16 (64 бита); старые 8-символьные хэши распознаются по префиксу
    (см. проверку дедупа в build_graph).
    """
    normalized = "\n".join(line.rstrip() for line in text.strip().splitlines())
    return hashlib.md5(normalized.encode("utf-8")).hexdigest()[:16]


def read_markdown(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except UnicodeDecodeError:
        with open(path, "r", encoding="cp1251", errors="ignore") as f:
            return f.read()


def load_graph(path):
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError("cauldron graph must be a JSON list")
    return data


def iter_atoms(content):
    content = content.replace("\r\n", "\n")
    for paragraph in content.split("\n\n"):
        atom = paragraph.strip()
        if len(atom) < 30:
            continue
        if atom.startswith("---") or atom.startswith("status: historical"):
            continue
        yield atom


def build_graph(source_dir=SOURCE_DIR, graph_path=GRAPH_FILE, limit=0):
    if not os.path.isdir(source_dir):
        raise FileNotFoundError("source directory not found: %s" % source_dir)

    graph_db = load_graph(graph_path)
    existing_hashes = {atom.get("hash") for atom in graph_db if isinstance(atom, dict)}
    new_atoms = []
    files = []

    for filename in sorted(os.listdir(source_dir)):
        if not filename.endswith(".md"):
            continue
        filepath = os.path.join(source_dir, filename)
        if not os.path.isfile(filepath):
            continue
        files.append(filename)

        for content in iter_atoms(read_markdown(filepath)):
            atom_hash = generate_hash(content)
            # совместимость: старые атомы хранят 8-символьные хэши
            if atom_hash in existing_hashes or atom_hash[:8] in existing_hashes:
                continue
            atom = {
                "hash": atom_hash,
                "source_file": filename,
                "content": content,
                "spiral_layer": 0,
                "type": "raw_matter",
                "tags": [],
                "links": []
            }
            
            try:
                from semantic_engine import AdvancedAlgorithms
                atom["tags"] = AdvancedAlgorithms.extract_textrank_keywords(content, top_n=3)

                # Knowledge Graph: честный Contradiction Engine (ФИКС Б1).
                # Старый критерий «Левенштейн > 0.8» был инвертирован:
                # реальные противоречия текстуально близки (~0.06), а далёкие
                # формулировки — чаще согласие. Теперь: общий концепт +
                # БЛИЗКИЕ тексты (SimHash) + разная полярность = противоречие;
                # та же полярность = поддержка.
                new_tags = set(atom["tags"])
                for existing_atom in graph_db:
                    common_tags = set(existing_atom.get("tags", [])).intersection(new_tags)
                    if not common_tags:
                        continue
                    check = AdvancedAlgorithms.contradiction_check(
                        content, existing_atom.get("content", ""))
                    if check["contradicts"]:
                        atom["links"].append({
                            "type": "contradicts",
                            "target": existing_atom["hash"],
                            "reason": "shared concept '%s': close texts (hamming %s) with opposite polarity"
                                      % (sorted(common_tags)[0], check["hamming"]),
                        })
                    elif check["related"]:
                        atom["links"].append({
                            "type": "supports",
                            "target": existing_atom["hash"],
                            "reason": "shared concept '%s': close texts (hamming %s), same polarity"
                                      % (sorted(common_tags)[0], check["hamming"]),
                        })
            except ImportError:
                pass
                
            graph_db.append(atom)
            new_atoms.append(atom)
            existing_hashes.add(atom_hash)
            if limit and len(new_atoms) >= limit:
                return {
                    "graph": graph_db,
                    "files": files,
                    "new_atoms": new_atoms,
                    "limited": True,
                }

    return {
        "graph": graph_db,
        "files": files,
        "new_atoms": new_atoms,
        "limited": False,
    }


def report_payload(result, source_dir, graph_path, applied):
    existing_atoms = len(result["graph"]) - len(result["new_atoms"])
    return {
        "schema": "butterfly_graph_builder.v1",
        "source_dir": source_dir,
        "graph": graph_path,
        "mode": "apply" if applied else "dry-run",
        "applied": applied,
        "files": len(result["files"]),
        "existing_atoms": existing_atoms,
        "new_atoms": len(result["new_atoms"]),
        "total_atoms": len(result["graph"]),
        "limited": bool(result["limited"]),
    }


def render_text(payload):
    lines = [
        "BUTTERFLY GRAPH BUILDER",
        "mode: %s" % payload["mode"],
        "source: %s" % payload["source_dir"],
        "graph: %s" % payload["graph"],
        "files: %s" % payload["files"],
        "existing_atoms: %s" % payload["existing_atoms"],
        "new_atoms: %s" % payload["new_atoms"],
        "total_atoms: %s" % payload["total_atoms"],
    ]
    if payload["limited"]:
        lines.append("note: stopped by --limit")
    if not payload["applied"]:
        lines.append("note: dry-run only; use --apply to write graph")
    return "\n".join(lines)


def parse_args(argv):
    parser = argparse.ArgumentParser(description="Build cauldron atom graph from markdown reports.")
    parser.add_argument("--source-dir", default=SOURCE_DIR, help="Directory with markdown source reports.")
    parser.add_argument("--graph", default=GRAPH_FILE, help="Graph JSON path to read/update.")
    parser.add_argument("--limit", type=int, default=0, help="Limit new atoms for preview/testing; 0 means no limit.")
    parser.add_argument("--apply", action="store_true", help="Write the graph file. Default is dry-run.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable report.")
    parser.add_argument("--force-truncate", action="store_true", help="Allow safe_write to shrink an existing graph.")
    return parser.parse_args(argv)


def main(argv=None):
    configure_output()
    args = parse_args(sys.argv[1:] if argv is None else argv)

    try:
        result = build_graph(args.source_dir, args.graph, args.limit)
        if args.apply:
            out_dir = os.path.dirname(args.graph)
            if out_dir:
                os.makedirs(out_dir, exist_ok=True)
            content = json.dumps(result["graph"], ensure_ascii=False, indent=2) + "\n"
            safe_write(args.graph, content, force_truncate=args.force_truncate)
        payload = report_payload(result, args.source_dir, args.graph, args.apply)
    except Exception as exc:
        if args.json:
            print(json.dumps({"schema": "butterfly_graph_builder.v1", "ok": False, "error": str(exc)}, ensure_ascii=False))
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