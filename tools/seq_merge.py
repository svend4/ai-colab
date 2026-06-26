"""seq_merge.py — 3-way ПОСТРОЧНЫЙ мёрж тела (diff3) поверх stdlib difflib.

Апгрейд для crdt_merge/git_reconcile: вместо «оба тронули тело → весь блок конфликт» — diff3 по СТРОКАМ.
Непересекающиеся правки обеих сторон сливаются чисто; маркеры `<<<<<<<` ставятся ТОЛЬКО на пересекающихся
строках. Это лёгкая форма sequence-CRDT под наш git-контекст (merge-base есть → diff3 даёт 90% пользы RGA).

Публичная: merge_lines(base, ours, theirs) -> (текст, есть_конфликт).

CLI:
  python tools/seq_merge.py base.txt ours.txt theirs.txt
"""
import os
from _ioutil import configure_output
from _cli import help_guard
import sys
import difflib

configure_output()
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.environ.get("COLLAB_ROOT") or os.path.dirname(HERE)


def merge_lines(base, ours, theirs):
    """3-way построчный мёрж. Правки в РАЗНЫХ base-диапазонах сливаются; конфликт — только при пересечении."""
    B, O, T = base.splitlines(), ours.splitlines(), theirs.splitlines()
    eo, et = _edits(B, O), _edits(B, T)         # списки (i1,i2,[новые строки]) изменённых регионов base→X
    out, conflict, bi = [], False, 0
    io = it = 0
    n = len(B)
    while bi < n or io < len(eo) or it < len(et):
        no = eo[io] if io < len(eo) else None
        nt = et[it] if it < len(et) else None
        start = min([e[0] for e in (no, nt) if e is not None] + [n])
        if bi < start:                          # неизменный base до следующей правки
            out += B[bi:start]; bi = start; continue
        oh = no is not None and no[0] <= bi
        th = nt is not None and nt[0] <= bi
        if oh and th and _overlap(no, nt):      # обе правки пересекаются по base → конфликт (или равны)
            if no[2] == nt[2]:
                out += no[2]
            else:
                conflict = True
                out += ["<<<<<<< ours"] + no[2] + ["======="] + nt[2] + [">>>>>>> theirs"]
            bi = max(no[1], nt[1]); io += 1; it += 1
        elif oh and not (th and _overlap(no, nt)):
            out += no[2]; bi = max(bi, no[1]); io += 1      # правка только ours
        elif th:
            out += nt[2]; bi = max(bi, nt[1]); it += 1      # правка только theirs
        else:
            out.append(B[bi]); bi += 1
    return "\n".join(out), conflict


def _edits(B, X):
    """Изменённые регионы base→X: [(i1, i2, [строки X])] для не-equal опкодов."""
    sm = difflib.SequenceMatcher(None, B, X, autojunk=False)
    return [(i1, i2, X[j1:j2]) for tag, i1, i2, j1, j2 in sm.get_opcodes() if tag != "equal"]


def _overlap(a, b):
    """Пересекаются ли base-диапазоны двух правок (вставка i1==i2 пересекается только при равной точке)."""
    a1, a2, _ = a
    b1, b2, _ = b
    if a1 == a2 or b1 == b2:                     # вставка(и) — пересечение только в одной точке
        return a1 == b1
    return a1 < b2 and b1 < a2


def main(argv):
    help_guard(__doc__, argv)
    args = [a for a in argv if not a.startswith("--")]
    if len(args) < 3:
        print("seq_merge: нужно 3 файла: base ours theirs"); return 2
    texts = []
    for p in args[:3]:
        fp = p if os.path.isabs(p) else os.path.join(ROOT, p)
        try:
            texts.append(open(fp, encoding="utf-8", errors="replace").read())
        except OSError as e:
            print("seq_merge: %s" % e); return 2
    text, conflict = merge_lines(*texts)
    print(text)
    sys.stderr.write("seq_merge: %s\n" % ("КОНФЛИКТ на пересечении строк" if conflict else "чисто слито построчно"))
    return 1 if conflict else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
