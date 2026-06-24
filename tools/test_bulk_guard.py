"""Тест bulk_guard.py — парсинг numstat + пороги массовой операции (D-026)."""
import os
import sys

os.environ.setdefault("PYTHONUTF8", "1")
HERE = os.path.dirname(os.path.abspath(__file__))
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

    if fails:
        print("FAIL test_bulk_guard:")
        for f in fails:
            print("  -", f)
        sys.exit(1)
    print("OK test_bulk_guard: numstat-парсинг + бинарный-пропуск + порог-строк + порог-файлов + не-массовая + check-структура")


if __name__ == "__main__":
    main()
