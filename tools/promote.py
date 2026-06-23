#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Promotion gate пирамиды рабочих областей (ответ на open-question 5
`docs/workspace-pyramid-levels.md`: «нужен ли tools/promote.py?» — да, как gate).

Формализует переходы L4 sandbox -> L3 collab -> L2 portals -> L1 core по правилам
`docs/promotion-rules.md`. Ничего не поднимается выше автоматически: каждый переход
проходит per-criterion gate, перемещение атомарно (write-new-THEN-remove-old) и
штампует promotion-метаданные во front-matter. collab/ остаётся ЛОГИЧЕСКИМ слоем
(без mass-migration существующих tasks/decisions/questions/streams/темы).

CLI:
    python tools/promote.py list
    python tools/promote.py check --artifact <path>
    python tools/promote.py move --artifact <path> --from L4 --to L3 \\
        [--reviewed-by NAME] [--decision-ref D-NNN] [--root DIR]
    python tools/promote.py export --to DIR --files a,b,c   # core-export: курируемая КОПИЯ набора
    python tools/promote.py export --to DIR --manifest core/engine-manifest.md  # files: из манифеста

--root DIR переопределяет корень пирамиды (для герметичных тестов / временных пирамид).

`export` — для L1 core-export: материализует переносимый набор файлов в отдельный каталог
(копия, НЕ move — живой `tools/` остаётся mainline). Доказывает переносимость ядра, не ломая ссылки.
"""
import os
import sys
import glob
import shutil
import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from _canon import parse_front_matter  # единый парсер front-matter канона


def configure_output():
    for name in ("stdout", "stderr"):
        s = getattr(sys, name, None)
        if s is not None and hasattr(s, "reconfigure"):
            s.reconfigure(encoding="utf-8", errors="replace")


configure_output()

# Уровни пирамиды. L3 — логический слой (несколько корневых каталогов).
LEVELS = ["L1", "L2", "L3", "L4"]
L1_DIR = "core"
L2_DIR = "portals"
L4_DIR = "sandbox"
# collab логически = эти корневые каталоги (карта L3, без физического переноса).
L3_DIRS = ["tasks", "decisions", "questions", "streams", "темы", "collab"]


def _root(root=None):
    return os.path.abspath(root) if root else ROOT


def level_of(artifact, root=None):
    """Определить уровень артефакта по его относительному пути под корнем пирамиды."""
    base = _root(root)
    rel = os.path.relpath(os.path.abspath(artifact), base).replace("\\", "/")
    top = rel.split("/", 1)[0]
    if top == L1_DIR:
        return "L1"
    if top == L2_DIR:
        return "L2"
    if top == L4_DIR:
        return "L4"
    if top in L3_DIRS:
        return "L3"
    return None


def _read_fm(path):
    if not os.path.isfile(path):
        return {}
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            return parse_front_matter(f.read())
    except OSError:
        return {}


def _list_field(value):
    s = (value or "").strip()
    if s.startswith("[") and s.endswith("]"):
        s = s[1:-1]
    return [x.strip() for x in s.split(",") if x.strip()]


def _manifest_l1_tokens(base):
    """Токены L1-инвентаря: basename из core/engine-manifest.md `files:` + все core/*.md."""
    tokens = set()
    man = os.path.join(base, L1_DIR, "engine-manifest.md")
    for rel in _list_field(_read_fm(man).get("files")):
        bn = os.path.basename(rel.replace("\\", "/").strip())
        if bn:
            tokens.add(bn)
    for md in glob.glob(os.path.join(base, L1_DIR, "*.md")):
        tokens.add(os.path.basename(md))
    return tokens


def derive_reuse(root=None):
    """Вывести ФАКТИЧЕСКОЕ повторное использование L1-токенов порталами (scan-derived, не самодекларация).

    Чинит two-channel grounding (Q-016/pyramid): `reused_in` не имел писателей и был непроходим/подделываем.
    Для каждого `portals/*/portal.md` собираем его `l1_basis` + тела markdown каталога портала; токен L1
    помечается reused-by-<portal_id>, если его basename встречается подстрокой. Возвращает {token: set(portal_ids)}.
    """
    base = _root(root)
    tokens = _manifest_l1_tokens(base)
    reuse = {t: set() for t in tokens}
    for pm in glob.glob(os.path.join(base, L2_DIR, "*", "portal.md")):
        pdir = os.path.dirname(pm)
        fm = _read_fm(pm)
        pid = (fm.get("id") or os.path.basename(pdir)).strip()
        blob_parts = list(_list_field(fm.get("l1_basis")))
        for md in glob.glob(os.path.join(pdir, "*.md")):
            try:
                with open(md, encoding="utf-8", errors="replace") as f:
                    blob_parts.append(f.read())
            except OSError:
                pass
        blob = "\n".join(blob_parts)
        for t in tokens:
            if t and t in blob:
                reuse[t].add(pid)
    return reuse


def _has_decision_ref(fm):
    for k in ("decision_ref", "decision", "decisions"):
        v = (fm.get(k) or "").strip()
        if v and v not in ("none", "-", "tbd"):
            return True
    # любое поле, ссылающееся на D-NNN
    for v in fm.values():
        if isinstance(v, str) and "D-" in v:
            return True
    return False


def _has_verification(fm):
    for k in ("tests", "gate_checks_passed", "verification", "verified"):
        v = (fm.get(k) or "").strip()
        if v and v.lower() not in ("", "none", "no", "false", "-"):
            return True
    return False


# --- gate-критерии по docs/promotion-rules.md -------------------------------

def _gate_L4_L3(path, fm, root):
    return [
        ("read_only_report", level_of(path, root) == "L4",
         "артефакт под sandbox/ (L4) как read-only summary"),
        ("decision_ref", _has_decision_ref(fm),
         "есть ссылка на решение (decision_ref / D-NNN), легализующее подъём из quarantine"),
        ("no_raw_execute", (fm.get("mode", "") != "execute"),
         "подъём не требует запуска внешнего кода (execute-gate отдельный)"),
    ]


def _gate_L3_L2(path, fm, root):
    blob = " ".join(str(v) for v in fm.values()).lower()
    history_markers = ("claim:", "done:", "fail:", "обсужд")
    clean = not any(m in blob for m in history_markers)
    return [
        ("clean_present_tense", clean,
         "чистовое present-tense состояние без длинной истории споров"),
        ("tests_green", _has_verification(fm),
         "тесты зелёные / есть verification-ссылка"),
        ("portal_target", True,
         "назначение — конкретный портал portals/<id>/ (проверяется при move --to L2)"),
    ]


def _gate_L2_L1(path, fm, root):
    # derived: считаем РАЗНЫЕ порталы, реально ссылающиеся на артефакт (scan), а не самодекларацию reused_in
    token = os.path.basename(path)
    reuse = derive_reuse(root)
    portals = set()
    for t, pids in reuse.items():
        if token == t or token in t or t in token:
            portals |= pids
    decision_override = _has_decision_ref(fm)
    return [
        ("reuse_across_portals", len(portals) >= 2 or decision_override,
         "повторное применение в >=2 порталах (derive_reuse-скан), либо decision-ref override (D-NNN)"),
        ("verification", _has_verification(fm),
         "строгая проверка: тесты ядра зелёные / verification-ссылка"),
        ("no_domain_coupling",
         not any(fm.get(k) for k in ("portal", "domain", "corpus")),
         "не привязано к одному домену/пользователю/корпусу"),
    ]


_GATES = {("L4", "L3"): _gate_L4_L3, ("L3", "L2"): _gate_L3_L2, ("L2", "L1"): _gate_L2_L1}


def _adjacent(frm, to):
    return frm in LEVELS and to in LEVELS and LEVELS.index(to) == LEVELS.index(frm) - 1


def check(artifact, frm=None, to=None, root=None):
    """Проверить готовность артефакта против promotion-rules. Возвращает dict."""
    base = _root(root)
    path = os.path.abspath(artifact)
    if not os.path.isfile(path):
        raise FileNotFoundError("нет артефакта: %s" % path)
    cur = level_of(path, base)
    frm = frm or cur
    if to is None and frm in LEVELS:
        idx = LEVELS.index(frm)
        to = LEVELS[idx - 1] if idx > 0 else None
    if not _adjacent(frm, to):
        raise ValueError("переход %s->%s не разрешён (только вверх на 1 уровень)" % (frm, to))
    fm = _read_fm(path)
    gate = _GATES[(frm, to)]
    criteria = gate(path, fm, base)
    results = [{"name": n, "passed": bool(p), "desc": d} for (n, p, d) in criteria]
    return {"artifact": path, "level": cur, "from": frm, "to": to,
            "criteria": results, "ready": all(r["passed"] for r in results)}


def list_levels(root=None):
    """Перечислить уровни и артефакты со статусом."""
    base = _root(root)
    out = []
    layout = [("L1", [L1_DIR]), ("L2", [L2_DIR]), ("L3", L3_DIRS), ("L4", [L4_DIR])]
    for level, dirs in layout:
        artifacts = []
        for d in dirs:
            dpath = os.path.join(base, d)
            if not os.path.isdir(dpath):
                continue
            for cur, _sub, files in os.walk(dpath):
                for fn in sorted(files):
                    if fn.endswith(".md"):
                        rel = os.path.relpath(os.path.join(cur, fn), base).replace("\\", "/")
                        artifacts.append(rel)
        out.append({"level": level, "dirs": dirs,
                    "count": len(artifacts), "artifacts": sorted(artifacts)})
    return out


def _stamp_fm(text, stamp):
    """Добавить/обновить поля stamp во front-matter; вернуть новый текст."""
    keys = list(stamp.keys())
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            head = text[3:end].strip("\n")
            rest = text[end + 4:]
            lines = [ln for ln in head.splitlines()
                     if ":" not in ln or ln.split(":", 1)[0].strip() not in keys]
            for k in keys:
                lines.append("%s: %s" % (k, stamp[k]))
            return "---\n" + "\n".join(lines) + "\n---" + rest
    # нет front-matter — создать
    body = text
    fm_lines = ["%s: %s" % (k, stamp[k]) for k in keys]
    return "---\n" + "\n".join(fm_lines) + "\n---\n\n" + body


def move(artifact, frm, to, reviewed_by="unspecified", decision_ref="",
         root=None, dest=None, force=False):
    """Атомарный подъём на соседний уровень + stamp метаданных.

    write-new-THEN-remove-old: новый путь создаётся первым, старый удаляется только
    после успешной записи. Гарантирует: нет half-move/orphan.
    """
    base = _root(root)
    src = os.path.abspath(artifact)
    if not os.path.isfile(src):
        raise FileNotFoundError("нет артефакта: %s" % src)
    if not _adjacent(frm, to):
        raise ValueError("переход %s->%s не разрешён (только вверх на 1 уровень)" % (frm, to))
    if not force:
        rep = check(src, frm=frm, to=to, root=base)
        if not rep["ready"]:
            failed = [r["name"] for r in rep["criteria"] if not r["passed"]]
            raise ValueError("gate не пройден (%s->%s): %s" % (frm, to, ", ".join(failed)))

    target_dir = {"L1": L1_DIR, "L2": L2_DIR, "L4": L4_DIR}.get(to)
    if target_dir is None:  # to == L3
        target_dir = L3_DIRS[0]
    if dest:
        new_path = os.path.abspath(dest)
    else:
        new_path = os.path.join(base, target_dir, os.path.basename(src))
    if os.path.abspath(new_path) == src:
        raise ValueError("источник и назначение совпадают: %s" % src)
    if os.path.exists(new_path):
        raise FileExistsError("назначение уже существует: %s" % new_path)

    with open(src, encoding="utf-8", errors="replace") as f:
        text = f.read()
    stamp = {
        "promoted_from": frm,
        "promoted_to": to,
        "promotion_date": datetime.date.today().isoformat(),
        "gate_checks_passed": "[%s]" % ", ".join(
            r["name"] for r in check(src, frm=frm, to=to, root=base)["criteria"]
            if force or r["passed"]) if not force else "[forced]",
        "reviewed_by": reviewed_by,
        "decision_ref": decision_ref or "none",
    }
    new_text = _stamp_fm(text, stamp)

    # 1) write-new (атомарно через tmp + replace)
    os.makedirs(os.path.dirname(new_path), exist_ok=True)
    tmp = new_path + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
        f.write(new_text)
    os.replace(tmp, new_path)
    # 2) THEN remove-old (только после успешной записи нового)
    os.remove(src)
    return {"from_path": src, "to_path": new_path, "from": frm, "to": to, "stamp": stamp}


def export(files, to, root=None, readme=None):
    """Курируемая КОПИЯ списка файлов в target-каталог (core-export), с сохранением repo-relative
    структуры. НЕ move: исходные файлы остаются. Возвращает {to, copied, missing}."""
    base = _root(root)
    dest_root = os.path.abspath(to)
    copied, missing = [], []
    for rel in files:
        rel = rel.replace("\\", "/").strip()
        src = os.path.join(base, rel)
        if not os.path.isfile(src):
            missing.append(rel)
            continue
        dst = os.path.join(dest_root, rel)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy2(src, dst)
        copied.append(rel)
    os.makedirs(dest_root, exist_ok=True)
    with open(os.path.join(dest_root, "EXPORT.md"), "w", encoding="utf-8", newline="\n") as f:
        f.write((readme or "Экспортированный переносимый набор (core-export).") + "\n\n")
        f.write("Файлы (%d):\n" % len(copied))
        for c in copied:
            f.write("- %s\n" % c)
    return {"to": dest_root, "copied": copied, "missing": missing}


def _arg(a, flag, default=None):
    return a[a.index(flag) + 1] if flag in a and a.index(flag) + 1 < len(a) else default


def main():
    a = sys.argv[1:]
    if not a:
        print(__doc__)
        return 2
    cmd = a[0]
    root = _arg(a, "--root")
    try:
        if cmd == "list":
            for lv in list_levels(root=root):
                print("%s  %-28s files=%d" % (lv["level"], "/".join(lv["dirs"]), lv["count"]))
                for art in lv["artifacts"]:
                    print("    %s" % art)
            return 0
        if cmd == "check" and "--artifact" in a:
            frm = _arg(a, "--from")
            to = _arg(a, "--to")
            rep = check(_arg(a, "--artifact"), frm=frm, to=to, root=root)
            print("check %s  (%s->%s)" % (rep["artifact"], rep["from"], rep["to"]))
            for r in rep["criteria"]:
                print("  [%s] %-22s — %s" % ("PASS" if r["passed"] else "FAIL", r["name"], r["desc"]))
            print("READY" if rep["ready"] else "NOT READY")
            return 0 if rep["ready"] else 1
        if cmd == "move" and "--artifact" in a and "--from" in a and "--to" in a:
            r = move(_arg(a, "--artifact"), _arg(a, "--from"), _arg(a, "--to"),
                     reviewed_by=_arg(a, "--reviewed-by", "unspecified"),
                     decision_ref=_arg(a, "--decision-ref", ""),
                     root=root, dest=_arg(a, "--dest"), force=("--force" in a))
            print("moved %s -> %s (%s->%s)" % (r["from_path"], r["to_path"], r["from"], r["to"]))
            return 0
        if cmd == "export" and "--to" in a:
            files = [x for x in (_arg(a, "--files", "") or "").split(",") if x.strip()]
            manifest = _arg(a, "--manifest")
            if manifest and not files:
                files = _list_field(_read_fm(os.path.join(_root(root), manifest)).get("files"))
            if not files:
                print("export: нужны --files a,b,... или --manifest с полем files:")
                return 2
            r = export(files, _arg(a, "--to"), root=root)
            print("export -> %s: скопировано %d, отсутствует %d" %
                  (r["to"], len(r["copied"]), len(r["missing"])))
            for m in r["missing"]:
                print("  MISSING: %s" % m)
            return 0 if not r["missing"] else 1
    except Exception as exc:
        print("ОШИБКА: %s: %s" % (type(exc).__name__, exc))
        return 1
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main())
