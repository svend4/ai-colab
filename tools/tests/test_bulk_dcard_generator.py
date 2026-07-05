"""
# ==========================================
# [FILE ID CARD]
# ID: tools.tests.test_bulk_dcard_generator
# TYPE: active-script
# DOMAIN: core.indexing
# DEPTH_LEVEL: 1
# SUMMARY: Тест bulk_dcard_generator.py — вставка D-Card grow-only, идемпотентность, safe_write-контур (C33).
# ==========================================
"""
"""Тест bulk_dcard_generator.py — D-Card добавляется, ничего не теряется, запись через safe_write."""
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
import time

os.environ.setdefault("PYTHONUTF8", "1")
HERE = _TOOLS_DIR  # tools/ — тест перенесён в tools/tests/ (C14)
sys.path.insert(0, HERE)
import bulk_dcard_generator as bg

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass


def main():
    fails = []
    d = os.path.join(os.path.dirname(HERE), "tmp-work",
                     "bulk_dcard_test_%d_%d" % (os.getpid(), time.time_ns()))
    os.makedirs(d, exist_ok=True)

    # C33: инструмент переписывает рукописные исходники целиком → обязан идти через safe_write
    if not hasattr(bg, "safe_write"):
        fails.append("bulk_dcard_generator должен импортировать _ioutil.safe_write (C33)")

    # 1) файл без D-Card: карта добавляется, все исходные строки сохранены (grow-only)
    p = os.path.join(d, "sample_tool.py")
    body = "#!/usr/bin/env python3\nimport os\n\ndef work():\n    return 42\n"
    with open(p, "w", encoding="utf-8", newline="\n") as f:
        f.write(body)
    if not bg.process_file(p, "sample_tool.py"):
        fails.append("process_file должен вернуть True для файла без D-Card")
    after = open(p, encoding="utf-8").read()
    if "[FILE ID CARD]" not in after:
        fails.append("D-Card не вставлена")
    for ln in body.splitlines():
        if ln and ln not in after:
            fails.append("строка исходника потеряна: %r" % ln)
    if len(after) <= len(body):
        fails.append("вставка D-Card обязана только ДОБАВЛЯТЬ (grow-only)")

    # 2) повторный прогон — идемпотентно (уже есть карта → файл не трогается)
    if bg.process_file(p, "sample_tool.py"):
        fails.append("повторный прогон не должен менять файл с D-Card")
    if open(p, encoding="utf-8").read() != after:
        fails.append("повторный прогон изменил содержимое")

    # 3) shebang остаётся первой строкой (карта вставляется после него)
    if not after.splitlines()[0].startswith("#!/usr/bin/env"):
        fails.append("shebang должен остаться первой строкой")

    if fails:
        print("FAIL test_bulk_dcard_generator:")
        for f in fails:
            print("  -", f)
        sys.exit(1)
    print("OK test_bulk_dcard_generator: D-Card grow-only · идемпотентность · shebang · safe_write-контур")


if __name__ == "__main__":
    main()
