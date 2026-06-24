"""
# ==========================================
# [FILE ID CARD]
# ID: tools.command_index
# TYPE: active-script
# DOMAIN: core
# DEPTH_LEVEL: 1
# SUMMARY: Скрипт command_index.py. Описание сгенерировано автоматически.
# ==========================================
"""
"""command_index.py — индекс команд всех инструментов (metadata-indexes lane A; нахождение команд).

Из cauldron lane A «metadata-indexes» (9/10 docs) + запрос Stefan «быстрая навигация / нахождение
команд и операций». Сканирует tools/*.py, извлекает CLI-команды из docstring (строки вида
`python tools/X.py <verb> …`), собирает машинно-навигируемый индекс tool→команды+суть.
Завершает триаду метаданных-навигации: файлы=header.py · папки=dir_health.py · КОМАНДЫ=этот файл.

CLI:
    python tools/command_index.py                 # индекс всех команд (по инструментам)
    python tools/command_index.py --search <term>  # найти команды/инструменты по слову
    python tools/command_index.py --json
"""
import os
import re
import sys
import glob

os.environ.setdefault("PYTHONUTF8", "1")
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from _ioutil import configure_output
from _cli import help_guard

configure_output()
import json

DOC_RE = re.compile(r'(?:"""|\'\'\')(.*?)(?:"""|\'\'\')', re.S)


def _doc(path):
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            head = f.read(4000)
    except OSError:
        return ""
    m = DOC_RE.search(head)
    return m.group(1).strip() if m else ""


def _gist(doc):
    first = doc.splitlines()[0].strip() if doc else ""
    if " — " in first:
        return first.split(" — ", 1)[1].strip()
    return first.split(":", 1)[1].strip() if ":" in first else first


def _commands(name, doc):
    """Команды из строк `python tools/<name>.py <verb> …` в docstring."""
    cmds, seen = [], set()
    for m in re.finditer(r"python\s+tools/%s\.py\s+([^\n#]*)" % re.escape(name), doc):
        rest = m.group(1).strip()
        toks = rest.split()
        verb = next((t for t in toks if not t.startswith(("-", "<", "[", "$"))), "")
        usage = rest[:80]
        key = (verb, usage)
        if key not in seen:
            seen.add(key)
            cmds.append({"verb": verb or "(default)", "usage": usage})
    return cmds


def collect():
    out = {}
    for p in sorted(glob.glob(os.path.join(HERE, "*.py"))):
        b = os.path.basename(p)
        name = b[:-3]
        if b.startswith("test_") or b.startswith("_"):
            continue
        doc = _doc(p)
        if not doc:
            continue
        out[name] = {"gist": _gist(doc)[:120], "commands": _commands(name, doc)}
    return out


def main(argv):
    help_guard(__doc__, argv)
    a = list(argv)
    as_json = "--json" in a
    term = None
    if "--search" in a:
        i = a.index("--search")
        term = a[i + 1].lower() if i + 1 < len(a) else None
    data = collect()
    if term:
        data = {k: v for k, v in data.items()
                if term in k.lower() or term in v["gist"].lower()
                or any(term in c["verb"].lower() or term in c["usage"].lower() for c in v["commands"])}
    if as_json:
        print(json.dumps(data, ensure_ascii=False, indent=2))
        return 0
    n_cmd = sum(len(v["commands"]) for v in data.values())
    title = "ПОИСК «%s»" % term if term else "ИНДЕКС КОМАНД"
    print("=== %s — %d инструментов, %d команд ===" % (title, len(data), n_cmd))
    for name in sorted(data):
        v = data[name]
        print("\n%-20s %s" % (name + ".py", v["gist"]))
        for c in v["commands"]:
            print("   %-12s %s" % (c["verb"], c["usage"]))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
