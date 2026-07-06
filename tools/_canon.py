#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ==========================================
# [FILE ID CARD]
# ID: tools._canon
# TYPE: helper-module
# DOMAIN: core.parsing
# DEPTH_LEVEL: 1
# SUMMARY: Единые источники канона: parser front-matter, реестр CANON_DIRS, ростер агентов, слои L3.
# ==========================================
"""
Единые источники для инструментов канона (T-085, ревью T-078 находка L; волна 2: P9-a, C36-a).

Здесь живут константы/функции, которые раньше были продублированы по `tools/*.py`
(и молча расходились). Логика намеренно идентична прежним копиям, чтобы
консолидация не меняла поведение:

- `parse_front_matter` / `parse_fm` — канонический парсер front-matter
  (блок между первым `---` и следующим `\n---`, строки `key: value` через `split(':', 1)`);
- `CANON_DIRS` / `CANON_DIRS_EXTENDED` — реестр каталогов канона (P9-a);
- `AGENTS_ROSTER` — ростер агентов для ownership/cohort/variants (C36-a);
- `SERVICE_AGENTS` / `EXCLUDED_AGENTS` — служебные исполнители роёв (не WARN) и
  исключённые из ростера с причиной для WARN (решение Stefan 2026-07-06, A4-1);
- `observed_agents` — имена агентов, реально встречающиеся в рабочих артефактах
  (claim/heartbeat/streams) для advisory-сверки с ростером (Q-W2-9b);
- `PYRAMID_L3_DIRS` — рабочие каталоги слоя L3 пирамиды (promote/layer_check);
- `missing_canon_dirs` / `require_canon_dirs` — контракт «обход несуществующего
  канон-пути → ERROR, а не тихий 0» (симптом (f) дрейфа деривата).
"""
import os

# --- Реестр каталогов канона (P9-a, аудит 2026-07-02) -----------------------------------
# До консолидации константа CANON_DIRS была продублирована в view.py, canon_index.py и
# info_verify.py, и копии УЖЕ разошлись: view/canon_index знали ядро из 5 каталогов,
# info_verify — расширенный список из 9. Консолидация СОХРАНЯЕТ фактическое поведение
# каждого потребителя (ядро — для среза/retrieval, расширенный — для verify-инварианта).
# Составы ратифицированы: Stefan, 2026-07-06 — CANON_DIRS (5, strict) и
# CANON_DIRS_EXTENDED (9); оба уровня живут здесь как единый источник, локальные копии запрещены.
CANON_DIRS = ("tasks", "decisions", "questions", "topics", "docs")
CANON_DIRS_EXTENDED = CANON_DIRS + ("drivers", "streams", "portals", "core")

# --- Ростер агентов (C36-a, аудит 2026-07-02) --------------------------------------------
# Единый источник вместо трёх независимых хардкодов (ownership.py / cohort.py / variants.py,
# причём variants знал только claude|codex — пятый агент становился невидим МОЛЧА).
# Состав ратифицирован: Stefan, 2026-07-06 (A4-1) — claude/codex/mavis/novax;
# служебные и исключённые участники — отдельными реестрами ниже.
AGENTS_ROSTER = ("claude", "codex", "mavis", "novax")

# Служебные исполнители роёв (workflow-подагенты): их следы в рабочих артефактах —
# норма, validate НЕ даёт WARN (решение Stefan 2026-07-06).
SERVICE_AGENTS = ("subagent-worker",)

# Агенты, явно исключённые из ростера: validate даёт WARN с причиной из словаря —
# напоминание остаётся, но с провенансом решения (решение Stefan 2026-07-06).
EXCLUDED_AGENTS = {
    "antigravity": "вне ростера до объяснения по инциденту outbox-mass-strip "
                   "(решение Stefan 2026-07-06)",
}


def agents_regex_group():
    """Фрагмент regex `claude|codex|...` из единого ростера (для _AGENT_RE и суффиксов)."""
    return "|".join(AGENTS_ROSTER)


def _artifact_agent(path):
    """Имя агента из front-matter артефакта: `agent:` (claim/stream), фоллбэк `claimed_by:`.

    Читаются только первые 4КБ (front-matter — в голове файла). Битый/нечитаемый
    файл → пустая строка: наблюдение агентов advisory и не должно падать на мусоре.
    """
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            head = f.read(4096)
    except OSError:
        return ""
    fm = parse_front_matter(head)
    return (fm.get("agent") or fm.get("claimed_by") or "").strip().lower()


def observed_agents(root):
    """Q-W2-9(b): имена агентов, реально встречающиеся в рабочих артефактах.

    Возвращает {agent: [относительные пути-свидетельства]}; имена нормализованы
    к lower-case (ростер хранится в нижнем регистре). Источники — фактическая
    структура рабочих слоёв репозитория:

    - `queues/claimed/*.md` — front-matter `agent:` claim-файлов (pipeline.py /
      agent_queue.py; фоллбэк `claimed_by:` для legacy-формата), README.md пропускается;
    - `logs/heartbeat/*.json` — имя файла = имя агента (`pipeline.py heartbeat`
      пишет `logs/heartbeat/<agent>.json`);
    - `streams/<topic>/<stream-id>/STREAM.md` — front-matter `agent:` манифеста варианта;
    - `streams/<topic>/*.md` — front-matter `agent:` (divergence-файлы вида
      `<agent>-divergence.md`), README.md пропускается.

    Это ТОЛЬКО наблюдение. Сверку с AGENTS_ROSTER делает validate.py как
    advisory-WARN: состав ростера ратифицируется человеком (C32/Q-W2-9),
    а не выводится автоматически из артефактов.
    """
    found = {}

    def add(agent, place):
        agent = (agent or "").strip().lower()
        if not agent:
            return
        places = found.setdefault(agent, [])
        if place not in places:
            places.append(place)

    claimed = os.path.join(root, "queues", "claimed")
    if os.path.isdir(claimed):
        for fn in sorted(os.listdir(claimed)):
            if fn.endswith(".md") and fn != "README.md":
                add(_artifact_agent(os.path.join(claimed, fn)), "queues/claimed/" + fn)

    heartbeat = os.path.join(root, "logs", "heartbeat")
    if os.path.isdir(heartbeat):
        for fn in sorted(os.listdir(heartbeat)):
            if fn.endswith(".json"):
                add(fn[: -len(".json")], "logs/heartbeat/" + fn)

    streams = os.path.join(root, "streams")
    if os.path.isdir(streams):
        for topic in sorted(os.listdir(streams)):
            topic_dir = os.path.join(streams, topic)
            if not os.path.isdir(topic_dir):
                continue
            for entry in sorted(os.listdir(topic_dir)):
                path = os.path.join(topic_dir, entry)
                rel = "streams/%s/%s" % (topic, entry)
                if os.path.isdir(path):
                    manifest = os.path.join(path, "STREAM.md")
                    if os.path.isfile(manifest):
                        add(_artifact_agent(manifest), rel + "/STREAM.md")
                elif entry.endswith(".md") and entry != "README.md":
                    add(_artifact_agent(path), rel)

    return found


# --- Слои пирамиды: рабочие каталоги L3 (та же консолидация, дубли promote/layer_check) --
PYRAMID_L3_DIRS = ("tasks", "decisions", "questions", "streams", "topics", "collab")


def missing_canon_dirs(root, dirs=CANON_DIRS):
    """Список канон-каталогов из `dirs`, которых нет под `root` (порядок сохранён)."""
    return [d for d in dirs if not os.path.isdir(os.path.join(root, d))]


def require_canon_dirs(root, dirs=CANON_DIRS):
    """Контракт P9: обход несуществующего канон-пути — ERROR, а не тихий 0/пусто.

    «Немой ноль выглядит как валидный ответ» (симптом (f)): дериват, читающий
    несуществующий каталог, молча возвращает пустоту. Поднимаем FileNotFoundError,
    чтобы вызывающий инструмент упал громко (или явно обработал).
    """
    missing = missing_canon_dirs(root, dirs)
    if missing:
        raise FileNotFoundError(
            "ERROR: канон-каталог(и) не найдены под %s: %s — обход несуществующего "
            "пути запрещён (P9: тихий 0 маскирует дрейф)" % (root, ", ".join(missing)))


def parse_front_matter(text):
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    if end == -1:
        return {}
    fm = {}
    for line in text[3:end].strip().splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            fm[k.strip()] = v.strip()
    return fm


# Исторический синоним (queue/pipeline/dispatch/metrics/risk_gate/drivers_catalog).
parse_fm = parse_front_matter
