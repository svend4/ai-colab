#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ==========================================
# [FILE ID CARD]
# ID: tools.agenda_gen
# TYPE: active-script
# DOMAIN: core.generation
# DEPTH_LEVEL: 1
# SUMMARY: Материализатор повестки котла (M2/T-276): GEN-блок kotel/agenda из front-matter пакетов kotel/packages/PKG-*.md.
# ==========================================
"""
Материализатор agenda (механизм M2, Codex §4.5 «agenda генерируемая, не ручная»).

Сканирует `kotel/packages/PKG-*.md`, читает front-matter каждого пакета и собирает
единый GEN-блок для повестки котла: секцию «Пакеты» (id | orchestrator | status |
risk | зоны | связь T/Q/D) и секцию «Демонстрации» (пакеты в статусе `demonstrated`
со ссылкой на отчёт, если он указан во front-matter). Источник правды — сами пакеты;
повестка перестаёт быть ручной таблицей (замечание Codex: «agenda генерируемая»).

Запуск из корня проекта:
    python tools/agenda_gen.py build    # записать GEN-блок между маркерами
    python tools/agenda_gen.py --check   # ничего не писать; exit 1, если блок устарел

Маркеры (по образцу generate.py; всё между ними генерируется):
    <!-- GEN:kotel-agenda START ... -->  ...  <!-- GEN:kotel-agenda END -->

Целевой файл — kotel/agenda-generated.md (см. ниже «Выбор целевого файла»). Ручные
секции вне маркеров не трогаются: replace_block переписывает только внутренность блока.

--- Выбор целевого файла (объяснение решения) ---
Текущий `kotel/agenda.md` создан пилотом как РУЧНОЙ файл (`generated: false`,
`mode: manual-pilot`) с содержательными ручными колонками (Lead, Next, развёрнутые
Q1..Q5). Вставлять GEN-маркеры прямо в него рискованно: генератор затёр бы ручную
таблицу пакетов пилота более бедной сгенерированной версией и стёр ручные заметки.
Поэтому по умолчанию пишем в ОТДЕЛЬНЫЙ `kotel/agenda-generated.md` (создаётся с нуля
с front-matter `generated: true` и парой маркеров), а ручной пилот остаётся нетронутым.
Миграция ручной agenda на генерируемую — вопрос интеграции (после решения котла по
package/agenda-слою, Q1 a/b); до тех пор оба файла сосуществуют, генерируемый —
кандидат на замену. Переопределить целевой файл можно флагом `--target <path>`
(относительно корня) — на случай, если котёл решит писать блок прямо в agenda.md,
предварительно добавив туда маркеры вручную.
"""
import os
import sys
import glob

from _ioutil import configure_output
from _cli import help_guard

configure_output()

# COLLAB_ROOT — тот же контракт изоляции, что у generate.py/drivers_catalog.py:
# тесты подменяют корень через env, инструмент вычисляет пути на import-time.
ROOT = os.environ.get("COLLAB_ROOT") or os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

from _canon import parse_front_matter  # единый плоский парсер front-matter (T-085)

MARKER = "kotel-agenda"
DEFAULT_TARGET = os.path.join("kotel", "agenda-generated.md")
PACKAGES_GLOB = os.path.join("kotel", "packages", "PKG-*.md")

# Front-matter пилотного пакета несёт блочные YAML-списки (related / input_zones /
# output_zones), а канонический parse_front_matter — плоский (key: value). Поэтому для
# списков используем локальный парсер блочных списков ниже. Скалярные поля (id,
# orchestrator, status, risk) остаются за parse_front_matter.


def parse_block_lists(text):
    """Достать блочные YAML-списки front-matter: {key: [item, ...]}.

    Канонический parse_front_matter плоский и списки не собирает (элементы `- x`
    попадают в fm пустыми ключами). Здесь читаем ровно front-matter (между первой
    и второй линиями `---`) и группируем строки вида `  - value` под предшествующим
    ключом `key:` без inline-значения. Инлайновые списки (`tasks: [T-273]`) тоже
    поддержаны: если у ключа есть значение `[a, b]`, раскрываем его.
    """
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    if end == -1:
        return {}
    lists = {}
    current = None
    for raw in text[3:end].splitlines():
        stripped = raw.strip()
        if not stripped:
            continue
        # Элемент блочного списка: строка начинается с "- " (после отступа).
        if stripped.startswith("- ") and current is not None:
            item = stripped[2:].strip()
            if item:
                lists[current].append(item)
            continue
        # Строка вида "key: value" или "key:".
        if ":" in stripped:
            key, val = stripped.split(":", 1)
            key = key.strip()
            val = val.strip()
            if val == "":
                # Ключ без inline-значения — возможное начало блочного списка.
                current = key
                lists.setdefault(key, [])
            elif val.startswith("[") and val.endswith("]"):
                # Инлайновый список: tasks: [T-273, T-276].
                inner = val[1:-1].strip()
                items = [p.strip() for p in inner.split(",") if p.strip()] if inner else []
                lists[key] = items
                current = None
            else:
                # Обычный скаляр — сбрасываем текущий список-контекст.
                current = None
    return lists


def collect_packages():
    """Собрать пакеты kotel/packages/PKG-*.md в детерминированный список записей.

    Поля записи:
      id, orchestrator, status, risk — скаляры из front-matter;
      zones — объединение input_zones/output_zones (для колонки «зоны»);
      links — объединение tasks + T/Q/D-подобных элементов из related (связь T/Q/D);
      report — ссылка на отчёт (report/report_link/reports во front-matter), если есть.
    Сортировка по id — детерминизм (нет таймстампов, повторный прогон без диффа).
    """
    items = []
    for path in sorted(glob.glob(os.path.join(ROOT, PACKAGES_GLOB))):
        name = os.path.basename(path)
        if name.startswith("_"):
            continue  # служебные шаблоны (_template и т.п.) пропускаем
        with open(path, encoding="utf-8") as f:
            text = f.read()
        fm = parse_front_matter(text)
        if fm.get("type") != "package" or not fm.get("id"):
            continue
        lists = parse_block_lists(text)

        input_zones = lists.get("input_zones", [])
        output_zones = lists.get("output_zones", [])
        zones_parts = []
        if input_zones:
            zones_parts.append("in: " + ", ".join(input_zones))
        if output_zones:
            zones_parts.append("out: " + ", ".join(output_zones))
        zones = "; ".join(zones_parts) if zones_parts else fm.get("input_zones", "—")

        # Связь T/Q/D: tasks + элементы related, похожие на T-/Q-/D-идентификаторы.
        tasks = lists.get("tasks", [])
        related = lists.get("related", [])
        links = list(tasks)
        for r in related:
            if _looks_like_tqd(r) and r not in links:
                links.append(r)
        links_str = ", ".join(links) if links else "—"

        report = _first(fm, ("report", "report_link", "reports"))

        items.append({
            "id": fm["id"],
            "orchestrator": fm.get("orchestrator", "—"),
            "status": fm.get("status", "draft"),
            "risk": fm.get("risk", "—"),
            "zones": zones,
            "links": links_str,
            "report": report,
        })
    items.sort(key=lambda p: p["id"])
    return items


def _looks_like_tqd(value):
    """T-273 / Q-5 / D-035 — канонический T/Q/D-идентификатор (не тема/файл)."""
    v = value.strip()
    return len(v) >= 3 and v[0] in ("T", "Q", "D") and v[1] == "-" and v[2:].split("-")[0].isalnum()


def _first(fm, keys):
    """Первое непустое значение по списку ключей (для гибкой ссылки на отчёт)."""
    for k in keys:
        val = fm.get(k)
        if val:
            return val.strip()
    return ""


def _esc(value):
    """Экранировать `|`, чтобы значение не сломало markdown-таблицу."""
    return str(value).replace("|", "\\|")


def render_packages_table(items):
    out = [
        "### Пакеты",
        "",
        "| Package | Orchestrator | Status | Risk | Зоны | Связь T/Q/D |",
        "|---|---|---|---|---|---|",
    ]
    for p in items:
        out.append("| `%s` | %s | %s | %s | %s | %s |" % (
            _esc(p["id"]), _esc(p["orchestrator"]), _esc(p["status"]),
            _esc(p["risk"]), _esc(p["zones"]), _esc(p["links"]),
        ))
    if not items:
        out.append("| _(пакетов нет)_ |  |  |  |  |  |")
    return "\n".join(out)


def render_demos_table(items):
    demos = [p for p in items if p["status"] == "demonstrated"]
    out = [
        "### Демонстрации",
        "",
        "| Package | Отчёт |",
        "|---|---|",
    ]
    for p in demos:
        report = ("`%s`" % _esc(p["report"])) if p["report"] else "—"
        out.append("| `%s` | %s |" % (_esc(p["id"]), report))
    if not demos:
        out.append("| _(демонстраций нет)_ |  |")
    return "\n".join(out)


def render_block(items):
    """Внутренность GEN-блока: секция «Пакеты» + секция «Демонстрации»."""
    return "\n\n".join([render_packages_table(items), render_demos_table(items)])


def replace_block(text, marker, new_inner):
    """Переписать внутренность GEN-блока между маркерами (по образцу generate.py).

    Ручные секции вне маркеров не затрагиваются: возвращаем префикс до конца
    START-маркера + новую внутренность + суффикс от END-маркера. None, если
    маркеры отсутствуют или END стоит раньше START.
    """
    start = "<!-- GEN:%s START" % marker
    end = "<!-- GEN:%s END -->" % marker
    s = text.find(start)
    e = text.find(end)
    if s == -1 or e == -1 or e < s:
        return None
    close = text.find("-->", s)
    if close == -1 or close > e:
        return None
    close += 3
    return text[:close] + "\n" + new_inner + "\n" + text[e:]


# Шаблон нового генерируемого файла (создаётся с нуля, если target отсутствует).
# Ручных секций внутри нет — файл целиком служебный, поэтому маркеры и заголовок.
NEW_FILE_TEMPLATE = (
    "---\n"
    "id: kotel-agenda-generated\n"
    "type: agenda\n"
    'title: "Kotel agenda — generated"\n'
    "status: proposed\n"
    "generated: true\n"
    "source: tools/agenda_gen.py\n"
    "related:\n"
    "  - T-276\n"
    "  - closed-loop-agent-cauldron-conveyor\n"
    "  - orchestrator-cycle-proposal-2026-07-06\n"
    "---\n"
    "\n"
    "# KOTEL AGENDA (generated)\n"
    "\n"
    "> Сгенерировано `tools/agenda_gen.py` из front-matter `kotel/packages/PKG-*.md`.\n"
    "> Не редактировать вручную между маркерами GEN. Ручной пилот — `kotel/agenda.md`\n"
    "> (миграция ручной повестки на генерируемую — вопрос интеграции после решения\n"
    "> котла по package/agenda-слою).\n"
    "\n"
    "<!-- GEN:kotel-agenda START (генерируется tools/agenda_gen.py; не редактировать вручную) -->\n"
    "<!-- GEN:kotel-agenda END -->\n"
)


def _resolve_target(argv):
    """Определить целевой файл: --target <path> (относит. корня) или дефолт."""
    if "--target" in argv:
        i = argv.index("--target")
        if i + 1 < len(argv):
            return os.path.join(ROOT, argv[i + 1])
    return os.path.join(ROOT, DEFAULT_TARGET)


def run(argv):
    check = "--check" in argv
    target = _resolve_target(argv)
    items = collect_packages()
    inner = render_block(items)

    # Файла-цели ещё нет.
    if not os.path.exists(target):
        if check:
            # Несвежесть: генерируемого файла нет, а пакеты есть → его надо создать.
            print("STALE: %s — файл повестки ещё не создан" % os.path.relpath(target, ROOT).replace(os.sep, "/"))
            print("Повестка устарела — запусти: python tools/agenda_gen.py build")
            return 1
        os.makedirs(os.path.dirname(target), exist_ok=True)
        new = replace_block(NEW_FILE_TEMPLATE, MARKER, inner)
        with open(target, "w", encoding="utf-8", newline="\n") as f:
            f.write(new)
        print("OK: создан %s (пакетов: %d)" % (
            os.path.relpath(target, ROOT).replace(os.sep, "/"), len(items)))
        return 0

    with open(target, encoding="utf-8") as f:
        text = f.read()
    new = replace_block(text, MARKER, inner)
    if new is None:
        print("ERROR: маркер %s не найден в %s" % (
            MARKER, os.path.relpath(target, ROOT).replace(os.sep, "/")))
        return 2

    rel = os.path.relpath(target, ROOT).replace(os.sep, "/")
    if new != text:
        if check:
            print("STALE: %s — повестка устарела" % rel)
            print("Повестка устарела — запусти: python tools/agenda_gen.py build")
            return 1
        with open(target, "w", encoding="utf-8", newline="\n") as f:
            f.write(new)
        print("OK: обновлён %s (пакетов: %d)" % (rel, len(items)))
        return 0

    print("OK: %s уже актуален (пакетов: %d)" % (rel, len(items)))
    return 0


def main(argv):
    help_guard(__doc__, argv)
    args = list(argv)
    pos = [a for a in args if not a.startswith("--")]
    # --target потребляет следующий позиционный аргумент — уберём его из pos.
    if "--target" in args:
        i = args.index("--target")
        if i + 1 < len(args):
            tgt = args[i + 1]
            pos = [a for a in pos if a != tgt]
    if "--check" in args:
        return run(args)
    if pos and pos[0] == "build":
        return run(args)
    if not pos:
        # Без команды — показать краткую справку (не писать по умолчанию).
        print("agenda_gen.py — материализатор повестки котла (M2).")
        print("  python tools/agenda_gen.py build     # записать GEN-блок")
        print("  python tools/agenda_gen.py --check    # проверить несвежесть (exit 1)")
        print("  --target <path>                        # иной целевой файл (относит. корня)")
        return 0
    print("нет команды %r; используйте: build | --check" % pos[0])
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
