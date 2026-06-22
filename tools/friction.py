#!/usr/bin/env python3
# -*- coding: utf-8 -*-
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
import subprocess
import sys
import time

ROOT = os.environ.get("COLLAB_ROOT") or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PY = sys.executable

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
            "Use project tmp-work/ or C:\\tmp for tests.",
            "Prefer drivers/test_tmp.py for hermetic tests.",
            "Do not close runtime acceptance until the project-safe temp path is tested.",
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
            "If you need a specific task, do not call next blindly.",
            "Release only your own mistaken claim if this happens.",
            "Future improvement: pipeline.py claim <agent> <T-id> or top.py take <agent> <T-id>.",
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
]

BY_ID = {item["id"]: item for item in REGISTRY}
ALIASES = {}
for item in REGISTRY:
    ALIASES[item["id"].lower()] = item["id"]
    for alias in item.get("aliases", []):
        ALIASES[alias.lower()] = item["id"]


def configure_output():
    for name in ("stdout", "stderr"):
        stream = getattr(sys, name, None)
        if stream is not None and hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")


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


def check_git_status(status_text):
    rows = git_status_paths(status_text)
    dirty = [r["raw"] for r in rows]
    nonvolatile = [r["raw"] for r in rows if not path_matches(r["path"], VOLATILE)]
    volatile = [r["raw"] for r in rows if path_matches(r["path"], VOLATILE)]
    generated = [r["raw"] for r in rows if path_matches(r["path"], GENERATED_SHARED)]

    checks = []
    if nonvolatile:
        checks.append(make_check(
            "F-006", "warn", "shared tree has non-volatile uncommitted files",
            evidence=nonvolatile[:8],
            recipe_hint="Use selective-add only; consider Level 1 worktree if these files are foreign or contested.",
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


def check_stream(rc, out):
    text = out or ""
    if rc != 0:
        return make_check("F-013", "warn", "stream lifecycle check reports stale/broken streams", evidence=first_lines(text, 8))
    return make_check("F-013", "ok", "stream lifecycle check is clean", evidence=first_lines(text, 2))


def check_temp_probe(root=ROOT):
    base = os.path.join(root, "tmp-work")
    probe_dir = os.path.join(base, "friction-probe-%d-%d" % (int(time.time()), os.getpid()))
    probe_file = os.path.join(probe_dir, "probe.txt")
    try:
        os.makedirs(probe_dir, exist_ok=False)
        with open(probe_file, "w", encoding="utf-8", newline="\n") as f:
            f.write("ok\n")
        with open(probe_file, encoding="utf-8") as f:
            f.read()
        try:
            os.remove(probe_file)
            os.rmdir(probe_dir)
        except OSError:
            pass
        return make_check("F-004", "ok", "project tmp-work is writable", evidence=[rel(os.path.relpath(base, root))])
    except OSError as exc:
        return make_check(
            "F-004", "fail", "project tmp-work probe failed",
            evidence=[repr(exc), rel(probe_dir)],
            recipe_hint="Set TEMP/TMP/TMPDIR to project tmp-work or use C:\\tmp before running tests.",
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
        checks.extend(check_git_status(git["out"]))

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
    if warn_ids & {"F-006", "F-007", "F-011", "F-013", "F-015"}:
        return "LEVEL 1 OR SELECTIVE-ADD: dirty/drift/stream signals exist; do not use git add -A."
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


def build_parser():
    parser = argparse.ArgumentParser(description="Diagnose repeated repository friction and print recipes.")
    sub = parser.add_subparsers(dest="cmd")

    p = sub.add_parser("status", help="run read-mostly friction diagnostics")
    p.add_argument("--json", action="store_true")
    p.add_argument("--strict", action="store_true", help="return non-zero if any warning/failure is found")
    p.add_argument("--no-temp-probe", dest="temp_probe", action="store_false")
    p.add_argument("--stream-max-age-days", type=int, default=7)
    p.set_defaults(func=cmd_status, temp_probe=True)

    p = sub.add_parser("recipe", help="print one F-XXX recipe")
    p.add_argument("id_or_alias")
    p.set_defaults(func=cmd_recipe)

    p = sub.add_parser("list", help="list known friction archetypes")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_list)

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