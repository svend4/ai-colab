#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ==========================================
# [FILE ID CARD]
# ID: tools.topic_sanitation
# TYPE: active-script
# DOMAIN: core
# DEPTH_LEVEL: 1
# SUMMARY: advisory-детектор залежавшихся proposed/open-тем (болото идей, диагноз mavis FM-1).
# ==========================================
"""topic_sanitation.py — advisory-детектор «болота идей» (диагноз mavis: 60 proposed-тем = FM-1-риск).

Реализует диагноз mavis из аудита: масса тем в статусе `proposed`/`open`, которые давно
не двигались, — это болото недорешённых идей (риск FM-1: параллельная работа копится, но не
разрешается). Детектор находит такие темы и предлагает по каждой ДЕЙСТВИЕ, НО НИЧЕГО НЕ МЕНЯЕТ.

ЧТО ДЕЛАЕТ (read-only, proposed, НЕ enforced):
  - сканирует topics/**/*.md;
  - берёт темы в активном «болотном» статусе (по умолчанию proposed / open);
  - «залежалась» = ни один сигнал движения не свежее N дней (дефолт 14):
      сигнал movement = max(mtime файла, дата из front-matter `date`/`last_verified`);
    mtime — git last-commit (в git-репо), иначе fs-mtime;
  - для каждого кандидата печатает ПРЕДЛОЖЕНИЕ (done / archive / завести задачу) — dry-run,
    БЕЗ автозакрытия и БЕЗ смены статуса (это дело человека/эстафеты).

D-017-ВАРИАНТЫ НЕ СТИРАЕМ. Часть proposed-тем — это форк-варианты по D-017 (намеренно живут
параллельно). Детектор их только помечает флагом `variant?` («возможно вариант — решение за
человеком»), в предложении для них — «сверить с D-017», а не «archive». Стереть/закрыть — только
человек.

CLI:
  python tools/topic_sanitation.py scan                 # список залежавшихся (>14д) + предложения
  python tools/topic_sanitation.py scan --age-days 30   # свой порог
  python tools/topic_sanitation.py scan --json          # машиночитаемо (STDOUT чистый)
  python tools/topic_sanitation.py scan --now <epoch>   # зафиксировать «сейчас» (для тестов)
"""
import os
import re
import sys
import json
import glob
import time
import subprocess

from _ioutil import configure_output

configure_output()
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.environ.get("COLLAB_ROOT") or os.path.dirname(HERE)
sys.path.insert(0, HERE)
from _canon import parse_fm
from _cli import help_guard, die

DAY = 86400
# «болотные» статусы: незакрытая идея, которая копится (диагноз mavis FM-1).
SWAMP_STATUSES = ("proposed", "open")
# Порог «залежалась» по умолчанию (в днях). N задаётся через --age-days.
DEFAULT_AGE_DAYS = 14
# ISO-дата в front-matter: 2026-06-23 (берём только дату, время игнорируем).
_DATE_RE = re.compile(r"(\d{4})-(\d{2})-(\d{2})")


def git_mtimes():
    """{relpath: epoch последнего коммита} одним проходом git log (newest-first → первый = свежий).

    Не git-репо / git недоступен → пустой dict, вызывающий падёт на fs-mtime.
    Формат идентичен decay.py (единый сигнал «времени» по репозиторию).
    """
    out = {}
    try:
        p = subprocess.run(["git", "log", "--no-renames", "--format=C%ct", "--name-only"],
                           cwd=ROOT, capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=90)
    except (OSError, subprocess.SubprocessError):
        return out
    if p.returncode != 0:
        return out
    cur = None
    for line in p.stdout.splitlines():
        if line.startswith("C") and line[1:].isdigit():
            cur = int(line[1:])
        elif line.strip() and cur is not None:
            rel = line.strip().replace("\\", "/")
            if rel not in out:
                out[rel] = cur
    return out


def _mtime_epoch(rel, mtimes):
    """Epoch последнего движения файла: git last-commit, иначе fs-mtime. None — если недоступно."""
    epoch = mtimes.get(rel)
    if epoch is not None:
        return epoch
    try:
        return int(os.path.getmtime(os.path.join(ROOT, rel)))
    except OSError:
        return None


def _fm_date_epoch(fm):
    """Свежайшая дата из front-matter (date / last_verified) → epoch (полночь UTC). None — если нет."""
    best = None
    for key in ("last_verified", "date"):
        raw = (fm.get(key) or "").strip()
        m = _DATE_RE.search(raw)
        if not m:
            continue
        try:
            epoch = int(time.mktime((int(m.group(1)), int(m.group(2)), int(m.group(3)),
                                     0, 0, 0, 0, 0, -1)))
        except (ValueError, OverflowError):
            continue
        if best is None or epoch > best:
            best = epoch
    return best


def _looks_variant(fm, rel):
    """Мягкая эвристика «это форк-вариант по D-017 — не стирать».

    True, если явный сигнал варианта: поле variant/fork в front-matter, D-017 в related,
    либо «вариант»/«variant»/«fork» в id/title/имени файла. Осознанно узкая: широкое
    упоминание D-017 в теле темы НЕ считается (D-017 упоминается почти везде).
    """
    if str(fm.get("variant", "")).strip() or str(fm.get("fork", "")).strip():
        return True
    related = str(fm.get("related", ""))
    if re.search(r"\bD-?017\b", related, re.IGNORECASE):
        return True
    hay = " ".join([str(fm.get("id", "")), str(fm.get("title", "")),
                    os.path.basename(rel)]).lower()
    return any(w in hay for w in ("вариант", "variant", "fork-", "-fork"))


def _suggest(status, is_variant):
    """Предложение действия для человека (dry-run). НЕ меняет статус.

    - variant по D-017 → «сверить с D-017» (не archive: намеренно живёт параллельно);
    - proposed → «done (реализовано) / archive (устарело) / завести задачу (если ещё нужно)»;
    - open     → «завести задачу или закрыть».
    """
    if is_variant:
        return "сверить с D-017 (возможно форк-вариант — не стирать; решение за человеком)"
    if status == "proposed":
        return "done (реализовано) · archive (устарело) · завести задачу (если ещё нужно)"
    return "завести задачу (если ещё актуально) · archive (если неактуально)"


def collect(age_days=DEFAULT_AGE_DAYS, now=None, statuses=SWAMP_STATUSES):
    """Собрать залежавшиеся «болотные» темы.

    Возвращает dict:
      candidates — список залежавшихся (движение старше age_days), отсортирован старшее-первым;
      scanned    — сколько topics/*.md всего просмотрено;
      swamp_total— сколько тем в «болотном» статусе (любого возраста);
      age_days   — применённый порог.
    Каждый кандидат: {file, id, status, age_days, variant, suggestion}.
    """
    now = int(now if now is not None else time.time())
    mtimes = git_mtimes()
    candidates = []
    scanned = 0
    swamp_total = 0
    for p in sorted(glob.glob(os.path.join(ROOT, "topics", "**", "*.md"), recursive=True)):
        if os.path.basename(p) == "README.md":
            continue
        scanned += 1
        rel = os.path.relpath(p, ROOT).replace("\\", "/")
        try:
            fm = parse_fm(open(p, encoding="utf-8", errors="replace").read()) or {}
        except OSError:
            continue
        status = (fm.get("status") or "").strip().lower()
        if status not in statuses:
            continue
        swamp_total += 1
        # Свежайший сигнал движения: max(mtime, дата из front-matter).
        signals = [e for e in (_mtime_epoch(rel, mtimes), _fm_date_epoch(fm)) if e is not None]
        if not signals:
            continue  # ни одного сигнала времени — не судим (не залежалась «по умолчанию»)
        freshest = max(signals)
        age = (now - freshest) / DAY
        if age < age_days:
            continue  # ещё двигалась недавно — не болото
        is_variant = _looks_variant(fm, rel)
        candidates.append({
            "file": rel,
            "id": fm.get("id", "") or "",
            "status": status,
            "age_days": round(max(0.0, age), 1),
            "variant": is_variant,
            "suggestion": _suggest(status, is_variant),
        })
    candidates.sort(key=lambda r: -r["age_days"])
    return {"candidates": candidates, "scanned": scanned,
            "swamp_total": swamp_total, "age_days": age_days}


def _print_human(data):
    cands = data["candidates"]
    print("=== SANITATION ТЕМ: болото идей (диагноз mavis FM-1) ===")
    print("  просмотрено topics/*.md: %d   в статусе %s: %d   залежались (>%dд): %d" % (
        data["scanned"], "/".join(SWAMP_STATUSES), data["swamp_total"],
        data["age_days"], len(cands)))
    if not cands:
        print("\n  ✓ Залежавшихся proposed/open-тем нет — болото сухое.")
        return
    n_var = sum(1 for c in cands if c["variant"])
    print("\n  • Кандидаты на действие (dry-run, статусы НЕ меняются — решение за человеком):")
    if n_var:
        print("    из них помечено «возможно вариант по D-017» (не стирать): %d" % n_var)
    print()
    for c in cands:
        flag = " [variant?]" if c["variant"] else ""
        print("    ❄ %6sд  %-8s %s%s" % (c["age_days"], c["status"], c["id"] or c["file"], flag))
        print("        %s" % c["file"])
        print("        → %s" % c["suggestion"])


def main(argv):
    help_guard(__doc__, argv)
    if not argv or argv[0] in ("-h", "--help"):
        # без подкоманды — показываем scan (единственная команда), но подсказываем канон
        argv = ["scan"] + list(argv)
    cmd = argv[0]
    rest = argv[1:]
    if cmd != "scan":
        die("неизвестная команда %r (есть только: scan). См. --help." % cmd)

    as_json = "--json" in rest
    now = None
    if "--now" in rest:
        i = rest.index("--now")
        if i + 1 < len(rest):
            try:
                now = int(rest[i + 1])
            except ValueError:
                die("--now ожидает epoch (целое)")
    age_days = DEFAULT_AGE_DAYS
    if "--age-days" in rest:
        i = rest.index("--age-days")
        if i + 1 < len(rest):
            try:
                age_days = int(rest[i + 1])
            except ValueError:
                die("--age-days ожидает целое число дней")
        if age_days < 0:
            die("--age-days не может быть отрицательным")

    data = collect(age_days=age_days, now=now)
    if as_json:
        print(json.dumps(data, ensure_ascii=False, indent=2))
        return 0
    _print_human(data)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
