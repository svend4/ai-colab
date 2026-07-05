# ==========================================
# [FILE ID CARD]
# ID: tools.crdt_merge
# TYPE: active-script
# DOMAIN: core
# DEPTH_LEVEL: 1
# SUMMARY: 3-way field-level мёрж канон-файлов (вместо git-строчных конфликтов на хот-файлах).
# ==========================================
"""crdt_merge.py — 3-way field-level мёрж канон-файлов (вместо git-строчных конфликтов на хот-файлах).

Рациональная переработка CRDT-идеи из `.inf` (inf_crdt.py: LWW-регистры + OR-Set) под НАШ репо и его
боль T-263 (две правки одного файла → git-конфликт). Отличия от .inf-оригинала:
  • у git ЕСТЬ merge-base → 3-way (не state-CRDT без базы);
  • list-поля front-matter (related/tags/...) — 3-way OR-Set: добавленное любой стороной выживает,
    но УДАЛЕНИЕ durable (было в base, сторона убрала → НЕ воскресает; чистый union раньше воскрешал —
    тот же класс, что баг inf_crdt.remove_block);
  • скаляры — 3-way: изменил один → берём его; изменили ОБА по-разному → КОНФЛИКТ-флаг + КОММУТАТИВНЫЙ
    детерм. выбор (A⊕B==B⊕A), не позиционный «ours-wins» и не молчаливый LWW;
  • тело при двойной правке — КОНФЛИКТ-флаг, не тихая потеря (лечит LWW-on-body слабость .inf).

Это «мёрж на уровне ПОЛЯ/секции, а не строки» — то, чего T-263 не хватало (хот-файлы Codex).

CLI:
  python tools/crdt_merge.py base.md ours.md theirs.md        # печать слитого + конфликтов
  python tools/crdt_merge.py base.md ours.md theirs.md --out merged.md
  # --out часто перезаписывает ours/канон-файл → запись через safe_write (C33);
  # намеренное сильное сжатие подтверждается флагом --force-truncate
"""
import os
from _ioutil import configure_output, safe_write, DataLossGuardException
from _cli import help_guard
import sys
import re

configure_output()
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.environ.get("COLLAB_ROOT") or os.path.dirname(HERE)
LIST_FIELDS = ("related", "tags", "participants", "depends_on", "links")  # 3-way OR-Set: add-wins, remove durable via base


def parse_item(text):
    """Канон-файл → {fm: {ключ: значение|список}, body: str}."""
    fm, body = {}, text
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end >= 0:
            head = text[3:end]
            nl = text.find("\n", end + 1)
            body = text[nl + 1:] if nl >= 0 else ""
            fm = _parse_fm(head)
    return {"fm": fm, "body": body}


def merge3(base, ours, theirs):
    """3-way field-level мёрж. Возвращает {fm, body, conflicts:[...]}. Ничего не теряет молча."""
    fm, conflicts = {}, []
    keys = set(base["fm"]) | set(ours["fm"]) | set(theirs["fm"])
    for k in keys:
        bv, ov, tv = base["fm"].get(k), ours["fm"].get(k), theirs["fm"].get(k)
        if k in LIST_FIELDS:
            fm[k] = _union_lists(bv, ov, tv)                  # 3-way OR-Set: add-wins, remove durable
            continue
        merged, conf = _merge_scalar(bv, ov, tv)
        fm[k] = merged
        if conf:
            conflicts.append("front-matter '%s': ours=%r theirs=%r (детерм. tie-break → %r)" % (k, ov, tv, merged))
    body, bconf = _merge_body(base["body"], ours["body"], theirs["body"])
    if bconf:
        conflicts.append("body: обе стороны изменили тело по-разному (помечено маркерами, НЕ потеряно)")
    return {"fm": fm, "body": body, "conflicts": conflicts}


def render_item(merged):
    """Слитый item → текст канон-файла (front-matter + body)."""
    lines = ["---"]
    for k, v in merged["fm"].items():
        if v is None:
            continue
        if isinstance(v, list):
            lines.append("%s: [%s]" % (k, ", ".join(v)))
        else:
            lines.append("%s: %s" % (k, v))
    lines.append("---")
    return "\n".join(lines) + "\n" + merged["body"]


def _parse_fm(head):
    fm = {}
    for line in head.splitlines():
        m = re.match(r"^([A-Za-z0-9_\-]+):\s*(.*)$", line)
        if not m:
            continue
        key, val = m.group(1), m.group(2).strip()
        if val.startswith("[") and val.endswith("]"):
            fm[key] = [x.strip().strip("'\"") for x in val[1:-1].split(",") if x.strip()]
        else:
            fm[key] = val
    return fm


def _as_list(v):
    if v is None:
        return []
    return v if isinstance(v, list) else [v]


def _union_lists(bv, ov, tv):
    """3-way OR-Set: добавленное любой стороной выживает; удалённое стороной (было в base,
    нет у неё) — durable, НЕ воскресает. Без base (bv=None) = чистое объединение. Порядок
    детерминирован (ours, затем theirs, с dedup)."""
    base = set(_as_list(bv))
    ours, theirs = _as_list(ov), _as_list(tv)
    ours_set, theirs_set = set(ours), set(theirs)
    out, decided = [], set()
    for x in ours + theirs:
        if x in decided:
            continue
        decided.add(x)
        if x in base:
            keep = (x in ours_set) and (x in theirs_set)   # удаление любой стороной — durable
        else:
            keep = True                                    # новое → add-wins
        if keep:
            out.append(x)
    return out


def _scalar_hash(v):
    import hashlib
    return hashlib.sha256(repr(v).encode("utf-8")).hexdigest()


def _merge_scalar(bv, ov, tv):
    """3-way: (merged, conflict?). Изменил один → его; оба одинаково → оно; оба по-разному →
    КОММУТАТИВНЫЙ детерм. tie-break по sha256 (A⊕B==B⊕A) + конфликт-флаг (видимо, не молча)."""
    if ov == tv:
        return ov, False
    if ov == bv:
        return tv, False        # ours не трогал → берём theirs
    if tv == bv:
        return ov, False        # theirs не трогал → берём ours
    winner = max((ov, tv), key=_scalar_hash)   # порядко-независимо: один и тот же на (ov,tv) и (tv,ov)
    return winner, True         # оба изменили по-разному → конфликт, выбор детерминирован


def _merge_body(bb, ob, tb):
    if ob == tb:
        return ob, False
    if ob.strip() == bb.strip():
        return tb, False
    if tb.strip() == bb.strip():
        return ob, False
    import seq_merge                            # ПОСТРОЧНЫЙ diff3: непересекающиеся правки тела сливаются
    return seq_merge.merge_lines(bb, ob, tb)    # маркеры только на пересекающихся строках, не на всём теле


def main(argv):
    help_guard(__doc__, argv)
    args = [a for a in argv if not a.startswith("--")]
    if len(args) < 3:
        print("crdt_merge: нужно 3 файла: base ours theirs"); return 2
    items = []
    for p in args[:3]:
        fp = p if os.path.isabs(p) else os.path.join(ROOT, p)
        try:
            items.append(parse_item(open(fp, encoding="utf-8", errors="replace").read()))
        except OSError as e:
            print("crdt_merge: %s" % e); return 2
    m = merge3(*items)
    text = render_item(m)
    if "--out" in argv:
        i = argv.index("--out")
        if i + 1 < len(argv):
            op = argv[i + 1]
            op = op if os.path.isabs(op) else os.path.join(ROOT, op)
            # C33: --out часто указывает на ours/канон-файл — safe_write гвардит
            # случайное усечение; законное сильное сжатие — явным --force-truncate.
            try:
                safe_write(op, text, force_truncate="--force-truncate" in argv)
            except DataLossGuardException as exc:
                print(str(exc))
                print("crdt_merge: запись в %s ОТКЛОНЕНА гвардом потери — файл не тронут; "
                      "перезапустите с --force-truncate, если сжатие намеренно" % op)
                return 1
            print("→ слито в %s" % op)
    else:
        print(text)
    print("\n=== КОНФЛИКТЫ (ничего не потеряно молча): %d ===" % len(m["conflicts"]))
    for c in m["conflicts"]:
        print("  ⚠ " + c)
    if not m["conflicts"]:
        print("  (нет — чистое поле-уровневое слияние, обе правки сохранены)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
