#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for tools/report_diff.py (T-127)."""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, "drivers"))
import report_diff as rd
from test_tmp import temp_dir


A = """# Knowledge report — data/a

- Корпус: `data/a` — занесено документов: **8**

## Состав по типам
| Тип | Документов |
|---|---|
| md | 4 |
| txt | 2 |

## Запрос: «bridge» — 3 совпадений (ранжировано, FTS5)
"""

B = """# Knowledge report — docs

- Корпус: `docs` — занесено документов: **68**

## Состав по типам
| Тип | Документов |
|---|---|
| md | 68 |

## Запрос: «pipeline» — показано 10 совпадений (limit=10, ранжировано, FTS5)
"""


def run():
    with temp_dir("report_diff_") as d:
        a = os.path.join(d, "a.md")
        b = os.path.join(d, "b.md")
        out = os.path.join(d, "diff.md")
        open(a, "w", encoding="utf-8").write(A)
        open(b, "w", encoding="utf-8").write(B)
        pa = rd.parse_report(a)
        pb = rd.parse_report(b)
        assert pa["documents"] == 8, pa
        assert pb["types"]["md"] == 68, pb
        text = rd.render(pa, pb)
        assert "| documents | 8 | 68 | +60 |" in text, text
        assert "shown_query_hits" in text, text
        rd.write_out(text, out)
        assert os.path.exists(out), out
    print("TESTS OK report_diff: parse/render/write")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(run())
    except AssertionError as exc:
        print("TEST FAIL:", exc)
        sys.exit(1)