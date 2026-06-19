#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Генератор навигации (T-007).

Собирает таблицы тем в `STATUS.md` («Активные темы») и `Доска.md` («Темы»)
из YAML-front-matter каждого файла `темы/*.md`. Один источник правды на тему —
нет ручной синхронизации двух таблиц, значит нет класса дрейфа между ними.

Запуск из корня проекта:
    python tools/generate.py          # переписать таблицы между маркерами
    python tools/generate.py --check  # ничего не писать; exit 1, если навигация устарела

Маркеры в файлах (между ними всё генерируется):
    <!-- GEN:topics-status START ... -->   ... <!-- GEN:topics-status END -->
    <!-- GEN:topics-board  START ... -->   ... <!-- GEN:topics-board  END -->

Front-matter темы (наш простой парсер: key: value, value — всё после первого двоеточия):
    ---
    id: organization
    title: Организация папки и обоснование правок
    status: open
    wait: все
    next: краткий следующий шаг
    ---
"""
import os
import sys
import glob

ROOT = os.environ.get("COLLAB_ROOT") or os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

STATUS_RANK = {"needs-decision": 0, "waiting": 1, "open": 2, "done": 3, "archive": 4}


def parse_front_matter(text):
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    if end == -1:
        return {}
    fm = {}
    for line in text[3:end].strip().splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            fm[k.strip()] = v.strip()
    return fm


def collect_topics():
    topics = []
    for path in glob.glob(os.path.join(ROOT, "темы", "*.md")):
        with open(path, encoding="utf-8") as f:
            fm = parse_front_matter(f.read())
        if not fm.get("title"):
            continue  # тема без front-matter в навигацию не попадает
        rel = os.path.relpath(path, ROOT).replace(os.sep, "/")
        topics.append(
            {
                "id": fm.get("id", rel),
                "title": fm["title"],
                "file": rel,
                "status": fm.get("status", "open"),
                "wait": fm.get("wait", "—"),
                "next": fm.get("next", ""),
            }
        )
    topics.sort(key=lambda t: (STATUS_RANK.get(t["status"], 9), t["id"]))
    return topics


def render_status_table(topics):
    out = ["| Тема | Где | Статус | Следующее действие |", "|---|---|---|---|"]
    for t in topics:
        out.append(f"| {t['title']} | `{t['file']}` | {t['status']} | {t['next']} |")
    return "\n".join(out)


def render_board_table(topics):
    out = [
        "| Тема | Файл или папка | Статус | Ждем ответ от | Следующий шаг |",
        "|---|---|---|---|---|",
    ]
    for t in topics:
        out.append(
            f"| {t['title']} | `{t['file']}` | {t['status']} | {t['wait']} | {t['next']} |"
        )
    return "\n".join(out)


def replace_block(text, marker, new_inner):
    start = "<!-- GEN:%s START" % marker
    end = "<!-- GEN:%s END -->" % marker
    s = text.find(start)
    e = text.find(end)
    if s == -1 or e == -1:
        return None
    close = text.find("-->", s)
    if close == -1 or close > e:
        return None
    close += 3
    return text[:close] + "\n" + new_inner + "\n" + text[e:]


def main():
    check = "--check" in sys.argv
    topics = collect_topics()
    targets = [
        ("STATUS.md", "topics-status", render_status_table(topics)),
        ("Доска.md", "topics-board", render_board_table(topics)),
    ]
    changed_any = False
    error = False
    for fname, marker, table in targets:
        path = os.path.join(ROOT, fname)
        if not os.path.exists(path):
            print("ERROR: нет файла %s" % fname)
            error = True
            continue
        with open(path, encoding="utf-8") as f:
            text = f.read()
        new = replace_block(text, marker, table)
        if new is None:
            print("ERROR: маркер %s не найден в %s" % (marker, fname))
            error = True
            continue
        if new != text:
            changed_any = True
            if check:
                print("STALE: %s — навигация устарела" % fname)
            else:
                with open(path, "w", encoding="utf-8") as f:
                    f.write(new)
                print("OK: обновлён %s" % fname)
        else:
            print("OK: %s уже актуален" % fname)

    if error:
        sys.exit(1)
    if check and changed_any:
        print("Навигация устарела — запусти: python tools/generate.py")
        sys.exit(1)
    print("Тем в навигации: %d" % len(topics))
    sys.exit(0)


if __name__ == "__main__":
    main()
