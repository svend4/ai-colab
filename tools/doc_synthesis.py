#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
# ==========================================
# [FILE ID CARD]
# ID: tools.doc_synthesis
# TYPE: active-script
# DOMAIN: core
# DEPTH_LEVEL: 1
# SUMMARY: Скрипт doc_synthesis.py. Описание сгенерировано автоматически.
# ==========================================
"""
"""
Document synthesis intake (D-017/D-018 friendly).

Reads a set of Markdown documents as variants, counts recurring architecture themes,
and renders a proposed synthesis scaffold:
- consensus: points present in many sources;
- near-consensus: similar points that still need wording/contract choices;
- divergences: known decision forks that must stay outside the mainline until resolved.

This tool is read-only unless --out is provided. It does not mark decisions accepted.

CLI:
    python tools/doc_synthesis.py candidates architecture-core
    python tools/doc_synthesis.py scan architecture-core
    python tools/doc_synthesis.py scan architecture-core --with-streams
    python tools/doc_synthesis.py scan architecture-core --out docs/architecture-core-documents-synthesis-2026-06-24.md
    python tools/doc_synthesis.py scan custom --out report.md file1.md file2.md ...
"""
import argparse
import json
import os
import re
import sys

from _ioutil import configure_output

configure_output()

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

ARCHITECTURE_CORE_FILES = [
    "docs/optimal-information-architecture-2026-06-24.md",
    "docs/workspace-pyramid-levels.md",
    "docs/top-layer-throughput-methodology.md",
    "docs/top-layer-command-groups.md",
    "docs/orchestration-architecture-2026-06-23.md",
    "docs/workflow-conveyor-policy.md",
    "docs/agent-capacity-methodology.md",
    "docs/agent-onboarding.md",
    "queues/outbox/2026-06-23-lagrange-nested-system.md",
    "queues/outbox/2026-06-23-lagrange-nested-system-continuation.md",
]

CANDIDATE_SCAN_DIRS = ["docs", "queues/outbox", "topics", "streams"]
CANDIDATE_SKIP_PARTS = {".git", "tmp-work", "node_modules", "__pycache__"}

THEMES = [
    {
        "id": "universal-core-portals",
        "label": "Универсальное ядро + тематические порталы",
        "keywords": ["универсаль", "ядро", "core", "портал", "portal", "плагин"],
        "claim": "Доменная специфика должна жить в порталах/плагинах, а не в ядре.",
    },
    {
        "id": "layered-pyramid",
        "label": "Слои L1/L2/L3/L4 и разделение чистовика/истории/хаоса",
        "keywords": ["l1", "l2", "l3", "l4", "пирами", "sandbox", "collab", "история", "чистов"],
        "claim": "Рабочая область должна разделять переносимое ядро, порталы, полилог/evidence и входной хаос.",
    },
    {
        "id": "top-layer-facade",
        "label": "Верхний слой как фасад/панель команд",
        "keywords": ["верхн", "top.py", "top layer", "кноп", "фасад", "панел", "command groups"],
        "claim": "Людям и агентам нужен один верхний фасад команд вместо памяти о десятках скриптов.",
    },
    {
        "id": "workflow-conveyor",
        "label": "Конвейер, workflow, fan-out/fan-in, drain before refill",
        "keywords": ["конвей", "workflow", "fan-out", "fan-in", "landed", "process", "refill", "drain", "бригада"],
        "claim": "Параллельные агенты полезны только при дисциплине intake -> verify -> synthesize -> integrate.",
    },
    {
        "id": "synthesis-divergence",
        "label": "Варианты не удалять: synthesis + divergence streams",
        "keywords": ["синтез", "разноглас", "divergence", "вариант", "streams", "консенсус", "кот"],
        "claim": "Повторы и варианты надо сравнивать, а спорные пункты выносить в отдельные divergence-документы.",
    },
    {
        "id": "evidence-assurance",
        "label": "Evidence, assurance, checks, applied instructions",
        "keywords": ["evidence", "assurance", "провер", "checks", "validate", "drift", "applied"],
        "claim": "Задачи и инструкции должны закрываться доказательно: checks, evidence, assurance, drift/validate.",
    },
    {
        "id": "parallel-worktree",
        "label": "Параллельная работа через worktree/merge-gate/commit-lock",
        "keywords": ["worktree", "merge_gate", "commit_lock", "index.lock", "stale", "selective", "foreign"],
        "claim": "При конкуренции за hot-файлы агенты уходят в worktree/streams, а общий main остаётся интеграционным слоем.",
    },
    {
        "id": "metadata-indexes",
        "label": "Метаданные, front-matter, индексы и карты навигации",
        "keywords": ["front-matter", "metadata", "метадан", "индекс", "index", "navigation", "навигац", "карточ"],
        "claim": "Каждый важный объект должен иметь ID/статус/слой/связи, а навигация должна генерироваться.",
    },
    {
        "id": "file-section-cards",
        "label": "File cards / section cards / semantic elevator",
        "keywords": ["file card", "section card", "визит", "карточ", "semantic", "шапк", "30 секунд"],
        "claim": "Файл должен быть читаем сверху вниз: карточка, краткая карта, детали, evidence, next.",
    },
    {
        "id": "safety-execute-off",
        "label": "Execute OFF, sandbox, human gate",
        "keywords": ["execute", "sandbox", "docker", "human", "gate", "preflight", "runner", "безопас"],
        "claim": "Исполнение внешнего кода остаётся закрытым до backend/human/preflight/decision gate.",
    },
    {
        "id": "recursive-self-improvement",
        "label": "Система работает над улучшением самой себя",
        "keywords": ["сам", "self", "recursive", "улучш", "friction", "advice", "activation"],
        "claim": "Повторяющиеся проблемы должны становиться playbook -> tool -> guard -> assurance.",
    },
]

DIVERGENCES = [
    {
        "id": "DVG-001",
        "title": "Физически переносить L3 в collab/ или оставить логическим слоем",
        "options": ["physical-collab", "logical-collab"],
        "why": "Физический перенос делает архитектуру чище, но создаёт noisy diff и риск сломанных ссылок.",
    },
    {
        "id": "DVG-002",
        "title": "Отдельная папка indexes/ или расширение существующих generated files",
        "options": ["new-indexes-folder", "extend-existing-index-json-status-board"],
        "why": "Новый слой улучшает понятность, но может дублировать уже работающий index.json/STATUS/board.",
    },
    {
        "id": "DVG-003",
        "title": "File cards обязательны для всех файлов или только для важных L1/L2/policy/manual",
        "options": ["all-significant-files", "l1-l2-policy-first"],
        "why": "Полное покрытие удобно машинам, но может перегрузить мелкие файлы и увеличить ритуал.",
    },
    {
        "id": "DVG-004",
        "title": "Portal-local tools в portals/<name>/tools/ или только общий tools/",
        "options": ["portal-local-tools", "shared-tools-only"],
        "why": "Локальные tools делают портал похожим на мини-приложение, но усложняют discovery и safety.",
    },
    {
        "id": "DVG-005",
        "title": "GUI/кнопки сейчас или сначала CLI-контракт top.py",
        "options": ["gui-now", "cli-contract-first"],
        "why": "GUI удобен людям, но без стабильного CLI-контракта быстро станет декоративной оболочкой.",
    },
    {
        "id": "DVG-006",
        "title": "Расширять число агентов или сначала усиливать synthesis/drain слой",
        "options": ["scale-agents", "scale-upper-layer-first"],
        "why": "Параллелизм производит больше результатов, но узкое место часто в проверке, синтезе и интеграции.",
    },
    {
        "id": "DVG-007",
        "title": "Runner core считать завершением execute-track или только компонентом blocked umbrella",
        "options": ["runner-done", "umbrella-blocked-until-human-backend"],
        "why": "Код runner существует, но без backend/human/scenario gate execute не должен считаться operationally accepted.",
    },
]

RATIFY_BUILD_ACTIONS = {
    "layered-pyramid": "Ratify the L1/L2/L3/L4 contract, then build folder/layer budget checks.",
    "top-layer-facade": "Ratify command-group vocabulary, then wire a top.py wrapper/bundle.",
    "workflow-conveyor": "Ratify intake/verify/synthesize/integrate wording, then connect to conveyor status/drain tasks.",
    "synthesis-divergence": "Ratify the split of consensus vs divergence, then integrate doc_synthesis with streams/top.py.",
    "evidence-assurance": "Ratify evidence-required closure, then enforce it in pipeline/assurance gates.",
    "parallel-worktree": "Ratify worktree/merge-gate triggers, then improve guard/top recommendations.",
    "metadata-indexes": "Ratify metadata/index scope, then build file/folder/command index checks.",
    "safety-execute-off": "Ratify execute boundary, then keep runner work behind human/backend gates.",
    "recursive-self-improvement": "Ratify advice activation path, then mine friction/advice into tools and guards.",
}

DETAIL_ACTIONS = {
    "universal-core-portals": "Clarify why accepted D-016 is under-propagated in newer architecture docs.",
    "file-section-cards": "Collect more variants, define minimum card schema, then decide coverage scope.",
}
QUESTION_RE = re.compile(r"\?|\b(Q-\d+|вопрос|что делать|как сделать|нужно ли)\b", re.IGNORECASE)
PROPOSAL_RE = re.compile(r"\b(нужно|предлага|следующ|должен|правило|рекоменд|лучше|стоит|надо|future)\b", re.IGNORECASE)


def relpath(path):
    return path.replace("\\", "/")


def repo_path(path):
    return os.path.join(ROOT, path.replace("/", os.sep))


def read_text(path):
    with open(repo_path(path), encoding="utf-8", errors="replace") as f:
        return f.read()


def compact_line(raw, limit=180):
    line = re.sub(r"\s+", " ", (raw or "").strip())
    if len(line) > limit:
        line = line[: limit - 3] + "..."
    return line


def keyword_refs(path, text, keywords, limit=3):
    refs = []
    seen_lines = set()
    lowered_keywords = [k.lower() for k in keywords if k]
    for lineno, raw in enumerate(text.splitlines(), 1):
        low = raw.lower()
        matched = [k for k in lowered_keywords if k in low]
        if not matched or lineno in seen_lines:
            continue
        seen_lines.add(lineno)
        refs.append({
            "ref": "%s:%d" % (relpath(path), lineno),
            "line": compact_line(raw),
            "keywords": matched[:4],
        })
        if len(refs) >= limit:
            break
    return refs


def refs_text(refs, limit=5):
    if not refs:
        return "—"
    items = []
    for ref in refs[:limit]:
        items.append("`%s`" % ref.get("ref", ""))
    if len(refs) > limit:
        items.append("+%d" % (len(refs) - limit))
    return ", ".join(items)


def topic_terms(topic):
    words = re.split(r"[^0-9A-Za-zА-Яа-я_-]+", topic or "")
    terms = [w.lower() for w in words if len(w) >= 3]
    if topic == "architecture-core":
        extra = []
        for theme in THEMES:
            extra.extend(theme["keywords"])
        extra.extend(["architecture", "архитект", "верхн", "агент", "pipeline", "workflow", "synthesis"])
        terms.extend(extra)
    return sorted(set(t for t in terms if t))


def iter_markdown_files():
    for base in CANDIDATE_SCAN_DIRS:
        start = repo_path(base)
        if not os.path.isdir(start):
            continue
        for dirpath, dirnames, filenames in os.walk(start):
            dirnames[:] = [d for d in dirnames if d not in CANDIDATE_SKIP_PARTS]
            for fn in filenames:
                if not fn.endswith(".md"):
                    continue
                yield relpath(os.path.relpath(os.path.join(dirpath, fn), ROOT))


def candidate_score(path, text, topic):
    low = strip_frontmatter(text).lower()
    matched = [term for term in topic_terms(topic) if term.lower() in low]
    score = len(set(matched))
    if topic == "architecture-core" and path in ARCHITECTURE_CORE_FILES:
        score += 100
    if path.endswith("-documents-synthesis-2026-06-24.md"):
        score -= 10
    return score, sorted(set(matched))[:16]


def find_candidates(topic, limit=25):
    rows = []
    selected = set(ARCHITECTURE_CORE_FILES if topic == "architecture-core" else [])
    keywords = topic_terms(topic)
    for path in sorted(iter_markdown_files()):
        try:
            text = read_text(path)
        except OSError:
            continue
        score, matched = candidate_score(path, text, topic)
        if score <= 0:
            continue
        rows.append({
            "path": path,
            "title": title_from_text(path, text),
            "score": score,
            "selected": path in selected,
            "matched": matched,
            "refs": keyword_refs(path, text, keywords, limit=3),
        })
    rows.sort(key=lambda r: (not r["selected"], -r["score"], r["path"]))
    return rows[:limit]


def render_candidates(topic, rows, as_json=False):
    if as_json:
        return json.dumps({"topic": topic, "candidates": rows}, ensure_ascii=False, indent=2)
    lines = [
        "# Document synthesis candidates: %s" % topic,
        "",
        "| # | Score | Selected | File | Title | Refs |",
        "|---:|---:|---|---|---|---|",
    ]
    for i, row in enumerate(rows, 1):
        selected = "yes" if row.get("selected") else "no"
        lines.append("| %d | %d | %s | `%s` | %s | %s |" % (
            i, row["score"], selected, row["path"], row["title"], refs_text(row.get("refs", []), limit=3)
        ))
    if not rows:
        lines.append("| — | — | — | — | No candidates found | — |")
    return "\n".join(lines).rstrip() + "\n"

def strip_frontmatter(text):
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) == 3:
            return parts[2]
    return text


def title_from_text(path, text):
    for line in text.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return os.path.basename(path)


def snippets(text, pattern, limit=5):
    out = []
    for raw in strip_frontmatter(text).splitlines():
        line = raw.strip()
        if not line or line.startswith("---") or line.startswith("```"):
            continue
        if pattern.search(line):
            line = re.sub(r"\s+", " ", line)
            if len(line) > 220:
                line = line[:217] + "..."
            out.append(line)
        if len(out) >= limit:
            break
    return out


def has_theme(text, theme):
    low = text.lower()
    return any(k.lower() in low for k in theme["keywords"])


def scan(files):
    docs = []
    for path in files:
        text = read_text(path)
        docs.append({
            "path": relpath(path),
            "title": title_from_text(path, text),
            "text": text,
            "questions": snippets(text, QUESTION_RE, limit=6),
            "proposals": snippets(text, PROPOSAL_RE, limit=8),
        })
    theme_hits = []
    for theme in THEMES:
        hits = []
        refs = []
        for doc in docs:
            found = keyword_refs(doc["path"], doc["text"], theme["keywords"], limit=3)
            if found:
                hits.append(doc["path"])
                refs.extend(found)
        theme_hits.append({**theme, "count": len(hits), "sources": hits, "refs": refs})
    return docs, theme_hits


def classify(theme_hits, total):
    consensus_threshold = max(2, int(total * 0.6 + 0.999))
    near_threshold = max(2, int(total * 0.3 + 0.999))
    consensus = [t for t in theme_hits if t["count"] >= consensus_threshold]
    near = [t for t in theme_hits if near_threshold <= t["count"] < consensus_threshold]
    minority = [t for t in theme_hits if 0 < t["count"] < near_threshold]
    return consensus, near, minority

def build_lanes(consensus, near, minority, total):
    """Return two cauldron work lanes: ratify/build vs divergence/detail."""
    ratify_build = []
    for item in sorted(consensus, key=lambda x: (-x["count"], x["id"])):
        ratify_build.append({
            "lane": "ratify-build",
            "id": item["id"],
            "label": item["label"],
            "evidence": "%d/%d docs" % (item["count"], total),
            "claim": item["claim"],
            "next": RATIFY_BUILD_ACTIONS.get(item["id"], "Ratify wording, then turn it into an implementation task."),
            "sources": item["sources"],
            "refs": item.get("refs", [])[:8],
        })

    divergence_detail = []
    for item in sorted(near + minority, key=lambda x: (-x["count"], x["id"])):
        divergence_detail.append({
            "lane": "divergence-detail",
            "id": item["id"],
            "label": item["label"],
            "evidence": "%d/%d docs" % (item["count"], total),
            "claim": item["claim"],
            "next": DETAIL_ACTIONS.get(item["id"], "Collect more variants, clarify wording, then retry synthesis."),
            "sources": item["sources"],
            "refs": item.get("refs", [])[:8],
        })
    for dvg in DIVERGENCES:
        divergence_detail.append({
            "lane": "divergence-detail",
            "id": dvg["id"],
            "label": dvg["title"],
            "evidence": "open divergence",
            "claim": dvg["why"],
            "next": "Add agent/human positions in streams/<topic>/divergence.md until a ratifiable option exists.",
            "options": dvg["options"],
        })
    return {"ratify-build": ratify_build, "divergence-detail": divergence_detail}

def stream_path(topic):
    safe = re.sub(r"[^0-9A-Za-zА-Яа-я_-]+", "-", topic).strip("-") or "topic"
    return "streams/%s" % safe


def render_stream_readme(topic, files, lanes):
    return "\n".join([
        "---",
        "topic: %s" % topic,
        "type: stream-index",
        "status: proposed",
        "agent: codex",
        "date: 2026-06-24",
        "---",
        "",
        "# %s stream" % topic,
        "",
        "Generated by `python tools/doc_synthesis.py scan %s --with-streams`." % topic,
        "",
        "## Corpus",
        "",
        *["- `%s`" % f for f in files],
        "",
        "## Lanes",
        "",
        "- `ratify-build`: %d" % len(lanes.get("ratify-build", [])),
        "- `divergence-detail`: %d" % len(lanes.get("divergence-detail", [])),
        "",
        "Rule: do not erase existing divergence positions. Add new agent/human positions under explicit IDs.",
        "",
    ])


def render_divergence_scaffold(topic, lanes):
    lines = [
        "---",
        "topic: %s" % topic,
        "type: divergence-scaffold",
        "status: proposed",
        "agent: codex",
        "date: 2026-06-24",
        "---",
        "",
        "# Divergence scaffold: %s" % topic,
        "",
        "Generated scaffold. If `divergence.md` already exists, merge manually; do not overwrite other agents.",
        "",
    ]
    for item in lanes.get("divergence-detail", []):
        lines.extend([
            "## %s — %s" % (item.get("id"), item.get("label")),
            "",
            "Evidence: %s" % item.get("evidence", "—"),
            "",
            "Refs: %s" % refs_text(item.get("refs", [])),
            "",
            "Claim: %s" % item.get("claim", ""),
            "",
            "Next: %s" % item.get("next", ""),
            "",
            "Позиции агентов/людей:",
            "",
            "- (добавить позицию)",
            "",
        ])
    return "\n".join(lines).rstrip() + "\n"


def write_streams(topic, files):
    docs, theme_hits = scan(files)
    consensus, near, minority = classify(theme_hits, len(docs))
    lanes = build_lanes(consensus, near, minority, len(docs))
    base = stream_path(topic)
    base_abs = repo_path(base)
    os.makedirs(base_abs, exist_ok=True)
    written = []

    targets = [
        ("README.md", "README.generated.md", render_stream_readme(topic, files, lanes)),
        ("divergence.md", "divergence.generated.md", render_divergence_scaffold(topic, lanes)),
    ]
    for primary, fallback, body in targets:
        primary_abs = os.path.join(base_abs, primary)
        if os.path.exists(primary_abs):
            dest_abs = os.path.join(base_abs, fallback)
        else:
            dest_abs = primary_abs
        with open(dest_abs, "w", encoding="utf-8", newline="\n") as f:
            f.write(body)
        written.append(relpath(os.path.relpath(dest_abs, ROOT)))
    return written

def render(topic, files, as_json=False):
    docs, theme_hits = scan(files)
    consensus, near, minority = classify(theme_hits, len(docs))
    lanes = build_lanes(consensus, near, minority, len(docs))
    if as_json:
        return json.dumps({
            "topic": topic,
            "documents": [{"path": d["path"], "title": d["title"]} for d in docs],
            "themes": theme_hits,
            "lanes": lanes,
            "divergences": DIVERGENCES,
        }, ensure_ascii=False, indent=2)

    lines = []
    lines.extend([
        "---",
        f"id: synthesis-{topic}-2026-06-24",
        f"topic: {topic}",
        "type: document-synthesis",
        "status: proposed",
        "agent: codex",
        "date: 2026-06-24",
        f"documents: {len(docs)}",
        "---",
        "",
        f"# Синтез документов: {topic}",
        "",
        "> proposed — это материал для котла по D-017/D-018. Документ выделяет общий слой, похожие варианты и разногласия, но не принимает accepted-решение.",
        "",
        "## 00. Corpus",
        "",
        "| # | Файл | Заголовок |",
        "|---:|---|---|",
    ])
    for i, doc in enumerate(docs, 1):
        lines.append(f"| {i} | `{doc['path']}` | {doc['title']} |")

    lines.extend(["", "## 01. Две рабочие полосы котла", ""])
    lines.append("### 01A. ratify-build — уже достаточно сходится, нужно ратифицировать и строить")
    lines.append("")
    lines.append("| ID | Evidence | Refs | Что делать дальше |")
    lines.append("|---|---|---|---|")
    for item in lanes["ratify-build"]:
        lines.append(f"| {item['id']} | {item['evidence']} | {refs_text(item.get('refs', []))} | {item['next']} |")
    if not lanes["ratify-build"]:
        lines.append("| — | — | — | Нет consensus-ready пунктов |")
    lines.append("")
    lines.append("### 01B. divergence-detail — ещё не готово, нужно детализация/варианты/доказательства")
    lines.append("")
    lines.append("| ID | Evidence | Refs | Что делать дальше |")
    lines.append("|---|---|---|---|")
    for item in lanes["divergence-detail"]:
        lines.append(f"| {item['id']} | {item['evidence']} | {refs_text(item.get('refs', []))} | {item['next']} |")
    if not lanes["divergence-detail"]:
        lines.append("| — | — | — | Нет открытых detail/divergence пунктов |")
    lines.append("")
    lines.append("Пропорция работы выбирается агентом/человеком: 50/50 для балансировки, 70/30 если нужно быстрее строить consensus-ready, 30/70 если главная ценность сейчас в детализации разногласий.")

    lines.extend(["", "## 02. Верхний слой: полный или сильный консенсус", ""])
    if not consensus:
        lines.append("- (нет тем, найденных в большинстве документов)")
    for item in consensus:
        lines.append(f"### {item['id']} — {item['label']} ({item['count']}/{len(docs)})")
        lines.append(f"- Общее утверждение: {item['claim']}")
        lines.append("- Источники: " + ", ".join(f"`{s}`" for s in item["sources"][:8]))
        lines.append("- Evidence refs: " + refs_text(item.get("refs", [])))
        if len(item["sources"]) > 8:
            lines.append(f"- Ещё источников: {len(item['sources']) - 8}")
        lines.append("")

    lines.extend(["## 03. Средний слой: похожие пункты, но требуется нормализация", ""])
    if not near:
        lines.append("- (нет near-consensus тем)")
    for item in near:
        lines.append(f"### {item['id']} — {item['label']} ({item['count']}/{len(docs)})")
        lines.append(f"- Смысл: {item['claim']}")
        lines.append("- Почему не верхний слой: тема встречается не во всех вариантах или требует выбора формата/границ.")
        lines.append("- Источники: " + ", ".join(f"`{s}`" for s in item["sources"][:8]))
        lines.append("- Evidence refs: " + refs_text(item.get("refs", [])))
        lines.append("")

    lines.extend(["## 04. Нижний слой: одиночные полезные идеи", ""])
    if not minority:
        lines.append("- (нет одиночных тем)")
    for item in minority:
        lines.append(f"- **{item['label']}** ({item['count']}/{len(docs)}): {item['claim']} Источники: " + ", ".join(f"`{s}`" for s in item["sources"][:4]))

    lines.extend(["", "## 05. Разногласия для streams/architecture-core", ""])
    lines.append("| ID | Спор | Варианты | Почему важно |")
    lines.append("|---|---|---|---|")
    for dvg in DIVERGENCES:
        lines.append(f"| {dvg['id']} | {dvg['title']} | {', '.join(dvg['options'])} | {dvg['why']} |")

    lines.extend(["", "## 06. Вопросы, найденные в корпусе", ""])
    q_count = 0
    for doc in docs:
        if doc["questions"]:
            lines.append(f"### `{doc['path']}`")
            for q in doc["questions"][:4]:
                q_count += 1
                lines.append(f"- {q}")
            lines.append("")
    if q_count == 0:
        lines.append("- Явных вопросительных строк не найдено; вопросы выражены как proposed/next sections.")

    lines.extend(["## 07. Предложения, найденные в корпусе", ""])
    p_count = 0
    for doc in docs:
        props = doc["proposals"][:5]
        if props:
            lines.append(f"### `{doc['path']}`")
            for p in props:
                p_count += 1
                lines.append(f"- {p}")
            lines.append("")
    if p_count == 0:
        lines.append("- Явных предложений не найдено.")

    lines.extend([
        "## 08. Что делать дальше",
        "",
        "1. Перенести пункты из раздела 02 в clean architecture mainline или portal/core manuals.",
        "2. Пункты из раздела 03 превратить в конкретные tasks: file-card standard, indexes policy, portal v2 contract, top verify bundle.",
        "3. Пункты из раздела 05 держать в `streams/architecture-core/divergence.md` до выбора человеком/котлом.",
        "4. Не помечать этот синтез accepted: он proposed и требует review другими агентами/людьми.",
        "",
        "## 09. Counts",
        "",
        f"- Documents scanned: {len(docs)}",
        f"- Consensus themes: {len(consensus)}",
        f"- Near-consensus themes: {len(near)}",
        f"- Minority useful themes: {len(minority)}",
        f"- Divergences listed: {len(DIVERGENCES)}",
        f"- Question snippets: {q_count}",
        f"- Proposal snippets: {p_count}",
        "",
    ])
    return "\n".join(lines).rstrip() + "\n"


def resolve_files(topic, positional):
    if topic == "architecture-core" and not positional:
        return ARCHITECTURE_CORE_FILES
    if not positional:
        raise SystemExit("custom scan requires at least one file")
    return [relpath(p) for p in positional]


def main():
    parser = argparse.ArgumentParser(description="Synthesize multiple markdown documents into consensus/near/divergence scaffold.")
    sub = parser.add_subparsers(dest="cmd")

    p = sub.add_parser("candidates", help="find likely documents for a synthesis topic")
    p.add_argument("topic")
    p.add_argument("--limit", type=int, default=25)
    p.add_argument("--json", action="store_true")

    p = sub.add_parser("scan")
    p.add_argument("topic")
    p.add_argument("files", nargs="*")
    p.add_argument("--out")
    p.add_argument("--json", action="store_true")
    p.add_argument("--with-streams", action="store_true")
    args = parser.parse_args()

    if args.cmd == "candidates":
        print(render_candidates(args.topic, find_candidates(args.topic, args.limit), as_json=args.json), end="")
        return 0

    if args.cmd != "scan":
        parser.print_help()
        return 2

    files = resolve_files(args.topic, args.files)
    missing = [f for f in files if not os.path.exists(repo_path(f))]
    if missing:
        print("Missing files:")
        for m in missing:
            print("- " + m)
        return 1

    text = render(args.topic, files, as_json=args.json)
    if args.out:
        dest = args.out if os.path.isabs(args.out) else repo_path(args.out)
        dest_r = os.path.realpath(dest)
        if os.path.commonpath([dest_r, ROOT]) != os.path.realpath(ROOT):
            print("Refusing to write outside repo: %s" % args.out)
            return 1
        os.makedirs(os.path.dirname(dest_r), exist_ok=True)
        with open(dest_r, "w", encoding="utf-8", newline="\n") as f:
            f.write(text)
        print("Wrote " + os.path.relpath(dest_r, ROOT).replace("\\", "/"))
    else:
        print(text, end="")

    if args.with_streams:
        for path in write_streams(args.topic, files):
            print("Wrote " + path)
    return 0


if __name__ == "__main__":
    sys.exit(main())