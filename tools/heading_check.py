"""
# ==========================================
# [FILE ID CARD]
# ID: tools.heading_check
# TYPE: active-script
# DOMAIN: core
# DEPTH_LEVEL: 1
# SUMMARY: Скрипт heading_check.py. Описание сгенерировано автоматически.
# ==========================================
"""
HELP = """heading_check.py — внутренняя структура файла (C-11 «файл-как-дерево») — heading-lint + нумерация.

Из architecture-fundamentals §4 + razbor-consensus C-11: длинный файл — это дерево (метаданные →
тело → хвост, общее→частное), и крупные доки несут АБСОЛЮТНУЮ dotted-decimal нумерацию (1, 1.2, 1.2.3).
Линтит: пустые заголовки, пропуск уровней (# → ###), крупные доки (>порог строк) без нумерации.
Дополняет header.py (визитка ЕСТЬ) проверкой ВНУТРЕННЕЙ навигации файла.

CLI:
    python tools/heading_check.py            # отчёт по docs/+topics/ (exit 1 если структурные ошибки)
    python tools/heading_check.py <file>      # один файл
    python tools/heading_check.py --json
"""
import os
import re
import sys
import glob

os.environ.setdefault("PYTHONUTF8", "1")
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from _ioutil import configure_output
from _cli import help_guard

configure_output()
import json

LARGE_LINES = 300          # выше этого крупному доку нужна нумерация
HEAD_RE = re.compile(r"^(#{1,6})\s*(.*?)\s*$")
NUM_RE = re.compile(r"^\d+(\.\d+)*\.?\s")     # «1 », «1.2 », «1.2.3. »
FENCE_RE = re.compile(r"^```")


def _headings(text):
    """Заголовки вне code-fence: [(level, text, lineno)]."""
    out, in_fence = [], False
    for i, line in enumerate(text.splitlines(), 1):
        if FENCE_RE.match(line):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        m = HEAD_RE.match(line)
        if m:
            out.append((len(m.group(1)), m.group(2), i))
    return out


def check_file(path):
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            text = f.read()
    except OSError:
        return []
    rel = os.path.relpath(path, ROOT).replace("\\", "/")
    heads = _headings(text)
    n_lines = text.count("\n") + 1
    issues = []
    prev = 0
    for lvl, htext, ln in heads:
        if not htext:
            issues.append({"where": "%s:%d" % (rel, ln), "kind": "empty-heading",
                           "msg": "пустой заголовок (%s)" % ("#" * lvl)})
        if prev and lvl > prev + 1:
            issues.append({"where": "%s:%d" % (rel, ln), "kind": "skipped-level",
                           "msg": "пропуск уровня %d→%d (%s)" % (prev, lvl, htext[:30])})
        prev = lvl
    # крупный док без нумерации
    body_heads = [h for h in heads if h[0] >= 2]
    if n_lines > LARGE_LINES and body_heads:
        numbered = sum(1 for _l, t, _n in body_heads if NUM_RE.match(t))
        if numbered < len(body_heads) // 2:
            issues.append({"where": rel, "kind": "large-no-numbering",
                           "msg": "крупный док (%d строк) без нумерации (%d/%d секций)"
                                  % (n_lines, numbered, len(body_heads))})
    return issues


def scan(paths=None):
    if paths is None:
        paths = []
        for pat in ("docs/*.md", "topics/*.md"):
            paths += glob.glob(os.path.join(ROOT, pat))
    out = []
    for p in paths:
        out += check_file(p)
    return out


def main(argv):
    help_guard(HELP, argv)
    as_json = "--json" in argv
    pos = [a for a in argv if not a.startswith("--")]
    paths = [a if os.path.isabs(a) else os.path.join(ROOT, a) for a in pos] or None
    issues = scan(paths)
    if as_json:
        print(json.dumps({"issues": len(issues), "findings": issues}, ensure_ascii=False, indent=2))
        return 1 if issues else 0
    by_kind = {}
    for x in issues:
        by_kind.setdefault(x["kind"], 0)
        by_kind[x["kind"]] += 1
    print("=== HEADING-LINT (C-11 файл-как-дерево) — %d замечаний ===" % len(issues))
    print("  по типу: %s" % (", ".join("%s=%d" % (k, v) for k, v in by_kind.items()) or "нет"))
    for x in issues[:50]:
        print("  [%-18s] %-46s %s" % (x["kind"], x["where"], x["msg"]))
    if len(issues) > 50:
        print("  … ещё %d" % (len(issues) - 50))
    if not issues:
        print("  OK: структура заголовков чистая")
    return 1 if any(x["kind"] in ("empty-heading", "skipped-level") for x in issues) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
