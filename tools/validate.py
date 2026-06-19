#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Валидатор канона Markdown-инфраструктуры (T-006).

Проверяет инварианты между DECISIONS.md, QUESTIONS.md, TASKS.md, Доска.md,
STATUS.md и темами, чтобы заменить ручную «перепроверку».

Запуск из корня проекта:
    python tools/validate.py

Выход: 0 — нет ERROR; 1 — есть ERROR. WARN не валит.
"""
import os
import re
import sys


def configure_output():
    for stream_name in ("stdout", "stderr"):
        stream = getattr(sys, stream_name, None)
        if stream is None or not hasattr(stream, "reconfigure"):
            continue
        stream.reconfigure(encoding="utf-8", errors="replace")


configure_output()

ROOT = (
    os.environ.get("COLLAB_ROOT")
    or (sys.argv[1] if len(sys.argv) > 1 else None)
    or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)

ERRORS, WARNS, OKS = [], [], []


def err(m):
    ERRORS.append(m)


def warn(m):
    WARNS.append(m)


def ok(m):
    OKS.append(m)


def read(rel):
    path = os.path.join(ROOT, rel)
    if not os.path.exists(path):
        return None
    try:
        with open(path, encoding="utf-8") as f:
            return f.read()
    except UnicodeDecodeError as e:
        err(f"{rel}: не читается как UTF-8 (повреждён/обрезан?): {e}")
        return None


def strip_code_fences(text):
    """Убрать ```...``` блоки, чтобы примеры внутри не парсились как реальные записи."""
    return re.sub(r"```.*?```", "", text, flags=re.S)


def md_paths(cell):
    """Все `путь.md` (в backticks) из ячейки."""
    return re.findall(r"`([^`]+?\.md)`", cell)


def table_rows(text, id_prefix):
    """Строки markdown-таблицы, чья первая значащая ячейка начинается с id_prefix."""
    rows = []
    for line in text.splitlines():
        line = line.strip()
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if cells and cells[0].startswith(id_prefix):
            rows.append(cells)
    return rows


# ---------- DECISIONS ----------
def parse_decisions():
    text = read("DECISIONS.md")
    if text is None:
        err("DECISIONS.md отсутствует")
        return {}
    text = strip_code_fences(text)
    sections = re.findall(
        r"^##\s+(D-\d+)\b[^\n]*\n(.*?)(?=^##\s|\Z)", text, re.M | re.S
    )
    statuses = {}
    seen = set()
    valid = {"accepted", "proposed", "rejected", "superseded"}
    for did, body in sections:
        if did in seen:
            err(f"DECISIONS: дубликат {did}")
        seen.add(did)
        m = re.search(r"-\s*Статус:\s*([A-Za-zА-Яа-я]+)", body)
        st = m.group(1) if m else None
        statuses[did] = st
        if st is None:
            err(f"DECISIONS: у {did} нет поля «Статус»")
        elif st not in valid:
            warn(f"DECISIONS: у {did} нестандартный статус «{st}»")
    if statuses:
        ok(f"DECISIONS: {len(statuses)} решений, id уникальны")
    return statuses


# ---------- QUESTIONS ----------
def parse_questions(decisions):
    text = read("QUESTIONS.md")
    if text is None:
        err("QUESTIONS.md отсутствует")
        return
    rows = table_rows(text, "Q-")
    seen = set()
    valid = {"open", "answered", "closed"}
    for cells in rows:
        qid = cells[0]
        status = cells[2] if len(cells) > 2 else ""
        where = cells[5] if len(cells) > 5 else ""
        outcome = cells[6] if len(cells) > 6 else ""
        if qid in seen:
            err(f"QUESTIONS: дубликат {qid}")
        seen.add(qid)
        if status not in valid:
            warn(f"QUESTIONS: {qid} нестандартный статус «{status}»")
        # answered ⇒ итог осмысленный
        if status == "answered":
            if not outcome or "не решено" in outcome.lower():
                err(f"QUESTIONS: {qid} answered, но «Итог» пуст/не заполнен")
            for d in re.findall(r"D-\d+", outcome):
                if d not in decisions:
                    err(f"QUESTIONS: {qid} ссылается на несуществующее решение {d}")
        # ссылки на тему-файл существуют
        for p in md_paths(where):
            if not os.path.exists(os.path.join(ROOT, p)):
                err(f"QUESTIONS: {qid} «Где обсуждается» → нет файла {p}")
    if seen:
        ok(f"QUESTIONS: {len(seen)} вопросов, id уникальны, ссылки и итоги проверены")


# ---------- TASKS ----------
def parse_tasks():
    text = read("TASKS.md")
    if text is None:
        err("TASKS.md отсутствует")
        return
    rows = table_rows(text, "T-")
    seen = set()
    valid = {"todo", "doing", "blocked", "review", "done"}
    for cells in rows:
        tid = cells[0]
        status = cells[2] if len(cells) > 2 else ""
        topic = cells[4] if len(cells) > 4 else ""
        if tid in seen:
            err(f"TASKS: дубликат {tid}")
        seen.add(tid)
        if status not in valid:
            warn(f"TASKS: {tid} нестандартный статус «{status}»")
        for p in md_paths(topic):
            if not os.path.exists(os.path.join(ROOT, p)):
                err(f"TASKS: {tid} «Тема» → нет файла {p}")
    if seen:
        ok(f"TASKS: {len(seen)} задач, id уникальны, ссылки проверены")


# ---------- навигация: Доска / STATUS активные темы ----------
def check_nav():
    for fname in ("Доска.md", "STATUS.md"):
        text = read(fname)
        if text is None:
            err(f"{fname} отсутствует")
            continue
        missing = 0
        for line in text.splitlines():
            if not line.strip().startswith("|"):
                continue
            for p in md_paths(line):
                if p.startswith("темы/") and not os.path.exists(os.path.join(ROOT, p)):
                    err(f"{fname}: ссылка на отсутствующую тему {p}")
                    missing += 1
        if missing == 0:
            ok(f"{fname}: ссылки на темы валидны")


# ---------- имена файлов (D-005/D-007) ----------
def check_naming():
    cyr = []
    for dirpath, _dirs, files in os.walk(ROOT):
        if ".git" in dirpath:
            continue
        for fn in files:
            if fn.endswith(".md") and not all(ord(c) < 128 for c in fn):
                rel = os.path.relpath(os.path.join(dirpath, fn), ROOT)
                cyr.append(rel)
    if cyr:
        warn(
            "Имена с кириллицей (по D-007 мигрируют лениво, не ошибка): "
            + ", ".join(sorted(cyr))
        )
    else:
        ok("Все имена файлов ASCII (D-005)")


def main():
    decisions = parse_decisions()
    parse_questions(decisions)
    parse_tasks()
    check_nav()
    check_naming()

    for m in OKS:
        print("OK:   " + m)
    for m in WARNS:
        print("WARN: " + m)
    for m in ERRORS:
        print("ERROR:" + " " + m)
    print("-" * 50)
    print(f"OK={len(OKS)} WARN={len(WARNS)} ERROR={len(ERRORS)}")
    sys.exit(1 if ERRORS else 0)


if __name__ == "__main__":
    main()
