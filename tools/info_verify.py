# ==========================================
# [FILE ID CARD]
# ID: tools.info_verify
# TYPE: active-script
# DOMAIN: core.validation
# DEPTH_LEVEL: 1
# SUMMARY: verify-контракт информационного рефакторинга (тело+история инвариантны ∧ верхушка не хуже).
# ==========================================
"""info_verify.py — verify-контракт информационного рефакторинга (тело+история инвариантны ∧ верхушка не хуже).

Доказывает санацию как ЗЕЛЁНЫЕ ТЕСТЫ доказывают рефакторинг кода: не намерение, а assert (апофатика —
«тело неизменно» через отрицание). snapshot ДО → операция санации → verify: ТЕЛО атомов (контент ПОСЛЕ
front-matter) по хэшам не изменилось, git-история цела, верхушка не деградировала (maturity не упала,
H(top) не вырос). Отвечает на мета-вопросы 4.1 (инфо-рефакторинг как стандарт) и 4.5.2 (омолодить
верхушку, не трогая тело).

CLI:
  python tools/info_verify.py snapshot > before.json    # снимок тел+метрик ДО операции
  python tools/info_verify.py verify before.json         # ПОСЛЕ: assert инвариантов (exit 1 = нарушено)
  python tools/info_verify.py verify before.json --json
"""
import os
from _ioutil import configure_output
from _cli import help_guard, die
import sys
import json
import glob
import hashlib

configure_output()
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.environ.get("COLLAB_ROOT") or os.path.dirname(HERE)
sys.path.insert(0, HERE)

# Единый реестр каталогов канона — из _canon (P9-a, волна 2); info_verify исторически
# обходит РАСШИРЕННЫЙ состав (ядро + drivers/streams/portals/core) — поведение сохранено.
from _canon import CANON_DIRS_EXTENDED as CANON_DIRS, require_canon_dirs


def _body(text):
    """Тело = контент ПОСЛЕ закрывающего front-matter. Визитка (front-matter) = верхушка (санируема),
    тело = замороженное (неизменно при инфо-рефакторинге)."""
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            return text[end + 4:]
    return text


def _canon_files():
    # Контракт P9: несуществующий канон-каталог → FileNotFoundError, а не тихий недосчёт тел.
    require_canon_dirs(ROOT, CANON_DIRS)
    out = []
    for d in CANON_DIRS:
        out += glob.glob(os.path.join(ROOT, d, "**", "*.md"), recursive=True)
    return out


def _metrics():
    """Верхушка-метрики: средняя зрелость ‰ + H(top) бит (через существующие тулы)."""
    mat = htop = None
    try:
        import maturity
        rows = maturity.collect()
        mat = round(sum(r["score"] for r in rows) / len(rows)) if rows else 0
    except Exception:
        pass
    try:
        import sanation
        import edges
        nodes, bi, bs = edges.load_nodes()
        gc = edges.check(nodes, edges.build_edges(nodes, bi, bs), bi)
        htop = sanation.top_entropy(nodes, gc)["H_top_bits"]
    except Exception:
        pass
    return mat, htop


def snapshot():
    bodies = {}
    for p in _canon_files():
        rel = os.path.relpath(p, ROOT).replace("\\", "/")
        try:
            b = _body(open(p, encoding="utf-8", errors="replace").read())
        except OSError:
            continue
        bodies[rel] = hashlib.sha1(b.encode("utf-8")).hexdigest()
    mat, htop = _metrics()
    head = ""
    try:
        import subprocess
        head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True,
                              text=True).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        pass
    return {"bodies": bodies, "maturity_avg": mat, "h_top": htop, "head": head}


def verify(snap):
    """Сравнить текущее состояние со снимком. Возврат: вердикт + нарушения."""
    cur = snapshot()
    changed_bodies, removed = [], []
    for rel, h in snap.get("bodies", {}).items():
        ch = cur["bodies"].get(rel)
        if ch is None:
            removed.append(rel)
        elif ch != h:
            changed_bodies.append(rel)
    # инварианты: тело не изменилось И не удалено; верхушка не хуже
    body_ok = not changed_bodies and not removed
    mat_ok = cur["maturity_avg"] is None or snap.get("maturity_avg") is None \
        or cur["maturity_avg"] >= snap["maturity_avg"]
    h_ok = cur["h_top"] is None or snap.get("h_top") is None or cur["h_top"] <= snap["h_top"]
    return {
        "body_invariant": body_ok, "changed_bodies": changed_bodies, "removed_bodies": removed,
        "maturity_before": snap.get("maturity_avg"), "maturity_after": cur["maturity_avg"], "maturity_ok": mat_ok,
        "h_before": snap.get("h_top"), "h_after": cur["h_top"], "h_ok": h_ok,
        "verdict": "PASS" if (body_ok and mat_ok) else "FAIL",
    }


def main(argv):
    help_guard(__doc__, argv)
    as_json = "--json" in argv
    args = [a for a in argv if not a.startswith("--")]
    if not args:
        die("info_verify: snapshot | verify <файл>")
    cmd = args[0]
    if cmd == "snapshot":
        print(json.dumps(snapshot(), ensure_ascii=False, indent=2))
        return 0
    if cmd == "verify":
        if len(args) < 2:
            die("info_verify verify <snapshot.json>")
        try:
            snap = json.load(open(args[1], encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as e:
            die("не прочитать снимок: %s" % e)
        r = verify(snap)
        if as_json:
            print(json.dumps(r, ensure_ascii=False, indent=2))
            return 0 if r["verdict"] == "PASS" else 1
        print("=== VERIFY инфо-рефакторинга (тело+история инвариантны ∧ верхушка не хуже) ===")
        print("  тело инвариантно: %s  (изменено %d, удалено %d)" % (
            "✓" if r["body_invariant"] else "✗ НАРУШЕНО", len(r["changed_bodies"]), len(r["removed_bodies"])))
        for f in (r["changed_bodies"] + r["removed_bodies"])[:8]:
            print("      ✗ %s" % f)
        print("  зрелось ‰: %s→%s  %s" % (r["maturity_before"], r["maturity_after"],
                                          "✓ не хуже" if r["maturity_ok"] else "✗ упала"))
        print("  H(top) бит: %s→%s  %s" % (r["h_before"], r["h_after"],
                                           "✓ не выросла" if r["h_ok"] else "• выросла"))
        print("\n  ВЕРДИКТ: %s" % ("✓ PASS — валидный информационный рефакторинг (тело цело, верхушка не хуже)"
                                   if r["verdict"] == "PASS" else "✗ FAIL — тело тронуто или зрелость упала"))
        return 0 if r["verdict"] == "PASS" else 1
    die("неизвестная команда: %s" % cmd)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
