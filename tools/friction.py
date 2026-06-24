#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ==========================================
# [FILE ID CARD]
# ID: tools.friction
# TYPE: active-script
# DOMAIN: core.diagnostics
# DEPTH_LEVEL: 1
# SUMMARY: Диагностирует повторяющиеся проблемы репозитория и печатает рецепты F-XXX.
# ==========================================
"""
Friction diagnostics (T-150) — read-mostly detector for repeated repo problems.

This tool does not auto-fix the repository. It maps visible symptoms to the
F-XXX ledger entries, prints evidence, and points humans/agents to the stable
recipe. The only write done by default is a short tmp-work probe, which is
created and removed to check whether the controlled project temp area works.

CLI:
    python tools/friction.py status [--json] [--strict] [--no-temp-probe]
    python tools/friction.py recipe F-007
    python tools/friction.py list [--json]
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from _ioutil import configure_output
import tempfile
import time

ROOT = os.environ.get("COLLAB_ROOT") or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PY = sys.executable

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ownership  # общий классификатор владения dirty-файлами (T-153, синтез подсистем)

VOLATILE = [
    "LIVE.md",
    "PIPELINE.md",
    "logs/heartbeat.json",
    "logs/pipeline.json",
]

GENERATED_SHARED = [
    "TASKS.md",
    "QUESTIONS.md",
    "DECISIONS.md",
    "STATUS.md",
    "board.md",
    "index.json",
    "drivers/index.json",
    "drivers/CATALOG.md",
]

REGISTRY = [
    {
        "id": "F-001",
        "name": "apply_patch Windows sandbox fallback",
        "symptom": "apply_patch cannot prepare the Windows restricted-token sandbox wrapper.",
        "recipe": [
            "Explain that apply_patch is unavailable in this environment.",
            "Write only inside the workspace with UTF-8 without BOM.",
            "Do not use fallback writes for deleting or moving another agent's files.",
        ],
        "docs": ["docs/friction-ledger.md", "docs/friction-playbook.md"],
        "aliases": ["apply-patch", "sandbox-fallback"],
    },
    {
        "id": "F-002",
        "name": "PowerShell UTF-8/mojibake",
        "symptom": "Russian Markdown appears as mojibake in PowerShell output.",
        "recipe": [
            "Run chcp 65001.",
            "Set Console InputEncoding/OutputEncoding to UTF-8.",
            "Read files with Get-Content -Encoding UTF8 instead of repairing valid files.",
        ],
        "docs": ["docs/powershell-utf8-output.md", "docs/friction-playbook.md"],
        "aliases": ["encoding", "mojibake", "utf8"],
    },
    {
        "id": "F-003",
        "name": "Shell/Python runtime hangs",
        "symptom": "PowerShell, CMD, Python, or MCP stdio commands hang or fail in the Windows runtime.",
        "recipe": [
            "Use short commands and timeout wrappers.",
            "Check python --version and a tiny python -c smoke before larger tests.",
            "Use docs/runtime-recovery-playbook.md if the minimal smoke fails.",
        ],
        "docs": ["docs/runtime-recovery-playbook.md", "docs/runtime-diagnostics.md"],
        "aliases": ["runtime", "hang", "python"],
    },
    {
        "id": "F-004",
        "name": "TEMP PermissionError",
        "symptom": "%TEMP% or tempfile creates a directory that Python cannot write into.",
        "recipe": [
            "Use drivers/test_tmp.py / project tmp-work for hermetic tests.",
            "Do not rely on tempfile.mkdtemp() / TemporaryDirectory() in this Windows runtime unless probed.",
            "Do not close runtime acceptance until nested temp-directory write is tested.",
        ],
        "docs": ["docs/friction-ledger.md", "docs/files-mcp-acceptance-blocked-2026-06-21.md"],
        "aliases": ["temp", "permissionerror", "tmp-work"],
    },
    {
        "id": "F-005",
        "name": "Git index.lock / commit serialization",
        "symptom": "Git stage/commit collides on .git/index.lock or sandbox blocks .git writes.",
        "recipe": [
            "Run python tools/commit_lock.py status.",
            "Acquire commit_lock before generate + explicit git add + git commit.",
            "Release the lock after commit or after aborting the commit attempt.",
        ],
        "docs": ["docs/commit-stream-policy.md", "tools/commit_lock.py"],
        "aliases": ["git-lock", "index.lock", "commit-lock"],
    },
    {
        "id": "F-006",
        "name": "Foreign half-done work in shared tree",
        "symptom": "The shared working tree contains files not owned by the current task.",
        "recipe": [
            "Never use git add -A in a dirty shared tree.",
            "Stage only explicit files that belong to the current task.",
            "If the tree is hot or contested, switch to Level 1 worktree by D-022.",
        ],
        "docs": ["docs/parallel-work-policy.md", "docs/friction-ledger.md"],
        "aliases": ["half-done", "dirty", "foreign"],
    },
    {
        "id": "F-007",
        "name": "Stale generated indexes",
        "symptom": "TASKS/QUESTIONS/DECISIONS/board/index derived files are stale.",
        "recipe": [
            "Find whether stale output is caused by your own source files or another agent's half-done files.",
            "If it is yours, run python tools/generate.py and include source + generated indexes together.",
            "If it is foreign, do not commit a mixed generated index; use Level 1 worktree or wait for integration.",
        ],
        "docs": ["docs/friction-ledger.md", "tools/generate.py"],
        "aliases": ["stale-index", "generate", "generated"],
    },
    {
        "id": "F-008",
        "name": "Volatile runtime snapshots in commit scope",
        "symptom": "LIVE.md, PIPELINE.md, logs/heartbeat.json, or logs/pipeline.json show up in normal work.",
        "recipe": [
            "Read volatile files as live views, but do not stage them in ordinary commits.",
            "Commit source code/docs/tests that change snapshot behavior, not regenerated snapshot output.",
            "Use tools/test_volatile.py when changing volatile policy.",
        ],
        "docs": ["docs/t148-volatile-runtime-result-2026-06-22.md", "tools/test_volatile.py"],
        "aliases": ["volatile", "live", "pipeline-snapshot"],
    },
    {
        "id": "F-009",
        "name": "Placeholder tasks",
        "symptom": "Reserved task files remain todo and appear in pipeline state.",
        "recipe": [
            "Fill a reserved task before claim, or retire it as a placeholder with a real explanation.",
            "Do not let pipeline.py next hand placeholder tasks to agents.",
        ],
        "docs": ["docs/pipeline-placeholder-gating.md", "tasks/T-067.md"],
        "aliases": ["placeholder"],
    },
    {
        "id": "F-010",
        "name": "Doing without active claim",
        "symptom": "A task is marked doing but no fresh queue claim exists.",
        "recipe": [
            "Run python tools/pipeline.py status and python tools/pipeline.py mine <agent>.",
            "Do not silently close another agent's doing task.",
            "Use reconcile/outbox/question if the orphan blocks work.",
        ],
        "docs": ["docs/pipeline-orphan-doing-detection.md", "docs/stale-work-cleanup-policy-2026-06-21.md"],
        "aliases": ["orphan", "doing-without-claim", "claim"],
    },
    {
        "id": "F-011",
        "name": "Documentation/index drift",
        "symptom": "Docs, generated indexes, driver catalog, or capability catalog disagree with current facts.",
        "recipe": [
            "Run python tools/generate.py --check, python tools/validate.py, and python tools/drift_check.py.",
            "Fix the source of truth, then regenerate derived views.",
            "If drift is caused by foreign work, avoid committing mixed indexes.",
        ],
        "docs": ["tools/drift_check.py", "docs/friction-playbook.md"],
        "aliases": ["drift", "docs-drift"],
    },
    {
        "id": "F-012",
        "name": "External code/svend4 sandbox boundary",
        "symptom": "External source is requested, but no read-only intake source or execute sandbox exists.",
        "recipe": [
            "Register the source through sandbox/ intake; do not run external code directly.",
            "Keep execute off until docs/execute-sandbox-preflight.md and an accepted decision allow it.",
            "Treat svend4 as one example of generic external-source intake, not as a special exception.",
        ],
        "docs": ["docs/external-code-sandbox.md", "docs/execute-sandbox-preflight.md", "tools/sandbox.py"],
        "aliases": ["svend4", "external", "sandbox"],
    },
    {
        "id": "F-013",
        "name": "Streams without adoption",
        "symptom": "Semi-commit streams accumulate without status, related links, or adoption/rejection.",
        "recipe": [
            "Run python tools/stream.py check.",
            "Add related task/question/decision and adoption conditions to live streams.",
            "Close stale streams as adopted, superseded, rejected, or archived.",
        ],
        "docs": ["docs/commit-stream-policy.md", "streams/README.md", "tools/stream.py"],
        "aliases": ["stream", "adoption"],
    },
    {
        "id": "F-014",
        "name": "Too many separate commands",
        "symptom": "Humans/agents must remember many low-level commands for one workflow.",
        "recipe": [
            "Prefer top-level buttons such as python tools/top.py status, health, work-mode, friction.",
            "Only create a new wrapper after the same manual sequence repeats.",
        ],
        "docs": ["docs/top-layer-command-groups.md", "tools/top.py"],
        "aliases": ["too-many-commands", "top"],
    },
    {
        "id": "F-015",
        "name": "State changes between check and commit",
        "symptom": "Another agent changes files after preflight but before staging/commit.",
        "recipe": [
            "Run git status again immediately before staging.",
            "Stage explicit files only.",
            "Use commit_lock for the commit window; use worktree for contested work.",
        ],
        "docs": ["docs/parallel-work-policy.md", "docs/friction-ledger.md"],
        "aliases": ["precommit-race", "check-commit"],
    },
    {
        "id": "F-016",
        "name": "pipeline.py next takes the wrong ready task",
        "symptom": "An agent wants a specific task but next claims a different high-priority ready item.",
        "recipe": [
            "If you need a specific task, use pipeline.py claim <agent> <T-id> or top.py take <agent> <T-id>.",
            "If the T-id is not ready, targeted claim returns an error and does not take another task.",
            "If an old next-based mistake happens, release only your own mistaken claim.",
        ],
        "docs": ["docs/friction-complaints-suggestions.md"],
        "aliases": ["wrong-task", "targeted-claim"],
    },
    {
        "id": "F-017",
        "name": "Repeat counter is approximate",
        "symptom": "The ledger knows that a problem repeats, but counts are still human estimates.",
        "recipe": [
            "Record repeat evidence in docs/friction-complaints-suggestions.md.",
            "Promote to logs/friction.jsonl or tools/friction.py note only after the format stabilizes.",
        ],
        "docs": ["docs/friction-ledger.md", "docs/friction-complaints-suggestions.md"],
        "aliases": ["repeat-counter", "ledger-count"],
    },
    {
        "id": "F-018",
        "name": "Skill/docs drift",
        "symptom": "A project skill points to stale instructions or misses the canonical docs/tool.",
        "recipe": [
            "Keep skills thin; details stay in docs/friction-*.",
            "When adding a friction tool, update the skill first move and docs links.",
            "Later, validate skill-to-doc links automatically.",
        ],
        "docs": ["skills/repo-friction-playbook/SKILL.md", "docs/friction-ledger.md"],
        "aliases": ["skill-drift", "skill"],
    },
    {
        "id": "F-019",
        "name": "Skill metadata UTF-8/YAML frontmatter",
        "symptom": "Skill metadata generation fails on UTF-8 decoding or YAML descriptions with ':' characters.",
        "recipe": [
            "Run metadata scripts with PYTHONUTF8=1 when needed.",
            "Use YAML block scalars for long descriptions containing punctuation.",
        ],
        "docs": ["docs/friction-complaints-suggestions.md", "skills/repo-friction-playbook/SKILL.md"],
        "aliases": ["yaml", "frontmatter", "skill-metadata"],
    },
    {
        "id": "F-020",
        "name": "Gate-poison: общий validate-гейт КРАСНЫЙ",
        "symptom": "tools/validate.py: ERROR=N>0 (часто чужая half-done задача: done-карточка без артефакта, битая topic-ссылка, дубль id) — pre-commit hook блокирует коммиты ВСЕМ (инцидент T-150).",
        "recipe": [
            "Запусти python tools/validate.py и прочитай ERROR: строки — найди, ЧТО/КТО отравил гейт.",
            "Если источник — ТВОЙ claim, почини так, чтобы validate вернул ERROR=0; если чужой/unknown — не жди: эскалируй в Уровень-1 worktree от ЧИСТОЙ базы (python tools/cohort.py guard для вердикта).",
            "Никогда не правь/не удаляй чужой gate-source, чтобы озеленить validate, — это прячет отраву, а не чистит её.",
        ],
        "docs": ["topics/gate-poison-situation-2026-06-22.md", "docs/parallel-work-policy.md", "tools/cohort.py"],
        "aliases": ["gate-poison", "poison", "validate-error", "poisoned-gate"],
    },
    {
        "id": "F-021",
        "name": "next_id reservation collision",
        "symptom": "next_id.py creates a placeholder atomically, but a later parallel stream can still fill or overwrite the numeric id as its own work item.",
        "recipe": [
            "Create new Q/T/D ids with python tools/next_id.py <kind> --agent <agent> and save the printed reservation_token.",
            "Before filling, run python tools/next_id.py check <ID> --agent <agent> --token <token>.",
            "Prefer python tools/next_id.py fill <ID> --agent <agent> --token <token> --from <prepared.md> so id and reservation are checked before atomic replacement.",
            "If a collision is detected, do not rewrite the other task; leave an outbox collision report and continue under a fresh reservation.",
        ],
        "docs": ["queues/outbox/2026-06-24-t223-id-collision.md", "queues/outbox/2026-06-24-t226-id-collision.md", "tools/next_id.py"],
        "aliases": ["id-collision", "next-id", "reservation-token", "task-id-race"],
    },
]

BY_ID = {item["id"]: item for item in REGISTRY}
ALIASES = {}
for item in REGISTRY:
    ALIASES[item["id"].lower()] = item["id"]
    for alias in item.get("aliases", []):
        ALIASES[alias.lower()] = item["id"]

configure_output()

def rel(path):
    return path.replace("\\", "/")

def run_cmd(*args, timeout=30):
    try:
        p = subprocess.run(
            list(args),
            cwd=ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            stdin=subprocess.DEVNULL,
            timeout=timeout,
        )
        return {"rc": p.returncode, "out": (p.stdout or "") + (p.stderr or ""), "timeout": False}
    except subprocess.TimeoutExpired as exc:
        out = ""
        if exc.stdout:
            out += str(exc.stdout)
        if exc.stderr:
            out += str(exc.stderr)
        return {"rc": 124, "out": out, "timeout": True}

def first_lines(text, limit=4):
    lines = [line.strip() for line in (text or "").splitlines() if line.strip()]
    return lines[:limit]

def make_check(fid, status, summary, evidence=None, recipe_hint=None):
    item = BY_ID[fid]
    return {
        "id": fid,
        "name": item["name"],
        "status": status,
        "summary": summary,
        "evidence": evidence or [],
        "recipe": recipe_hint or (item["recipe"][0] if item.get("recipe") else ""),
        "docs": item.get("docs", []),
    }

def normalize_status_path(line):
    path = line[3:].strip() if len(line) >= 3 else line.strip()
    if " -> " in path:
        path = path.split(" -> ", 1)[1]
    return rel(path.strip('"'))

def git_status_paths(status_text):
    rows = []
    for raw in (status_text or "").splitlines():
        if not raw.strip():
            continue
        rows.append({"raw": raw, "path": normalize_status_path(raw)})
    return rows

def path_matches(path, candidates):
    p = rel(path)
    return p in candidates or any(p.startswith(c.rstrip("/") + "/") for c in candidates)

def check_git_status(status_text, agent=None, task_files=None):
    rows = git_status_paths(status_text)
    dirty = [r["raw"] for r in rows]
    nonvolatile = [r["raw"] for r in rows if not path_matches(r["path"], VOLATILE)]
    volatile = [r["raw"] for r in rows if path_matches(r["path"], VOLATILE)]
    generated = [r["raw"] for r in rows if path_matches(r["path"], GENERATED_SHARED)]
    # ownership-aware (T-153): отделить ЧУЖИЕ заявленные source-файлы от своих/неизвестных.
    own = ownership.summary([r["path"] for r in rows], agent=agent, task_files=task_files)
    foreign = own["by"]["foreign"]

    checks = []
    if foreign:
        checks.append(make_check(
            "F-006", "warn", "shared tree has FOREIGN uncommitted source (another agent's claimed work)",
            evidence=foreign[:8],
            recipe_hint="Foreign half-done — use Level 1 worktree (flow.py start <agent> <task> --worktree); do not couple via shared index.",
        ))
    elif nonvolatile:
        checks.append(make_check(
            "F-006", "warn", "shared tree has non-volatile uncommitted files (yours/unknown, not foreign)",
            evidence=nonvolatile[:8],
            recipe_hint="Selective-add (cohort ship); Level 0 ok if files are yours/generated and not foreign.",
        ))
    else:
        checks.append(make_check("F-006", "ok", "no non-volatile dirty files visible", evidence=dirty[:4]))

    if volatile:
        checks.append(make_check(
            "F-008", "warn", "volatile runtime snapshots are dirty",
            evidence=volatile[:8],
            recipe_hint="Read them as live state; do not stage them in an ordinary commit.",
        ))
    else:
        checks.append(make_check("F-008", "ok", "volatile runtime snapshots are not dirty"))

    if generated:
        checks.append(make_check(
            "F-015", "warn", "generated/shared files are currently dirty",
            evidence=generated[:8],
            recipe_hint="Re-check git status immediately before staging and use explicit file list.",
        ))
    elif dirty:
        checks.append(make_check(
            "F-015", "warn", "working tree changed; re-check before commit",
            evidence=dirty[:8],
            recipe_hint="Run git status again immediately before staging.",
        ))
    else:
        checks.append(make_check("F-015", "ok", "working tree is clean at this check"))
    return checks

def check_volatile_tracking(tracked_out, ignore_text):
    tracked = [rel(line.strip()) for line in (tracked_out or "").splitlines() if line.strip()]
    missing_ignore = [p for p in VOLATILE if p not in (ignore_text or "")]
    evidence = []
    if tracked:
        evidence.append("tracked: " + ", ".join(tracked))
    if missing_ignore:
        evidence.append("missing .gitignore: " + ", ".join(missing_ignore))
    if tracked:
        return make_check("F-008", "fail", "volatile files are still tracked by Git", evidence=evidence)
    if missing_ignore:
        return make_check("F-008", "warn", "volatile files are not fully listed in .gitignore", evidence=evidence)
    return make_check("F-008", "ok", "volatile files are untracked and ignored")

def check_generate(rc, out):
    if rc != 0 or "STALE" in (out or ""):
        return make_check(
            "F-007", "warn", "generated indexes appear stale or generator check failed",
            evidence=first_lines(out, 8),
            recipe_hint="Find the source; run generate.py only for your own source changes, not for foreign half-done work.",
        )
    return make_check("F-007", "ok", "generated indexes are current")

def check_commit_lock(out):
    text = out or ""
    if "свободен" in text or "free" in text.lower():
        return make_check("F-005", "ok", "commit-lock is free", evidence=first_lines(text, 2))
    if "протух" in text or "stale" in text.lower():
        return make_check("F-005", "warn", "commit-lock appears stale", evidence=first_lines(text, 4))
    return make_check("F-005", "warn", "commit-lock may be held", evidence=first_lines(text, 4))

def check_pipeline(out):
    text = out or ""
    checks = []
    if "placeholder task" in text:
        checks.append(make_check("F-009", "warn", "pipeline reports placeholder tasks", evidence=first_lines(text, 10)))
    else:
        checks.append(make_check("F-009", "ok", "pipeline does not report placeholder tasks"))
    if "doing without active claim" in text or "doing with stale claim" in text:
        checks.append(make_check("F-010", "warn", "pipeline reports doing without active/fresh claim", evidence=first_lines(text, 12)))
    else:
        checks.append(make_check("F-010", "ok", "no orphan doing task found in pipeline output"))
    return checks

def check_drift(rc, out):
    text = out or ""
    if rc != 0 or "ДРЕЙФ" in text or "STALE" in text:
        return make_check("F-011", "warn", "drift_check reports drift or failed", evidence=first_lines(text, 8))
    return make_check("F-011", "ok", "drift_check reports no drift", evidence=first_lines(text, 2))

def check_gate_poison(rc, out):
    """F-020: общий validate-гейт КРАСНЫЙ (ERROR=N>0) — pre-commit блокирует коммиты всем.

    Read-only детектор (тот же контракт ERROR=(\\d+), что cohort.py guard). Симптом T-150:
    чужая half-done задача отравляет общий gate. Делает рабочим cross-link cohort→friction.
    """
    text = out or ""
    m = re.search(r"ERROR=(\d+)", text)
    errs = [ln.strip()[:90] for ln in text.splitlines() if ln.strip().startswith("ERROR:")][:3]
    if (m and int(m.group(1)) > 0) or rc not in (0, None):
        return make_check(
            "F-020", "warn", "общий validate-гейт КРАСНЫЙ (коммиты заблокированы всем)",
            evidence=errs or first_lines(text, 4),
            recipe_hint="Чужая half-done? эскалируй в L1 worktree от чистой базы (cohort.py guard); слей, когда гейт очистится.",
        )
    return make_check("F-020", "ok", "общий validate-гейт зелёный")

def check_stream(rc, out):
    text = out or ""
    if rc != 0:
        return make_check("F-013", "warn", "stream lifecycle check reports stale/broken streams", evidence=first_lines(text, 8))
    return make_check("F-013", "ok", "stream lifecycle check is clean", evidence=first_lines(text, 2))

def check_temp_probe(root=ROOT):
    base = os.path.join(root, "tmp-work")
    probe_dir = os.path.join(base, "friction-probe-%d-%d" % (int(time.time()), os.getpid()))
    probe_file = os.path.join(probe_dir, "probe.txt")
    std_dir = None
    try:
        os.makedirs(probe_dir, exist_ok=False)
        with open(probe_file, "w", encoding="utf-8", newline="\n") as f:
            f.write("ok\n")
        with open(probe_file, encoding="utf-8") as f:
            f.read()

        std_status = "ok"
        std_evidence = []
        try:
            std_dir = tempfile.mkdtemp(prefix="stdlib-temp-probe_", dir=base)
            std_file = os.path.join(std_dir, "probe.txt")
            with open(std_file, "w", encoding="utf-8", newline="\n") as f:
                f.write("ok\n")
            with open(std_file, encoding="utf-8") as f:
                f.read()
        except OSError as exc:
            std_status = "warn"
            std_evidence = ["stdlib tempfile probe failed: %r" % (exc,), rel(std_dir or base)]

        try:
            os.remove(probe_file)
            os.rmdir(probe_dir)
            if std_dir:
                shutil.rmtree(std_dir, ignore_errors=True)
        except OSError:
            pass

        if std_status == "warn":
            return make_check(
                "F-004", "warn", "project tmp-work helper works, but stdlib tempfile is unsafe",
                evidence=[rel(os.path.relpath(base, root))] + std_evidence,
                recipe_hint="Use drivers/test_tmp.py / project-safe os.makedirs helper instead of tempfile.mkdtemp().",
            )
        return make_check("F-004", "ok", "project tmp-work and stdlib tempfile probe are writable", evidence=[rel(os.path.relpath(base, root))])
    except OSError as exc:
        return make_check(
            "F-004", "fail", "project tmp-work probe failed",
            evidence=[repr(exc), rel(probe_dir)],
            recipe_hint="Use drivers/test_tmp.py / project tmp-work after fixing workspace temp permissions.",
        )

def check_runtime_identity():
    return make_check(
        "F-003", "ok", "friction.py is running under Python",
        evidence=[sys.executable, sys.version.split()[0]],
        recipe_hint="If larger commands hang, fall back to short timeout-wrapped checks.",
    )

def check_sandbox_contract():
    required = [
        "docs/external-code-sandbox.md",
        "docs/execute-sandbox-preflight.md",
        "tools/sandbox.py",
        "sandbox/README.md",
    ]
    missing = [p for p in required if not os.path.exists(os.path.join(ROOT, p))]
    if missing:
        return make_check("F-012", "warn", "external-code sandbox contract is incomplete", evidence=missing)
    return make_check("F-012", "ok", "external-code sandbox contract exists", evidence=required)

def check_top_wrapper():
    top_path = os.path.join(ROOT, "tools", "top.py")
    try:
        with open(top_path, encoding="utf-8") as f:
            text = f.read()
    except OSError as exc:
        return make_check("F-014", "warn", "top.py is not readable", evidence=[repr(exc)])
    if "friction" in text:
        return make_check("F-014", "ok", "top-level friction button is available", evidence=["python tools/top.py friction"])
    return make_check("F-014", "warn", "top-level friction button is not wired", evidence=["python tools/friction.py status"])

def check_skill_links():
    path = os.path.join(ROOT, "skills", "repo-friction-playbook", "SKILL.md")
    try:
        with open(path, encoding="utf-8") as f:
            text = f.read()
    except OSError as exc:
        return make_check("F-018", "warn", "repo-friction skill is not readable", evidence=[repr(exc)])
    required = ["docs/friction-ledger.md", "docs/friction-playbook.md", "docs/friction-complaints-suggestions.md", "tools/friction.py"]
    missing = [p for p in required if p not in text]
    if missing:
        return make_check("F-018", "warn", "repo-friction skill misses canonical links", evidence=missing)
    return make_check("F-018", "ok", "repo-friction skill points to canonical docs/tool", evidence=required)

def collect_status(args):
    checks = []
    checks.append(check_runtime_identity())

    git = run_cmd("git", "status", "--short", "--untracked-files=all", timeout=20)
    if git["timeout"]:
        checks.append(make_check("F-003", "fail", "git status timed out", evidence=first_lines(git["out"], 4)))
    else:
        tf = list(getattr(args, "files", None) or [])
        if getattr(args, "task", None):
            tf.append("tasks/%s.md" % args.task)  # карточка моей задачи = mine
        checks.extend(check_git_status(
            git["out"], agent=getattr(args, "agent", None), task_files=tf or None))

    ls = run_cmd("git", "ls-files", "--", *VOLATILE, timeout=20)
    try:
        with open(os.path.join(ROOT, ".gitignore"), encoding="utf-8") as f:
            ignore_text = f.read()
    except OSError:
        ignore_text = ""
    checks.append(check_volatile_tracking(ls["out"], ignore_text))

    gen = run_cmd(PY, os.path.join(ROOT, "tools", "generate.py"), "--check", timeout=45)
    checks.append(check_generate(gen["rc"], gen["out"]))

    lock = run_cmd(PY, os.path.join(ROOT, "tools", "commit_lock.py"), "status", timeout=20)
    checks.append(check_commit_lock(lock["out"]))

    pipe = run_cmd(PY, os.path.join(ROOT, "tools", "pipeline.py"), "status", timeout=30)
    checks.extend(check_pipeline(pipe["out"]))

    drift = run_cmd(PY, os.path.join(ROOT, "tools", "drift_check.py"), timeout=45)
    checks.append(check_drift(drift["rc"], drift["out"]))

    val = run_cmd(PY, os.path.join(ROOT, "tools", "validate.py"), timeout=45)
    checks.append(check_gate_poison(val["rc"], val["out"]))

    stream = run_cmd(PY, os.path.join(ROOT, "tools", "stream.py"), "check", "--max-age-days", str(args.stream_max_age_days), timeout=30)
    checks.append(check_stream(stream["rc"], stream["out"]))

    if args.temp_probe:
        checks.append(check_temp_probe(ROOT))
    else:
        checks.append(make_check("F-004", "info", "temp probe skipped by --no-temp-probe"))

    checks.append(check_sandbox_contract())
    checks.append(check_top_wrapper())
    checks.append(check_skill_links())
    return checks

def recommendation(checks):
    by_id = {}
    for ch in checks:
        by_id.setdefault(ch["id"], []).append(ch)
    fail_ids = {ch["id"] for ch in checks if ch["status"] == "fail"}
    warn_ids = {ch["id"] for ch in checks if ch["status"] == "warn"}

    if fail_ids & {"F-003", "F-004"}:
        return "STOP: fix runtime/temp first, then re-run friction status."
    if warn_ids & {"F-005"}:
        return "WAIT/COORDINATE: commit-lock is not free; do not stage or commit yet."
    if warn_ids & {"F-006", "F-007", "F-011", "F-013", "F-015", "F-020"}:
        return "LEVEL 1 OR SELECTIVE-ADD: dirty/drift/stream/gate-poison signals exist; do not use git add -A."
    if warn_ids & {"F-008", "F-009", "F-010", "F-012", "F-014", "F-018"}:
        return "LEVEL 0 WITH CAUTION: fix listed governance/runtime warnings before commit."
    return "LEVEL 0 OK: shared tree is acceptable; use commit_lock + explicit staging for commits."

def status_payload(args):
    checks = collect_status(args)
    return {"root": ROOT, "recommendation": recommendation(checks), "checks": checks}

def print_status(payload):
    print("FRICTION STATUS")
    print("root: %s" % payload["root"])
    print("recommendation: %s" % payload["recommendation"])
    print("")
    for ch in payload["checks"]:
        mark = ch["status"].upper()
        print("[%s] %s — %s" % (mark, ch["id"], ch["summary"]))
        if ch.get("evidence"):
            for ev in ch["evidence"][:5]:
                print("  evidence: %s" % ev)
        if ch.get("recipe") and ch["status"] in {"warn", "fail"}:
            print("  recipe: %s" % ch["recipe"])
    print("")
    print("Recipes: python tools/friction.py recipe <F-id>")

def resolve_fid(value):
    if not value:
        return None
    key = value.strip().lower()
    return ALIASES.get(key)

def recipe_text(fid):
    item = BY_ID[fid]
    lines = ["# %s — %s" % (item["id"], item["name"]), "", "Symptom: %s" % item["symptom"], "", "Recipe:"]
    for step in item.get("recipe", []):
        lines.append("- %s" % step)
    if item.get("docs"):
        lines.extend(["", "Docs:"])
        for doc in item["docs"]:
            lines.append("- %s" % doc)
    return "\n".join(lines)

def cmd_status(args):
    payload = status_payload(args)
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print_status(payload)
    if args.strict and any(ch["status"] in {"warn", "fail"} for ch in payload["checks"]):
        return 1
    return 0

def cmd_recipe(args):
    fid = resolve_fid(args.id_or_alias)
    if not fid:
        print("Unknown friction id/alias: %s" % args.id_or_alias)
        return 1
    print(recipe_text(fid))
    return 0

def cmd_list(args):
    if args.json:
        print(json.dumps({"friction": REGISTRY}, ensure_ascii=False, indent=2))
        return 0
    print("# Friction registry")
    print("")
    print("| ID | Name | Symptom |")
    print("|---|---|---|")
    for item in REGISTRY:
        print("| %s | %s | %s |" % (item["id"], item["name"], item["symptom"]))
    return 0

FRICTION_LOG = os.path.join(ROOT, "logs", "friction.jsonl")


def _ladder(n):
    """Лестница автоматизации по числу повторов (F-017: data-driven detector→guard)."""
    if n >= 8:
        return "8+ → авто-фикс (SAFE_AUTO)"
    if n >= 6:
        return "6+ → guard (гейт/хук)"
    if n >= 4:
        return "4+ → детектор (tool)"
    if n >= 2:
        return "2-3 → рецепт (recipe)"
    return "1 → разовая заметка"


def cmd_note(args):
    """Записать friction-событие в logs/friction.jsonl (точный лог вместо ручной бухгалтерии)."""
    fid = resolve_fid(args.fid)
    if not fid:
        print("Unknown friction id/alias: %s" % args.fid)
        return 1
    rec = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "fid": fid,
           "agent": args.agent or "—", "where": args.where or "—", "result": args.result or "—"}
    os.makedirs(os.path.dirname(FRICTION_LOG), exist_ok=True)
    with open(FRICTION_LOG, "a", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    print("OK: friction-событие записано (%s @ %s) → logs/friction.jsonl" % (fid, rec["where"]))
    return 0


def _read_friction_log():
    out = []
    if not os.path.exists(FRICTION_LOG):
        return out
    with open(FRICTION_LOG, encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    return out


def cmd_log(args):
    """Показать события + счётчики по F-id с подсказкой ступени автоматизации."""
    import collections
    events = _read_friction_log()
    if args.fid:
        fid = resolve_fid(args.fid) or args.fid
        events = [e for e in events if e.get("fid") == fid]
    if args.json:
        print(json.dumps({"events": events}, ensure_ascii=False, indent=2))
        return 0
    counts = collections.Counter(e.get("fid") for e in events)
    if not counts:
        print("friction-лог пуст. Записывай: python tools/friction.py note <F-id> --where ... --result ...")
        return 0
    print("# Friction event log — счётчики по лестнице автоматизации (logs/friction.jsonl)")
    print("")
    print("| F-id | событий | следующая ступень |")
    print("|---|---|---|")
    for fid, n in counts.most_common():
        print("| %s | %d | %s |" % (fid, n, _ladder(n)))
    return 0


def build_parser():
    parser = argparse.ArgumentParser(description="Diagnose repeated repository friction and print recipes.")
    sub = parser.add_subparsers(dest="cmd")

    p = sub.add_parser("status", help="run read-mostly friction diagnostics")
    p.add_argument("--json", action="store_true")
    p.add_argument("--strict", action="store_true", help="return non-zero if any warning/failure is found")
    p.add_argument("--no-temp-probe", dest="temp_probe", action="store_false")
    p.add_argument("--stream-max-age-days", type=int, default=7)
    p.add_argument("--task", help="мой текущий T-ID — его карточка считается mine (T-153)")
    p.add_argument("--files", nargs="*", help="явные файлы моей задачи → mine (T-153)")
    p.add_argument("--agent", help="кто я (mine vs foreign по claim'ам) (T-153)")
    p.set_defaults(func=cmd_status, temp_probe=True)

    p = sub.add_parser("recipe", help="print one F-XXX recipe")
    p.add_argument("id_or_alias")
    p.set_defaults(func=cmd_recipe)

    p = sub.add_parser("list", help="list known friction archetypes")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_list)

    p = sub.add_parser("note", help="записать friction-событие в logs/friction.jsonl")
    p.add_argument("fid", help="F-id или алиас")
    p.add_argument("--where", help="путь/контекст, где случилось")
    p.add_argument("--result", help="исход (workaround/fixed/blocked/…)")
    p.add_argument("--agent", help="кто записал")
    p.set_defaults(func=cmd_note)

    p = sub.add_parser("log", help="события + счётчики по F-id (лестница автоматизации)")
    p.add_argument("--json", action="store_true")
    p.add_argument("--fid", help="фильтр по F-id")
    p.set_defaults(func=cmd_log)

    return parser

def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    if not hasattr(args, "func"):
        parser.print_help()
        return 2
    return args.func(args)

if __name__ == "__main__":
    sys.exit(main())