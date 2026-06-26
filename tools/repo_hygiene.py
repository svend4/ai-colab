"""repo_hygiene.py — гигиена РАБОЧЕГО ДЕРЕВА (комплемент sanation.py, что лечит верхушку канона).

sanation.py оздоравливает семантическую верхушку (визитки/граф/свежесть). А этот инструмент чистит ДРУГОЙ
слой — файловую гигиену git-дерева, где копится боль многоагентной работы: untracked-cruft зашумляет
`git status` (не видно реальных изменений), runtime-артефакты не в `.gitignore` (риск случайного коммита),
посторонние staged-файлы (T-263: коммит сметёт чужое). Это применение «формулы санации дефектов» (D-031):
сделать cruft ВИДИМЫМ/измеримым → безопасный фикс (.gitignore) → НИКОГДА не удалять (чужую работу не трогаем).

Классы untracked-файлов:
  • scratch/runtime  — должно быть в .gitignore (sandbox runtime subdirs, reports/audit_*, queues/commit-queue/, *.lock, ...)
  • canon-md         — *.md под tasks/decisions/questions/topics/docs = РЕАЛЬНАЯ работа без коммита (владельцу)
  • stray-root       — файл в корне, не канон и не scratch (на ревью, НЕ авто-удаляем)
  • other            — прочее untracked (новый инструмент без add и т.п.)
Плюс: staged-файлы (риск selective-commit) и hygiene-score (0..100, измеримо).

Read-only по умолчанию. Единственное авто-действие — `--fix-gitignore` (идемпотентно дописывает БЕЗОПАСНЫЕ
паттерны для уже-найденного scratch). Удаления нет вообще — по формуле «minority/чужое не теряем».

CLI:
  python tools/repo_hygiene.py                 # отчёт гигиены рабочего дерева
  python tools/repo_hygiene.py --json
  python tools/repo_hygiene.py --fix-gitignore # дописать безопасные паттерны в .gitignore (идемпотентно)
"""
import os
from _ioutil import configure_output
from _cli import help_guard
import sys
import re
import json
import subprocess

configure_output()
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.environ.get("COLLAB_ROOT") or os.path.dirname(HERE)
CANON_RE = re.compile(r"^(tasks|decisions|questions|topics|docs)/.*\.md$")
SANDBOX_SCRATCH = ("sandbox/audit", "sandbox/canvas-demo", "sandbox/paradigm_shift")


def is_scratch(path):
    """runtime/scratch, что должно быть в .gitignore (не канон)."""
    p = path.rstrip("/")
    return bool(
        any(p == x or p.startswith(x + "/") for x in SANDBOX_SCRATCH)
        or p.startswith("queues/commit-queue")
        or re.match(r"reports/audit_.*\.json$", p)
        or re.match(r"reports/output_.*\.log$", p)
        or p.endswith(".lock") or p.endswith(".tmp") or p.endswith(".pyc")
        or p == "_picks.json"
    )


def _gitignore_pattern(path):
    """Каноническая .gitignore-строка для scratch-пути (классом, не поштучно)."""
    p = path.rstrip("/")
    for x in SANDBOX_SCRATCH:
        if p == x or p.startswith(x + "/"):
            return x + "/"
    if p.startswith("queues/commit-queue"):
        return "queues/commit-queue/"
    if re.match(r"reports/audit_.*\.json$", p):
        return "reports/audit_*.json"
    if re.match(r"reports/output_.*\.log$", p):
        return "reports/output_*.log"
    if p == "_picks.json":
        return "_picks.json"
    if p.endswith(".lock"):
        return "*.lock"
    if p.endswith(".tmp"):
        return "*.tmp"
    return None


def classify(porcelain_lines):
    """Чистая классификация строк `git status --porcelain`. Тестируема без git."""
    cats = {"scratch": [], "canon_md": [], "stray_root": [], "other": [], "staged": []}
    for ln in porcelain_lines:
        if len(ln) < 4:
            continue
        xy, path = ln[:2], ln[3:].strip()
        if " -> " in path:                      # rename: берём новый путь
            path = path.split(" -> ", 1)[1]
        path = path.strip().strip('"')
        if xy == "??":
            if is_scratch(path):
                cats["scratch"].append(path)
            elif CANON_RE.match(path):
                cats["canon_md"].append(path)
            elif "/" not in path.rstrip("/"):
                cats["stray_root"].append(path)
            else:
                cats["other"].append(path)
        elif xy[0] not in (" ", "?"):            # X-колонка непустая → staged в индексе
            cats["staged"].append(path)
    return cats


def gitignore_suggestions(scratch_paths, existing_patterns):
    """Какие паттерны дописать в .gitignore (классом, без дублей с уже существующими)."""
    want = []
    for p in scratch_paths:
        pat = _gitignore_pattern(p)
        if pat and pat not in existing_patterns and pat not in want:
            want.append(pat)
    return want


def hygiene_score(cats):
    """0..100 — выше чище. Главный штраф — неигнорируемый scratch (зашумляет status)."""
    penalty = 2 * len(cats["scratch"]) + 3 * len(cats["stray_root"]) + 1 * len(cats["staged"]) + 1 * len(cats["other"])
    return max(0, 100 - min(100, penalty))


def _git_status():
    try:
        p = subprocess.run(["git", "status", "--porcelain"], cwd=ROOT, capture_output=True, text=True,
                           encoding="utf-8", errors="replace", stdin=subprocess.DEVNULL)
        return [ln for ln in (p.stdout or "").splitlines() if ln.strip()]
    except Exception:
        return []


def _existing_patterns():
    gi = os.path.join(ROOT, ".gitignore")
    if not os.path.exists(gi):
        return set()
    return {ln.strip() for ln in open(gi, encoding="utf-8") if ln.strip() and not ln.startswith("#")}


def collect():
    cats = classify(_git_status())
    sugg = gitignore_suggestions(cats["scratch"], _existing_patterns())
    return {"score": hygiene_score(cats), "cats": cats, "gitignore_suggest": sugg}


def fix_gitignore(suggest):
    """Идемпотентно дописать безопасные паттерны. Возвращает список добавленных."""
    if not suggest:
        return []
    gi = os.path.join(ROOT, ".gitignore")
    existing = _existing_patterns()
    add = [s for s in suggest if s not in existing]
    if not add:
        return []
    with open(gi, "a", encoding="utf-8", newline="\n") as fh:
        fh.write("\n# repo_hygiene авто-санация (%d паттерн(ов))\n" % len(add))
        for s in add:
            fh.write(s + "\n")
    return add


def main(argv):
    help_guard(__doc__, argv)
    r = collect()
    if "--fix-gitignore" in argv:
        added = fix_gitignore(r["gitignore_suggest"])
        print("repo_hygiene --fix-gitignore: добавлено %d паттерн(ов): %s" % (len(added), ", ".join(added) or "—"))
        return 0
    if "--json" in argv:
        print(json.dumps(r, ensure_ascii=False, indent=2)); return 0
    c = r["cats"]
    print("=== ГИГИЕНА РАБОЧЕГО ДЕРЕВА · score %d/100 ===" % r["score"])
    print("  scratch/runtime (→ .gitignore): %d %s" % (len(c["scratch"]), c["scratch"][:6]))
    print("  canon-md без коммита (владельцу): %d %s" % (len(c["canon_md"]), c["canon_md"][:6]))
    print("  stray-root (ревью, НЕ удаляем):   %d %s" % (len(c["stray_root"]), c["stray_root"][:6]))
    print("  other untracked:                  %d %s" % (len(c["other"]), c["other"][:6]))
    print("  ⚠ staged (риск selective-commit T-263): %d %s" % (len(c["staged"]), c["staged"][:6]))
    if r["gitignore_suggest"]:
        print("\n  → предложение .gitignore (--fix-gitignore): %s" % ", ".join(r["gitignore_suggest"]))
    if c["staged"]:
        print("\n  ⚠ перед коммитом: в индексе чужие/staged файлы — коммить пути явно: git commit -- <свои пути>")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
