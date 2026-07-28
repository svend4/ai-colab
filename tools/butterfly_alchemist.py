#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ==========================================
# [FILE ID CARD]
# ID: tools.butterfly_alchemist
# TYPE: active-script
# DOMAIN: core.synthesis
# DEPTH_LEVEL: 2
# SUMMARY: Creates a synthesis prompt from cauldron graph atoms; dry-run by default.
# ==========================================
"""Butterfly Alchemist — безопасная генерация задач синтеза из смыслового графа.

Инструмент выбирает несколько атомов из `indexes/cauldron_graph.json` и собирает
из них markdown-задание для агента/человека. По умолчанию он ничего не пишет:
запись в `topics/` или явный файл выполняется только с `--apply`.

CLI:
    python tools/butterfly_alchemist.py
    python tools/butterfly_alchemist.py --seed 42
    python tools/butterfly_alchemist.py --apply --out topics/alchemy_synthesis_demo.md
"""

import argparse
import json
import os
import random
import sys
from datetime import datetime

from _ioutil import configure_output, safe_write


GRAPH_FILE = os.path.join("indexes", "cauldron_graph.json")
TOPICS_DIR = "topics"


def load_graph(path):
    if not os.path.exists(path):
        raise FileNotFoundError("graph not found: %s" % path)
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError("cauldron graph must be a JSON list")
    return data


def select_atoms(graph_db, sample_size=3, seed=None):
    atoms = [atom for atom in graph_db if isinstance(atom, dict) and atom.get("content")]
    if sample_size < 1:
        raise ValueError("sample size must be positive")
    if len(atoms) < sample_size:
        raise ValueError("not enough atoms: need %s, found %s" % (sample_size, len(atoms)))
    rng = random.Random(seed)
    return rng.sample(atoms, sample_size)


# --- Стратегия «пробел» (A1 из мастер-плана MERIDIAN docs/18) -----------------
# А+Б = самая БЛИЗКАЯ пара атомов, ещё дающая нетривиальный синтез;
# В (и далее) = дальний КАТАЛИЗАТОР — атом с минимальной средней близостью
# к уже выбранным (приносит третье измерение). Близость — TF-IDF-косинус
# по содержимому (stdlib-only, в духе принципов тулкита).

_GAP_STOP = {"и", "в", "на", "с", "по", "не", "что", "это", "как", "а", "но",
             "для", "из", "у", "о", "же", "к", "то",
             "the", "a", "an", "of", "to", "in", "and", "or", "is", "are"}


def _gap_tokenize(text):
    import re
    return [w for w in re.findall(r"[a-zа-яё][a-zа-яё\-]{2,}", text.lower())
            if w not in _GAP_STOP]


def _gap_vectors(contents):
    import math
    from collections import Counter
    docs = [Counter(_gap_tokenize(c)) for c in contents]
    df = Counter()
    for d in docs:
        for t in d:
            df[t] += 1
    n = len(docs)
    vecs = []
    for d in docs:
        total = max(sum(d.values()), 1)
        vecs.append({t: (c / total) * (math.log((n + 1) / (df[t] + 1)) + 1.0)
                     for t, c in d.items()})
    return vecs


def _gap_cos(a, b):
    import math
    common = set(a) & set(b)
    if not common:
        return 0.0
    dot = sum(a[t] * b[t] for t in common)
    na = math.sqrt(sum(v * v for v in a.values()))
    nb = math.sqrt(sum(v * v for v in b.values()))
    return dot / (na * nb) if na and nb else 0.0


def select_atoms_by_gap(graph_db, sample_size=3, gap_rank=0):
    """Осмысленный выбор вместо лотереи: близкая пара + дальние катализаторы.

    gap_rank=0 берёт сильнейшую пару; 1 — следующую и т.д. (для серии заданий).
    Пары с косинусом >= 0.999 пропускаются как дубли.
    """
    atoms = [atom for atom in graph_db if isinstance(atom, dict) and atom.get("content")]
    if sample_size < 1:
        raise ValueError("sample size must be positive")
    if len(atoms) < sample_size:
        raise ValueError("not enough atoms: need %s, found %s" % (sample_size, len(atoms)))
    if sample_size == 1 or len(atoms) < 2:
        return [atoms[gap_rank % len(atoms)]]

    vecs = _gap_vectors([a.get("content", "") for a in atoms])
    pairs = []
    for i in range(len(atoms)):
        for j in range(i + 1, len(atoms)):
            c = _gap_cos(vecs[i], vecs[j])
            if c < 0.999:
                pairs.append((c, i, j))
    if not pairs:
        return atoms[:sample_size]
    pairs.sort(key=lambda p: -p[0])
    _, i, j = pairs[gap_rank % len(pairs)]

    chosen = [i, j]
    while len(chosen) < sample_size:
        best_k, best_score = None, None
        for k in range(len(atoms)):
            if k in chosen:
                continue
            avg = sum(_gap_cos(vecs[k], vecs[m]) for m in chosen) / len(chosen)
            if best_score is None or avg < best_score:
                best_score, best_k = avg, k
        chosen.append(best_k)
    return [atoms[k] for k in chosen[:sample_size]]


def default_output_path(out_dir, created_at):
    stamp = created_at.strftime("%Y%m%d_%H%M%S")
    return os.path.join(out_dir, "alchemy_synthesis_%s.md" % stamp)


def format_atom(atom, index):
    return "%s. Источник: `%s` / hash `%s`\n   > %s" % (
        index,
        atom.get("source_file", "?"),
        atom.get("hash", "?"),
        atom.get("content", "").replace("\n", "\n   > "),
    )


def concept_labels(n):
    """ФИКС Б5: метки под любой sample_size (А, Б, В, Г, Д…), а не только 3."""
    return [chr(ord("А") + i) for i in range(n)]


def build_question(labels):
    """Вопрос синтеза строится из фактических меток, без ссылок на несуществующие концепты."""
    if len(labels) >= 3:
        extra = "" if len(labels) == 3 else " (остальные концепты — дополнительные ограничения)"
        return ("Вопрос: как концепт %s может решить проблему из концепта %s, "
                "используя метод или ограничение из концепта %s%s?"
                % (labels[0], labels[1], labels[2], extra))
    if len(labels) == 2:
        return "Вопрос: как концепт %s может решить проблему из концепта %s?" % (labels[0], labels[1])
    return "Вопрос: какую проверяемую гипотезу порождает концепт %s?" % labels[0]


def build_markdown(sample, graph_path, created_at):
    concepts = []
    for idx, atom in enumerate(sample, 1):
        concepts.append(format_atom(atom, idx))

    labels = concept_labels(len(sample))
    concept_lines = []
    for label, atom in zip(labels, sample):
        concept_lines.append("Концепт %s: %s" % (label, atom.get("content", "")))

    return """---
status: proposed
type: synthesis-task
source: tools/butterfly_alchemist.py
---
# Алхимический синтез

**Дата генерации:** %s
**Источник данных:** `%s`

## Исходные атомы

%s

## Задача для агента

Синтезировать эти переменные в единый концепт, функцию или проверяемую гипотезу.

```text
АЛХИМИЧЕСКИЙ СИНТЕЗ
-------------------
Попробуй найти новую архитектурную связь между независимыми концептами:
%s

%s
```

## Следующий шаг

Если идея выглядит полезной, оформить её как вариант в `streams/<topic>/<agent>/`
или как задачу `tasks/T-*.md`, а не записывать сразу в canonical-документ.
""" % (
        created_at.isoformat(timespec="seconds"),
        graph_path,
        "\n\n".join(concepts),
        "\n\n".join(concept_lines),
        build_question(labels),
    )


def parse_created_at(value):
    if not value:
        return datetime.now()
    return datetime.fromisoformat(value)


def payload(sample, graph_path, output_path, applied):
    return {
        "schema": "butterfly_alchemist.v1",
        "graph": graph_path,
        "mode": "apply" if applied else "dry-run",
        "applied": applied,
        "output": output_path,
        "sample": [
            {
                "hash": atom.get("hash"),
                "source_file": atom.get("source_file"),
                "preview": atom.get("content", "")[:120],
            }
            for atom in sample
        ],
    }


def render_text(data):
    lines = [
        "BUTTERFLY ALCHEMIST",
        "mode: %s" % data["mode"],
        "strategy: %s" % data.get("strategy", "random"),
        "graph: %s" % data["graph"],
        "output: %s" % data["output"],
        "sample:",
    ]
    for idx, atom in enumerate(data["sample"], 1):
        lines.append("  %s. %s %s" % (idx, atom.get("hash") or "?", atom.get("source_file") or "?"))
    if not data["applied"]:
        lines.append("note: dry-run only; use --apply to write markdown task")
    return "\n".join(lines)


def parse_args(argv):
    parser = argparse.ArgumentParser(description="Create a synthesis task from cauldron graph atoms.")
    parser.add_argument("--graph", default=GRAPH_FILE, help="Input cauldron graph JSON.")
    parser.add_argument("--out-dir", default=TOPICS_DIR, help="Output directory when --out is omitted.")
    parser.add_argument("--out", help="Explicit output markdown path.")
    parser.add_argument("--sample-size", type=int, default=3, help="Number of atoms to combine.")
    parser.add_argument("--strategy", choices=("random", "gap"), default="random",
                        help="random = rng.sample (как раньше); gap = близкая пара + дальний катализатор.")
    parser.add_argument("--gap-rank", type=int, default=0,
                        help="Для --strategy gap: взять N-ю по силе пару (0 = сильнейшая).")
    parser.add_argument("--seed", help="Deterministic random seed for reproducible selection.")
    parser.add_argument("--created-at", help="ISO timestamp for deterministic tests/reports.")
    parser.add_argument("--apply", action="store_true", help="Write markdown output. Default is dry-run.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable report.")
    parser.add_argument("--force-truncate", action="store_true", help="Allow safe_write to shrink an existing output file.")
    return parser.parse_args(argv)


def main(argv=None):
    configure_output()
    args = parse_args(sys.argv[1:] if argv is None else argv)

    try:
        created_at = parse_created_at(args.created_at)
        graph = load_graph(args.graph)
        if args.strategy == "gap":
            sample = select_atoms_by_gap(graph, args.sample_size, args.gap_rank)
        else:
            sample = select_atoms(graph, args.sample_size, args.seed)
        out_path = args.out or default_output_path(args.out_dir, created_at)
        content = build_markdown(sample, args.graph, created_at)

        if args.apply:
            out_dir = os.path.dirname(out_path)
            if out_dir:
                os.makedirs(out_dir, exist_ok=True)
            safe_write(out_path, content, force_truncate=args.force_truncate)

        data = payload(sample, args.graph, out_path, args.apply)
        data["strategy"] = args.strategy
    except Exception as exc:
        if args.json:
            print(json.dumps({"schema": "butterfly_alchemist.v1", "ok": False, "error": str(exc)}, ensure_ascii=False))
        else:
            sys.stderr.write("ERROR: %s\n" % exc)
        return 1

    if args.json:
        print(json.dumps(data, ensure_ascii=False, indent=2))
    else:
        print(render_text(data))
    return 0


if __name__ == "__main__":
    sys.exit(main())