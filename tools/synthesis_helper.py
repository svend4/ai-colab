#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
synthesis_helper (форк-синтез, D-017/D-018) — собирает форк-варианты темы в СКЕЛЕТ синтеза.

Закрывает вторую половину инструментария «дубли vs варианты»: `variants.py` отвечает «где все
форки по теме», а `synthesis_helper.py` раскладывает их рядом и даёт готовый каркас для решения —
стороны, слоты «консенсус»/«расхождения», чек-лист двойной перепроверки (техн.+гуман., D-018) и
секцию «предложение синтеза».

ВАЖНО: инструмент ГОТОВИТ материал, а не принимает решение. Он ничего не помечает accepted, не
пишет в DECISIONS.md и не сводит варианты сам — финальный синтез делает коллектив (D-018).

CLI:
    python tools/synthesis_helper.py topics                       # темы с >=2 вариантами (кандидаты)
    python tools/synthesis_helper.py report <topic> [--out PATH]  # скелет синтеза по теме
"""
import os
import re
import sys
from _ioutil import configure_output
import json
import subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOLS = os.path.join(ROOT, "tools")
sys.path.insert(0, TOOLS)
try:
    from _canon import parse_front_matter
except ImportError:
    def parse_front_matter(text):
        return {}

configure_output()

def _variants_index():
    """Индекс форк-вариантов от variants.py (topic -> [{agent,file,status,kind}])."""
    p = subprocess.run([sys.executable, os.path.join(TOOLS, "variants.py"), "index"],
                       cwd=ROOT, capture_output=True, text=True,
                       encoding="utf-8", errors="replace", stdin=subprocess.DEVNULL)
    try:
        return json.loads(p.stdout or "{}")
    except ValueError:
        return {}

def _outline(rel):
    """Заголовки секций (## / ###) файла-варианта + первая содержательная строка каждого."""
    path = os.path.join(ROOT, rel)
    out = []
    try:
        lines = open(path, encoding="utf-8", errors="replace").read().splitlines()
    except OSError:
        return out
    cur = None
    for ln in lines:
        m = re.match(r"^(#{2,3})\s+(.*)", ln)
        if m:
            cur = {"h": m.group(2).strip(), "gist": ""}
            out.append(cur)
        elif cur and not cur["gist"] and ln.strip() and not ln.startswith("#"):
            cur["gist"] = ln.strip()[:100]
    return out[:12]

def topics(as_json=False):
    idx = _variants_index()
    cand = {t: v for t, v in idx.items() if len(v) >= 2}
    if as_json:
        print(json.dumps(cand, ensure_ascii=False, indent=2))
        return 0
    print("Кандидаты на синтез (>=2 вариантов):")
    if not cand:
        print("  (нет тем с несколькими вариантами)")
    for t, v in sorted(cand.items()):
        agents = ", ".join(sorted({x.get("agent", "?") for x in v}))
        print("  %-28s %d вар. [%s]" % (t, len(v), agents))
    print("\nСкелет по теме: `python tools/synthesis_helper.py report <topic>`")
    return 0

def report(topic, out_path=None, with_streams=False):
    idx = _variants_index()
    variants = idx.get(topic, [])
    if not variants:
        print("Нет вариантов для темы %r (см. `variants.py list`)." % topic)
        return 1
    agents = sorted({v.get("agent", "?") for v in variants})

    L = []
    L.append("---")
    L.append("id: synthesis-%s" % topic)
    L.append("topic: %s" % topic)
    L.append("type: synthesis-scaffold")
    L.append("status: proposed")
    L.append("agents: %s" % ", ".join(agents))
    L.append("variants: %d" % len(variants))
    L.append("---")
    L.append("")
    L.append("# Синтез (скелет): %s" % topic)
    L.append("")
    L.append("> **proposed** — материал для котла (D-018). Скелет собран автоматически из форк-вариантов;")
    L.append("> консенсус/расхождения/решение заполняет коллектив с двойной перепроверкой. Инструмент")
    L.append("> ничего не решает и не помечает accepted.")
    L.append("")
    L.append("## Варианты (%d)" % len(variants))
    L.append("")
    L.append("| Агент | Статус | Тип | Файл |")
    L.append("|---|---|---|---|")
    for v in variants:
        L.append("| %s | %s | %s | `%s` |" % (v.get("agent", "?"), v.get("status", "?"),
                                              v.get("kind", "?"), v.get("file", "?")))
    L.append("")
    for v in variants:
        L.append("### %s — `%s`" % (v.get("agent", "?"), v.get("file", "?")))
        ol = _outline(v.get("file", ""))
        if not ol:
            L.append("- (нет секций ## — короткий файл/иной формат)")
        for sec in ol:
            gist = (" — " + sec["gist"]) if sec["gist"] else ""
            L.append("- **%s**%s" % (sec["h"], gist))
        L.append("")
    L.append("## Консенсус (общее во всех вариантах) — ЗАПОЛНИТЬ")
    L.append("- [ ] ...")
    L.append("")
    L.append("## Расхождения → в решение — ЗАПОЛНИТЬ")
    L.append("- [ ] пункт спора · варианты сторон · доказательная база · что выбрать")
    if with_streams:
        L.append("")
        L.append("### Файлы для детальных разногласий (Streams)")
        for a in agents:
            stream_rel = "streams/%s/%s-divergence.md" % (topic, a)
            L.append("- [%s: %s](file:///%s)" % (a, stream_rel, os.path.abspath(os.path.join(ROOT, stream_rel)).replace("\\", "/")))
            # Create the stream file if requested
            stream_abs = os.path.join(ROOT, "streams", topic, "%s-divergence.md" % a)
            if not os.path.exists(stream_abs):
                os.makedirs(os.path.dirname(stream_abs), exist_ok=True)
                with open(stream_abs, "w", encoding="utf-8") as sf:
                    sf.write("---\ntopic: %s\nagent: %s\ntype: divergence-stream\n---\n\n# Разногласия от %s\n\n- [ ] Детализируйте здесь пункты, по которым вы не согласны с mainline консенсусом.\n" % (topic, a, a))
    L.append("")
    L.append("## Двойная перепроверка (D-018)")
    L.append("- **Техническая:** [ ] корректность · [ ] тесты · [ ] нет новой поверхности риска")
    L.append("- **Гуманитарная:** [ ] польза людям/пользователям · [ ] понятность · [ ] последствия")
    L.append("")
    L.append("## Предложение синтеза (proposed, не решение)")
    L.append("- ...")
    text = "\n".join(L)

    if out_path:
        dest = out_path if os.path.isabs(out_path) else os.path.join(ROOT, out_path)
        dest_r = os.path.realpath(dest)
        if os.path.commonpath([dest_r, ROOT]) != os.path.realpath(ROOT):
            print("Путь вне репозитория — отказ: %s" % out_path)
            return 1
        os.makedirs(os.path.dirname(dest_r), exist_ok=True)
        with open(dest_r, "w", encoding="utf-8", newline="\n") as f:
            f.write(text + "\n")
        print("Скелет синтеза записан: %s" % os.path.relpath(dest_r, ROOT))
    else:
        print(text)
    return 0

def main():
    a = sys.argv[1:]
    if not a:
        print(__doc__)
        return 2
    cmd = a[0]
    rest = a[1:]
    as_json = "--json" in rest
    pos = [x for x in rest if not x.startswith("--")]
    out_path = None
    if "--out" in rest:
        i = rest.index("--out")
        if i + 1 < len(rest):
            out_path = rest[i + 1]
    with_streams = "--with-streams" in rest
    try:
        if cmd == "topics":
            return topics(as_json=as_json)
        if cmd == "report" and pos:
            return report(pos[0], out_path=out_path, with_streams=with_streams)
    except Exception as exc:  # noqa: BLE001 — единая понятная ошибка
        print("ОШИБКА: %s: %s" % (type(exc).__name__, exc))
        return 1
    print(__doc__)
    return 2

if __name__ == "__main__":
    sys.exit(main())
