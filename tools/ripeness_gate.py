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
