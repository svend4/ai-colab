# ==========================================
# [FILE ID CARD]
# ID: tools.autonomy_guard
# TYPE: active-script
# DOMAIN: core.validation
# DEPTH_LEVEL: 1
# SUMMARY: детектор АВТОНОМНЫХ `accept` без подтверждения человека (B2 / дисциплина D-033 §0).
# ==========================================
"""autonomy_guard.py — детектор АВТОНОМНЫХ `accept` без подтверждения человека (B2 / дисциплина D-033 §0).

Запрос Stefan: «если что-то производится без участия человека — указывать, комментировать, подтверждать
несколько раз, оставлять черновиком, корректировать, технически перепроверять». Этот детектор находит
ТЕРМИНАЛЬНЫЕ автономные accept'ы в `decisions/D-*.md` (status:accepted), у которых НЕТ достаточного следа
подтверждения ЧЕЛОВЕКОМ, и ФЛАГИРУЕТ их с комментарием. Он НЕ правит D-файлы (это был бы тот же автономный
терминальный accept — по §0 дисциплины проверка флагирует, но не авто-блокирует/не авто-правит).

«Сигнал подтверждения человеком» (≥2 нужно для accepted): структурный `confirmed_by:` · `human_confirmations:≥1`
· участник-человек (Stefan/Max) · прозаическое «Stefan ратифицировал». Матрица случаев — D-033 §2.

CLI:
  python tools/autonomy_guard.py                 # отчёт: flag/warn по decisions/
  python tools/autonomy_guard.py --json
  python tools/autonomy_guard.py --require 2      # сколько подтверждений требовать (дефолт 2)
"""
import os
from _ioutil import configure_output
from _cli import help_guard
import sys
import re
import json
import glob

configure_output()
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.environ.get("COLLAB_ROOT") or os.path.dirname(HERE)
KNOWN_HUMANS = ("stefan", "max")


def _parse(text):
    """front-matter (key: value) + body. Простой парсер (как crdt_merge/view)."""
    fm, body = {}, text
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end >= 0:
            for line in text[3:end].splitlines():
                m = re.match(r"^([A-Za-z0-9_\-]+):\s*(.*)$", line)
                if m:
                    fm[m.group(1)] = m.group(2).strip()
            nl = text.find("\n", end + 1)
            body = text[nl + 1:] if nl >= 0 else ""
    return fm, body


def _human_signals(fm, body):
    """Число РАЗЛИЧНЫХ сигналов подтверждения человеком (структурные + участник + проза)."""
    sig = 0
    if str(fm.get("confirmed_by", "")).strip():
        sig += 1
    try:
        hc = int(fm.get("human_confirmations", 0))
        if hc > 0:
            sig += hc
    except (ValueError, TypeError):
        pass
    if any(h in str(fm.get("participants", "")).lower() for h in KNOWN_HUMANS):
        sig += 1
    if re.search(r"stefan|\bmax\b|ратифиц|человек\s+подтвер|confirmed\s+by", body, re.I):
        sig += 1
    return sig


def classify_decision(fm, body, require=2):
    """Вердикт по матрице D-033 §2: ok / warn / flag. Чистая (тестируема)."""
    status = (fm.get("status") or "").strip().lower()
    autonomous = str(fm.get("autonomous", "")).strip().lower() in ("true", "1", "yes")
    if status != "accepted":
        tail = " [autonomous-черновик — ок по §0: помечен и не accepted]" if autonomous else ""
        return {"status": status or "—", "signals": 0, "verdict": "ok",
                "comment": "не accepted — терминального автономного accept нет%s" % tail}
    sig = _human_signals(fm, body)
    if autonomous and sig < require:
        return {"status": status, "signals": sig, "verdict": "flag",
                "comment": "accepted + autonomous:true, %d/%d подтверждений — САМОЗАЯВЛЕННЫЙ автономный accept" % (sig, require)}
    if sig >= require:
        return {"status": status, "signals": sig, "verdict": "ok",
                "comment": "человек подтвердил (%d ≥ %d сигнал.)" % (sig, require)}
    if sig == 1:
        return {"status": status, "signals": 1, "verdict": "warn",
                "comment": "1 подтверждение < %d: добавить confirmed_by/human_confirmations (машинно-проверяемое, не только проза)" % require}
    return {"status": status, "signals": 0, "verdict": "flag",
            "comment": "АВТОНОМНЫЙ accept: 0 сигналов человека → понизить до proposed, пометить autonomous:true, требовать ≥%d подтверждений" % require}


def scan(decisions_dir=None, require=2):
    decisions_dir = decisions_dir or os.path.join(ROOT, "decisions")
    out = []
    for p in sorted(glob.glob(os.path.join(decisions_dir, "D-*.md"))):
        fm, body = _parse(open(p, encoding="utf-8", errors="replace").read())
        c = classify_decision(fm, body, require)
        out.append({"id": fm.get("id") or os.path.basename(p)[:-3],
                    "file": os.path.relpath(p, ROOT).replace("\\", "/"), **c})
    return out


def main(argv):
    help_guard(__doc__, argv)
    require = int(argv[argv.index("--require") + 1]) if "--require" in argv else 2
    rows = scan(require=require)
    flags = [r for r in rows if r["verdict"] == "flag"]
    warns = [r for r in rows if r["verdict"] == "warn"]
    if "--json" in argv:
        print(json.dumps({"require": require, "total": len(rows), "flag": flags, "warn": warns}, ensure_ascii=False, indent=2))
        return 1 if flags else 0
    print("=== AUTONOMY GUARD · accept без подтверждения человека (≥%d) · %d решений ===" % (require, len(rows)))
    print("  ✗ FLAG (автономный accept): %d · ⚠ WARN (1 подтв.): %d · ✓ ok: %d" % (
        len(flags), len(warns), len(rows) - len(flags) - len(warns)))
    for r in flags:
        print("  ✗ %-7s %s" % (r["id"], r["comment"]))
    for r in warns:
        print("  ⚠ %-7s %s" % (r["id"], r["comment"]))
    if flags:
        print("\n  (read-only: D-файлы НЕ изменены — флаг+коммент; правит человек/гейт, §0 D-033)")
    return 1 if flags else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
