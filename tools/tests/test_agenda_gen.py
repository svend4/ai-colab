# ast: allow-subprocess
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
# ==========================================
# [FILE ID CARD]
# ID: tools.tests.test_agenda_gen
# TYPE: active-script
# DOMAIN: core.testing
# DEPTH_LEVEL: 1
# SUMMARY: Hermetic-тесты tools/agenda_gen.py (материализатор повестки котла M2): парсер пакетов + build/--check контракт.
# ==========================================
"""
"""
Hermetic-тесты материализатора повестки котла (tools/agenda_gen.py, механизм M2).

Покрывают два слоя (двухступенчатый канон, Q-W2-3):
  1. Чистые функции (parse_block_lists, collect_packages через COLLAB_ROOT,
     render_*_table) — детерминированно, на фикстуре-PKG во временном каталоге.
  2. Контракт CLI через subprocess на изолированном COLLAB_ROOT:
       - build с нуля создаёт kotel/agenda-generated.md с GEN-блоком (rc=0);
       - --check сразу после build → rc=0, нет STALE;
       - правка front-matter пакета → --check видит дрейф → rc=1 + STALE;
       - build идемпотентен (повторный прогон без диффа → «актуален»);
       - демонстрации: пакет со status=demonstrated и report попадает в секцию
         «Демонстрации» со ссылкой на отчёт;
       - ручной текст вне маркеров сохраняется (replace_block не трогает ручные секции).

agenda_gen.py вычисляет ROOT на import-time (COLLAB_ROOT), поэтому изоляция —
через subprocess с временной папкой (тот же приём, что в test_generate/test_drivers_catalog).
"""
# --- бутстрап путей (C14, аудит 2026-07-02): тест живёт в tools/tests/, инструменты — в tools/.
# Вставка ДО локальных импортов, чтобы standalone-запуск работал из нового места.
import os as _os
import sys as _sys
_TOOLS_DIR = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
if _TOOLS_DIR not in _sys.path:
    _sys.path.insert(0, _TOOLS_DIR)
# --- конец бутстрапа ---

import os
import sys
import tempfile
import shutil
import subprocess

from _ioutil import configure_output

HERE = _TOOLS_DIR  # tools/ — тест в tools/tests/ (C14)
sys.path.insert(0, HERE)
configure_output()

import agenda_gen as ag


# --- фикстуры-PKG ---------------------------------------------------------

# Пилотный пакет: draft, orchestrator=pool, блочные списки (input/output_zones, related),
# инлайновый список tasks. Проверяет сбор зон и связь T/Q/D.
PKG_DRAFT = """\
---
id: PKG-20260706-fixt-draft
type: package
title: "Fixture draft package"
status: draft
orchestrator: pool
risk: medium
tasks: [T-901]
related:
  - T-901
  - Q-5
  - D-035
  - closed-loop-agent-cauldron-conveyor
input_zones:
  - docs/
  - drivers/
output_zones:
  - reports/
  - tmp-work/
---

# body
"""

# Демонстрационный пакет: demonstrated + ссылка на отчёт → секция «Демонстрации».
PKG_DEMO = """\
---
id: PKG-20260706-fixt-demo
type: package
title: "Fixture demonstrated package"
status: demonstrated
orchestrator: claude
risk: low
report: reports/fixt-demo-2026-07-06.md
tasks: [T-902]
related:
  - T-902
input_zones:
  - fixtures/
output_zones:
  - reports/
---

# body
"""

# Не-пакет: type != package → должен быть пропущен collect_packages.
NOT_A_PACKAGE = """\
---
id: PKG-20260706-not-a-pkg
type: note
title: "Not a package"
status: draft
---

# body
"""


def make_canon(root):
    """Подготовить фикстуру: kotel/packages/ с тремя PKG-файлами.

    Имя make_canon распознаётся conftest-fixture `root` (C12-a): pytest вызовет её
    и передаст строковый путь в тесты, ждущие аргумент `root`.
    """
    pkg_dir = os.path.join(root, "kotel", "packages")
    os.makedirs(pkg_dir, exist_ok=True)
    _write(os.path.join(pkg_dir, "PKG-20260706-fixt-draft.md"), PKG_DRAFT)
    _write(os.path.join(pkg_dir, "PKG-20260706-fixt-demo.md"), PKG_DEMO)
    _write(os.path.join(pkg_dir, "PKG-20260706-not-a-pkg.md"), NOT_A_PACKAGE)
    return pkg_dir


def _write(path, text):
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


# --- слой 1: чистые функции ----------------------------------------------

def test_parse_block_lists():
    lists = ag.parse_block_lists(PKG_DRAFT)
    # блочные списки собраны
    assert lists["input_zones"] == ["docs/", "drivers/"], lists
    assert lists["output_zones"] == ["reports/", "tmp-work/"], lists
    assert lists["related"] == ["T-901", "Q-5", "D-035",
                                "closed-loop-agent-cauldron-conveyor"], lists
    # инлайновый список раскрыт
    assert lists["tasks"] == ["T-901"], lists


def test_looks_like_tqd():
    assert ag._looks_like_tqd("T-273")
    assert ag._looks_like_tqd("Q-5")
    assert ag._looks_like_tqd("D-035")
    # не T/Q/D — тема/файл
    assert not ag._looks_like_tqd("closed-loop-agent-cauldron-conveyor")
    assert not ag._looks_like_tqd("orchestrator-cycle-proposal-2026-07-06")


def test_collect_and_render(root):
    # collect_packages читает COLLAB_ROOT на import-time → подменяем ag.ROOT на temp.
    # Контракт conftest (C12-a): `root` — корень tmp; make_canon создал kotel/packages
    # под ним, поэтому ag.ROOT указываем прямо на root.
    saved = ag.ROOT
    try:
        ag.ROOT = root
        items = ag.collect_packages()
        ids = [it["id"] for it in items]
        # не-пакет пропущен; сортировка по id (demo < draft)
        assert ids == ["PKG-20260706-fixt-demo", "PKG-20260706-fixt-draft"], ids

        demo = items[0]
        draft = items[1]
        # зоны собраны из input/output_zones
        assert "in: docs/, drivers/" in draft["zones"], draft
        assert "out: reports/, tmp-work/" in draft["zones"], draft
        # связь T/Q/D: tasks + T/Q/D-элементы related, без темы/файла
        assert draft["links"] == "T-901, Q-5, D-035", draft["links"]
        # отчёт демонстрационного пакета прочитан
        assert demo["report"] == "reports/fixt-demo-2026-07-06.md", demo

        # секция «Пакеты»: обе строки, порядок = порядок items
        pkgs = ag.render_packages_table(items)
        assert "| `PKG-20260706-fixt-demo` | claude | demonstrated | low |" in pkgs, pkgs
        assert "| `PKG-20260706-fixt-draft` | pool | draft | medium |" in pkgs, pkgs
        assert pkgs.index("fixt-demo") < pkgs.index("fixt-draft"), pkgs

        # секция «Демонстрации»: только demonstrated, со ссылкой на отчёт
        demos = ag.render_demos_table(items)
        assert "| `PKG-20260706-fixt-demo` | `reports/fixt-demo-2026-07-06.md` |" in demos, demos
        assert "fixt-draft" not in demos, demos
    finally:
        ag.ROOT = saved


# --- слой 2: контракт CLI через subprocess -------------------------------

def _run(root, *args):
    env = dict(os.environ)
    env["COLLAB_ROOT"] = root
    env["PYTHONUTF8"] = "1"
    return subprocess.run(
        [sys.executable, os.path.join(HERE, "agenda_gen.py"), *args],
        env=env, capture_output=True, text=True, encoding="utf-8",
        errors="replace", stdin=subprocess.DEVNULL,
    )


def test_check_and_build_contract(root):
    # root от conftest == корень tmp; make_canon создал kotel/packages под ним.
    base = root
    target = os.path.join(base, "kotel", "agenda-generated.md")

    # 1. --check на отсутствующем файле повестки, но при наличии пакетов → STALE, exit 1.
    p = _run(base, "--check")
    assert p.returncode == 1, (p.returncode, p.stdout, p.stderr)
    assert "STALE" in p.stdout, p.stdout
    assert not os.path.exists(target), "--check не должен создавать файл"

    # 2. build → exit 0, файл создан, обе секции присутствуют.
    p = _run(base, "build")
    assert p.returncode == 0, (p.returncode, p.stdout, p.stderr)
    assert os.path.exists(target), p.stdout
    with open(target, encoding="utf-8") as f:
        body = f.read()
    assert "### Пакеты" in body and "### Демонстрации" in body, body
    assert "PKG-20260706-fixt-demo" in body, body
    assert "reports/fixt-demo-2026-07-06.md" in body, body
    # не-пакет не попал в повестку
    assert "not-a-pkg" not in body, body

    # 3. --check сразу после build → актуально, exit 0.
    p = _run(base, "--check")
    assert p.returncode == 0, (p.returncode, p.stdout, p.stderr)
    assert "STALE" not in p.stdout, p.stdout

    # 4. build идемпотентен → «актуален», exit 0, без диффа.
    p = _run(base, "build")
    assert p.returncode == 0, (p.returncode, p.stdout, p.stderr)
    assert "актуален" in p.stdout, p.stdout

    # 5. Правка front-matter пакета → --check видит дрейф → exit 1 + STALE.
    changed = PKG_DRAFT.replace("status: draft", "status: demonstrated")
    _write(os.path.join(base, "kotel", "packages", "PKG-20260706-fixt-draft.md"), changed)
    p = _run(base, "--check")
    assert p.returncode == 1, (p.returncode, p.stdout, p.stderr)
    assert "STALE" in p.stdout, p.stdout


def test_manual_sections_preserved(root):
    """replace_block переписывает только внутренность GEN-блока; ручной текст цел."""
    base = root
    target = os.path.join(base, "kotel", "agenda-generated.md")
    # build создаёт файл, затем добавим ручную секцию ПОСЛЕ END-маркера.
    p = _run(base, "build")
    assert p.returncode == 0, (p.returncode, p.stdout, p.stderr)
    with open(target, encoding="utf-8") as f:
        body = f.read()
    manual = "\n## Ручная секция\n\nРучной текст, который генератор не должен трогать.\n"
    with open(target, "w", encoding="utf-8", newline="\n") as f:
        f.write(body + manual)
    # Меняем пакет и перезапускаем build — ручная секция обязана уцелеть.
    changed = PKG_DEMO.replace("risk: low", "risk: high")
    _write(os.path.join(base, "kotel", "packages", "PKG-20260706-fixt-demo.md"), changed)
    p = _run(base, "build")
    assert p.returncode == 0, (p.returncode, p.stdout, p.stderr)
    with open(target, encoding="utf-8") as f:
        after = f.read()
    assert "## Ручная секция" in after, after
    assert "Ручной текст, который генератор не должен трогать." in after, after
    # новое значение risk дошло до блока
    assert "| high |" in after, after


def test_replace_block_no_markers():
    """Файл без маркеров → replace_block вернёт None (в CLI это ERROR, exit 2)."""
    assert ag.replace_block("no markers here", ag.MARKER, "x") is None
    # END раньше START → тоже None
    bad = ("<!-- GEN:%s END -->\n<!-- GEN:%s START -->" % (ag.MARKER, ag.MARKER))
    assert ag.replace_block(bad, ag.MARKER, "x") is None


# --- standalone-раннер (вторая ступень: python tools/tests/test_agenda_gen.py) ---

def run():
    tmp = tempfile.mkdtemp(prefix="agenda_gen_test_")
    try:
        make_canon(tmp)  # создаёт kotel/packages под tmp; `root` — сам tmp (контракт C12-a)
        test_parse_block_lists()
        test_looks_like_tqd()
        test_collect_and_render(tmp)
        test_replace_block_no_markers()
        test_check_and_build_contract(tmp)
        test_manual_sections_preserved(tmp)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print("TESTS OK agenda_gen: parse_block_lists + collect/render (зоны/связь T/Q/D/демо) + "
          "build/--check контракт (создание/дрейф/идемпотентность) + сохранение ручных секций")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(run())
    except AssertionError as exc:
        print("TEST FAIL:", exc)
        sys.exit(1)
