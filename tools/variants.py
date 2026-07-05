#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
# ==========================================
# [FILE ID CARD]
# ID: tools.variants
# TYPE: active-script
# DOMAIN: core
# DEPTH_LEVEL: 1
# SUMMARY: Скрипт variants.py. Описание сгенерировано автоматически.
# ==========================================
"""
"""
Variants (D-018) — READ-ONLY реестр/дискавери параллельных форк-вариантов по всему репо.

Закрывает пробел №1: форки (параллельные варианты одной темы) живут в ad-hoc местах —
нет единого способа найти ВСЕ варианты одной темы и их авторов/статусы. Этот инструмент
сканирует известные места обитания форков и строит индекс `тема -> [варианты]`.

Сканируются:
  - topics/*.md                         — тематические обсуждения/форки (kind=topic-note)
  - docs/*.md взаимодополняющие пары   — Claude ↔ Codex онбординг/манул (kind=doc)
  - streams/<topic>/<id>/STREAM.md     — draft-пакеты вариантов (kind=stream)
  - queues/outbox/*.md                 — форк-артефакты в исходящих (kind=outbox)

Для каждого варианта выводится: agent (из front-matter author/agent/owner, иначе из имени
файла -claude/-codex, иначе из текста), status (front-matter или «Статус: ...» в теле, иначе
unknown), file, kind. Группировка по нормализованному ключу темы (срезаются даты и -agent суффиксы).

CLI:
    python tools/variants.py list [--topic X] [--json]
    python tools/variants.py index            # JSON в stdout
"""
import os
import re
import sys
from _ioutil import configure_output
from _cli import help_guard
import json

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from _canon import parse_front_matter  # единый парсер front-matter

configure_output()

# Темы (русское имя папки) и прочие сканируемые директории.
TOPICS_DIR = os.path.join(ROOT, "topics")
DOCS_DIR = os.path.join(ROOT, "docs")
STREAMS_DIR = os.path.join(ROOT, "streams")
OUTBOX_DIR = os.path.join(ROOT, "queues", "outbox")

# Известные взаимодополняющие doc-пары (форк-варианты одной темы разными агентами).
DOC_PAIRS = [
    {
        "topic": "agent-onboarding",
        "files": [
            ("docs/agent-onboarding.md", "claude"),
            ("docs/top-agent-operating-manual.md", "codex"),
        ],
    },
]

# Не-форки: служебные/индексные файлы, которые надо пропускать.
SKIP_NAMES = {"README.md", "index.md", "example.md"}

_DATE_RE = re.compile(r"-?\d{4}-\d{2}-\d{2}")
# Ростер — из _canon.AGENTS_ROSTER (C36-a): раньше variants молча знал только claude|codex,
# и форки mavis/novax не распознавались как агентские. Теперь суффиксы/инференс — по ростеру.
from _canon import AGENTS_ROSTER, agents_regex_group
_AGENT_SUFFIX_RE = re.compile(r"-(%s)\b" % agents_regex_group())
_STATUS_BODY_RE = re.compile(
    r"(?:Статус|status)\s*[:\-]\s*\**\s*"
    r"(proposed|adopted|ready|open|draft|done|closed)",
    re.IGNORECASE,
)

def _read(path):
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            return f.read()
    except OSError:
        return ""

def _rel(path):
    return os.path.relpath(path, ROOT).replace("\\", "/")

def normalize_topic(name):
    """Нормализованный ключ темы: режем даты и -agent суффиксы, .md, мусор по краям."""
    key = name
    if key.lower().endswith(".md"):
        key = key[:-3]
    key = _DATE_RE.sub("", key)
    key = _AGENT_SUFFIX_RE.sub("", key)
    key = re.sub(r"^\d{4}-\d{2}-\d{2}-?", "", key)
    key = key.strip("-_ ").lower()
    return key or name.lower()

def _infer_agent(fm, filename, text):
    for field in ("author", "agent", "owner"):
        v = (fm.get(field) or "").strip()
        if v:
            return v.lower()
    low = filename.lower()
    # Имя файла: первый агент из ростера, чьё имя встречается (порядок ростера = приоритет,
    # как раньше claude→codex, но теперь для ВСЕХ агентов ростера).
    for a in AGENTS_ROSTER:
        if a in low:
            return a
    # Тело: агент выводится, только если упомянут РОВНО один агент ростера (без неоднозначности).
    body = (text or "")[:2000].lower()
    present = [a for a in AGENTS_ROSTER if a in body]
    if len(present) == 1:
        return present[0]
    return "unknown"

def _infer_status(fm, text):
    v = (fm.get("status") or "").strip()
    if v:
        return v.lower()
    m = _STATUS_BODY_RE.search(text or "")
    if m:
        return m.group(1).lower()
    return "unknown"

def _entry(path, kind, agent_hint=None):
    text = _read(path)
    fm = parse_front_matter(text)
    filename = os.path.basename(path)
    agent = agent_hint or _infer_agent(fm, filename, text)
    return {
        "agent": agent,
        "file": _rel(path),
        "status": _infer_status(fm, text),
        "kind": kind,
        "topic_raw": fm.get("topic") or fm.get("id") or filename,
    }

def _scan_dir_flat(directory, kind):
    out = []
    if not os.path.isdir(directory):
        return out
    for name in sorted(os.listdir(directory)):
        if not name.lower().endswith(".md") or name in SKIP_NAMES:
            continue
        out.append(_entry(os.path.join(directory, name), kind))
    return out

def _scan_streams():
    out = []
    if not os.path.isdir(STREAMS_DIR):
        return out
    for topic in sorted(os.listdir(STREAMS_DIR)):
        tdir = os.path.join(STREAMS_DIR, topic)
        if not os.path.isdir(tdir):
            continue
        for sid in sorted(os.listdir(tdir)):
            sp = os.path.join(tdir, sid, "STREAM.md")
            if os.path.isfile(sp):
                e = _entry(sp, "stream")
                # для streams front-matter обычно несёт явный topic
                fm = parse_front_matter(_read(sp))
                e["topic_raw"] = fm.get("topic") or topic
                out.append(e)
    return out

def _scan_doc_pairs():
    out = []
    for pair in DOC_PAIRS:
        for rel, agent in pair["files"]:
            path = os.path.join(ROOT, rel.replace("/", os.sep))
            if os.path.isfile(path):
                e = _entry(path, "doc", agent_hint=agent)
                e["topic_raw"] = pair["topic"]
                out.append(e)
    return out

def discover():
    """Собрать все варианты из всех источников (плоский список dict)."""
    items = []
    items += _scan_dir_flat(TOPICS_DIR, "topic-note")
    items += _scan_streams()
    items += _scan_doc_pairs()
    items += _scan_dir_flat(OUTBOX_DIR, "outbox")
    return items

def build_index():
    """тема(нормализованная) -> [{agent, file, status, kind}], отсортировано."""
    index = {}
    for it in discover():
        key = normalize_topic(it.get("topic_raw") or it["file"])
        index.setdefault(key, []).append({
            "agent": it["agent"],
            "file": it["file"],
            "status": it["status"],
            "kind": it["kind"],
        })
    for key in index:
        index[key].sort(key=lambda v: (v["kind"], v["file"]))
    return dict(sorted(index.items()))

def _filter_topic(index, topic):
    if not topic:
        return index
    needle = topic.strip().lower()
    return {k: v for k, v in index.items() if needle in k}

def render_table(index):
    lines = []
    if not index:
        lines.append("(вариантов не найдено)")
        return "\n".join(lines)
    for topic, variants in index.items():
        lines.append("== %s (%d) ==" % (topic, len(variants)))
        for v in variants:
            lines.append("  %-8s %-11s %-11s %s"
                         % (v["agent"], v["status"], v["kind"], v["file"]))
        lines.append("")
    return "\n".join(lines).rstrip()

def main():
    help_guard(__doc__)
    a = sys.argv[1:]
    if not a:
        print(__doc__)
        return 2
    cmd = a[0]
    topic = a[a.index("--topic") + 1] if "--topic" in a and a.index("--topic") + 1 < len(a) else None
    want_json = "--json" in a
    try:
        if cmd == "index":
            print(json.dumps(_filter_topic(build_index(), topic), ensure_ascii=False, indent=2))
            return 0
        if cmd == "list":
            index = _filter_topic(build_index(), topic)
            if want_json:
                print(json.dumps(index, ensure_ascii=False, indent=2))
            else:
                print(render_table(index))
            return 0
    except Exception as exc:
        print("ОШИБКА: %s: %s" % (type(exc).__name__, exc))
        return 1
    print(__doc__)
    return 2

if __name__ == "__main__":
    sys.exit(main())
