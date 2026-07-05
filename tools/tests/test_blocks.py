"""
# ==========================================
# [FILE ID CARD]
# ID: tools.tests.test_blocks
# TYPE: active-script
# DOMAIN: core
# DEPTH_LEVEL: 1
# SUMMARY: Скрипт test_blocks.py. Описание сгенерировано автоматически.
# ==========================================
"""
"""Тест blocks.py — сборные блоки (кластеры проверенных примитивов).

Проверяет СТРУКТУРУ блока (не конкретный вердикт — он зависит от состояния дерева):
list работает, run_block('audit') возвращает агрегат с gate-классификацией и шагами.
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

os.environ.setdefault("PYTHONUTF8", "1")
HERE = _TOOLS_DIR  # tools/ — тест перенесён в tools/tests/ (C14)
sys.path.insert(0, HERE)
import blocks

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass


def main():
    fails = []
    # реестр непуст и audit есть
    if "audit" not in blocks.BLOCKS:
        fails.append("блок 'audit' отсутствует в реестре")
    # audit имеет хотя бы 1 gate-шаг (иначе вердикт бессмыслен)
    kinds = [k for _, _, k in blocks.BLOCKS["audit"]["steps"]]
    if "gate" not in kinds:
        fails.append("audit без gate-шага")

    # все блоки реестра (audit/adoption/self/improve/pyramid) валидны: kinds ∈ {gate,advisory} (hermetic)
    for bname, b in blocks.BLOCKS.items():
        for tool, args, kind in b["steps"]:
            if kind not in ("gate", "advisory"):
                fails.append("блок %s шаг %s: kind %r вне {gate,advisory}" % (bname, tool, kind))
    if "improve" not in blocks.BLOCKS:
        fails.append("нет блока 'improve' (петля само-улучшения)")

    # run_block возвращает корректную структуру (последовательно — детерминированнее в тесте)
    res = blocks.run_block("audit", parallel=False)
    for key in ("block", "gates_passed", "advisory_flags", "steps"):
        if key not in res:
            fails.append("run_block без ключа %r" % key)
    if not isinstance(res.get("steps"), list) or len(res["steps"]) != len(blocks.BLOCKS["audit"]["steps"]):
        fails.append("steps не совпадает по числу шагов")
    if not isinstance(res.get("gates_passed"), bool):
        fails.append("gates_passed не bool")
    # каждый шаг несёт tool/kind/rc/skipped
    for st in res.get("steps", []):
        for key in ("tool", "kind", "rc", "skipped"):
            if key not in st:
                fails.append("шаг без ключа %r: %s" % (key, st.get("tool")))
                break

    # параллельный путь даёт ту же структуру (число шагов)
    resp = blocks.run_block("audit", parallel=True)
    if len(resp["steps"]) != len(res["steps"]):
        fails.append("параллельный run_block дал другое число шагов")

    if fails:
        print("FAIL test_blocks:")
        for f in fails:
            print("  -", f)
        sys.exit(1)
    print("OK test_blocks: реестр + run_block(audit) seq/parallel — структура валидна (%d шагов)"
          % len(res["steps"]))


if __name__ == "__main__":
    main()
