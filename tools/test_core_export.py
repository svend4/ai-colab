#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
# ==========================================
# [FILE ID CARD]
# ID: tools.test_core_export
# TYPE: active-script
# DOMAIN: core
# DEPTH_LEVEL: 1
# SUMMARY: Скрипт test_core_export.py. Описание сгенерировано автоматически.
# ==========================================
"""
"""
Регрессия портативности L1 core-export (D-021 п.1): экспортируем набор `core/engine-manifest.md`
во временный каталог и ПРОГОНЯЕМ экспортированные тесты STANDALONE. Если кто-то добавит в файл ядра
зависимость от репо-специфики, этот тест станет красным — переносимость остаётся доказанной, а не
заявленной. Использует `tools/promote.py export` (COPY, не move) — живой `tools/` не трогается.
"""
import os
import sys
import subprocess
import shutil

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, "drivers"))
import promote
from _canon import parse_front_matter
from test_tmp import make_temp_dir


def configure_output():
    for name in ("stdout", "stderr"):
        s = getattr(sys, name, None)
        if s is not None and hasattr(s, "reconfigure"):
            s.reconfigure(encoding="utf-8", errors="replace")


configure_output()


def run():
    ok = True
    dest = make_temp_dir("coreexport_ci_")
    try:
        manifest = os.path.join(ROOT, "core", "engine-manifest.md")
        fm = parse_front_matter(open(manifest, encoding="utf-8").read())
        files = promote._list_field(fm.get("files"))
        tests = promote._list_field(fm.get("tests"))
        export_files = files + [t for t in tests if t not in files]
        assert files, "engine-manifest.md без поля files:"

        # 1) экспорт = курируемая копия, без потерь
        r = promote.export(export_files, dest)
        assert not r["missing"], "в экспорте отсутствуют: %s" % r["missing"]

        # 2) экспортированные тесты ядра запускаются STANDALONE (из временного каталога)
        exported_tests = tests or [f for f in export_files if os.path.basename(f.replace("\\", "/")).startswith("test_")]
        assert exported_tests, "в манифесте нет тестов ядра для проверки переносимости"
        env = dict(os.environ, PYTHONUTF8="1")
        failures = []
        for t in exported_tests:
            tp = os.path.join(dest, t)
            p = subprocess.run([sys.executable, tp], cwd=os.path.dirname(tp),
                               capture_output=True, text=True, encoding="utf-8",
                               errors="replace", stdin=subprocess.DEVNULL, env=env)
            if p.returncode != 0:
                failures.append((t, p.returncode, (p.stdout or "") + (p.stderr or "")))

        assert not failures, "standalone-провал: " + "; ".join(
            "%s rc=%d :: %s" % (t, rc, out.strip().splitlines()[-1] if out.strip() else "") for t, rc, out in failures)

        print("TESTS OK core_export: ядро экспортировано (%d файлов), %d тест(ов) зелёные STANDALONE — переносимо"
              % (len(export_files), len(exported_tests)))
    except AssertionError as e:
        ok = False
        print("TEST FAIL:", e)
    finally:
        shutil.rmtree(dest, ignore_errors=True)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(run())
