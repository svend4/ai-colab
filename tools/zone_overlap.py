#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
# ==========================================
# [FILE ID CARD]
# ID: tools.zone_overlap
# TYPE: active-script
# DOMAIN: core
# DEPTH_LEVEL: 1
# SUMMARY: Zone-overlap advisory (M3, Codex §4.4) — пересечения зон активных пакетов котла (proposed, не enforced).
# ==========================================
"""
"""
zone_overlap.py — совещательный детектор пересечения зон пакетов котла (M3, Codex §4.4; proposed).

Пакет `kotel/packages/PKG-*.md` объявляет свои input/output зоны (`input_zones` /
`output_zones` / `zones`) — пути, которые рой пакета будет читать и писать. Когда два
пакета одновременно активны (status `in-swarm`/`agreed`), их ВЫХОДНЫЕ зоны не должны
пересекаться: два роя, пишущие в один каталог, гарантированно сталкиваются в общем дереве.
Этот детектор читает зоны активных пакетов и печатает советы ДО запуска роёв.

Три класса находок (по возрастанию серьёзности):

- WARN  — output-зоны двух активных пакетов пересекаются (glob-пересечение). Рои столкнутся;
          развести зоны или пустить один через свой worktree.
- FAIL   / HUMAN — зона пакета задевает deny-пути (`_deny_agents` из tools/permissions.json):
          критические пути (permissions.json, githooks, approvals) правит только человек
          (решение Stefan 2026-07-06, gate-10/C31). Пакету туда нельзя.
- ADVICE — зона задевает генерируемые индексы (TASKS.md/index.json/…): их регенерируют,
          прямая правка связывает агентов через индекс → совет «работать через worktree».

Логика глоб-пересечения переиспользует семантику `permissions.match` (тот же язык зон:
`**` = всё; `dir/**` = внутри dir/; `*.md` = любой .md; иначе точный путь). Классификатор
генерируемых путей берётся из `ownership.GENERATED` (единый источник, не форк).

Аудитория двойная: человек читает таблицы; агент берёт `--json`.

CLI:
    python tools/zone_overlap.py check              # проверить активные пакеты котла
    python tools/zone_overlap.py check --json       # машиночитаемый отчёт
    python tools/zone_overlap.py check --all        # НЕ фильтровать по статусу (все PKG)
    python tools/zone_overlap.py policy             # показать классы находок и язык зон

Exit-коды (advisory — сигнализируют, но НИГДЕ не enforced; pre-commit не трогает, канон не меняют):
    0 — чисто (нет WARN/FAIL);
    1 — есть WARN (пересечение output-зон) и/или FAIL (deny-путь): совет уйти в worktree/развести зоны;
    2 — ошибка вызова (нет команды, мусорный аргумент).
"""
import glob
import json
import os
import sys

from _ioutil import configure_output
from _cli import help_guard

# Переиспользуем язык зон permissions.match (тот же glob-словарь для агентов и пакетов).
import permissions as perm
# Единый классификатор генерируемых индексов (не форкаем список — читаем ownership).
import ownership as own

configure_output()

ROOT = os.environ.get("COLLAB_ROOT") or os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

SCHEMA = "zone-overlap.v1"

# Каталог пакетов котла (относительно ROOT).
PACKAGES_DIR = os.path.join("kotel", "packages")

# Статусы, при которых пакет считается АКТИВНЫМ (рой либо идёт, либо согласован к запуску).
# Нормализуем регистр и разделители (in-swarm == in_swarm).
ACTIVE_STATUSES = {"in-swarm", "agreed"}

# Поля front-matter, из которых собираем зоны пакета.
# output-зоны критичны для пересечений (куда пишут рои); input-зоны учитываем для deny/generated.
OUTPUT_ZONE_FIELDS = ("output_zones", "zones")
INPUT_ZONE_FIELDS = ("input_zones",)


def _norm_status(raw):
    """Нормализовать статус пакета: нижний регистр, '_'→'-', обрезка кавычек/пробелов."""
    return str(raw or "").strip().strip("'\"").lower().replace("_", "-")


def _norm_zone(raw):
    """Нормализовать путь зоны: обратные слэши → прямые, обрезка кавычек/пробелов."""
    return str(raw or "").strip().strip("'\"").replace("\\", "/")


def parse_zones_block(text):
    """Собрать зоны пакета из front-matter, включая YAML-блочные списки.

    `_canon.parse_fm` НЕ собирает блочные списки (перенос + `  - item`), а зоны в PKG
    пишутся именно так (`input_zones:` \\n `  - docs/`). Здесь построчный парсер front-matter:
    ключ с пустым значением открывает блок, последующие `  - item` пополняют его список;
    inline-форма (`zones: [a, b]`) тоже поддержана. Возвращает
    {"status": str, "id": str, "input": [..], "output": [..]}.
    """
    result = {"status": "", "id": "", "input": [], "output": []}
    if not text.startswith("---"):
        return result
    end = text.find("\n---", 3)
    if end == -1:
        return result
    body = text[3:end]

    cur_field = None  # имя открытого блочного поля (ждём его `- item` строки)
    cur_bucket = None  # список, куда складывать items открытого блока
    for raw_line in body.splitlines():
        line = raw_line.rstrip("\n")
        stripped = line.strip()
        if not stripped:
            continue
        # Пункт блочного списка: "  - item"
        if stripped.startswith("- ") or stripped == "-":
            if cur_bucket is not None:
                item = _norm_zone(stripped[1:].strip())
                if item:
                    cur_bucket.append(item)
            continue
        # Иначе это "ключ: значение" — блок закрывается.
        cur_field = None
        cur_bucket = None
        if ":" not in stripped:
            continue
        key, _, val = stripped.partition(":")
        key = key.strip()
        val = val.strip()
        bucket = None
        if key in OUTPUT_ZONE_FIELDS:
            bucket = result["output"]
        elif key in INPUT_ZONE_FIELDS:
            bucket = result["input"]
        elif key == "status":
            result["status"] = _norm_status(val)
            continue
        elif key == "id":
            result["id"] = str(val).strip().strip("'\"")
            continue
        else:
            continue
        # Зональное поле. Значение либо inline-список, либо пусто (откроется блок).
        if val:
            for item in _split_inline_list(val):
                z = _norm_zone(item)
                if z:
                    bucket.append(z)
        else:
            cur_field = key
            cur_bucket = bucket
    return result


def _split_inline_list(raw):
    """Inline-список front-matter `[a, b]` или `a, b` → список строк (пустые отсеяны)."""
    s = str(raw).strip()
    if s.startswith("[") and s.endswith("]"):
        s = s[1:-1]
    return [x.strip() for x in s.split(",") if x.strip()]


def zones_overlap(a, b):
    """Пересекаются ли две зоны (glob-язык permissions.match), симметрично.

    Зона может быть как конкретным путём (`docs/x.md`), так и глобом (`docs/**`).
    Считаем пересечение, если ЛЮБАЯ из зон покрывает другую как паттерн ИЛИ
    совпадает буквально. Так `docs/**` пересекается с `docs/a.md`, `**` — со всем,
    а `docs/` (dir-префикс) — с `docs/x.md` и обратно.
    """
    za, zb = _norm_zone(a), _norm_zone(b)
    if not za or not zb:
        return False
    if za == zb:
        return True
    # Каталог-префикс "docs/" ведём себя как "docs/**" для сравнения.
    pa = za if za.endswith("/**") else (za[:-1] + "/**" if za.endswith("/") else za)
    pb = zb if zb.endswith("/**") else (zb[:-1] + "/**" if zb.endswith("/") else zb)
    # a покрывает b (как паттерн покрывает путь) или наоборот; проверяем в обе стороны
    # на обоих представлениях (исходном пути и dir→glob), чтобы поймать dir-vs-file.
    return (perm.match(zb, pa) or perm.match(za, pb)
            or perm.match(zb, za) or perm.match(za, zb))


def _touches_generated(zone):
    """Задевает ли зона генерируемый индекс (ownership.GENERATED: TASKS.md/index.json/…).

    Прямая правка таких файлов роем связывает агентов через индекс → совет worktree.
    Каталог/glob-зона считается задевающей, если её паттерн покрывает индекс.
    """
    z = _norm_zone(zone)
    for gen in own.GENERATED:
        if z == gen or perm.match(gen, z) or z.endswith("/" + gen):
            return True
        # dir-зона "dir/" ~ "dir/**": индекс лежит в корне, поэтому покрывает только "**"/корневые
        if z.endswith("/") and perm.match(gen, z[:-1] + "/**"):
            return True
    return False


def _touches_deny(zone, deny_globs):
    """Задевает ли зона критический deny-путь (`_deny_agents`): туда только человек.

    Пересечение зоны с deny-глобом = пакету туда нельзя (permissions.json/githooks/approvals).
    Используем ту же симметричную glob-логику, что и для пересечения зон.
    """
    return sorted({g for g in deny_globs if zones_overlap(zone, g)})


def read_package_zones(path):
    """Прочитать зоны+статус пакета (только чтение). None при ошибке ввода-вывода."""
    try:
        with open(path, encoding="utf-8") as f:
            data = parse_zones_block(f.read())
    except OSError:
        return None
    data["file"] = os.path.relpath(path, ROOT).replace(os.sep, "/")
    if not data.get("id"):
        # id по имени файла, если во front-matter пусто
        data["id"] = os.path.splitext(os.path.basename(path))[0]
    return data


def list_packages():
    """Все kotel/packages/PKG-*.md под ROOT (отсортировано). Пусто, если каталога нет."""
    pdir = os.path.join(ROOT, PACKAGES_DIR)
    if not os.path.isdir(pdir):
        return []
    return sorted(glob.glob(os.path.join(pdir, "PKG-*.md")))


def _deny_globs():
    """Критические deny-пути из tools/permissions.json (`_deny_agents`); [] при отсутствии.

    Читаем permissions.json рядом С САМИМ zone_overlap.py (каталог tools/), а НЕ по
    COLLAB_ROOT: deny-список — свойство настоящего репо (permissions.json/githooks/
    approvals правит только человек, gate-10/C31), а не временного каталога пакетов.
    Так детектор видит реальные критические пути, даже когда пакеты берутся из fixture.
    """
    here_tools = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(here_tools, "permissions.json")
    if not os.path.exists(path):
        return []
    try:
        with open(path, encoding="utf-8") as f:
            policy = json.load(f)
    except (OSError, ValueError):
        return []
    return policy.get("_deny_agents") or []


def collect_active(paths, all_statuses=False):
    """Собрать зоны пакетов, отфильтровав по активному статусу (если не --all).

    Возвращает список dict пакетов (id, file, status, input[], output[]).
    all_statuses=True — не фильтровать (диагностика: посмотреть все PKG).
    """
    out = []
    for path in paths:
        data = read_package_zones(path)
        if data is None:
            continue
        if not all_statuses and data["status"] not in ACTIVE_STATUSES:
            continue
        out.append(data)
    return out


def analyze(packages, deny_globs=None):
    """Собрать находки по активным пакетам. Возвращает отчёт-dict.

    Находки:
      - overlaps[]  — пары пакетов с пересечением OUTPUT-зон (WARN);
      - deny[]      — (пакет, зона, deny-путь) для input+output, задевающих критические пути (FAIL);
      - generated[] — (пакет, зона) для зон, задевающих генерируемые индексы (ADVICE).
    """
    deny_globs = _deny_globs() if deny_globs is None else deny_globs

    overlaps = []
    # Пары пакетов: пересечение ВЫХОДНЫХ зон (куда пишут рои) — главный источник коллизий.
    for i in range(len(packages)):
        for j in range(i + 1, len(packages)):
            a, b = packages[i], packages[j]
            hits = []
            for za in a["output"]:
                for zb in b["output"]:
                    if zones_overlap(za, zb):
                        hits.append({"a_zone": za, "b_zone": zb})
            if hits:
                overlaps.append({
                    "a": a["id"], "b": b["id"],
                    "a_file": a["file"], "b_file": b["file"],
                    "pairs": hits,
                })

    deny_hits = []
    gen_hits = []
    for p in packages:
        # deny/generated проверяем и для input, и для output зон пакета.
        for kind in ("input", "output"):
            for zone in p[kind]:
                dn = _touches_deny(zone, deny_globs)
                if dn:
                    deny_hits.append({"pkg": p["id"], "file": p["file"],
                                      "zone_kind": kind, "zone": zone, "deny": dn})
                if _touches_generated(zone):
                    gen_hits.append({"pkg": p["id"], "file": p["file"],
                                     "zone_kind": kind, "zone": zone})

    report = {
        "schema": SCHEMA,
        "active_count": len(packages),
        "active": [{"id": p["id"], "file": p["file"], "status": p["status"],
                    "input": p["input"], "output": p["output"]} for p in packages],
        "overlaps": overlaps,
        "deny": deny_hits,
        "generated": gen_hits,
        "warn": len(overlaps),
        "fail": len(deny_hits),
        "advice": len(gen_hits),
    }
    return report


def _rc(report):
    """Advisory exit-код: 1 если есть WARN (overlap) или FAIL (deny); иначе 0.

    Совет «через worktree» (generated) НЕ поднимает код — это подсказка, не блок.
    """
    return 1 if (report["warn"] or report["fail"]) else 0


def _print_human(report):
    """Человекочитаемый вывод отчёта."""
    line = "=" * 64
    print(line)
    print("ZONE-OVERLAP — пересечения зон активных пакетов (M3, advisory)")
    print(line)
    print("Активных пакетов (in-swarm/agreed): %d" % report["active_count"])
    for p in report["active"]:
        print("  %-28s [%s] out=%s" % (
            p["id"], p["status"] or "—", ", ".join(p["output"]) or "(нет)"))

    print("\nFAIL — зона задевает deny-путь (только человек, gate-10/C31): %d" % report["fail"])
    for d in report["deny"] or []:
        print("  [FAIL/HUMAN] %s: %s-зона %r → deny %s" % (
            d["pkg"], d["zone_kind"], d["zone"], ", ".join(d["deny"])))
    if not report["deny"]:
        print("  (нет)")

    print("\nWARN — пересечение output-зон двух активных пакетов: %d" % report["warn"])
    for o in report["overlaps"] or []:
        pairs = "; ".join("%s∩%s" % (h["a_zone"], h["b_zone"]) for h in o["pairs"][:4])
        more = " …" if len(o["pairs"]) > 4 else ""
        print("  [WARN] %s ↔ %s: %s%s" % (o["a"], o["b"], pairs, more))
    if not report["overlaps"]:
        print("  (нет)")

    print("\nADVICE — зона задевает генерируемый индекс → через worktree: %d" % report["advice"])
    for g in report["generated"] or []:
        print("  [advice] %s: %s-зона %r задевает генерат → работать через worktree" % (
            g["pkg"], g["zone_kind"], g["zone"]))
    if not report["generated"]:
        print("  (нет)")

    print("\nВывод: %s" % (
        "есть WARN/FAIL — развести зоны или уйти в worktree "
        "(python tools/flow.py start <agent> <task> --worktree --run)"
        if _rc(report) else "чисто — зоны активных пакетов не сталкиваются."))
    print("(advisory: нигде не enforced; pre-commit не трогает; канон не меняется)")
    print(line)


def _print_policy():
    print("Классы находок zone_overlap (по возрастанию серьёзности):")
    print("  ADVICE — зона задевает генерируемый индекс (TASKS.md/index.json/…) → через worktree")
    print("  WARN   — output-зоны двух активных пакетов пересекаются → рои столкнутся")
    print("  FAIL   — зона задевает deny-путь (_deny_agents) → туда только человек (gate-10/C31)")
    print("\nЯзык зон (как в permissions.match):")
    print("  **      — всё")
    print("  dir/**  — всё внутри dir/ (эквивалент 'dir/')")
    print("  *.md    — любой .md")
    print("  иначе   — точный путь")
    print("\nАктивные статусы пакета: %s" % ", ".join(sorted(ACTIVE_STATUSES)))
    print("advisory: WARN/FAIL как exit-код, НИГДЕ не enforced.")


def check(paths=None, all_statuses=False, as_json=False):
    """Проверить активные пакеты котла на пересечение зон/deny/generated. (rc, report)."""
    paths = list_packages() if paths is None else paths
    packages = collect_active(paths, all_statuses=all_statuses)
    report = analyze(packages)
    if as_json:
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        _print_human(report)
    return _rc(report), report


def main(argv=None):
    help_guard(__doc__)
    argv = sys.argv[1:] if argv is None else list(argv)
    if not argv:
        print("usage: zone_overlap.py check [--all] [--json] | policy")
        return 2

    cmd = argv[0]
    rest = argv[1:]

    if cmd == "policy":
        _print_policy()
        return 0

    if cmd != "check":
        print("usage: zone_overlap.py check [--all] [--json] | policy")
        return 2

    as_json = "--json" in rest
    all_statuses = "--all" in rest
    rc, _ = check(all_statuses=all_statuses, as_json=as_json)
    return rc


if __name__ == "__main__":
    sys.exit(main())
