#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ==========================================
# [FILE ID CARD]
# ID: tools.generate
# TYPE: active-script
# DOMAIN: core.generation
# DEPTH_LEVEL: 1
# SUMMARY: Генерирует STATUS.md, board.md, TASKS.md, QUESTIONS.md, DECISIONS.md и index.json из источников.
# ==========================================
"""
Генератор навигации (T-007).

Собирает таблицы тем в `STATUS.md` («Активные темы») и `board.md` («Темы»)
из YAML-front-matter каждого файла `topics/*.md`. Один источник правды на тему —
нет ручной синхронизации двух таблиц, значит нет класса дрейфа между ними.

Запуск из корня проекта:
    python tools/generate.py          # переписать таблицы между маркерами
    python tools/generate.py --check  # ничего не писать; exit 1, если навигация устарела

Маркеры в файлах (между ними всё генерируется):
    <!-- GEN:topics-status START ... -->   ... <!-- GEN:topics-status END -->
    <!-- GEN:topics-board  START ... -->   ... <!-- GEN:topics-board  END -->
    <!-- GEN:counters      START ... -->   ... <!-- GEN:counters      END -->
      (счётчики канона в STATUS.md, аудит C17-b; маркер опциональный —
       корни без него не ломаются, блок аддитивный)
    <!-- GEN:tools-index   START ... -->   ... <!-- GEN:tools-index   END -->
      (полный индекс не-тестовых tools/*.py в tools/README.md, T-268 / аудит C3-a;
       маркер опциональный — песочницы без tools/README.md не ломаются)

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
from _ioutil import configure_output
from _cli import help_guard
import glob
import json


configure_output()

ROOT = os.environ.get("COLLAB_ROOT") or os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

STATUS_RANK = {"needs-decision": 0, "waiting": 1, "open": 2, "done": 3, "archive": 4}

# Маркеры, отсутствие которых в файле — не ошибка (аддитивные блоки, аудит C17-b):
# старые песочницы/фикстуры без маркера продолжают работать, генератор лишь предупреждает.
# tools-index (T-268): опционален по той же причине — тестовые COLLAB_ROOT-корни без
# tools/README.md не должны ломаться; в реальном репо маркер есть и --check ловит несвежесть.
OPTIONAL_MARKERS = {"counters", "tools-index"}


from _canon import parse_front_matter  # единый парсер front-matter (T-085, находка L)


def title_from_heading(text):
    """Фоллбэк-заголовок темы: первый `# ...` вне код-фенсов (аудит C18).

    Раньше тема без front-matter title молча выпадала из index.json/STATUS/board,
    хотя folder_index её видел — 12 тем были невидимы в навигации.
    """
    in_fence = False
    for line in text.splitlines():
        s = line.strip()
        if s.startswith("```"):
            in_fence = not in_fence
            continue
        if not in_fence and s.startswith("# "):
            return s[2:].strip()
    return ""


def collect_topics():
    topics = []
    for path in glob.glob(os.path.join(ROOT, "topics", "*.md")):
        with open(path, encoding="utf-8") as f:
            text = f.read()
        fm = parse_front_matter(text)
        title = fm.get("title") or title_from_heading(text)
        if not title:
            continue  # тема без title (ни front-matter, ни '#'-заголовка) в навигацию не попадает
        rel = os.path.relpath(path, ROOT).replace(os.sep, "/")
        topics.append(
            {
                "id": fm.get("id", rel),
                "title": title,
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


def collect_tasks():
    tasks = []
    for path in glob.glob(os.path.join(ROOT, "tasks", "*.md")):
        with open(path, encoding="utf-8") as f:
            fm = parse_front_matter(f.read())
        if not fm.get("id") or not fm.get("title"):
            continue  # задача без id/title в индекс не попадает
        tasks.append(
            {
                "id": fm["id"],
                "title": fm["title"],
                "status": fm.get("status", "todo"),
                "owner": fm.get("owner", "—"),
                "priority": fm.get("priority", ""),
                "risk": fm.get("risk", ""),
                "depends_on": fm.get("depends_on", ""),
                "topic": fm.get("topic", ""),
                "next": fm.get("next", ""),
            }
        )
    tasks.sort(key=lambda t: t["id"])
    return tasks


def render_tasks_table(tasks):
    out = [
        "| ID | Задача | Статус | Ответственный | Тема | Следующий шаг |",
        "|---|---|---|---|---|---|",
    ]
    for t in tasks:
        topic = "`%s`" % t["topic"] if t["topic"] else "—"
        out.append(
            "| %s | %s | %s | %s | %s | %s |"
            % (t["id"], t["title"], t["status"], t["owner"], topic, t["next"])
        )
    return "\n".join(out)


def collect_questions():
    items = []
    for path in glob.glob(os.path.join(ROOT, "questions", "*.md")):
        with open(path, encoding="utf-8") as f:
            fm = parse_front_matter(f.read())
        if not fm.get("id") or not fm.get("title"):
            continue
        items.append(
            {
                "id": fm["id"],
                "title": fm["title"],
                "status": fm.get("status", "open"),
                "asked_by": fm.get("asked_by", "—"),
                "addressed_to": fm.get("addressed_to", "все"),
                "where": fm.get("where", ""),
                "outcome": fm.get("outcome", ""),
            }
        )
    items.sort(key=lambda q: q["id"])
    return items


def render_questions_table(items):
    out = [
        "| ID | Вопрос | Статус | Кто задал | Кому адресован | Где обсуждается | Итог |",
        "|---|---|---|---|---|---|---|",
    ]
    for q in items:
        where = "`%s`" % q["where"] if q["where"] else "—"
        out.append(
            "| %s | %s | %s | %s | %s | %s | %s |"
            % (q["id"], q["title"], q["status"], q["asked_by"], q["addressed_to"], where, q["outcome"])
        )
    return "\n".join(out)


def collect_decisions():
    items = []
    for path in glob.glob(os.path.join(ROOT, "decisions", "*.md")):
        with open(path, encoding="utf-8") as f:
            fm = parse_front_matter(f.read())
        if not fm.get("id") or not fm.get("title"):
            continue
        rel = os.path.relpath(path, ROOT).replace(os.sep, "/")
        items.append(
            {
                "id": fm["id"],
                "title": fm["title"],
                "status": fm.get("status", "proposed"),
                "date": fm.get("date", ""),
                "file": rel,
            }
        )
    items.sort(key=lambda d: d["id"])
    return items


def collect_drivers():
    items = []
    for path in glob.glob(os.path.join(ROOT, "drivers", "*.md")):
        name = os.path.basename(path)
        if name.startswith("_"):
            continue
        with open(path, encoding="utf-8") as f:
            fm = parse_front_matter(f.read())
        if fm.get("type") != "driver" or not fm.get("id") or not fm.get("title"):
            continue
        rel = os.path.relpath(path, ROOT).replace(os.sep, "/")
        items.append(
            {
                "id": fm["id"],
                "title": fm["title"],
                "file": rel,
                "status": fm.get("status", "draft"),
                "level": fm.get("level", ""),
                "mode": fm.get("mode", ""),
                "owner": fm.get("owner", "—"),
                "risk": fm.get("risk", ""),
                "activation": fm.get("activation", ""),
                "interfaces": fm.get("interfaces", ""),
                "inputs": fm.get("inputs", ""),
                "outputs": fm.get("outputs", ""),
                "sandbox": fm.get("sandbox", ""),
                "secrets": fm.get("secrets", ""),
                "related": fm.get("related", ""),
            }
        )
    items.sort(key=lambda d: d["id"])
    return items


def render_counters(tasks, decisions, questions, topics, drivers):
    """Счётчики канона для GEN-блока STATUS.md (аудит C17-b).

    Числа считаются из тех же источников (front-matter файлов), что и index.json,
    поэтому не могут устареть отдельно от канона. Пока счётчики были ручными,
    они отстали на 59 задач / 8 решений / 40 тем (аудит 2026-07-02, находка C17).
    Строка детерминирована — повторный прогон без изменений канона не даёт диффа.
    """
    return (
        "Задач: %d · решений: %d · вопросов: %d · тем в навигации: %d · драйверов: %d "
        "(источник — front-matter канона, как в `index.json`; "
        "обновляется `python tools/generate.py`)."
        % (len(tasks), len(decisions), len(questions), len(topics), len(drivers))
    )


# Плейсхолдер батч-генератора визиток (bulk_dcard_generator): такое SUMMARY неинформативно,
# в индексе инструментов вместо него берём первую строку докстринга (T-268 / C3-a).
DCARD_PLACEHOLDER = "Описание сгенерировано автоматически"


def _tools_doc_line(text):
    """Первая содержательная строка описания модуля (фоллбэк для GEN:tools-index).

    Нюансы репо (все три паттерна встречаются в tools/):
    - у части инструментов D-Card лежит ВНУТРИ докстринга (первый string-литерал —
      визитка от bulk_dcard_generator), а человеческое описание — во ВТОРОМ
      string-литерале модуля; `ast.get_docstring` видит только первый;
    - у части описание живёт в ведущем присваивании `HELP = \"\"\"...\"\"\"`
      (conveyor/dispatch/dir_health и др.), а не в докстринге.

    Поэтому идём по ВЕДУЩИМ узлам тела модуля, пока это string-литералы или
    присваивания string-констант, и берём первую строку, не являющуюся строкой
    D-Card-блока (не начинается с '#').
    """
    import ast
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return ""

    def _str_value(node):
        if isinstance(node, ast.Expr):
            node = node.value
        elif isinstance(node, ast.Assign):
            node = node.value
        else:
            return None
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            return node.value
        return None

    for node in tree.body:
        value = _str_value(node)
        if value is None:
            break  # ведущие докстринги/HELP-константы кончились — дальше код
        for line in value.splitlines():
            line = line.strip()
            if line and not line.startswith("#"):
                return line[:160]
    return ""


def collect_tools_index():
    """Полный индекс не-тестовых tools/*.py для GEN:tools-index (T-268, аудит C3-a).

    Правило «не-тестовый» — то же, что в cli_inventory.iter_python_files: *.py верхнего
    уровня tools/, кроме test_*.py (каталог tools/tests/ не сканируется). Описание:
    D-Card SUMMARY ([FILE ID CARD], канонический парсер dcard_indexer — без локальной
    копии логики); если SUMMARY нет или это плейсхолдер батч-генератора — первая
    содержательная строка докстринга (_tools_doc_line). Детерминировано: сортировка
    по имени файла, контент — только из самих файлов.
    """
    import dcard_indexer   # extract_py_dcard — канонический парсер [FILE ID CARD]
    tools_dir = os.path.join(ROOT, "tools")
    items = []
    if not os.path.isdir(tools_dir):
        return items  # песочница без tools/ — блок пуст (маркер и так опциональный)
    for name in sorted(os.listdir(tools_dir)):
        path = os.path.join(tools_dir, name)
        if not name.endswith(".py") or name.startswith("test_") or not os.path.isfile(path):
            continue
        card = dcard_indexer.extract_py_dcard(path) or {}
        summary = (card.get("summary") or "").strip()
        if not summary or DCARD_PLACEHOLDER in summary:
            try:
                with open(path, encoding="utf-8", errors="replace") as f:
                    text = f.read()
            except OSError:
                text = ""
            summary = _tools_doc_line(text) or summary or "—"
        # `|` внутри описания сломал бы markdown-таблицу — экранируем
        items.append({"name": name, "summary": summary.replace("|", "\\|")})
    return items


def render_tools_index(items):
    """Markdown-блок GEN:tools-index: счётчик + таблица «имя | однострочное назначение»."""
    out = [
        "Всего не-тестовых инструментов: %d. Источник описаний: D-Card SUMMARY "
        "([FILE ID CARD]) или первая строка докстринга модуля; обновляется "
        "`python tools/generate.py`, несвежесть ловит `--check` (hook/CI)." % len(items),
        "",
        "| Инструмент | Назначение |",
        "|---|---|",
    ]
    for it in items:
        out.append("| `%s` | %s |" % (it["name"], it["summary"]))
    return "\n".join(out)


def render_decisions_index(items):
    out = ["| ID | Решение | Статус | Дата | Файл |", "|---|---|---|---|---|"]
    for d in items:
        out.append(
            "| %s | %s | %s | %s | `%s` |"
            % (d["id"], d["title"], d["status"], d["date"], d["file"])
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


def build_index():
    # Машинный индекс всего канона из front-matter (детерминированный, без таймстампов).
    topics = [
        {"id": t["id"], "title": t["title"], "file": t["file"],
         "status": t["status"], "next": t["next"]}
        for t in collect_topics()
    ]
    tasks = [
        {"id": t["id"], "title": t["title"], "status": t["status"],
         "owner": t["owner"], "priority": t.get("priority", ""),
         "risk": t.get("risk", ""), "depends_on": t.get("depends_on", ""),
         "topic": t["topic"], "next": t["next"]}
        for t in collect_tasks()
    ]
    questions = [
        {"id": q["id"], "title": q["title"], "status": q["status"],
         "where": q["where"], "outcome": q["outcome"]}
        for q in collect_questions()
    ]
    decisions = [
        {"id": d["id"], "title": d["title"], "status": d["status"],
         "date": d["date"], "file": d["file"]}
        for d in collect_decisions()
    ]
    drivers = [
        {"id": d["id"], "title": d["title"], "file": d["file"],
         "status": d["status"], "level": d["level"], "mode": d["mode"],
         "owner": d["owner"], "risk": d["risk"], "activation": d["activation"],
         "interfaces": d["interfaces"], "inputs": d["inputs"],
         "outputs": d["outputs"], "sandbox": d["sandbox"],
         "secrets": d["secrets"], "related": d["related"]}
        for d in collect_drivers()
    ]
    return {"topics": topics, "tasks": tasks,
            "questions": questions, "decisions": decisions,
            "drivers": drivers}


def main():
    help_guard(__doc__)
    check = "--check" in sys.argv
    topics = collect_topics()
    tasks = collect_tasks()
    questions = collect_questions()
    decisions = collect_decisions()
    drivers = collect_drivers()
    targets = [
        # counters — до topics-status: оба блока в STATUS.md, файл перечитывается
        # на каждой итерации, поэтому порядок безопасен; маркер counters опциональный.
        ("STATUS.md", "counters",
         render_counters(tasks, decisions, questions, topics, drivers)),
        ("STATUS.md", "topics-status", render_status_table(topics)),
        ("board.md", "topics-board", render_board_table(topics)),
        ("TASKS.md", "tasks", render_tasks_table(tasks)),
        ("QUESTIONS.md", "questions", render_questions_table(questions)),
        ("DECISIONS.md", "decisions", render_decisions_index(decisions)),
        # T-268 (C3-a): полный автоиндекс инструментов; маркер опциональный (см. OPTIONAL_MARKERS)
        ("tools/README.md", "tools-index", render_tools_index(collect_tools_index())),
    ]
    changed_any = False
    error = False
    for fname, marker, table in targets:
        path = os.path.join(ROOT, fname)
        if not os.path.exists(path):
            if marker in OPTIONAL_MARKERS:
                # Аддитивная поверхность (tools/README.md в песочницах-фикстурах может
                # отсутствовать): нет файла — нет блока, это не ошибка корня.
                print("WARN: нет файла %s — блок %s пропущен" % (fname, marker))
                continue
            print("ERROR: нет файла %s" % fname)
            error = True
            continue
        with open(path, encoding="utf-8") as f:
            text = f.read()
        new = replace_block(text, marker, table)
        if new is None:
            if marker in OPTIONAL_MARKERS:
                # Аддитивный блок: корень без маркера (старая песочница/фикстура)
                # не ломается — только предупреждение, без ERROR/STALE.
                print("WARN: маркер %s не найден в %s — блок пропущен" % (marker, fname))
                continue
            print("ERROR: маркер %s не найден в %s" % (marker, fname))
            error = True
            continue
        if new != text:
            changed_any = True
            if check:
                print("STALE: %s — навигация устарела" % fname)
            else:
                with open(path, "w", encoding="utf-8", newline="\n") as f:
                    f.write(new)
                print("OK: обновлён %s" % fname)
        else:
            print("OK: %s уже актуален" % fname)

    # index.json — машинный индекс (целый файл, без маркеров)
    index_text = json.dumps(build_index(), ensure_ascii=False, indent=2) + "\n"
    ipath = os.path.join(ROOT, "index.json")
    old_index = ""
    if os.path.exists(ipath):
        with open(ipath, encoding="utf-8") as f:
            old_index = f.read()
    if index_text != old_index:
        changed_any = True
        if check:
            print("STALE: index.json")
        else:
            with open(ipath, "w", encoding="utf-8", newline="\n") as f:
                f.write(index_text)
            print("OK: обновлён index.json")
    else:
        print("OK: index.json актуален")

    # folder-индексы (навигация по крупным папкам) — освежаем вместе с агрегатами: системный фикс
    # рецидива «folder_index STALE» из петли саморефлексии (logs/reflection). Best-effort, не валит generate.
    if not check:
        try:
            import folder_index
            for d in folder_index.BIG:
                folder_index.write(d)
        except Exception as e:
            print("WARN: folder-индексы не обновлены (%s)" % e)

    if error:
        sys.exit(1)
    if check and changed_any:
        print("Навигация устарела — запусти: python tools/generate.py")
        sys.exit(1)
    print("Тем в навигации: %d" % len(topics))
    sys.exit(0)


if __name__ == "__main__":
    main()
