#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
# ==========================================
# [FILE ID CARD]
# ID: tools.tests.test_generate
# TYPE: active-script
# DOMAIN: core
# DEPTH_LEVEL: 1
# SUMMARY: Скрипт test_generate.py. Описание сгенерировано автоматически.
# ==========================================
"""
"""
Hermetic-тесты генератора навигации (tools/generate.py).

Покрывают два слоя:
  1. Чистые функции рендера/замены (replace_block, render_*_table) —
     детерминированно, без файловой системы.
  2. main() через subprocess на изолированном COLLAB_ROOT-фикстуре:
       - дефолтный прогон заполняет маркеры и пишет index.json (rc=0);
       - повторный --check на актуальном каноне → rc=0, нет STALE;
       - --check после правки источника детектит дрейф → rc=1 + STALE;
       - C17-b: GEN:counters в STATUS.md заполняется счётчиками канона;
         legacy-корень без маркера counters → WARN, rc=0 (маркер опциональный).

main() читает module-level ROOT (COLLAB_ROOT), поэтому изоляция через subprocess
с временной папкой — единственный способ инвариантного теста без записи в реальный
репо (T-007: один источник правды, --check ловит дрейф навигации/index.json).
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
import json
import subprocess

HERE = _TOOLS_DIR  # tools/ — тест перенесён в tools/tests/ (C14)
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, "drivers"))
import generate as g
from test_tmp import temp_dir


def configure_output():
    for name in ("stdout", "stderr"):
        s = getattr(sys, name, None)
        if s is not None and hasattr(s, "reconfigure"):
            s.reconfigure(encoding="utf-8", errors="replace")


configure_output()


# ---------- фикстуры с GEN-маркерами ----------
def _gen(marker):
    return "<!-- GEN:%s START -->\nстарое\n<!-- GEN:%s END -->\n" % (marker, marker)


# C17-b: STATUS содержит и счётчиковый GEN-блок (counters), и таблицу тем
STATUS = ("# Статус\n\n## Фокус\n\n" + _gen("counters")
          + "\n## Активные topics\n\n" + _gen("topics-status"))
# Корень «до C17»: STATUS без маркера counters — генератор не должен падать (маркер опциональный)
STATUS_LEGACY = "# Статус\n\n## Активные topics\n\n" + _gen("topics-status")
BOARD = "# Доска\n\n## Темы\n\n" + _gen("topics-board")
TASKS = "# Задачи\n\n" + _gen("tasks")
QUESTIONS = "# Вопросы\n\n" + _gen("questions")
DECISIONS = "# Решения\n\n" + _gen("decisions")


def _write(root, rel, text):
    path = os.path.join(root, rel)
    os.makedirs(os.path.dirname(path) or root, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def _build_root(root):
    _write(root, "STATUS.md", STATUS)
    _write(root, "board.md", BOARD)
    _write(root, "TASKS.md", TASKS)
    _write(root, "QUESTIONS.md", QUESTIONS)
    _write(root, "DECISIONS.md", DECISIONS)
    # topics/ — путь как в проде (кириллица), один источник правды
    _write(root, "topics/x.md", "---\nid: x\ntitle: Тема X\nstatus: open\nnext: шаг\n---\n# X\n")
    # C18: тема БЕЗ front-matter — title должен взяться фоллбэком из первого '#'-заголовка
    _write(root, "topics/no-fm.md", "# Тема без front-matter\n\nтекст\n")
    _write(root, "tasks/T-001.md",
           "---\nid: T-001\ntitle: Задача 1\nstatus: todo\nowner: pool\ntopic: themes/x\n---\n# t\n")
    _write(root, "questions/Q-001.md",
           "---\nid: Q-001\ntitle: Вопрос 1\nstatus: open\n---\n# q\n")
    _write(root, "decisions/D-001.md",
           "---\nid: D-001\ntitle: Решение 1\nstatus: accepted\ndate: 2026-01-01\n---\n# d\n")


def _run_generate(root, *args):
    env = dict(os.environ)
    env["COLLAB_ROOT"] = root
    env["PYTHONUTF8"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"
    proc = subprocess.run(
        [sys.executable, os.path.join(HERE, "generate.py"), *args],
        env=env, capture_output=True, text=True, encoding="utf-8",
    )
    return proc.returncode, proc.stdout


def run():
    # ---- слой 1: чистые функции ----
    # replace_block: подмена между маркерами; None при отсутствии маркера
    txt = _gen("tasks")
    out = g.replace_block(txt, "tasks", "НОВОЕ")
    assert out is not None and "НОВОЕ" in out and "старое" not in out, out
    assert g.replace_block("без маркеров", "tasks", "x") is None

    # render_tasks_table детерминирован и содержит шапку
    tasks = [{"id": "T-001", "title": "t", "status": "todo", "owner": "pool",
              "topic": "themes/x", "next": "шаг"}]
    rt = g.render_tasks_table(tasks)
    assert rt.startswith("| ID | Задача |"), rt
    assert "| T-001 |" in rt and "`themes/x`" in rt, rt

    # C18: фоллбэк заголовка — первый '# ...' вне код-фенсов; пусто, если заголовка нет
    assert g.title_from_heading("# Заголовок\n\nтекст\n") == "Заголовок"
    assert g.title_from_heading("```\n# комментарий в фенсе\n```\n# Реальный\n") == "Реальный"
    assert g.title_from_heading("текст без заголовка\n") == ""

    # C17-b: render_counters детерминирован, числа — len() входных списков
    line = g.render_counters([1, 2], [1], [], [1, 2, 3], [])
    assert "Задач: 2" in line and "решений: 1" in line, line
    assert "вопросов: 0" in line and "тем в навигации: 3" in line, line
    assert "драйверов: 0" in line and "index.json" in line, line
    assert line == g.render_counters([1, 2], [1], [], [1, 2, 3], []), "недетерминизм render_counters"
    # маркер counters объявлен опциональным (корни без него не ломаются)
    assert "counters" in g.OPTIONAL_MARKERS

    # ---- слой 2: main() через subprocess ----
    with temp_dir("generate_") as root:
        _build_root(root)

        # первый прогон: заполнить маркеры + написать index.json
        rc, gen_out = _run_generate(root)
        assert rc == 0, "первый generate должен пройти (rc=%d):\n%s" % (rc, gen_out)
        with open(os.path.join(root, "TASKS.md"), encoding="utf-8") as f:
            tasks_md = f.read()
        assert "| T-001 | Задача 1 |" in tasks_md, "таблица задач не заполнена:\n%s" % tasks_md
        # C17-b: счётчиковый GEN-блок STATUS.md заполнен из источников
        # (фикстура: 1 задача, 1 решение, 1 вопрос, 2 темы, 0 драйверов)
        with open(os.path.join(root, "STATUS.md"), encoding="utf-8") as f:
            status_md = f.read()
        assert ("Задач: 1 · решений: 1 · вопросов: 1 · тем в навигации: 2 · драйверов: 0"
                in status_md), "счётчики не заполнены:\n%s" % status_md
        assert "старое" not in status_md.split("GEN:counters START")[1].split("GEN:counters END")[0], \
            "плейсхолдер внутри GEN:counters не заменён"
        ipath = os.path.join(root, "index.json")
        assert os.path.exists(ipath), "index.json не создан"
        with open(ipath, encoding="utf-8") as f:
            idx = json.load(f)
        assert {"topics", "tasks", "questions", "decisions", "drivers"} <= set(idx), idx
        assert idx["tasks"][0]["id"] == "T-001", idx["tasks"]
        # C18: тема без front-matter видна в index.json с title из '#'-заголовка
        titles = {t["title"] for t in idx["topics"]}
        assert "Тема без front-matter" in titles, "фоллбэк-title не попал в index.json: %r" % titles

        # --check на актуальном каноне: нет дрейфа → rc=0, нет STALE
        rc, chk_out = _run_generate(root, "--check")
        assert rc == 0, "--check на актуальном каноне должен быть rc=0:\n%s" % chk_out
        assert "STALE" not in chk_out, "ложный дрейф:\n%s" % chk_out

        # правим источник темы → навигация устаревает → --check ловит дрейф
        _write(root, "topics/x.md",
               "---\nid: x\ntitle: Тема X ИЗМЕНЕНА\nstatus: open\nnext: шаг\n---\n# X\n")
        rc, drift_out = _run_generate(root, "--check")
        assert rc == 1, "--check после правки источника должен валить (rc=%d):\n%s" % (rc, drift_out)
        assert "STALE" in drift_out, "--check не сообщил STALE при дрейфе:\n%s" % drift_out

    # ---- C17-b: legacy-корень без маркера counters — WARN, но не ERROR/rc=1 ----
    with temp_dir("generate_legacy_") as root:
        _build_root(root)
        _write(root, "STATUS.md", STATUS_LEGACY)  # STATUS «до C17», без GEN:counters
        rc, out = _run_generate(root)
        assert rc == 0, "generate без маркера counters должен пройти (rc=%d):\n%s" % (rc, out)
        assert "WARN: маркер counters" in out, "нет WARN о пропущенном опциональном блоке:\n%s" % out
        assert "ERROR" not in out, "опциональный маркер не должен давать ERROR:\n%s" % out
        # и --check на таком корне тоже зелёный (пропуск блока — не дрейф)
        rc, out = _run_generate(root, "--check")
        assert rc == 0, "--check на legacy-корне должен быть rc=0:\n%s" % out
        assert "STALE" not in out, "пропуск опционального блока не должен считаться дрейфом:\n%s" % out

    print("TESTS OK generate: helpers (replace_block/render_tasks_table/title_from_heading/"
          "render_counters) + main() контракт (fill→0, --check sync→0, --check drift→1 STALE, "
          "index.json, C18 фоллбэк, C17 счётчики + опциональный маркер)")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(run())
    except AssertionError as exc:
        print("TEST FAIL:", exc)
        sys.exit(1)
