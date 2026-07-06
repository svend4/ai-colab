"""
# ==========================================
# [FILE ID CARD]
# ID: tools.test_bulk_guard
# TYPE: active-script
# DOMAIN: core
# DEPTH_LEVEL: 1
# SUMMARY: Скрипт test_bulk_guard.py. Описание сгенерировано автоматически.
# ==========================================
"""
"""Тест bulk_guard.py — парсинг numstat + пороги массовой операции (D-026)."""
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
import bulk_guard as bg

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass


def _isbulk(stat):
    return stat["deletions"] >= bg.THRESHOLD_LINES or stat["bulk_files"] >= bg.THRESHOLD_FILES


def main():
    fails = []

    # парсинг: numstat = «добавлено<TAB>удалено<TAB>файл»
    txt = "3\t367\tqueues/outbox/a.md\n2\t10\tfoo.py\n-\t-\timg.png\n1\t40\tbar.md\n"
    s = bg.parse_numstat(txt)
    if s["deletions"] != 367 + 10 + 40:
        fails.append("deletions неверно: %s" % s["deletions"])
    if s["insertions"] != 3 + 2 + 1:
        fails.append("insertions неверно: %s" % s["insertions"])
    # бинарный (-/-) пропущен
    if any("img.png" in r[0] for r in s["top"]):
        fails.append("бинарный файл не пропущен")
    # bulk_files: ≥FILE_DEL_MIN(30) → a.md(367) + bar.md(40) = 2
    if s["bulk_files"] != 2:
        fails.append("bulk_files ожидал 2, факт %s" % s["bulk_files"])
    # top отсортирован по удалениям (a.md первый)
    if s["top"][0][0] != "queues/outbox/a.md":
        fails.append("top не отсортирован по удалениям")

    # порог по СТРОКАМ: 600 удалений в 1 файле → массовая
    big_lines = bg.parse_numstat("0\t600\tx.md\n")
    if not _isbulk(big_lines):
        fails.append("600 удалений не распознано как массовое")

    # порог по ФАЙЛАМ: 12 файлов по 40 удалений → массовая (по числу файлов)
    many = "".join("1\t40\tf%d.md\n" % i for i in range(12))
    sm = bg.parse_numstat(many)
    if sm["bulk_files"] != 12 or not _isbulk(sm):
        fails.append("12 крупно-урезанных файлов не распознано как массовое: %s" % sm["bulk_files"])

    # НЕ массовая: удаления в 3 мелких файлах (<FILE_DEL_MIN, <порогов)
    small = bg.parse_numstat("5\t20\ta.md\n2\t15\tb.md\n1\t10\tc.md\n")
    if _isbulk(small):
        fails.append("мелкая правка ложно массовая")

    # check() возвращает структуру с verdict (git-вызов реальный, но структуру проверим)
    r = bg.check()
    for k in ("is_bulk", "insured", "verdict", "deletions"):
        if k not in r:
            fails.append("check() без ключа %s" % k)

    # --- C44 (волна 2, Q-W2-13c): условная строгость --hook по машинному статусу D-026 ---
    # чистая логика hook_rc: блок ТОЛЬКО при (STOP-uninsured И accepted)
    if bg.hook_rc("STOP-uninsured", "proposed") != 0:
        fails.append("hook: proposed D-026 не имеет права блокировать (D-006)")
    if bg.hook_rc("STOP-uninsured", "") != 0:
        fails.append("hook: отсутствующий D-026 не должен блокировать")
    if bg.hook_rc("STOP-uninsured", "accepted") != 1:
        fails.append("hook: accepted D-026 + STOP обязан блокировать (exit 1)")
    if bg.hook_rc("ok-insured", "accepted") != 0:
        fails.append("hook: застрахованная массовая операция не блокируется")
    if bg.hook_rc("ok-not-bulk", "accepted") != 0:
        fails.append("hook: не-массовая операция не блокируется")
    insured, verdict = bg.classify_verdict(True, ["backup-old"], [])
    if insured or verdict != "STOP-uninsured":
        fails.append("старый backup-тег не на HEAD не должен страховать bulk-diff")
    insured, verdict = bg.classify_verdict(True, ["backup-current"], ["backup-current"])
    if not insured or verdict != "ok-insured":
        fails.append("backup-тег на HEAD должен страховать bulk-diff")

    # d026_status: машинное чтение front-matter из fixture-корня
    import shutil
    repo_root = os.path.abspath(os.path.join(HERE, os.pardir))
    tmp_root = os.path.join(repo_root, "tmp-work")
    froot = os.path.join(tmp_root, "bulk_guard_d026_fixture")
    if not os.path.abspath(froot).startswith(os.path.abspath(tmp_root) + os.sep):
        fails.append("fixture path escaped tmp-work")
    try:
        shutil.rmtree(froot, ignore_errors=True)
        os.makedirs(os.path.join(froot, "decisions"), exist_ok=True)
        p = os.path.join(froot, "decisions", "D-026.md")
        with open(p, "w", encoding="utf-8", newline="\n") as f:
            f.write("---\nid: D-026\ntype: decision\ntitle: t\nstatus: proposed\n---\n# D-026\n")
        if bg.d026_status(root=froot) != "proposed":
            fails.append("d026_status: proposed из fixture не прочитан")
        with open(p, "w", encoding="utf-8", newline="\n") as f:
            f.write("---\nid: D-026\ntype: decision\ntitle: t\nstatus: accepted\n---\n# D-026\n")
        if bg.d026_status(root=froot) != "accepted":
            fails.append("d026_status: accepted из fixture не прочитан")
        if bg.d026_status(root=os.path.join(froot, "no-such")) != "":
            fails.append("d026_status: отсутствие файла должно давать ''")
        # связка: fixture-статус → hook_rc (эмуляция обеих фаз жизни D-026)
        if bg.hook_rc("STOP-uninsured", bg.d026_status(root=froot)) != 1:
            fails.append("связка d026_status(accepted)+STOP должна блокировать")
    finally:
        shutil.rmtree(froot, ignore_errors=True)
    # реальный репо-статус сейчас proposed → hook-режим НЕ блокирует независимо от вердикта
    real_status = bg.d026_status()
    if real_status == "proposed" and bg.hook_rc(bg.check(staged=True)["verdict"], real_status) != 0:
        fails.append("на живом репо (D-026 proposed) hook не должен блокировать")

    if fails:
        print("FAIL test_bulk_guard:")
        for f in fails:
            print("  -", f)
        sys.exit(1)
    print("OK test_bulk_guard: numstat-парсинг + бинарный-пропуск + порог-строк + порог-файлов + "
          "не-массовая + check-структура + strict backup-on-HEAD insurance + C44 hook (proposed→советник, accepted→блок; d026_status fixture)")


if __name__ == "__main__":
    main()
