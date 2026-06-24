#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
# ==========================================
# [FILE ID CARD]
# ID: tools.ownership
# TYPE: active-script
# DOMAIN: core
# DEPTH_LEVEL: 1
# SUMMARY: Скрипт ownership.py. Описание сгенерировано автоматически.
# ==========================================
"""
"""
ownership (T-153, синтез двух подсистем) — общий классификатор «чей dirty-файл».

Единая функция `classify(path) -> mine|generated|volatile|foreign|unknown`, которую используют ОБЕ
подсистемы: `tools/friction.py status` (детектор) и `tools/cohort.py guard` (исполнитель). Раньше
каждая по-своему грубо считала «чужие незакоммиченные файлы», из-за чего guard триггерил даже на
МОИ собственные правки. Здесь — один источник правды:

- **generated** — канонические индексы (`TASKS.md`/`index.json`/…): регенерируются, не связывают агентов.
- **volatile** — рантайм-снимки (`LIVE.md`/`PIPELINE.md`/`logs/*`): не коммитятся в обычный commit.
- **mine** — файл текущей задачи агента (по claim'у или явному списку `task_files`).
- **foreign** — source-файл, привязанный к задаче, которую держит ДРУГОЙ агент (по `queues/claimed/`).
- **unknown** — source-файл без явной привязки (tools/docs/темы без claim) — не обязательно чужой.

Только **foreign** обязан вести в Уровень-1 (D-022); generated/volatile/unknown/mine — нет.
"""
import os
import re
import glob

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

GENERATED = {"TASKS.md", "QUESTIONS.md", "DECISIONS.md", "board.md", "STATUS.md", "index.json"}
VOLATILE = {"LIVE.md", "PIPELINE.md", "logs/heartbeat.json", "logs/pipeline.json"}
VOLATILE_PREFIXES = ("logs/",)
VOLATILE_BASENAMES = {"heartbeat.json", "pipeline.json"}
SOURCE_DIRS = ("tasks/", "decisions/", "questions/", "tools/", "drivers/", "topics/", "docs/", "streams/")
_ID_RE = re.compile(r"\b(T-\d+|Q-\d+|D-\d+)\b")
_AGENT_RE = re.compile(r"\b(claude|codex|mavis|novax)\b")


def _norm(path):
    return str(path).replace("\\", "/").lstrip("./")


def claims(root=None):
    """task_id -> agent-держатель из queues/claimed/*.claim.md."""
    base = root or ROOT
    out = {}
    for p in glob.glob(os.path.join(base, "queues", "claimed", "*.claim.md")):
        task = os.path.basename(p)[:-len(".claim.md")]
        holder = None
        try:
            for line in open(p, encoding="utf-8", errors="replace"):
                m = re.match(r"\s*agent\s*:\s*(\S+)", line)
                if m:
                    holder = m.group(1)
                    break
        except OSError:
            pass
        out[task] = holder
    return out


def _entity_id(path):
    m = _ID_RE.search(os.path.basename(_norm(path)))
    return m.group(1) if m else None


def classify(path, agent=None, task_files=None, claim_map=None, root=None):
    """Вернуть один из: mine | generated | volatile | foreign | unknown."""
    p = _norm(path)
    base = p.split("/")[-1]

    if task_files:
        tf = {_norm(f) for f in task_files}
        if p in tf or base in {x.split("/")[-1] for x in tf}:
            return "mine"
    if p in VOLATILE or base in VOLATILE_BASENAMES or p.startswith(VOLATILE_PREFIXES):
        return "volatile"
    if base in GENERATED:
        return "generated"

    cm = claim_map if claim_map is not None else claims(root)
    tid = _entity_id(p)
    if tid and tid in cm:
        holder = cm[tid]
        if agent and holder == agent:
            return "mine"
        if holder:
            return "foreign"
    # форк/outbox другого агента по суффиксу имени
    if ("outbox/" in p or "streams/" in p):
        m = _AGENT_RE.search(base)
        if m and agent and m.group(1) != agent:
            return "foreign"
    return "unknown"


def classify_all(paths, agent=None, task_files=None, root=None):
    cm = claims(root)
    return {_norm(p): classify(p, agent=agent, task_files=task_files, claim_map=cm, root=root)
            for p in paths}


def summary(paths, agent=None, task_files=None, root=None):
    """Свод по категориям + флаг has_foreign (нужен ли Уровень-1)."""
    cls = classify_all(paths, agent=agent, task_files=task_files, root=root)
    by = {"mine": [], "generated": [], "volatile": [], "foreign": [], "unknown": []}
    for p, c in cls.items():
        by[c].append(p)
    return {"by": by, "has_foreign": bool(by["foreign"])}
