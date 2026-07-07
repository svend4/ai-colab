# ast: allow-subprocess
#!/usr/bin/env python3
# [FILE ID CARD]
# id: tools/validate_staged.py
# purpose: БЫСТРАЯ валидация ТОЛЬКО staged канон-файлов (для облегчённого pre-commit).
#          Полный validate.py (~2 мин на 290 задач) уходит в CI; локально — секунды.
# inputs: git diff --cached (staged tasks/questions/decisions/topics/*.md)
# outputs: ERROR-список по staged-файлам; exit 0 (ок) / 1 (ERROR) / 2 (git недоступен, fail-open)
# mode: read-only (git read + чтение файлов), ничего не пишет
# related: validate.py (полный, → CI), pre-commit-lightening-proposal-2026-07-07, D-036
"""validate_staged.py — быстрый локальный гейт: проверяет ТОЛЬКО staged канон-файлы.

Мотив: pre-commit гоняет полный tools/validate.py (~2 мин на всём каноне) на КАЖДОМ
коммите — под многоагентной нагрузкой это даёт коммиты по 5-10 мин и насыщает машину.
Оборона в глубину (docs/commit-safety-standard.md): локальный хук должен быть БЫСТРЫМ
(проверка только staged, секунды), а полный validate — в CI (.github/workflows).

Что проверяет по каждому staged tasks|questions|decisions|topics/*.md:
  1. есть YAML front-matter с `id:`; id == имя файла (без .md);
  2. `status:` из допустимого набора для типа; `type:` корректен;
  3. `depends_on`/`related` ссылки на T-/D-/Q- указывают на существующие файлы;
  4. нет дубля id среди staged.
Это НЕ заменяет полный validate (перекрёстные инварианты, счётчики, синтез) — тот в CI.
"""
from __future__ import annotations
import os
import re
import subprocess
import sys

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

CANON_DIRS = ("tasks", "questions", "decisions", "topics")
_PREFIX = {"tasks": "T", "questions": "Q", "decisions": "D", "topics": None}
# Допустимые статусы (мягко — суперсет; строгую проверку статус-переходов делает полный validate).
_STATUS_OK = {
    "task": {"todo", "open", "doing", "in_progress", "review", "blocked", "done", "closed", "cancelled"},
    "question": {"open", "answered", "closed", "superseded"},
    "decision": {"proposed", "accepted", "rejected", "superseded", "draft"},
    "doc": None, "topic": None,  # у тем/доков статус свободный
}
_ID_REF_RE = re.compile(r"\b([TDQ]-\d{3,})\b")


def _run(args):
    return subprocess.run(args, capture_output=True, text=True, encoding="utf-8", errors="replace")


def staged_canon_files():
    r = _run(["git", "diff", "--cached", "--name-only", "--diff-filter=ACM"])
    if r.returncode != 0:
        return None  # git недоступен
    out = []
    for line in r.stdout.splitlines():
        line = line.strip().replace("\\", "/")
        if line.endswith(".md") and line.split("/", 1)[0] in CANON_DIRS:
            out.append(line)
    return out


def parse_front_matter(text):
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    if end < 0:
        return {}
    fm = {}
    for line in text[3:end].splitlines():
        m = re.match(r"^([a-zA-Z_][\w-]*):\s*(.*)$", line)
        if m:
            fm[m.group(1)] = m.group(2).strip()
    return fm


def _exists(root, ref):
    d = {"T": "tasks", "Q": "questions", "D": "decisions"}[ref[0]]
    return os.path.exists(os.path.join(root, d, ref + ".md"))


def check(root=None):
    root = root or os.getcwd()
    files = staged_canon_files()
    if files is None:
        return 2, ["git недоступен — быстрая валидация пропущена (fail-open; полную сделает CI)"]
    errors = []
    seen_ids = {}
    for rel in files:
        path = os.path.join(root, rel)
        try:
            text = open(path, encoding="utf-8", errors="replace").read()
        except OSError:
            continue
        d0 = rel.split("/", 1)[0]
        base = os.path.basename(rel)[:-3]
        fm = parse_front_matter(text)
        if not fm:
            errors.append(f"{rel}: нет YAML front-matter")
            continue
        fid = fm.get("id", "")
        # (1) id == имя файла
        if fid != base:
            errors.append(f"{rel}: id '{fid}' != имя файла '{base}'")
        # префикс id по каталогу
        pref = _PREFIX[d0]
        if pref and fid and not fid.startswith(pref + "-"):
            errors.append(f"{rel}: id '{fid}' не по префиксу '{pref}-' каталога {d0}")
        # дубль id среди staged
        if fid:
            if fid in seen_ids:
                errors.append(f"{rel}: дубль id '{fid}' (также в {seen_ids[fid]})")
            seen_ids[fid] = rel
        # (2) статус
        typ = (fm.get("type") or {"tasks": "task", "questions": "question",
                                   "decisions": "decision", "topics": "topic"}[d0]).strip()
        allowed = _STATUS_OK.get(typ)
        st = (fm.get("status") or "").strip()
        if allowed is not None and st and st not in allowed:
            errors.append(f"{rel}: статус '{st}' вне допустимых для type={typ}")
        # (3) ссылки depends_on/related на существующие T/D/Q
        for field in ("depends_on", "related"):
            for ref in _ID_REF_RE.findall(fm.get(field, "")):
                if not _exists(root, ref):
                    errors.append(f"{rel}: {field} ссылается на несуществующий {ref}")
    return (1 if errors else 0), errors


def main(argv=None):
    rc, msgs = check(os.getcwd())
    if rc == 2:
        print("validate_staged: " + msgs[0])
        return 0  # fail-open: git недоступен — не блокируем, CI проверит
    if rc == 1:
        print("validate_staged: ERROR в staged канон-файлах (%d):" % len(msgs))
        for m in msgs:
            print("  - " + m)
        return 1
    n = len(staged_canon_files() or [])
    print("validate_staged: OK — %d staged канон-файлов проверены (полный validate — в CI)" % n)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
