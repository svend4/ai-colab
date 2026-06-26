"""git_reconcile.py — git merge-driver: при коллизии канон-файла зовёт crdt_merge (field-level 3-way).

Закрывает T-263 инструментально: вместо git-СТРОЧНЫХ конфликтов на хот-файлах — слияние на уровне ПОЛЯ.
Git вызывает драйвер с тремя версиями (%O base, %A ours, %B theirs); драйвер прогоняет crdt_merge.merge3,
пишет результат в ours (%A): list-поля front-matter (related/tags) union (ничего не теряется), скаляры
3-way, тело при двойной правке — маркеры <<<<. Exit 0 = чисто слито; exit 1 = остались конфликты (git
оставит файл на доразбор человеку, но УЖЕ field-merged, не строчная каша).

Установка (печатает команды, git-конфиг сам не трогаю):
  python tools/git_reconcile.py --install

Использование (обычно git вызывает сам):
  python tools/git_reconcile.py <base> <ours> <theirs>     # %O %A %B
"""
import os
from _ioutil import configure_output
from _cli import help_guard
import sys
import crdt_merge as cm

configure_output()
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.environ.get("COLLAB_ROOT") or os.path.dirname(HERE)


def reconcile_files(base_path, ours_path, theirs_path):
    """3-way field-level мёрж трёх версий файла; результат пишется в ours_path. Возвращает список конфликтов."""
    base = cm.parse_item(_read(base_path))
    ours = cm.parse_item(_read(ours_path))
    theirs = cm.parse_item(_read(theirs_path))
    m = cm.merge3(base, ours, theirs)
    open(ours_path, "w", encoding="utf-8", newline="\n").write(cm.render_item(m))
    return m["conflicts"]


def _read(p):
    try:
        return open(p, encoding="utf-8", errors="replace").read()
    except OSError:
        return ""


def _install_hint():
    return (
        "# 1) зарегистрировать merge-драйвер (одноразово, в репо):\n"
        "git config merge.crdt.name 'canon field-level CRDT merge'\n"
        "git config merge.crdt.driver 'python tools/git_reconcile.py %O %A %B'\n"
        "# 2) включить для канон-файлов (.gitattributes):\n"
        "echo 'tasks/**/*.md   merge=crdt' >> .gitattributes\n"
        "echo 'decisions/**/*.md merge=crdt' >> .gitattributes\n"
        "echo 'topics/**/*.md  merge=crdt' >> .gitattributes\n"
        "# Теперь коллизии канон-файлов сливаются на уровне ПОЛЯ, не строки (T-263)."
    )


def main(argv):
    help_guard(__doc__, argv)
    if "--install" in argv:
        print("=== Установка git_reconcile как merge-драйвера канона ===")
        print(_install_hint())
        return 0
    args = [a for a in argv if not a.startswith("--")]
    if len(args) < 3:
        print("git_reconcile: нужно 3 пути: base ours theirs (git даёт %O %A %B). Или --install."); return 2
    base, ours, theirs = args[:3]
    conflicts = reconcile_files(base, ours, theirs)
    if conflicts:
        sys.stderr.write("git_reconcile: field-merged, но %d конфликт(ов) на доразбор:\n" % len(conflicts))
        for c in conflicts:
            sys.stderr.write("  ⚠ " + c + "\n")
        return 1                                  # git пометит как требующий доразбора (но уже field-merged)
    sys.stderr.write("git_reconcile: чисто слито на уровне поля (0 конфликтов)\n")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
