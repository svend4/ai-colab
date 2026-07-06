# ast: allow-subprocess
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ==========================================
# [FILE ID CARD]
# ID: tools.gap_scan
# TYPE: active-script
# DOMAIN: core
# DEPTH_LEVEL: 1
# SUMMARY: Детектор разрывов «замысел ↔ реальность»: orphan-код, тихий дрейф деривата, висячие ссылки.
# ==========================================
"""gap_scan.py — исполняемая «формула» поиска разрывов замысел↔реальность.

Операционализирует topics/defect-class-formula-2026-06-26 (симптом (f) тихий дрейф деривата,
+ открытая проблема #1 «единый CANON_DIRS») и обобщает архетип commit_queue («механизм построен,
но не подключён»). Это детектор для класса «построено/решено/описано, но НЕ активно».

Четыре механических детектора (что можно ловить без человека):

  orphans  — G1: tools/*.py, на который НИЧТО в активной поверхности не ссылается (ни import,
             ни `X.py` в docs/PROTOCOL/AGENTS/skills/хуках/top, ни tools/README). Только сам файл
             и его test_. Архетип: commit_queue.py. (allowlist = очевидные entrypoints/хелперы.)
  drift    — (f): мёртвые/переименованные строковые литералы каталогов в коде (напр. "темы" → "topics"),
             из-за которых дериват (счётчик/индекс/портал) МОЛЧА читает несуществующий путь и
             возвращает 0/пусто. «Немой ноль выглядит как валидный ответ».
  dangling — G5: ссылки на tools/<name>.py в docs/README/PROTOCOL/AGENTS/glossary, где файла нет
             (напр. queue.py → реально agent_queue.py). Строки с маркером [planned] пропускаются:
             это явно помеченный roadmap-план, а не документация несуществующей команды (C40).
  dcard    — P8-b (волна 2): не-тестовый tools/*.py без блока `[FILE ID CARD]` — метаданные-визитка
             обязательна для новых инструментов (enforcement регрессии 67→74; из pre-commit — WARN).

CLI:
  python tools/gap_scan.py                  # все детекторы, человекочитаемо
  python tools/gap_scan.py orphans          # только orphan-код
  python tools/gap_scan.py drift            # только дрейф деривата
  python tools/gap_scan.py dangling         # только висячие ссылки
  python tools/gap_scan.py dcard            # только tools/*.py без [FILE ID CARD]
  python tools/gap_scan.py --json           # машиночитаемо (чистый stdout)
  python tools/gap_scan.py --strict         # exit 1, если найдено хоть что-то (для CI/хука)
"""
import os
import sys
import re
import ast
import json
import glob

from _ioutil import configure_output
from _cli import help_guard

configure_output()
_SELF_TOOLS = os.path.dirname(os.path.abspath(__file__))
ROOT = os.environ.get("COLLAB_ROOT") or os.path.dirname(_SELF_TOOLS)
TOOLS = os.path.join(ROOT, "tools")

# Каталоги, которые переименованы и теперь МЁРТВЫ как строковый литерал (источник тихого дрейфа (f)).
DEAD_DIR_LITERALS = {
    "темы": "topics",  # D-005/D-007: миграция кириллических имён к ASCII; дир теперь topics/
}

# Маркер «инструмент только запланирован, файла ещё нет» в доках (аудит C40): строку с ним
# G5 не считает висячей ссылкой — план помечен явно, читатель не примет его за рабочую команду.
PLANNED_MARKER = "[planned]"

# Entrypoints/хелперы, которые легитимны без входящих ссылок (человеко-CLI, запускаются напрямую).
# Намеренно узкий список: всё остальное без ссылок — настоящий orphan-кандидат.
ORPHAN_ALLOWLIST = {
    "pipeline", "top", "validate", "generate", "conveyor", "onboard", "race_test",
    "demo_bridge", "sandbox_runner", "execute_audit", "execute_preflight", "execute_human_gate",
    "gap_scan", "mutmeta",  # сами детекторы формулы (запускаются вручную/из хука)
    # --- Волна 2, C15-b (решение Stefan по Q-W2-1: «подключить полезные, остальные — в allowlist»).
    # Осознанно «про запас»: не удаляются, не подключаются к активной поверхности, шуметь не должны.
    "cli_inventory",    # генератор автосписка CLI-инструментов; точка входа для C3-a (автоиндекс README)
    "fold",             # свёртка/агрегация текстов — экспериментальный примитив, ждёт потребителя
    "retrieval_bench",  # бенчмарк retrieval-слоя (canon_index BM25/FTS5) — запускается вручную при замерах
    "text_brain",       # экспериментальный текст-движок (исследовательский, вне активного пути)
    "text_scene",       # сценарная сборка текста поверх view.load_canon — исследовательский
    "thread_runner",    # локальный LLM-раннер (llama-server) — включается только при локальной модели
}


def _read(path):
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            return f.read()
    except OSError:
        return ""


def _tools_modules():
    """Имена модулей tools/*.py без test_* и без _хелперов (_cli, _ioutil, _canon)."""
    mods = []
    for p in sorted(glob.glob(os.path.join(TOOLS, "*.py"))):
        name = os.path.basename(p)[:-3]
        if name.startswith("test_") or name.startswith("_"):
            continue
        mods.append(name)
    return mods


def _active_surface():
    """Файлы «активной поверхности»: где легитимный инструмент должен быть упомянут/вызван."""
    files = []
    for rel in ("README.md", "PROTOCOL.md", "AGENTS.md", "STATUS.md"):
        p = os.path.join(ROOT, rel)
        if os.path.exists(p):
            files.append(p)
    for d in ("docs", "skills", ".agents"):
        files += glob.glob(os.path.join(ROOT, d, "**", "*.md"), recursive=True)
    files += glob.glob(os.path.join(TOOLS, "githooks", "*"))
    files.append(os.path.join(TOOLS, "README.md"))
    files += [p for p in glob.glob(os.path.join(TOOLS, "*.py"))]  # импорты/subprocess между тулами
    # тесты перенесены в tools/tests/ (C14): ссылка из ЧУЖОГО теста — по-прежнему часть поверхности
    files += [p for p in glob.glob(os.path.join(TOOLS, "tests", "*.py"))]
    return [f for f in files if os.path.isfile(f)]


def find_orphans():
    """tools/*.py, на который ничто не ссылается (кроме себя и своего test_)."""
    surface = _active_surface()
    out = []
    for mod in _tools_modules():
        if mod in ORPHAN_ALLOWLIST:
            continue
        own = os.path.join(TOOLS, mod + ".py")
        own_test = os.path.join(TOOLS, "tests", "test_" + mod + ".py")  # C14: тесты в tools/tests/
        token = re.compile(r"\b" + re.escape(mod) + r"\b")
        referenced = False
        for f in surface:
            if os.path.abspath(f) in (os.path.abspath(own), os.path.abspath(own_test)):
                continue
            if token.search(_read(f)):
                referenced = True
                break
        if not referenced:
            has_test = os.path.exists(own_test)
            out.append({
                "kind": "orphan-code", "name": "tools/%s.py" % mod,
                "evidence": "нет ссылок (import/CLI/доки/хуки/top) вне tools/%s.py%s" % (
                    mod, " и tools/tests/test_%s.py" % mod if has_test else ""),
                "has_test": has_test,
                "why": "механизм построен и протестирован, но не подключён к активному пути (как commit_queue)",
            })
    return out


def _docstring_const_ids(tree):
    """id() узлов-докстрингов (Module/Func/Class) — прозу про каталог не считаем дрейфом."""
    ids = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            body = getattr(node, "body", [])
            if (body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant)
                    and isinstance(body[0].value.value, str)):
                ids.add(id(body[0].value))
    return ids


def find_drift():
    """Мёртвые литералы каталогов в РЕАЛЬНОМ коде (AST string-const, не докстринг/коммент) →
    дериват молча читает несуществующий путь и возвращает 0/пусто (симптом f)."""
    out = []
    for p in sorted(glob.glob(os.path.join(TOOLS, "*.py"))):
        if os.path.basename(p) == "gap_scan.py":
            continue  # сам детектор держит литералы в карте — не считать
        txt = _read(p)
        try:
            tree = ast.parse(txt)
        except SyntaxError:
            continue
        lines = txt.splitlines()
        skip = _docstring_const_ids(tree)
        for node in ast.walk(tree):
            if (isinstance(node, ast.Constant) and isinstance(node.value, str)
                    and node.value in DEAD_DIR_LITERALS and id(node) not in skip):
                dead = node.value
                alive = DEAD_DIR_LITERALS[dead]
                ln = getattr(node, "lineno", 0)
                src = lines[ln - 1].strip()[:120] if 0 < ln <= len(lines) else ""
                out.append({
                    "kind": "derivation-drift", "name": "tools/%s:%d" % (os.path.basename(p), ln),
                    "evidence": "литерал каталога %r (мёртв; теперь %r): %s" % (dead, alive, src),
                    "why": "дериват читает несуществующий путь → молча 0/пусто; немой ноль выглядит валидным (f)",
                    "fix": "заменить %r на %r или импортировать общий реестр каталогов" % (dead, alive),
                })
    return out


def find_dangling():
    """Ссылки на tools/<name>.py в доках, где файла нет (висячая ссылка, G5).
    Строки с PLANNED_MARKER пропускаются: помеченный roadmap-план — не висячая ссылка (C40)."""
    out = []
    ref = re.compile(r"tools/([A-Za-z_][A-Za-z0-9_]*)\.py")
    seen = set()
    docs = [os.path.join(ROOT, x) for x in ("README.md", "PROTOCOL.md", "AGENTS.md")]
    docs += glob.glob(os.path.join(ROOT, "docs", "**", "*.md"), recursive=True)
    docs.append(os.path.join(TOOLS, "README.md"))
    for d in docs:
        if not os.path.isfile(d):
            continue
        for line in _read(d).splitlines():
            if PLANNED_MARKER in line:
                continue  # явный план [planned] — читатель предупреждён, не считаем разрывом
            for m in ref.finditer(line):
                name = m.group(1)
                if not os.path.exists(os.path.join(TOOLS, name + ".py")):
                    key = (os.path.relpath(d, ROOT).replace("\\", "/"), name)
                    if key in seen:
                        continue
                    seen.add(key)
                    out.append({
                        "kind": "dangling-ref", "name": "tools/%s.py" % name,
                        "evidence": "упомянут в %s, но файла нет" % key[0],
                        "why": "доки/инструкции учат несуществующей команде (G5)",
                    })
    return out


DCARD_MARKER = "[FILE ID CARD]"


def find_missing_dcards():
    """Не-тестовые tools/*.py без блока [FILE ID CARD] (P8-b, enforcement регрессии D-Card).

    Смотрим только «модули инструментов» (_tools_modules: без test_* и _хелперов) — батч
    по тестовым файлам отложен до их переноса (C14), чтобы не заливать WARN-шумом хук.
    Маркер ищем в голове файла (первые ~3000 байт), как dcard_indexer (первые 30 строк).
    """
    out = []
    for mod in _tools_modules():
        head = _read(os.path.join(TOOLS, mod + ".py"))[:3000]
        if DCARD_MARKER not in head:
            out.append({
                "kind": "missing-dcard", "name": "tools/%s.py" % mod,
                "evidence": "нет блока %s в голове файла" % DCARD_MARKER,
                "why": "инструмент без визитки-метаданных невидим для dcard_indexer/автоиндекса (P8)",
                "fix": "добавить блок [FILE ID CARD] (ID/TYPE/DOMAIN/DEPTH_LEVEL/SUMMARY) в голову файла",
            })
    return out


DETECTORS = {"orphans": find_orphans, "drift": find_drift, "dangling": find_dangling,
             "dcard": find_missing_dcards}


def run(which=None):
    res = {}
    for name, fn in DETECTORS.items():
        if which in (None, name):
            res[name] = fn()
    return res


def _print_human(res):
    total = 0
    titles = {"orphans": "G1 ORPHAN-КОД (построено, но не подключено)",
              "drift": "(f) ДРЕЙФ ДЕРИВАТА (мёртвый литерал каталога → молчаливый 0)",
              "dangling": "G5 ВИСЯЧИЕ ССЫЛКИ (доки → несуществующий tools/*.py)",
              "dcard": "P8 БЕЗ ВИЗИТКИ (tools/*.py без [FILE ID CARD])"}
    print("=== GAP SCAN — разрывы замысел↔реальность ===")
    for name, items in res.items():
        print("\n## %s — %d" % (titles.get(name, name), len(items)))
        for it in items:
            total += 1
            print("  • %s" % it["name"])
            print("      %s" % it["evidence"])
            if it.get("fix"):
                print("      fix: %s" % it["fix"])
    print("\nИТОГО разрывов: %d" % total)
    return total


def main(argv):
    help_guard(__doc__, argv)
    which = None
    for a in argv:
        if a in DETECTORS:
            which = a
    res = run(which)
    total = sum(len(v) for v in res.values())
    if "--json" in argv:
        print(json.dumps(res, ensure_ascii=False, indent=2))
    else:
        _print_human(res)
    if "--strict" in argv and total:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
