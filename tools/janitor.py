# ast: allow-subprocess
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ==========================================
# [FILE ID CARD]
# ID: tools.janitor
# TYPE: active-script
# DOMAIN: core.hygiene
# DEPTH_LEVEL: 1
# SUMMARY: Дворник runtime-артефактов: dry-run отчёт ротации (audit/reflection/tmp-work/dialog); удаление только явным --delete.
# ==========================================
"""janitor.py — дворник runtime-артефактов: ЧТО БЫ удалилось/уехало в архив (аудит C53/C56, волна 2).

Аудит 2026-07-02 зафиксировал монотонный рост gitignored-накопителей: reports/audit_*.json +
output_*.log (пары одного прогона), logs/reflection/*.json (в т.ч. 0-байтные), tmp-work/* —
и рост ручного журнала dialog.md (167 КБ). По решению Q-W2-15 инструмент работает ТОЛЬКО в
режиме dry-run/отчёта: перечисляет кандидатов, но ничего не удаляет и не переносит. Флаг
--delete существует как задел для будущего включения человеком, по умолчанию ВЫКЛЮЧЕН и в
волне 2 не используется. Ротация dialog.md (C56-a: реплики старше N недель → dialog-archive-
YYYY-MM.md, хвост остаётся) реализована ТОЛЬКО как отчёт — сам перенос реплик даже при
--delete не выполняется (общий координационный журнал, решение за человеком, Q-W2-17).

Секции отчёта:
  • audit-пары   — reports/audit_YYYYMMDD_HHMMSS.json + output_*.log сверх N последних пар
  • reflection   — logs/reflection/*.json сверх N последних (по mtime); 0-байтные — всегда
                   кандидаты; ledger.json (дедуп-журнал reflect_ingest) не трогается никогда
  • tmp-work     — записи tmp-work/* (файлы и каталоги) старше X дней по mtime
  • dialog       — реплики `### YYYY-MM-DD HH:MM - Имя` старше N недель, кроме последних K
                   (хвост); группировка по целевым архивам dialog-archive-YYYY-MM.md

Опция --gc (задел под C54, по умолчанию выключена) вызывает `git gc --auto` — единственное
действие, не относящееся к файлам канона; включается явно и осознанно.

CLI:
  python tools/janitor.py                          # dry-run отчёт (ничего не меняет)
  python tools/janitor.py --json                   # машинный отчёт
  python tools/janitor.py --keep-audits 10 --keep-reflections 100 --tmp-age-days 14
  python tools/janitor.py --dialog-age-weeks 8 --dialog-keep-last 20
  python tools/janitor.py --delete                 # РЕАЛЬНОЕ удаление кандидатов (только по решению человека, Q-W2-15)
  python tools/janitor.py --gc                     # дополнительно git gc --auto (C54)
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime, timedelta

from _ioutil import configure_output

configure_output()

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.environ.get("COLLAB_ROOT") or os.path.dirname(HERE)

# Консервативные дефолты (Q-W2-15: финальные N/X утверждает человек).
DEFAULT_KEEP_AUDITS = 10        # пар audit_*/output_* оставить
DEFAULT_KEEP_REFLECTIONS = 100  # записей logs/reflection оставить
DEFAULT_TMP_AGE_DAYS = 14       # tmp-work/* старше — кандидат
DEFAULT_DIALOG_AGE_WEEKS = 8    # реплики dialog.md старше — кандидаты в архив
DEFAULT_DIALOG_KEEP_LAST = 20   # последних реплик не трогаем даже старыми (хвост)

AUDIT_RE = re.compile(r"^audit_(\d{8}_\d{6})\.json$")
OUTPUT_RE = re.compile(r"^output_(\d{8}_\d{6})\.log$")
# Заголовок реплики dialog.md: `### YYYY-MM-DD HH:MM - Имя`
DIALOG_HEADER_RE = re.compile(r"^### (\d{4}-\d{2}-\d{2}) (\d{2}:\d{2}) - ")
# Дедуп-журнал саморефлексии — НЕ ротационная запись, не трогаем никогда.
REFLECTION_KEEP_ALWAYS = {"ledger.json"}


def _rel(path, root):
    """Стабильный относительный путь с forward-slash (для отчётов/тестов на Windows)."""
    return os.path.relpath(path, root).replace("\\", "/")


def _size(path):
    try:
        return os.path.getsize(path)
    except OSError:
        return 0


def collect_audit_candidates(reports_dir, keep):
    """Пары audit_<stamp>.json / output_<stamp>.log: оставить `keep` последних по stamp.

    Пара группируется по общему таймстампу; непарные файлы (audit без output и наоборот)
    участвуют в той же группировке — старше порога уходят в кандидаты целиком.
    Файлы вне паттерна (audit-claude-*.json и пр.) не рассматриваются вовсе.
    """
    groups = {}  # stamp -> [имена файлов]
    if os.path.isdir(reports_dir):
        for name in os.listdir(reports_dir):
            m = AUDIT_RE.match(name) or OUTPUT_RE.match(name)
            if m:
                groups.setdefault(m.group(1), []).append(name)
    stamps = sorted(groups, reverse=True)          # свежие первыми (stamp лексикографически = хронологически)
    kept, candidates = [], []
    for i, stamp in enumerate(stamps):
        names = sorted(groups[stamp])
        if i < max(0, keep):
            kept.extend(names)
        else:
            for name in names:
                full = os.path.join(reports_dir, name)
                candidates.append({"path": name, "reason": "сверх %d последних пар" % keep,
                                   "bytes": _size(full)})
    return {"kept": sorted(kept), "candidates": candidates,
            "pairs_total": len(stamps), "keep": keep}


def collect_reflection_candidates(reflection_dir, keep):
    """logs/reflection: 0-байтные — кандидаты всегда; остальные сверх `keep` последних по mtime.

    ledger.json (и всё из REFLECTION_KEEP_ALWAYS) исключается до любых порогов.
    """
    entries = []
    if os.path.isdir(reflection_dir):
        for name in os.listdir(reflection_dir):
            if name in REFLECTION_KEEP_ALWAYS:
                continue
            full = os.path.join(reflection_dir, name)
            if os.path.isfile(full):
                entries.append((name, os.path.getmtime(full), _size(full)))
    zero = [(n, m, s) for (n, m, s) in entries if s == 0]
    rest = sorted([(n, m, s) for (n, m, s) in entries if s > 0],
                  key=lambda t: t[1], reverse=True)  # свежие первыми
    candidates = [{"path": n, "reason": "0 байт (пустая запись)", "bytes": 0}
                  for (n, m, s) in sorted(zero)]
    for (n, m, s) in rest[max(0, keep):]:
        candidates.append({"path": n, "reason": "сверх %d последних" % keep, "bytes": s})
    return {"kept_count": len(rest[:max(0, keep)]), "entries_total": len(entries),
            "candidates": candidates, "keep": keep}


def collect_tmpwork_candidates(tmp_dir, age_days, now):
    """tmp-work/*: записи (файлы И каталоги первого уровня) старше `age_days` по mtime.

    mtime каталога меняется при изменении прямых детей — для dry-run отчёта этого
    достаточно; глубокий обход не делаем (дёшево и консервативно).
    """
    cutoff = now - timedelta(days=max(0, age_days))
    candidates, total = [], 0
    if os.path.isdir(tmp_dir):
        for name in sorted(os.listdir(tmp_dir)):
            full = os.path.join(tmp_dir, name)
            total += 1
            try:
                mtime = datetime.fromtimestamp(os.path.getmtime(full))
            except OSError:
                continue
            if mtime < cutoff:
                candidates.append({"path": name,
                                   "reason": "старше %d дн. (mtime %s)" % (age_days, mtime.date()),
                                   "is_dir": os.path.isdir(full),
                                   "bytes": _size(full) if os.path.isfile(full) else None})
    return {"entries_total": total, "candidates": candidates, "age_days": age_days}


def parse_dialog_entries(text):
    """Разбить dialog.md на преамбулу и реплики по заголовкам `### YYYY-MM-DD HH:MM - Имя`.

    Возвращает (preamble_lines, entries), entry = {"date": datetime, "start": №строки (0-based),
    "lines": [...], "header": строка}. Реплики с нераспознанной датой прилипают к предыдущей
    (консервативно: не двигаем то, что не поняли).
    """
    lines = text.splitlines()
    entries, preamble, current = [], [], None
    for i, line in enumerate(lines):
        m = DIALOG_HEADER_RE.match(line)
        if m:
            try:
                dt = datetime.strptime("%s %s" % (m.group(1), m.group(2)), "%Y-%m-%d %H:%M")
            except ValueError:
                dt = None
            if dt is not None:
                current = {"date": dt, "start": i, "lines": [line], "header": line.strip()}
                entries.append(current)
                continue
        if current is None:
            preamble.append(line)
        else:
            current["lines"].append(line)
    return preamble, entries


def collect_dialog_rotation(dialog_path, age_weeks, keep_last, now):
    """C56-a (dry-run): какие реплики старше `age_weeks` недель уехали бы в dialog-archive-YYYY-MM.md.

    Хвост из `keep_last` ПОСЛЕДНИХ по положению в файле реплик не трогается даже старым
    (журнал должен оставаться читабельным без архива). Перенос НЕ выполняется — только отчёт.
    """
    if not os.path.isfile(dialog_path):
        return {"exists": False, "entries_total": 0, "candidates_total": 0, "archives": {},
                "age_weeks": age_weeks, "keep_last": keep_last,
                "note": "перенос реплик — только по решению человека (Q-W2-17); janitor не пишет dialog.md"}
    with open(dialog_path, "r", encoding="utf-8") as f:
        text = f.read()
    _, entries = parse_dialog_entries(text)
    cutoff = now - timedelta(weeks=max(0, age_weeks))
    protected_from = max(0, len(entries) - max(0, keep_last))  # индекс, с которого начинается хвост
    archives = {}
    candidates_total = 0
    for idx, entry in enumerate(entries):
        if idx >= protected_from:
            continue  # хвост — не трогаем
        if entry["date"] >= cutoff:
            continue  # свежая реплика
        target = "dialog-archive-%s.md" % entry["date"].strftime("%Y-%m")
        bucket = archives.setdefault(target, {"entries": 0, "bytes": 0, "from": None, "to": None})
        bucket["entries"] += 1
        bucket["bytes"] += sum(len(ln) + 1 for ln in entry["lines"])
        stamp = entry["date"].strftime("%Y-%m-%d %H:%M")
        bucket["from"] = min(bucket["from"], stamp) if bucket["from"] else stamp
        bucket["to"] = max(bucket["to"], stamp) if bucket["to"] else stamp
        candidates_total += 1
    return {"exists": True, "entries_total": len(entries), "candidates_total": candidates_total,
            "archives": archives, "age_weeks": age_weeks, "keep_last": keep_last,
            "note": "перенос реплик — только по решению человека (Q-W2-17); janitor не пишет dialog.md"}


def collect(root, args, now):
    """Собрать полный отчёт по всем секциям (чистое чтение, без побочных эффектов)."""
    sections = {
        "audit_reports": collect_audit_candidates(os.path.join(root, "reports"), args.keep_audits),
        "reflection": collect_reflection_candidates(os.path.join(root, "logs", "reflection"),
                                                    args.keep_reflections),
        "tmp_work": collect_tmpwork_candidates(os.path.join(root, "tmp-work"),
                                               args.tmp_age_days, now),
        "dialog": collect_dialog_rotation(os.path.join(root, "dialog.md"),
                                          args.dialog_age_weeks, args.dialog_keep_last, now),
    }
    deletable = (len(sections["audit_reports"]["candidates"])
                 + len(sections["reflection"]["candidates"])
                 + len(sections["tmp_work"]["candidates"]))
    return {"schema": "janitor.v1",
            "mode": "delete" if args.delete else "dry-run",
            "root": root,
            "now": now.isoformat(timespec="seconds"),
            "params": {"keep_audits": args.keep_audits,
                       "keep_reflections": args.keep_reflections,
                       "tmp_age_days": args.tmp_age_days,
                       "dialog_age_weeks": args.dialog_age_weeks,
                       "dialog_keep_last": args.dialog_keep_last},
            "sections": sections,
            "deletable_total": deletable}


def apply_delete(report, root):
    """РЕАЛЬНОЕ удаление кандидатов (audit/reflection/tmp-work). Вызывается ТОЛЬКО при --delete.

    Ротация dialog.md сюда сознательно НЕ входит: перенос реплик — решение человека (Q-W2-17).
    Возвращает список удалённых относительных путей; ошибки собираются, не роняют прогон.
    """
    deleted, errors = [], []
    plan = [
        (os.path.join(root, "reports"), report["sections"]["audit_reports"]["candidates"]),
        (os.path.join(root, "logs", "reflection"), report["sections"]["reflection"]["candidates"]),
        (os.path.join(root, "tmp-work"), report["sections"]["tmp_work"]["candidates"]),
    ]
    for base, candidates in plan:
        for cand in candidates:
            full = os.path.join(base, cand["path"])
            try:
                if os.path.isdir(full):
                    shutil.rmtree(full)
                elif os.path.exists(full):
                    os.remove(full)
                deleted.append(_rel(full, root))
            except OSError as exc:
                errors.append({"path": _rel(full, root), "error": str(exc)})
    return deleted, errors


def run_gc(root):
    """`git gc --auto` (задел C54). Только по явному --gc; сбой не роняет отчёт."""
    try:
        p = subprocess.run(["git", "gc", "--auto"], cwd=root, capture_output=True,
                           text=True, encoding="utf-8", errors="replace",
                           stdin=subprocess.DEVNULL, timeout=600)
        return {"rc": p.returncode, "stderr": (p.stderr or "").strip()[:500]}
    except Exception as exc:  # git отсутствует/таймаут — отчёт важнее
        return {"rc": -1, "stderr": str(exc)[:500]}


def render_text(report):
    """Человекочитаемый отчёт (stdout)."""
    s = report["sections"]
    lines = ["=== JANITOR · режим %s · %s ===" % (report["mode"], report["now"])]
    a = s["audit_reports"]
    lines.append("reports/audit_*+output_*: пар %d, оставить %d, кандидатов %d" % (
        a["pairs_total"], a["keep"], len(a["candidates"])))
    for c in a["candidates"][:8]:
        lines.append("  - reports/%s (%s)" % (c["path"], c["reason"]))
    r = s["reflection"]
    lines.append("logs/reflection: записей %d, оставить %d, кандидатов %d (ledger.json не трогаем)" % (
        r["entries_total"], r["keep"], len(r["candidates"])))
    for c in r["candidates"][:8]:
        lines.append("  - logs/reflection/%s (%s)" % (c["path"], c["reason"]))
    t = s["tmp_work"]
    lines.append("tmp-work: записей %d, старше %d дн. — кандидатов %d" % (
        t["entries_total"], t["age_days"], len(t["candidates"])))
    for c in t["candidates"][:8]:
        lines.append("  - tmp-work/%s (%s)" % (c["path"], c["reason"]))
    d = s["dialog"]
    if d["exists"]:
        lines.append("dialog.md: реплик %d, старше %d нед. (кроме хвоста %d) — в архив ушло бы %d" % (
            d["entries_total"], d["age_weeks"], d["keep_last"], d["candidates_total"]))
        for target, info in sorted(d["archives"].items()):
            lines.append("  → %s: %d реплик, ~%d байт (%s … %s)" % (
                target, info["entries"], info["bytes"], info["from"], info["to"]))
        lines.append("  примечание: %s" % d["note"])
    else:
        lines.append("dialog.md: не найден — секция пропущена")
    if report["mode"] == "dry-run":
        lines.append("итого удаляемых кандидатов: %d — НИЧЕГО НЕ УДАЛЕНО (dry-run; включение --delete — за человеком, Q-W2-15)"
                     % report["deletable_total"])
    else:
        lines.append("итого удалено: %d" % len(report.get("deleted", [])))
        for e in report.get("delete_errors", [])[:5]:
            lines.append("  ! ошибка: %s — %s" % (e["path"], e["error"]))
    if report.get("gc"):
        lines.append("git gc --auto: rc=%s" % report["gc"]["rc"])
    return "\n".join(lines)


def parse_args(argv):
    parser = argparse.ArgumentParser(
        description="Дворник runtime-артефактов: dry-run отчёт ротации; удаление только явным --delete.")
    parser.add_argument("--root", default=ROOT, help="Корень репозитория (для тестов — tmp-каталог).")
    parser.add_argument("--keep-audits", type=int, default=DEFAULT_KEEP_AUDITS,
                        help="Сколько последних пар audit_*/output_* оставить (деф. %(default)s).")
    parser.add_argument("--keep-reflections", type=int, default=DEFAULT_KEEP_REFLECTIONS,
                        help="Сколько последних записей logs/reflection оставить (деф. %(default)s).")
    parser.add_argument("--tmp-age-days", type=int, default=DEFAULT_TMP_AGE_DAYS,
                        help="tmp-work/* старше N дней — кандидат (деф. %(default)s).")
    parser.add_argument("--dialog-age-weeks", type=int, default=DEFAULT_DIALOG_AGE_WEEKS,
                        help="Реплики dialog.md старше N недель — кандидаты в архив (деф. %(default)s).")
    parser.add_argument("--dialog-keep-last", type=int, default=DEFAULT_DIALOG_KEEP_LAST,
                        help="Последние K реплик не трогать даже старыми (деф. %(default)s).")
    parser.add_argument("--now", help="ISO-время «сейчас» для детерминированных тестов.")
    parser.add_argument("--delete", action="store_true",
                        help="РЕАЛЬНОЕ удаление кандидатов (по умолчанию выключено; включает человек, Q-W2-15). "
                             "Реплики dialog.md НЕ переносятся даже с этим флагом.")
    parser.add_argument("--gc", action="store_true",
                        help="Вызвать git gc --auto после отчёта (задел C54; по умолчанию выключено).")
    parser.add_argument("--json", action="store_true", help="Машинный отчёт JSON.")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(sys.argv[1:] if argv is None else argv)
    now = datetime.fromisoformat(args.now) if args.now else datetime.now()
    root = os.path.abspath(args.root)
    report = collect(root, args, now)
    if args.delete:
        deleted, errors = apply_delete(report, root)
        report["deleted"] = deleted
        report["delete_errors"] = errors
    if args.gc:
        report["gc"] = run_gc(root)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(render_text(report))
    return 0


if __name__ == "__main__":
    sys.exit(main())
