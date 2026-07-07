# ast: allow-subprocess
#!/usr/bin/env python3
# [FILE ID CARD]
# id: tools/worktree_gate.py
# purpose: Гейт worktree-изоляции — детектит «коммит в общий main при высокой одновременности»
#          и направляет в worktree. Advisory сейчас; BLOCK после ратификации (паттерн bulk_guard).
# inputs: текущая ветка (git) + свежие claim'ы (queues/claimed) как сигнал одновременности
# outputs: вердикт SHARED-BUSY/OK; exit 0 (ок/advisory) / 1 (блок при ратификации)
# mode: read-only; ничего не пишет, не мутирует
# related: D-022 (worktree Ур.1), D-036 (эстафета), T-274 (tripwire), flow.py, commit.py,
#          worktree-isolation-enforcement-2026-07-07
"""worktree_gate.py — направляет агентов в worktree при высокой одновременности.

Мотив: агенты работают на общем дереве + main; 3+ параллельных тяжёлых validate насыщают
машину (reports/machine-saturation-diagnosis-2026-07-07.md). Механизм изоляции есть
(flow.py --worktree, D-022), но не используется — документация не связывает. Гейт ставит
правило в choke point (путь коммита) и делает его СОРАЗМЕРНЫМ: срабатывает только при
одновременности ≥ порога.

Условная строгость (как bulk_guard/D-026): пока правило proposed — WARN (exit 0, советник);
после ратификации решения о обязательном worktree — BLOCK (exit 1) на «общий main + N≥порог».

Команды:
  python tools/worktree_gate.py check [--json]   # вердикт (advisory)
  python tools/worktree_gate.py --hook           # для commit.py/pre-commit: условный exit-код
Пороги: SHARED-ветки {main, master}; порог одновременности N (по умолчанию 3 = точка насыщения).
"""
from __future__ import annotations
import json
import os
import re
import subprocess
import sys
import time

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

SHARED_BRANCHES = {"main", "master"}
CONCURRENCY_THRESHOLD = 3          # Гейт A: ≥ N одновременных → worktree обязателен (точка насыщения)
MACHINE_SLOTS = 3                  # Гейт B: CAP тяжёлых агентов ≈ ядра−запас; лишние — в очередь
FRESH_CLAIM_SECONDS = 20 * 60      # claim считается «свежим» (агент активен) в пределах 20 мин
# Решение, ратификация которого превращает WARN→BLOCK (пока такого нет — гейт advisory).
RATIFY_DECISION = "D-039"          # placeholder: «worktree обязателен при N≥порог» (см. котёл §6 доки)
ROOT = os.getcwd()


def _run(args):
    try:
        return subprocess.run(args, capture_output=True, text=True, encoding="utf-8",
                              errors="replace", timeout=15)
    except (OSError, subprocess.SubprocessError):
        return None


def current_branch():
    r = _run(["git", "rev-parse", "--abbrev-ref", "HEAD"])
    if not r or r.returncode != 0:
        return None
    return r.stdout.strip()


def active_agents(root=None):
    """Свежие claim'ы в queues/claimed/ как прокси одновременности (быстро, без git log)."""
    root = root or ROOT
    d = os.path.join(root, "queues", "claimed")
    if not os.path.isdir(d):
        return 0
    now = time.time()
    n = 0
    try:
        for name in os.listdir(d):
            if not name.endswith(".md"):
                continue
            try:
                if now - os.path.getmtime(os.path.join(d, name)) <= FRESH_CLAIM_SECONDS:
                    n += 1
            except OSError:
                pass
    except OSError:
        return 0
    return n


def _decision_accepted(did, root=None):
    root = root or ROOT
    p = os.path.join(root, "decisions", "%s.md" % did)
    try:
        txt = open(p, encoding="utf-8", errors="replace").read(2000)
        m = re.search(r"^status:\s*(.+)$", txt, re.M)
        return bool(m) and m.group(1).strip().lower() == "accepted"
    except OSError:
        return False


def evaluate(root=None):
    """Вердикт: ('SHARED-BUSY'|'OK'|'ISOLATED'|'UNKNOWN', branch, n_active)."""
    root = root or ROOT
    branch = current_branch()
    n = active_agents(root)
    if branch is None:
        return "UNKNOWN", branch, n           # git недоступен — fail-open
    if branch not in SHARED_BRANCHES:
        return "ISOLATED", branch, n          # уже в worktree/agent-ветке — хорошо
    if n >= CONCURRENCY_THRESHOLD:
        return "SHARED-BUSY", branch, n       # общий main + высокая одновременность — нужен worktree
    return "OK", branch, n


def hook_rc(verdict, ratified):
    """Чистая логика --hook (тестируемо): BLOCK (1) только SHARED-BUSY И ратифицировано."""
    return 1 if (verdict == "SHARED-BUSY" and ratified) else 0


def _advice(branch, n):
    msg = (
        "⚠ Высокая одновременность: %d активных агентов, а ты коммитишь в общий '%s'.\n"
        "  [Гейт A] Работай изолированно — машина не грузится, чужую работу не тронешь,\n"
        "  и пишешь СВОЮ версию независимо (independent-first D-028):\n"
        "    python tools/flow.py start <agent> <T-id> --worktree\n"
        "  затем — быстрый selective-merge готового. (D-022 Ур.1)" % (n, branch)
    )
    if n > MACHINE_SLOTS:
        msg += (
            "\n  [Гейт B] Агентов больше слотов машины (%d > %d) — worktree НЕ снимет перегрузку "
            "CPU.\n  Встань в ОЧЕРЕДЬ: заверши/освободи слот или подожди, пока освободится "
            "(work_admission / pipeline cap)." % (n, MACHINE_SLOTS)
        )
    msg += "\n  Детали: docs/worktree-isolation-enforcement-2026-07-07.md"
    return msg


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    as_json = "--json" in argv
    hook = "--hook" in argv
    verdict, branch, n = evaluate(ROOT)
    ratified = _decision_accepted(RATIFY_DECISION)

    if as_json:
        print(json.dumps({"verdict": verdict, "branch": branch, "active_agents": n,
                          "threshold": CONCURRENCY_THRESHOLD, "ratified": ratified},
                         ensure_ascii=False))
        return hook_rc(verdict, ratified) if hook else (1 if verdict == "SHARED-BUSY" else 0)

    if verdict == "SHARED-BUSY":
        print(_advice(branch, n))
        if hook:
            rc = hook_rc(verdict, ratified)
            if rc == 1:
                print("worktree_gate: коммит в общий main при N≥%d отклонён (ратифицировано %s)."
                      % (CONCURRENCY_THRESHOLD, RATIFY_DECISION))
            else:
                print("worktree_gate: advisory (правило %s не ратифицировано — пока не блокирует)."
                      % RATIFY_DECISION)
            return rc
        return 1
    if verdict == "ISOLATED":
        print("worktree_gate: OK — ты в изолированной ветке '%s' (не общий main)." % branch)
    elif verdict == "OK":
        print("worktree_gate: OK — одновременность %d < порога %d, общий main допустим."
              % (n, CONCURRENCY_THRESHOLD))
    else:
        print("worktree_gate: git недоступен — проверка пропущена (fail-open).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
