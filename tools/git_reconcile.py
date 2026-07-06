# ast: allow-subprocess
# ==========================================
# [FILE ID CARD]
# ID: tools.git_reconcile
# TYPE: active-script
# DOMAIN: core
# DEPTH_LEVEL: 1
# SUMMARY: git merge-driver: при коллизии канон-файла зовёт crdt_merge (field-level 3-way).
# ==========================================
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
from _ioutil import configure_output, safe_write, DataLossGuardException
from _cli import help_guard
import sys
import subprocess
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
    # C33: ours (%A) переписывается целиком — safe_write ловит аномальное усечение.
    # У 3-way мёржа сжатие бывает ЗАКОННЫМ (theirs намеренно удалил крупный кусок,
    # ours не трогал → берём theirs), поэтому гвард не роняет драйвер: пишем с force,
    # но добавляем конфликт-строку → exit 1, git оставит файл человеку на доразбор.
    text = cm.render_item(m)
    try:
        safe_write(ours_path, text)
    except DataLossGuardException as exc:
        safe_write(ours_path, text, force_truncate=True)
        m["conflicts"].append(
            "size-guard: слитый результат сильно меньше ours — проверьте, что сжатие намеренно (%s)"
            % str(exc).splitlines()[0])
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


# Канон-файлы front-matter, для которых поле-уровневое слияние не теряет вкладов (grow-only).
CANON_GLOBS = ["tasks/**/*.md", "decisions/**/*.md", "questions/**/*.md", "topics/**/*.md"]


def _apply():
    """Реально активировать драйвер: git config (локально) + идемпотентно дописать .gitattributes.
    Grow-only: только ДОБАВляет конфиг/атрибуты, ничего не удаляет; merge3 union-ит list-поля."""
    done = []
    for k, v in (("merge.crdt.name", "canon field-level CRDT merge"),
                 ("merge.crdt.driver", "python tools/git_reconcile.py %O %A %B")):
        subprocess.run(["git", "config", k, v], cwd=ROOT, check=False, stdin=subprocess.DEVNULL)
        done.append("git config %s" % k)
    ga = os.path.join(ROOT, ".gitattributes")
    text = _read(ga)
    lines = text.splitlines()
    added = []
    for g in CANON_GLOBS:
        if not any(ln.split() and ln.split()[0] == g and "merge=crdt" in ln for ln in lines):
            text = text.rstrip("\n") + "\n%s merge=crdt\n" % g
            added.append(g)
    if added:
        # C33: .gitattributes — рукописный файл; правка grow-only (только дописываем
        # строки), так что гвард safe_write молчит на легальном пути и ловит баг-усечение.
        safe_write(ga, text)
    return done, added


def main(argv):
    help_guard(__doc__, argv)
    if "--install" in argv:
        if "--apply" in argv:
            done, added = _apply()
            print("=== git_reconcile --install --apply: драйвер канона активирован ===")
            for d in done:
                print("  ✓ " + d)
            print("  .gitattributes: " + (", ".join(added) if added else "уже настроено (без изменений)"))
            return 0
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
