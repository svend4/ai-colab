#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
result_intake — read-only classifier for landed/outbox workflow outputs.

Goal: before the top layer verifies or synthesizes a result, classify what kind of
result it is. This keeps intake from treating governance, build patches, variants,
external-code notes and plain reports as the same object.

CLI:
    python tools/result_intake.py classify <path> [--json]
"""
import json
import os
import re
import sys
from _ioutil import configure_output

from _canon import parse_fm

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

CLASSES = [
    "read-only-report",
    "variant",
    "docs-change",
    "build-change",
    "governance",
    "external-code",
]

PRIORITY = ["external-code", "governance", "build-change", "variant", "docs-change", "read-only-report"]

configure_output()

def _rel(path, root=ROOT):
    return os.path.relpath(path, root).replace("\\", "/")

def _read(path):
    with open(path, encoding="utf-8", errors="replace") as f:
        return f.read()

def _bump(scores, signals, cls, points, reason):
    scores[cls] += points
    signals.append({"class": cls, "points": points, "reason": reason})

def _extract_repo_paths(text):
    hits = []
    # Conservative: repo-like paths, not arbitrary prose with slashes.
    pat = r"(?<![A-Za-z0-9_./-])(?:tools|docs|tasks|queues|reports|drivers|core|portals|sandbox|streams|темы)/[^\s`'\")]+"
    for m in re.finditer(pat, text):
        item = m.group(0).rstrip(".,;:")
        if item not in hits:
            hits.append(item)
        if len(hits) >= 20:
            break
    return hits

def _evidence(text, fm):
    return {
        "has_front_matter": bool(fm),
        "has_applied_instructions": bool(re.search(r"(?mi)^##\s+Applied instructions\b|^Applied instructions\s*:", text)),
        "has_checks": bool(re.search(r"(?mi)^##\s+Checks\b|^Checks\s*:", text)),
        "has_status_proposed": (fm.get("status") == "proposed" or bool(re.search(r"(?mi)^status\s*:\s*proposed\b", text))),
        "mentioned_paths": _extract_repo_paths(text),
    }

def _recommended(relpath, cls, fm):
    checks = []
    if relpath.endswith(".md"):
        checks.append("python tools\\instructions.py check-report %s" % relpath.replace("/", "\\"))
    if cls == "read-only-report":
        checks += [
            "python tools\\validate.py",
            "python tools\\generate.py --check",
        ]
    elif cls == "variant":
        checks += [
            "python tools\\synthesis_helper.py report <topic> --out темы\\<topic>-synthesis.md",
            "python tools\\doc_consensus.py report --files <a.md> <b.md> --out reports\\doc-consensus.md",
            "python tools\\validate.py",
        ]
    elif cls == "docs-change":
        checks += [
            "python tools\\validate.py",
            "python tools\\generate.py --check",
            "python tools\\top.py assurance all --json",
        ]
    elif cls == "build-change":
        task = fm.get("task") or "<T-id>"
        checks += [
            "python tools\\top.py work-mode codex %s --parallel --hot-files" % task,
            "python -m py_compile <changed-python-files>",
            "python tools\\validate.py",
            "python tools\\generate.py --check",
        ]
    elif cls == "governance":
        checks += [
            "python tools\\instructions.py preflight codex %s" % (fm.get("task") or "<T-id>"),
            "python tools\\validate.py",
            "human approval required before accepted status",
        ]
    elif cls == "external-code":
        checks += [
            "python tools\\sandbox.py intake --help",
            "python tools\\validate.py",
            "execute stays OFF unless D-014/human preflight allows it",
        ]
    return checks

def classify_path(path, root=ROOT):
    abs_path = path if os.path.isabs(path) else os.path.join(root, path)
    text = _read(abs_path)
    relpath = _rel(abs_path, root)
    low = text.lower()
    rel_low = relpath.lower()
    fm = parse_fm(text)
    scores = {cls: 0 for cls in CLASSES}
    signals = []

    fm_type = (fm.get("type") or "").lower()
    title = (fm.get("title") or "").lower()
    task = (fm.get("task") or "").lower()

    if rel_low.startswith(("queues/outbox/", "reports/")) or fm_type in ("report", "review", "audit"):
        _bump(scores, signals, "read-only-report", 2, "outbox/report/audit surface")
    if "# " in text and rel_low.endswith(".md"):
        _bump(scores, signals, "docs-change", 1, "markdown document output")

    variant_terms = ["fork", "stream", "alternative", "disagreement", "разноглас", "вариант", "форк"]
    if rel_low.startswith("streams/") or any(term in low for term in variant_terms):
        _bump(scores, signals, "variant", 4, "variant/fork/disagreement vocabulary")

    governance_terms = [
        "human approval", "accepted", "proposed decision", "ratification", "d-014", "d-006",
        "решение", "утвержд", "accepted status", "human gate",
    ]
    if fm_type == "decision" or rel_low.startswith("decisions/") or "decisions.md" in rel_low:
        _bump(scores, signals, "governance", 5, "decision surface")
    elif any(term in low for term in governance_terms):
        _bump(scores, signals, "governance", 5, "governance/human-approval vocabulary")

    external_terms = ["external code", "svend4", "source intake", "quarantine", "внешн", "песочниц"]
    if rel_low.startswith("sandbox/") or any(term in low for term in external_terms):
        _bump(scores, signals, "external-code", 5, "external code / sandbox vocabulary")
    elif "execute" in low and "sandbox" in low:
        _bump(scores, signals, "external-code", 3, "execute+sandbox requires external-code handling")

    # Build-change must mean the result claims code/tool/test changes, not just
    # that its Checks section mentions tools. Generic commands like
    # `python tools\validate.py` are deliberately weak signals.
    build_claim = re.search(
        r"(?is)\b(added|created|updated|changed|fixed|implemented|добав\w*|созда\w*|обнов\w*|исправ\w*|реализ\w*)"
        r".{0,45}(?:`?(?:tools|drivers)/[^`\s]+\.py`?|test_[A-Za-z0-9_]+\.py|py_compile|regression-test)",
        text,
    )
    line_build_claim = any(
        re.search(r"(?i)(added|created|updated|changed|fixed|implemented|добав\w*|созда\w*|обнов\w*|исправ\w*|реализ\w*)", ln)
        and re.search(r"(?:tools|drivers)/[^`\s]+\.py|test_[A-Za-z0-9_]+\.py|py_compile|regression-test", ln)
        and "потому" not in ln.lower()
        and " next" not in ln.lower()
        for ln in text.splitlines()
    )
    if build_claim or line_build_claim:
        _bump(scores, signals, "build-change", 6, "explicit code/tool/test change claim")
    elif re.search(r"(?mi)^python\s+tools[\\/].+\.py", text):
        _bump(scores, signals, "build-change", 1, "tool command mentioned in checks")

    docs_terms = ["docs/", "темы/", "documentation", "документац", "readme", "manual", "методолог"]
    if any(term in low for term in docs_terms):
        _bump(scores, signals, "docs-change", 3, "documentation/topic vocabulary")

    if not any(scores.values()):
        _bump(scores, signals, "read-only-report", 1, "fallback: no stronger signal")

    # Pick by score, then by explicit priority for ties.
    best = sorted(CLASSES, key=lambda cls: (-scores[cls], PRIORITY.index(cls)))[0]
    top = scores[best]
    second = max((v for k, v in scores.items() if k != best), default=0)
    if top >= 6 and top - second >= 2:
        confidence = "high"
    elif top >= 3:
        confidence = "medium"
    else:
        confidence = "low"

    ev = _evidence(text, fm)
    return {
        "schema": "result_intake.v1",
        "path": relpath,
        "class": best,
        "confidence": confidence,
        "scores": scores,
        "front_matter": fm,
        "evidence": ev,
        "signals": signals,
        "recommended_next_checks": _recommended(relpath, best, fm),
    }

def render(result):
    lines = []
    lines.append("# Result intake")
    lines.append("")
    lines.append("path: %s" % result["path"])
    lines.append("class: %s" % result["class"])
    lines.append("confidence: %s" % result["confidence"])
    lines.append("")
    lines.append("## Evidence")
    for key, value in result["evidence"].items():
        if key == "mentioned_paths":
            lines.append("- %s: %d" % (key, len(value)))
        else:
            lines.append("- %s: %s" % (key, value))
    lines.append("")
    lines.append("## Signals")
    for s in result["signals"][:12]:
        lines.append("- %s +%s: %s" % (s["class"], s["points"], s["reason"]))
    lines.append("")
    lines.append("## Recommended next checks")
    for c in result["recommended_next_checks"]:
        lines.append("- %s" % c)
    return "\n".join(lines)

def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or argv[0] != "classify" or len(argv) < 2:
        print(__doc__)
        return 2
    json_out = "--json" in argv
    paths = [a for a in argv[1:] if a != "--json"]
    if len(paths) != 1:
        print("Нужен ровно один путь: result_intake.py classify <path> [--json]")
        return 2
    try:
        result = classify_path(paths[0])
    except OSError as exc:
        print("ОШИБКА: %s" % exc)
        return 1
    if json_out:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(render(result))
    return 0

if __name__ == "__main__":
    sys.exit(main())