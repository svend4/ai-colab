"""ripeness_gate.py — структурное принуждение политики «независимый вариант → сверка по смыслу».

Закрывает два инварианта методички independent-first (variants/independent-first-reconcile-2026-06-25):
  И-2 «зрелость-до-сверки»  — вариант входит в котёл, ТОЛЬКО если выработал потенциал
                              (есть условия / полный ответ / уникальный вклад / риски / вопросы).
                              Тонкий рано-остановленный — отклоняется НАЗАД, а не подмешивается.
  И-1 «запечатанная независимость» — у варианта есть seal (front-matter sealed:) + seal_hash тела;
                              хеш = доказательство «писал ДО чтения чужих» (порядок виден по git-времени).

Это машинный гейт: рефлекс «гляну на чужих, потом допишу» перехватывается ДО сверки, а не доверяется
доброй воле (наблюдение сессии: намерения мало). Тула ГОТОВИТ вердикт, решение-по-смыслу — отдельный шаг.

CLI:
  python tools/ripeness_gate.py <variant.md>     # вердикт по одному варианту
  python tools/ripeness_gate.py --board          # сводка по variants/**/*.md
  python tools/ripeness_gate.py --seal <file>    # напечатать строку seal_hash для front-matter
  python tools/ripeness_gate.py --json
"""
import os
from _ioutil import configure_output
from _cli import help_guard
import sys
import glob
import hashlib
import subprocess

configure_output()
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.environ.get("COLLAB_ROOT") or os.path.dirname(HERE)

# Поля «ready-for-synthesis» (D-028 + мой вариант): present, если любой синоним есть в теле.
FIELDS = {
    "условия":    ("услови примен", "когда применя", "applicab", "applies", "primenim", "условия примен"),
    "ответ":      ("дизайн", "design", "полный ответ", "механизм", "фаз", "устройств"),
    "уникальное": ("уникальн", "unique", "вклад", "contribution"),
    "риски":      ("риск", "risk"),
    "вопросы":    ("вопрос", "question", "открыт"),
}
EVIDENCE = ("evidence", "обоснован", "доказат")  # рекомендуемое 6-е поле
MIN_FIELDS = 5  # из 5 обязательных — все; evidence считается бонусом


def ripeness(path):
    """Вердикт зрелости+печати одного варианта: какие поля есть, запечатан ли, ripe?"""
    try:
        text = open(path, encoding="utf-8", errors="replace").read()
    except OSError as e:
        return {"file": path, "error": str(e)[:60]}
    fm = _front_matter(text)
    body = _body(text).lower()
    present = [k for k, syns in FIELDS.items() if any(s in body for s in syns)]
    missing = [k for k in FIELDS if k not in present]
    has_evidence = any(s in body for s in EVIDENCE)
    sealed = "sealed" in fm
    status_ok = fm.get("status", "").strip() == "ready-for-synthesis"
    ripe = (len(present) >= MIN_FIELDS) and status_ok
    return {
        "file": os.path.relpath(path, ROOT).replace("\\", "/"),
        "present": present, "missing": missing, "has_evidence": has_evidence,
        "sealed": sealed, "status_ok": status_ok, "ripe": ripe,
        "seal_hash": seal_hash(path),
        "flags": _flags(missing, sealed, status_ok, has_evidence),
    }


def seal_hash(path):
    """sha1 тела варианта (после front-matter) — «отпечаток печати»; неизменность = независимость."""
    try:
        return hashlib.sha1(_body(open(path, encoding="utf-8", errors="replace").read())
                            .encode("utf-8")).hexdigest()[:12]
    except OSError:
        return ""


def seal_verified(path, root=None):
    """Провенанс печати по GIT: тело НЕ менялось с ПЕРВОГО коммита → печать цела (не подделана задним числом).

    Закрывает OQ-вопрос: `sealed: blind` — самозаявленный флаг, подделываем. Здесь — проверяемый ФАКТ:
    sha1 тела сейчас == sha1 тела в коммите, который ВПЕРВЫЕ добавил файл. Иначе печать нарушена/недоказуема.
    """
    root = root or ROOT
    path = os.path.abspath(path)
    rel = os.path.relpath(path, root).replace("\\", "/")
    log = _git(["log", "--diff-filter=A", "--format=%H", "--", rel], root)
    commits = [c for c in log.splitlines() if c.strip()]
    if not commits:
        return {"verified": False, "why": "не в git (провенанс недоказуем)"}
    first = commits[-1]
    orig = _git(["show", "%s:%s" % (first, rel)], root)
    if not orig:
        return {"verified": False, "why": "не прочесть первый коммит файла"}
    try:
        cur = open(path, encoding="utf-8", errors="replace").read()
    except OSError as e:
        return {"verified": False, "why": str(e)[:40]}
    if hashlib.sha1(_body(orig).encode("utf-8")).hexdigest() == hashlib.sha1(_body(cur).encode("utf-8")).hexdigest():
        return {"verified": True, "seal_commit": first[:12]}
    return {"verified": False, "why": "тело изменено после первого коммита (печать нарушена)"}


def provenance_independence(a, b, root=None):
    """Парная провенанс-независимость по git: ранее-закоммиченный НЕ мог скопировать поздний.

    Независимость по совпадению — это суждение; здесь — проверяемый ФАКТ порядка. Если A в git раньше B,
    то A НЕ мог скопировать B (A независим от B по провенансу); B — под подозрением (мог видеть A). Один
    коммит (атомарно вместе) → взаимная независимость (ни один не видел другого до общей печати).
    """
    root = root or ROOT
    ta = _first_commit_time(a, root)
    tb = _first_commit_time(b, root)
    na, nb = os.path.basename(a), os.path.basename(b)
    if ta is None or tb is None:
        return {"direction": "unknown", "why": "не в git (порядок недоказуем)"}
    both_verified = seal_verified(a, root)["verified"] and seal_verified(b, root)["verified"]
    if ta == tb:
        return {"direction": "mutual", "independent": "both", "both_verified": both_verified}
    early, late = (na, nb) if ta < tb else (nb, na)
    return {"direction": "ordered", "independent": early, "suspect": late, "both_verified": both_verified}


def _first_commit_time(path, root):
    rel = os.path.relpath(os.path.abspath(path), root).replace("\\", "/")
    out = _git(["log", "--diff-filter=A", "--format=%ct", "--", rel], root)
    times = [int(t) for t in out.splitlines() if t.strip().isdigit()]
    return min(times) if times else None


def _git(args, cwd):
    try:
        p = subprocess.run(["git"] + args, cwd=cwd, capture_output=True, text=True,
                           encoding="utf-8", errors="replace", stdin=subprocess.DEVNULL)
        return p.stdout if p.returncode == 0 else ""
    except (OSError, ValueError):
        return ""


def gate(paths):
    """Пропустить в котёл только ripe-варианты; вернуть (passed, rejected)."""
    rows = [ripeness(p) for p in paths]
    rows = [r for r in rows if "error" not in r]
    return ([r for r in rows if r["ripe"]], [r for r in rows if not r["ripe"]])


def _front_matter(text):
    fm = {}
    if not text.startswith("---"):
        return fm
    end = text.find("\n---", 3)
    if end < 0:
        return fm
    for line in text[3:end].splitlines():
        if ":" in line and not line.startswith(" "):
            k, _, v = line.partition(":")
            fm[k.strip()] = v.strip()
    return fm


def _body(text):
    """Содержимое ПОСЛЕ закрывающего front-matter (как в info_verify)."""
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end >= 0:
            nl = text.find("\n", end + 1)
            return text[nl + 1:] if nl >= 0 else ""
    return text


def _flags(missing, sealed, status_ok, has_evidence):
    f = []
    if missing:
        f.append("нет полей: " + ", ".join(missing))
    if not sealed:
        f.append("не запечатан (нет sealed: — независимость недоказуема, И-1)")
    if not status_ok:
        f.append("статус не ready-for-synthesis")
    if not has_evidence:
        f.append("нет evidence (рекомендуется)")
    return f


def _glyph(ripe, sealed):
    if ripe and sealed:
        return "✅ в котёл (зрел+запечатан)"
    if ripe:
        return "🔶 зрел, но не запечатан"
    return "⛔ назад (не выработал потенциал)"


def main(argv):
    help_guard(__doc__, argv)
    import json
    as_json = "--json" in argv
    if "--seal" in argv:
        i = argv.index("--seal")
        if i + 1 < len(argv):
            p = argv[i + 1]
            p = p if os.path.isabs(p) else os.path.join(ROOT, p)
            print("sealed: blind  # seal_hash: %s" % seal_hash(p))
            return 0
        print("ripeness_gate: --seal требует файл"); return 2
    if "--verify" in argv:
        paths = sorted(glob.glob(os.path.join(ROOT, "variants", "**", "*.md"), recursive=True))
        print("=== ПРОВЕРКА ПЕЧАТИ ПО GIT (провенанс, не самозаявление) ===")
        ok = 0
        for p in paths:
            v = seal_verified(p)
            print("  %-46s %s" % (os.path.basename(p),
                  "✅ git-verified (%s)" % v["seal_commit"] if v["verified"] else "✗ " + v.get("why", "")))
            ok += 1 if v["verified"] else 0
        print("  итого: %d/%d печатей подтверждены git (тело == первый коммит)" % (ok, len(paths)))
        return 0
    if "--provenance" in argv:
        i = argv.index("--provenance")
        rest = [a for a in argv[i + 1:] if not a.startswith("--")]
        d = rest[0] if rest else "variants"
        d = d if os.path.isabs(d) else os.path.join(ROOT, d)
        files = glob.glob(os.path.join(d, "*.md")) or glob.glob(os.path.join(d, "**", "*.md"), recursive=True)
        rows = [(f, _first_commit_time(f, ROOT)) for f in files]
        rows = sorted([r for r in rows if r[1] is not None], key=lambda r: r[1])
        print("=== ПРОВЕНАНС-ПОРЯДОК по git (ранее = независим от поздних) ===")
        for f, _ in rows:
            print("  %s" % os.path.basename(f))
        print("  → каждый независим (по провенансу) от всех НИЖЕ; верхний ни у кого не мог скопировать")
        return 0
    args = [a for a in argv if not a.startswith("--")]
    if "--board" in argv or not args:
        paths = sorted(glob.glob(os.path.join(ROOT, "variants", "**", "*.md"), recursive=True))
        passed, rejected = gate(paths)
        if as_json:
            print(json.dumps({"passed": passed, "rejected": rejected}, ensure_ascii=False, indent=2)); return 0
        print("=== ГЕЙТ ЗРЕЛОСТИ+ПЕЧАТИ (И-1/И-2) — variants/ ===")
        print("  вариантов: %d · в котёл: %d · назад: %d" % (len(passed) + len(rejected), len(passed), len(rejected)))
        for r in passed + rejected:
            print("    %-46s %s" % (os.path.basename(r["file"]), _glyph(r["ripe"], r["sealed"])))
            if r["flags"]:
                print("        ⚠ " + " · ".join(r["flags"]))
        return 0
    p = args[0] if os.path.isabs(args[0]) else os.path.join(ROOT, args[0])
    r = ripeness(p)
    if as_json:
        print(json.dumps(r, ensure_ascii=False, indent=2)); return 0
    if "error" in r:
        print("ripeness_gate: %s" % r["error"]); return 2
    print("=== ГЕЙТ: %s ===" % r["file"])
    print("  поля (%d/5): %s" % (len(r["present"]), ", ".join(r["present"]) or "—"))
    if r["missing"]:
        print("  не хватает: %s" % ", ".join(r["missing"]))
    print("  запечатан: %s · status ready-for-synthesis: %s · seal_hash: %s" % (
        "да" if r["sealed"] else "НЕТ", "да" if r["status_ok"] else "нет", r["seal_hash"]))
    print("  вердикт: %s" % _glyph(r["ripe"], r["sealed"]))
    if r["flags"]:
        print("  ⚠ " + " · ".join(r["flags"]))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
