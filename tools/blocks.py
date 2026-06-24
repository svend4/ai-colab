"""blocks.py — сборные БЛОКИ (кластеры проверенных примитивов) вместо россыпи скриптов.

Adoption-вывод (`topics/adoption-statistics-2026-06-23.md`): проверенные подсистемы работают,
но применяются россыпью («стройматериалы»). БЛОК = одна команда запускает кластер проверенных
tools **параллельно** и сводит в единый вердикт — собранная, переиспользуемая, автоматическая
единица для работы над ошибками/кодом/доками и рекурсивного само-улучшения.

CLI:
    python tools/blocks.py list                 # реестр блоков
    python tools/blocks.py audit [--json] [--seq]   # запустить блок самопроверки
    python tools/blocks.py run <block> [--json] [--seq] [--auto-safe]

Блок `audit` кластеризует: validate + generate --check (gate) + friction/assurance/reconcile/drift
(advisory). Gate-шаг с rc!=0 валит блок (exit 1); advisory только считаются. По умолчанию — параллельно.

Флаг `--auto-safe` (пока применяется в основном с `improve`) автоматически запускает
ратифицированные обратимые фиксы (SAFE_AUTO_RULES) если обнаружены проблемы.
"""
import os
from _ioutil import configure_output
import sys
import json
import threading
import subprocess
# NB: сырые threading.Thread (не concurrent.futures). Историческая причина — tools/queue.py
# затенял stdlib `queue`, ломая ThreadPoolExecutor из tools/; устранено переименованием в
# agent_queue.py (ретро-improve), threading.Thread оставлен как рабочий и достаточный.

configure_output()
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

# Блоки = кластеры проверенных примитивов. kind: gate (rc решает вердикт) | advisory (собираем, не валим).
BLOCKS = {
    "audit": {
        "desc": "самопроверка: проверенные детекторы параллельно → единый вердикт (над ошибками)",
        "steps": [
            ("validate.py", [], "gate"),
            ("generate.py", ["--check"], "gate"),
            ("friction.py", ["status"], "advisory"),
            ("assurance.py", [], "advisory"),
            ("reconcile_state.py", ["check"], "advisory"),
            ("drift_check.py", [], "advisory"),
            ("test_execute_audit.py", [], "gate"),
        ],
    },
    "adoption": {
        "desc": "само-мониторинг применения: dormant-инструменты + doc-only решения + orphan-доки",
        "steps": [
            ("adoption.py", [], "advisory"),
        ],
    },
    "self": {
        "desc": "рекурсивная самопроверка: audit (над ошибками) + adoption (над применением) вместе",
        "steps": [
            ("validate.py", [], "gate"),
            ("generate.py", ["--check"], "gate"),
            ("friction.py", ["status"], "advisory"),
            ("assurance.py", [], "advisory"),
            ("adoption.py", [], "advisory"),
            ("metrics.py", [], "advisory"),
        ],
    },
    "improve": {
        "desc": "петля само-улучшения: adoption(применение)+audit(дефекты)+propagation(решения→исполнение) → вход роутеру",
        "steps": [
            ("adoption.py", ["--json"], "advisory"),
            ("friction.py", ["status"], "advisory"),
            ("assurance.py", [], "advisory"),
            ("drift_check.py", [], "advisory"),
            ("decision_propagation.py", [], "advisory"),
            ("validate.py", [], "gate"),
            ("generate.py", ["--check"], "gate"),
        ],
    },
    "propagation": {
        "desc": "решения→потребители: ловит «решение принято, но не дошло до исполнения» (корень svend4-провала)",
        "steps": [
            ("decision_propagation.py", [], "advisory"),
        ],
    },
    "pyramid": {
        "desc": "здоровье пирамиды L4->L1: assurance(coverage/flow) + promote/portal инвентарь -> единый вердикт (над структурой)",
        "steps": [
            ("assurance.py", ["coverage", "--strict"], "gate"),
            ("assurance.py", ["flow", "--strict"], "gate"),
            ("promote.py", ["list"], "advisory"),
            ("portal.py", ["list"], "advisory"),
        ],
    },
    "execute-preflight": {
        "desc": "preflight-гейты для sandbox (P3, P5, P9): проверки изоляции до первого execute",
        "steps": [
            ("execute_preflight.py", ["check-probe"], "gate"),
        ],
    },
    "structure": {
        "desc": "здоровье структуры (консенсус C-07/C-10/C-11/layered-pyramid): папки + визитки + слои L1-L4 + heading-дерево",
        "steps": [
            ("dir_health.py", [], "advisory"),
            ("header.py", ["board"], "advisory"),
            ("layer_check.py", [], "advisory"),
            ("heading_check.py", [], "advisory"),
            ("folder_index.py", ["check-all"], "advisory"),
        ],
    },
}

# Реестр безопасных авто-исправлений (SAFE_AUTO), применяемых при --auto-safe
# Только идемпотентные и полностью обратимые (derived) операции.
SAFE_AUTO_RULES = [
    ("generate.py", [], "Восстановление индексов (TASKS, STATUS, board, index.json)"),
    ("reconcile_state.py", ["fix", "--apply"], "Синхронизация derived-данных и snapshot"),
    ("stream.py", ["archive", "--apply"], "Архивация заброшенных (stale) streams"),
]


def _run_step(step):
    tool, args, kind = step
    path = os.path.join(HERE, tool)
    if not os.path.exists(path):
        return {"tool": tool, "kind": kind, "rc": None, "skipped": True, "tail": "(нет файла)"}
    env = dict(os.environ, PYTHONUTF8="1")
    try:
        p = subprocess.run([sys.executable, path] + args, cwd=ROOT, env=env,
                           capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=180)
        out = ((p.stdout or "") + (p.stderr or "")).strip()
        tail = "\n".join(out.splitlines()[-3:])
        return {"tool": tool, "kind": kind, "rc": p.returncode, "skipped": False, "tail": tail}
    except subprocess.TimeoutExpired:
        return {"tool": tool, "kind": kind, "rc": 124, "skipped": False, "tail": "(timeout)"}


def run_block(name, parallel=True):
    """Запустить блок: кластер шагов (параллельно по умолчанию) → агрегат-вердикт."""
    blk = BLOCKS[name]
    steps = blk["steps"]
    if parallel and len(steps) > 1:
        results = [None] * len(steps)

        def _worker(i, s):
            results[i] = _run_step(s)

        threads = [threading.Thread(target=_worker, args=(i, s)) for i, s in enumerate(steps)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
    else:
        results = [_run_step(s) for s in steps]
    gates = [r for r in results if r["kind"] == "gate" and not r["skipped"]]
    gates_passed = all(r["rc"] == 0 for r in gates)
    advisory_flags = sum(1 for r in results
                         if r["kind"] == "advisory" and not r["skipped"] and r["rc"] not in (0, None))
    return {"block": name, "gates_passed": gates_passed,
            "advisory_flags": advisory_flags, "steps": results}


def cmd_list():
    print("Доступные БЛОКИ (кластеры проверенных примитивов):")
    for n, b in BLOCKS.items():
        print("  %-10s — %s  (%d шагов)" % (n, b["desc"], len(b["steps"])))
    return 0


def cmd_run(name, as_json=False, parallel=True, auto_safe=False):
    if name not in BLOCKS:
        print("нет блока %r; доступны: %s" % (name, ", ".join(BLOCKS)))
        return 2
    res = run_block(name, parallel=parallel)
    
    if auto_safe and (not res["gates_passed"] or res["advisory_flags"] > 0):
        if not as_json:
            print("\n=== AUTO-SAFE APPLY ===")
            print("Обнаружены проблемы, применяются безопасные авто-исправления (SAFE_AUTO_RULES)...")
        safe_results = []
        for tool, args, desc in SAFE_AUTO_RULES:
            r = _run_step((tool, args, "auto"))
            safe_results.append((desc, r))
            if not as_json:
                mark = "OK" if r["rc"] == 0 else "rc=%s" % r["rc"]
                print("  [auto    ] %-22s %s" % (tool, mark))
        
        # Перепроверяем после авто-исправлений
        if not as_json:
            print("Перепроверка после auto-safe...")
        res = run_block(name, parallel=parallel)

    if as_json:
        print(json.dumps(res, ensure_ascii=False, indent=2))
    else:
        mode = "параллельно" if parallel else "последовательно"
        print("=== БЛОК %s (%s) ===" % (name, mode))
        for r in res["steps"]:
            if r["skipped"]:
                mark = "skip"
            elif r["rc"] == 0:
                mark = "OK"
            else:
                mark = "rc=%s" % r["rc"]
            print("  [%-8s] %-22s %s" % (r["kind"], r["tool"], mark))
        verdict = "BLOCK-OK" if res["gates_passed"] else "BLOCK-FAIL (gate rc!=0)"
        print("\nВердикт: %s; advisory-флагов: %d" % (verdict, res["advisory_flags"]))
        if auto_safe:
            print("Остальные PRIMARY/governance проблемы оставлены для решения человеку.")
    return 0 if res["gates_passed"] else 1


def main(argv):
    args = list(argv)
    as_json = "--json" in args
    parallel = "--seq" not in args
    auto_safe = "--auto-safe" in args
    pos = [a for a in args if not a.startswith("--")]
    if not pos or pos[0] == "list":
        return cmd_list()
    cmd = pos[0]
    if cmd == "run" and len(pos) >= 2:
        return cmd_run(pos[1], as_json=as_json, parallel=parallel, auto_safe=auto_safe)
    # сокращение: `blocks.py audit` == `blocks.py run audit`
    return cmd_run(cmd, as_json=as_json, parallel=parallel, auto_safe=auto_safe)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
