#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
assurance (Q-016) — единый READ-ONLY апекс-дашборд проверяемости инструкций.

Отвечает на вопрос Q-016: «где гарантия, что инструкции реально применяются, актуальны и доходят
от основания пирамиды до вершины». Сводит ЧЕТЫРЕ ранее разрозненных сигнала в один вид с вердиктом:

  applied   — applied-evidence: % служебных задач, закрытых с реальным evidence (а не формально);
  currency  — актуальность: accepted-решения/политики без last_verified, протухшие, с битыми ссылками;
  coverage  — поток вверх: orphan-L1 (ядро, на которое не ссылается ни один портал) и
              ungrounded-L2 (портал без опоры на L1);
  flow      — база→вершина: существование файлов реестра инструкций и accepted-решения, не
              упомянутые в поверхности инструкций (висячие D-NNN).

Инструмент НИЧЕГО не мутирует и НЕ принимает решений (граница read/observe, как у friction.py).
По умолчанию advisory (exit 0); с `--strict` возвращает 1, если есть находки — тогда top.py/health/CI
могут на него опираться. Переиспользует существующее, не плодит парсеров/индексов:
  `_canon.parse_front_matter`, `pipeline._needs_applied_evidence`, `instructions.check_report_text`/
  `INSTRUCTIONS`, `promote.level_of`/`_list_field`.

CLI:
    python tools/assurance.py [applied|currency|coverage|flow|all] [--root DIR] [--json] [--strict] [--max-age N]
"""
import os
import re
import sys
from _ioutil import configure_output
import json
import glob
import datetime

ROOT_DEFAULT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOLS = os.path.join(ROOT_DEFAULT, "tools")
sys.path.insert(0, TOOLS)

from _canon import parse_front_matter  # единый парсер front-matter
import pipeline as pl                  # _needs_applied_evidence + SERVICE_* константы
import instructions as ins             # INSTRUCTIONS реестр + check_report_text
import promote as pr                   # level_of / _list_field / уровни пирамиды

configure_output()

DOC_REF_RE = re.compile(
    r"(?:tools|docs|decisions|questions|topics|core|portals|drivers|collab|sandbox|queues|streams)"
    r"/[\wа-яёА-ЯЁ./-]+?\.(?:md|py|json)")
DREF_RE = re.compile(r"\bD-\d{3}\b")
BOILERPLATE = {"agents.md", "protocol.md", "checks", "checks:"}
# Конвенция --applied введена с T-156 (pipeline.cmd_done); раньше evidence не существовало.
CONVENTION_MIN = 156
# Сколько находок показывать в тексте на секцию (полный список — в --json).
DISPLAY_CAP = 8

def _structural_refs(text):
    """Ссылки на файлы ТОЛЬКО из структурных позиций (front-matter + markdown-линки),
    НЕ из прозы/примеров — иначе гипотетические пути в таблицах примеров дают ложные битые ссылки."""
    refs = set()
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            refs.update(DOC_REF_RE.findall(text[3:end]))
    for m in re.finditer(r"\]\(([^)]+)\)", text):
        refs.update(DOC_REF_RE.findall(m.group(1)))
    return refs

def _tid_num(tid):
    m = re.search(r"(\d+)", tid or "")
    return int(m.group(1)) if m else None

def _read(path):
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            return f.read()
    except OSError:
        return ""

def _fm(path):
    return parse_front_matter(_read(path))

def _finding(level, msg, where):
    return {"level": level, "msg": msg, "where": where}

def _today():
    return datetime.date.today()

def _age_days(datestr):
    """Возраст в днях по ISO-дате (YYYY-MM-DD) либо None."""
    s = (datestr or "").strip()
    if not re.match(r"^\d{4}-\d{2}-\d{2}$", s):
        return None
    try:
        return (_today() - datetime.date.fromisoformat(s)).days
    except ValueError:
        return None

# --- (а) applied-evidence ----------------------------------------------------

def _is_boilerplate(applied):
    """True, если в evidence нет ни одного task-specific токена (только AGENTS/PROTOCOL/Checks)."""
    parts = [p.strip().lower() for p in re.split(r"[,\n]", applied) if p.strip()]
    meaningful = [p for p in parts if p not in BOILERPLATE]
    for p in meaningful:
        if "/" in p or re.search(r"\b[dft]-\d", p) or p.endswith(".md") or p.endswith(".py"):
            return False
    return True


def _evidence_addenda_by_task(root):
    """Post-hoc evidence addenda keyed by task id.

    This keeps queues/done/*.done.md immutable as execution history while allowing
    later reviewers to attach missing Applied instructions evidence in a separate file.
    """
    evidence_dir = os.path.join(root, "queues", "evidence")
    out = {}
    for path in sorted(glob.glob(os.path.join(evidence_dir, "*.evidence.md"))):
        text = _read(path)
        meta = parse_front_matter(text)
        tid = (meta.get("task") or "").strip().upper()
        if not tid:
            m = re.match(r"^(T-\d+)", os.path.basename(path), re.I)
            if m:
                tid = m.group(1).upper()
        if not tid:
            continue
        out.setdefault(tid, []).append({"path": path, "text": text, "meta": meta})
    return out


def _combined_applied(meta, addenda):
    parts = [(meta.get("applied") or "").strip()]
    for item in addenda:
        parts.append((item["meta"].get("applied") or "").strip())
    return ", ".join(p for p in parts if p)


def _combined_report_text(done_text, addenda):
    if not addenda:
        return done_text
    return done_text + "\n\n" + "\n\n".join(item["text"] for item in addenda)


def _evidence_where(default_where, addenda, root):
    if not addenda:
        return default_where
    rels = [os.path.relpath(item["path"], root).replace("\\", "/") for item in addenda]
    return default_where + " + " + ", ".join(rels)

def section_applied(root):
    done_dir = os.path.join(root, "queues", "done")
    tasks_dir = os.path.join(root, "tasks")
    addenda_by_task = _evidence_addenda_by_task(root)
    findings, era_total, era_ev, legacy_missing = [], 0, 0, 0
    for path in sorted(glob.glob(os.path.join(done_dir, "*.done.md"))):
        text = _read(path)
        meta = parse_front_matter(text)
        tid = (meta.get("task") or "").strip().upper()
        task_fm = _fm(os.path.join(tasks_dir, "%s.md" % tid)) if tid else {}
        scope = {"topic": task_fm.get("topic", ""), "title": task_fm.get("title", "")}
        if not pl._needs_applied_evidence(scope):
            continue
        addenda = addenda_by_task.get(tid, [])
        applied = _combined_applied(meta, addenda)
        report_text = _combined_report_text(text, addenda)
        ok = (applied and applied.lower() not in ("none", "-")
              and not ins.check_report_text(report_text) and not _is_boilerplate(applied))
        num = _tid_num(tid)
        if num is not None and num < CONVENTION_MIN:  # легаси до конвенции — не actionable
            if not ok:
                legacy_missing += 1
            continue
        era_total += 1
        where = _evidence_where("queues/done/%s" % os.path.basename(path), addenda, root)
        if not applied or applied.lower() in ("none", "-"):
            findings.append(_finding("high", "%s: служебная задача закрыта без applied-evidence" % tid, where))
            continue
        missing = ins.check_report_text(report_text)
        if missing:
            findings.append(_finding("medium", "%s: слабое evidence (нет: %s)" % (tid, ", ".join(missing)), where))
            continue
        if _is_boilerplate(applied):
            findings.append(_finding("low", "%s: evidence формальное (нет task-specific ссылки)" % tid, where))
            continue
        era_ev += 1
    findings.sort(key=lambda f: -(_tid_num(f["msg"]) or 0))  # свежие задачи первыми
    pct = round(100.0 * era_ev / era_total, 1) if era_total else 100.0
    return {
        "name": "applied-evidence",
        "metric": "%d/%d задач конвенц-эры (T>=%d) с реальным evidence (%.1f%%); legacy без evidence: %d"
                  % (era_ev, era_total, CONVENTION_MIN, pct, legacy_missing),
        "findings": findings,
    }

# --- (б) currency / freshness ------------------------------------------------

TERMINAL_DECISION_STATUSES = {"rejected", "superseded", "superseded_by"}
HISTORICAL_DREF_MARKERS = (
    "связано", "related", "history", "истор", "context", "контекст",
    "evidence", "postscript", "superseded", "source", "источник",
)

def _decision_status_index(root):
    idx = {}
    for path in glob.glob(os.path.join(root, "decisions", "D-*.md")):
        fm = _fm(path)
        did = (fm.get("id") or os.path.splitext(os.path.basename(path))[0]).strip()
        idx[did] = (fm.get("status") or "").strip().lower()
    return idx

def _historical_dref_line(line):
    low = (line or "").lower()
    return any(marker in low for marker in HISTORICAL_DREF_MARKERS)

def _currency_targets(root):
    """decisions/*.md + политики (docs/ цели реестра инструкций + явные политики)."""
    targets = sorted(glob.glob(os.path.join(root, "decisions", "D-*.md")))
    docs = set(i["path"] for i in ins.INSTRUCTIONS if i["path"].startswith("docs/"))
    docs.update([
        "docs/parallel-work-policy.md", "docs/promotion-rules.md",
        "docs/workflow-orchestration-policy.md", "docs/instruction-assurance.md",
    ])
    for rel in sorted(docs):
        p = os.path.join(root, rel)
        if os.path.isfile(p):
            targets.append(p)
    return targets

def section_currency(root, max_age):
    findings = []
    dstatus = _decision_status_index(root)
    missing_lv = []
    for path in _currency_targets(root):
        rel = os.path.relpath(path, root).replace("\\", "/")
        text = _read(path)
        fm = parse_front_matter(text)
        status = (fm.get("status") or "").strip().lower()
        body = text
        # 1) accepted без last_verified — нудж на принятие конвенции (info)
        if status == "accepted" and not (fm.get("last_verified") or "").strip():
            missing_lv.append(rel)
        # 2) возраст по last_verified|date
        age = _age_days(fm.get("last_verified") or fm.get("date"))
        if age is not None and age > max_age:
            findings.append(_finding("medium", "%s: не сверялось %d дн. (> %d)" % (rel, age, max_age), rel))
        # 3) Нормативные ссылки на rejected/superseded решения в живом доке.
        # Исторические/related ссылки и сами terminal-документы не являются drift: они сохраняют provenance.
        current_id = (fm.get("id") or os.path.splitext(os.path.basename(path))[0]).strip()
        if status not in TERMINAL_DECISION_STATUSES:
            for line in body.splitlines():
                if _historical_dref_line(line):
                    continue
                for dref in set(DREF_RE.findall(line)):
                    if dref == current_id:
                        continue
                    st = dstatus.get(dref)
                    if st in TERMINAL_DECISION_STATUSES:
                        findings.append(_finding("high", "%s: ссылается на %s со статусом %s" % (rel, dref, st), rel))
        # 4) битые ссылки на файлы/инструменты — ТОЛЬКО структурные (не примеры в прозе)
        for ref in _structural_refs(text):
            if not os.path.exists(os.path.join(root, ref)):
                findings.append(_finding("high", "%s: битая структурная ссылка на %s (файла нет)" % (rel, ref), rel))
    if missing_lv:
        findings.append(_finding(
            "info",
            "accepted-доков без last_verified: %d (%s%s)" % (
                len(missing_lv), ", ".join(missing_lv[:4]), " …" if len(missing_lv) > 4 else ""),
            "convention"))
    return {
        "name": "currency",
        "metric": "%d находок актуальности; без last_verified: %d" % (len(findings), len(missing_lv)),
        "findings": findings,
    }

# --- (в) promotion-coverage --------------------------------------------------

def _portal_text(root):
    parts = []
    for path in glob.glob(os.path.join(root, "portals", "**", "*.md"), recursive=True):
        parts.append(_read(path))
    return "\n".join(parts)

def section_coverage(root):
    findings = []
    core_dir = os.path.join(root, pr.L1_DIR)
    manifest = os.path.join(core_dir, "engine-manifest.md")
    mfm = _fm(manifest)
    l1_items = pr._list_field(mfm.get("files"))
    for p in glob.glob(os.path.join(core_dir, "*.md")):
        l1_items.append(os.path.relpath(p, root).replace("\\", "/"))
    ptext = _portal_text(root)
    orphans = []
    for item in l1_items:
        token = os.path.basename(item)
        if token and token not in ptext:
            orphans.append(token)
    if orphans:
        findings.append(_finding(
            "medium",
            "orphan-L1: ядро без ссылок из порталов: %d (%s%s)" % (
                len(orphans), ", ".join(orphans[:6]), " …" if len(orphans) > 6 else ""),
            "core/engine-manifest.md"))
    # ungrounded-L2 and existence-checked grounding
    l1_tokens = pr._manifest_l1_tokens(root)
    n_portals = 0
    for portal in glob.glob(os.path.join(root, "portals", "*", "portal.md")):
        n_portals += 1
        rel = os.path.relpath(portal, root).replace("\\", "/")
        text = _read(portal)
        fm = parse_front_matter(text)

        basis_list = pr._list_field(fm.get("l1_basis"))
        grounded = bool(basis_list)
        if not grounded and "core/" not in text:
            findings.append(_finding("high", "%s: портал без опоры на L1 (пустой l1_basis)" % rel, rel))

        for token in basis_list:
            bn = os.path.basename(token.replace("\\", "/").strip())
            if bn and bn not in l1_tokens:
                findings.append(_finding("high", "%s: заявленный базис '%s' не найден в L1-инвентаре (stale/unresolved)" % (rel, token), rel))
    return {
        "name": "promotion-coverage",
        "metric": "L1-инвентарь: %d, порталов: %d, orphan-L1: %d" % (len(l1_items), n_portals, len(orphans)),
        "findings": findings,
    }

# --- base→apex flow ----------------------------------------------------------

def section_flow(root):
    findings = []
    surface = []
    for item in ins.INSTRUCTIONS:
        p = os.path.join(root, item["path"])
        if not os.path.isfile(p):
            findings.append(_finding("high", "файл инструкции отсутствует: %s (id=%s)" % (item["path"], item["id"]), item["path"]))
        else:
            surface.append(_read(p))
    surface_text = "\n".join(surface)
    # two-spine join (piece 3): решение заземлено, если упомянуто в прозе ИЛИ объявлено в
    # structured `surfaces`-ключе инструкции (точный join вместо fuzzy substring; см. instructions.trace).
    surfaced_ids = {s.strip().upper() for item in ins.INSTRUCTIONS for s in item.get("surfaces", [])}
    orphan_dec = []
    for path in sorted(glob.glob(os.path.join(root, "decisions", "D-*.md"))):
        fm = _fm(path)
        if (fm.get("status") or "").strip().lower() != "accepted":
            continue
        did = (fm.get("id") or os.path.splitext(os.path.basename(path))[0]).strip()
        if did not in surface_text and did.upper() not in surfaced_ids:
            orphan_dec.append(did)
    if orphan_dec:
        findings.append(_finding(
            "medium",
            "accepted-решения, не упомянутые в поверхности инструкций: %d (%s%s)" % (
                len(orphan_dec), ", ".join(orphan_dec[:8]), " …" if len(orphan_dec) > 8 else ""),
            "instructions.INSTRUCTIONS"))
    return {
        "name": "flow",
        "metric": "файлов реестра: %d, висячих accepted-решений: %d" % (len(ins.INSTRUCTIONS), len(orphan_dec)),
        "findings": findings,
    }

SECTIONS = {
    "applied": lambda root, max_age: section_applied(root),
    "currency": lambda root, max_age: section_currency(root, max_age),
    "coverage": lambda root, max_age: section_coverage(root),
    "flow": lambda root, max_age: section_flow(root),
}
ORDER = ["applied", "currency", "coverage", "flow"]

def run(which, root, max_age):
    keys = ORDER if which in (None, "all") else [which]
    return [SECTIONS[k](root, max_age) for k in keys]

_ICON = {"high": "✗", "medium": "!", "low": "·", "info": "i"}

def render(results):
    L = ["=" * 60, "ASSURANCE — проверяемость инструкций (Q-016) · READ-ONLY", "=" * 60]
    total = 0
    hard = 0
    for sec in results:
        finds = sec["findings"]
        total += len(finds)
        hard += sum(1 for f in finds if f["level"] in ("high", "medium"))
        head = "OK" if not finds else "%d находок" % len(finds)
        L.append("")
        L.append("[%s] %s — %s" % (head, sec["name"], sec["metric"]))
        for f in finds[:DISPLAY_CAP]:
            L.append("    %s %s" % (_ICON.get(f["level"], "-"), f["msg"]))
        if len(finds) > DISPLAY_CAP:
            L.append("    … ещё %d (полный список: --json)" % (len(finds) - DISPLAY_CAP))
    L.append("")
    L.append("-" * 60)
    verdict = "PASS" if total == 0 else ("WARN" if hard == 0 else "ATTENTION")
    L.append("Вердикт: %s · всего находок: %d (high/medium: %d)" % (verdict, total, hard))
    L.append("=" * 60)
    return "\n".join(L), hard

def main():
    a = sys.argv[1:]
    which = None
    for tok in a:
        if tok in SECTIONS or tok == "all":
            which = tok
    root = ROOT_DEFAULT
    if "--root" in a:
        i = a.index("--root")
        if i + 1 < len(a):
            root = os.path.abspath(a[i + 1])
    max_age = 180
    if "--max-age" in a:
        i = a.index("--max-age")
        if i + 1 < len(a):
            try:
                max_age = int(a[i + 1])
            except ValueError:
                pass
    as_json = "--json" in a
    strict = "--strict" in a
    try:
        results = run(which, root, max_age)
    except Exception as exc:  # noqa: BLE001
        print("ОШИБКА: %s: %s" % (type(exc).__name__, exc))
        return 1
    if as_json:
        hard = sum(1 for s in results for f in s["findings"] if f["level"] in ("high", "medium"))
        print(json.dumps({"sections": results}, ensure_ascii=False, indent=2))
    else:
        text, hard = render(results)
        print(text)
    return 1 if (strict and hard > 0) else 0

if __name__ == "__main__":
    sys.exit(main())
